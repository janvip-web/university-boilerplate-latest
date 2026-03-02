from typing import Annotated, List, Optional
from uuid import UUID
import io

from fastapi import APIRouter, Body, Depends, Path, Request, dependencies, status, Query
from fastapi.responses import JSONResponse, StreamingResponse

import constants
from apps.user.models.user import UserModel
from apps.user.schemas.request import EncryptedRequest, CreateUserRequest
from apps.user.schemas.response import BaseUserResponse
from apps.user.services import UserService
from core.auth import HasPermission
from core.types import RoleType
from core.utils.schema import BaseResponse
from core.utils.set_cookies import set_auth_cookies
import jwt
from config import settings
from apps.course.schemas.response import StudentCourseResponse, CourseResponse

router = APIRouter(prefix="/api/user", tags=["User"])


@router.post(
    "/sign-in",
    status_code=status.HTTP_200_OK,
)
async def sign_in(
    request: Request,
    body: Annotated[EncryptedRequest, Body()],
    service: Annotated[UserService, Depends()],
) -> JSONResponse:
    """
    Authenticate a user and issue authentication tokens.

    This endpoint handles user login with encrypted credentials, returning
    access and refresh tokens and setting appropriate cookies on success.

    Args:
        request: The FastAPI request object.
        body: EncryptedRequest containing login credentials.
        service: UserService instance for business logic.

    Returns:
        JSONResponse: Response containing auth tokens and cookies.

    Raises:
        InvalidCredentialsException: If login credentials are invalid.
        BadRequestError: If required fields are missing.
    """
    res = await service.login_user(request=request, **body.model_dump())

    if "access_token" in res and res.get("access_token"):
        access_token = res["access_token"]

        # 🔥 Decode token directly here
        payload = jwt.decode(
            access_token,
            settings.JWT_SECRET_KEY,
            algorithms=settings.JWT_ALGORITHM,
        )

        role = payload.get("role")   

        data = {
            "status": constants.SUCCESS,
            "code": status.HTTP_200_OK,
            "data": res,
        }

        response = JSONResponse(content=data)

        return set_auth_cookies(response, res, role=role)


@router.get(
    "/self",
    status_code=status.HTTP_200_OK,
    name="get self",
    description="Get Self",
    operation_id="get_self",
)
async def get_self_handler(
    user: Annotated[UserModel, Depends(HasPermission(role_name=["STUDENT", "FACULTY"]))],
    service: Annotated[UserService, Depends()],
) -> BaseResponse[BaseUserResponse]:
    """
    Retrieve profile information of the authenticated user.

    Args:
        user: Authenticated user model injected by the permission dependency.
        service: UserService instance for business logic.

    Returns:
        BaseResponse[BaseUserResponse]: The authenticated user's profile data.

    Raises:
        HasPermission: If the user lacks the required roles.
    """
    # print("INSIDE SELF API")
    return BaseResponse(data=await service.get_self(user_id=user.id))

@router.get(
    "/student/my-courses",
    status_code=status.HTTP_200_OK,
    name="Get my courses",          
    description="Get my courses",
    operation_id="get_my_courses",
    # dependencies=[Depends(HasPermission(role_name="STUDENT"))]
)
async def get_my_courses(
    service: Annotated[UserService , Depends()],
    current_user: Annotated[UserModel, Depends(HasPermission(role_name=["STUDENT","FACULTY"]))]
)-> List[StudentCourseResponse]:
    """
    Get the courses associated with the current user.

    This endpoint returns all courses the authenticated student or faculty member is
    enrolled in or teaching.

    Args:
        service: UserService instance for business logic.
        current_user: The authenticated user model.

    Returns:
        List[StudentCourseResponse]: A list of course responses for the user.

    Raises:
        HasPermission: If user does not have student or faculty role.
    """
    return await service.get_my_courses(current_user.id)

@router.get(
    "/export",
    status_code=status.HTTP_200_OK,
    name = "Export my courses to Excel",
    description="Download course data as an excel file",
    operation_id="export_my_courses"
)
async def export_my_courses(
    service: Annotated[UserService, Depends()],
    current_user: Annotated[UserModel, Depends(HasPermission(role_name=["STUDENT","FACULTY"]))]
)-> StreamingResponse:
    """
    Export the user's courses to an Excel file.

    A spreadsheet containing all courses for the authenticated user is generated
    and streamed back as an ``.xlsx`` file.

    Args:
        service: UserService instance for business logic.
        current_user: The authenticated user model.

    Returns:
        StreamingResponse: The Excel workbook as a downloadable stream.

    Raises:
        HasPermission: If user lacks the required role.
    """
    data = await service.export_my_courses(current_user.id)
    fname = "my_courses.xlsx"

    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={fname}"}
    )

@router.patch(
    "/change-password",
    name="change user password",
    description="Change user Password",
    operation_id="change_user_password",
    status_code=status.HTTP_200_OK,
)
async def change_password(
    request: Request,
    user: Annotated[UserModel, Depends(HasPermission(role_name=["STUDENT","FACULTY"]))],
    body: Annotated[EncryptedRequest, Body()],
    service: Annotated[UserService, Depends()],
) -> BaseResponse[BaseUserResponse]:
    """
    Change the password for the authenticated user.

    This endpoint allows students or faculty to update their account password.
    The request must include the current password for verification and a new
    password that meets security requirements.

    Args:
        request: The FastAPI request object
        user: Authenticated user model from token
        body: EncryptedRequest containing current and new passwords
        service: UserService instance for business logic

    Returns:
        BaseResponse[BaseUserResponse]: Updated user data

    Raises:
        InvalidCredentialsException: If current password is incorrect
        WeakPasswordException: If new password doesn't meet requirements
        UserNotFoundException: If user is not found
        HasPermission: If user lacks the required role
    """
    return BaseResponse(
        data=await service.change_password(
            request=request, **body.model_dump(), user=user.id
        )
    )

@router.get(
    "/search-course",
    name="search course",
    description="search course based on course name",
    operation_id="search_course",
    status_code=status.HTTP_200_OK
)
async def search_course(
    search: Annotated[str, Query()],
    service: Annotated[UserService, Depends()]
)-> BaseResponse[List[CourseResponse]]:
    """
    Search for courses by name.

    Args:
        search: Query string to search in course names.
        service: UserService instance for business logic.

    Returns:
        BaseResponse[List[CourseResponse]]: A list of matching courses.

    Raises:
        BadRequestError: If search term is empty or invalid.
    """
    return BaseResponse(
        data = await service.search_course(search=search)
    )

@router.get(
    "/recent-courses",
    status_code=200,
    name="Recently Added Courses",
    description="Get latest courses excluding enrolled ones",
    operation_id="get_recent_courses",
    # dependencies=[Depends(HasPermission(role_name="STUDENT"))]
)
async def get_recent_courses(
    service: Annotated[UserService, Depends()],
    current_user: Annotated[UserModel, Depends(HasPermission(role_name=["STUDENT", "FACULTY"]))],
    limit: Annotated[int, Query()] = 5
) -> List[StudentCourseResponse]:
    """
    Fetch the most recently added courses not yet enrolled by the user.

    Args:
        service: UserService instance for business logic.
        current_user: The authenticated user model.
        limit: Maximum number of courses to return (default 5).

    Returns:
        List[StudentCourseResponse]: Recent course list for the user.

    Raises:
        HasPermission: If the user lacks appropriate role.
    """
    return await service.get_recent_course(
        user_id=current_user.id,
        limit=limit
    )

