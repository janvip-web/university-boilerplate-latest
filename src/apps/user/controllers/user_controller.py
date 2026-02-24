from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, Request, status
from fastapi.responses import JSONResponse

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
from apps.course.schemas.response import StudentCourseResponse

router = APIRouter(prefix="/api/user", tags=["User"])


# @router.post(
#     "/sign-in",
#     status_code=status.HTTP_200_OK,
#     name="sign-in",
#     description="sign-in",
#     operation_id="sign_in",
# )
# async def sign_in(
#     request: Request,
#     body: Annotated[EncryptedRequest, Body()],
#     service: Annotated[UserService, Depends()],
# ) -> JSONResponse:
#     """
#     Log in a user using email and password.

#     Args:
#         body (UserLoginRequest): The request object containing login information.
#         service (AuthService): The authentication service.

#     Returns:
#         Response: The response with authentication cookies set.
#     """

#     res = await service.login_user(request=request, **body.model_dump())
#     if "access_token" in res and res.get("access_token"):
#         data = {"status": constants.SUCCESS, "code": status.HTTP_200_OK, "data": res}
#         response = JSONResponse(content=data)
#         # print(res.get("role_id"))
#         return set_auth_cookies(response, res, role_id=res.get("role_id"))

@router.post(
    "/sign-in",
    status_code=status.HTTP_200_OK,
)
async def sign_in(
    request: Request,
    body: Annotated[EncryptedRequest, Body()],
    service: Annotated[UserService, Depends()],
) -> JSONResponse:

    res = await service.login_user(request=request, **body.model_dump())

    if "access_token" in res and res.get("access_token"):
        access_token = res["access_token"]

        # 🔥 Decode token directly here
        payload = jwt.decode(
            access_token,
            settings.JWT_SECRET_KEY,
            algorithms=settings.JWT_ALGORITHM,
        )

        role_id = payload.get("role_id")   # 👈 Extract role_id

        data = {
            "status": constants.SUCCESS,
            "code": status.HTTP_200_OK,
            "data": res,
        }

        response = JSONResponse(content=data)

        return set_auth_cookies(response, res, role_id=role_id)

# @router.post(
#     "",
#     status_code=status.HTTP_201_CREATED,
#     name="Create user",
#     description="Create user",
#     operation_id="create_user",
#     deprecated=True
# )
# async def create_user(
#     request: Request,
#     body: Annotated[CreateUserRequest, Body()],
#     service: Annotated[UserService, Depends()],
# ) -> BaseResponse[BaseUserResponse]:
#     """
#     Create a new user.

#     Args:
#         body (CreateUserRequest): The request object containing user information.
#         service (AuthService): The authentication service.

#     Returns:
#         BaseResponse[BaseUserResponse]: The response containing the created user information.
#     """
#     return BaseResponse(
#         data=await service.create_user(request=request, **body.model_dump())
#     )


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
    
    print("INSIDE SELF API")
    """
    Get data for a user.

    Args:
        user (UserModel): The authenticated user.
        service (AuthService): The authentication service.

    Returns:
        dict[str, Any]: The response containing the user data.
    """
    return BaseResponse(data=await service.get_self(user_id=user.id))


# @router.get(
#     "/{user_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(HasPermission(role_name=["STUDENT", "FACULTY"]))],
#     name="get user by id",
#     description="Get User By Id",
#     operation_id="get_user_by_id",
#     deprecated=True
# )
# async def get_user_by_id(
#     user_id: Annotated[UUID, Path()], service: Annotated[UserService, Depends()]
# ) -> BaseResponse[BaseUserResponse]:
#     """
#     Get data for a user by ID.

#     Args:
#         user_id (int): The ID of the user.
#         service (AuthService): The authentication service.

#     Returns:
#         dict[str, Any]: The response containing the user data.
#     """
#     return BaseResponse(data=await service.get_user_by_id(user_id=user_id))

# router.put(
#     "/{user_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(HasPermission(role_name=["STUDENT", "FACULTY"]))],
#     name="update user by id",
#     description="Update User By Id",
#     operation_id="update_user_by_id",
# )
# async def update_user_by_id(
#     user_id: Annotated[UUID, Path()], service: Annotated[UserService, Depends()]
# ) -> BaseResponse[BaseUserResponse]:

#     return BaseResponse(data=await service.update_user_by_id(user_id=user_id))


# @router.delete(
#     "/{user_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(HasPermission(role_name=["STUDENT", "FACULTY"]))],
#     name="delete user by id",
#     description="delete user by id",
#     operation_id="delete_user_by_id",
#     deprecated=True
# )
# async def delete_user_by_id(
#     user_id: Annotated[UUID, Path()],
#     service: Annotated[UserService, Depends()]
# ) -> BaseResponse[BaseUserResponse]:
#     deleted_user = await service.delete_user_by_id(user_id=user_id)
#     return BaseResponse(data=deleted_user)


# @router.delete(
#     "/{user_id}",
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(HasPermission(role_name=[""]))],
#     name="soft delete user by id",
#     description="soft delete user by id",
#     operation_id="soft_delete_user_by_id",
# )
# async def soft_delete_user_by_id(
#     user_id: Annotated[UUID, Path()],
#     service: Annotated[UserService, Depends()]
# ) -> BaseResponse[BaseUserResponse]:
#     deleted_user = await service.soft_delete_user_by_id(user_id=user_id)
#     return BaseResponse(data=deleted_user)

@router.get(
    "/student/my-courses",
    status_code=status.HTTP_200_OK,
    name="Get my courses",          
    description="Get my courses",
    operation_id="get_my_courses",
    dependencies=[Depends(HasPermission(role_name="STUDENT"))]
)
async def get_my_courses(
    service: Annotated[UserService , Depends()],
    current_user: Annotated[UserModel, Depends(HasPermission(role_name="STUDENT"))]
)-> List[StudentCourseResponse]:
    return await service.get_my_courses(current_user.id)

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
    Change the password for the authenticated admin user.

    This endpoint allows admins to update their password. The request must
    include the current password for verification and a new password that
    meets security requirements.

    Args:
        request: The FastAPI request object
        user: Authenticated admin user from token
        body: Encrypted request containing current and new passwords
        service: AdminUserService instance for business logic

    Returns:
        BaseResponse[BaseUserResponse]: Updated admin user data

    Raises:
        InvalidCredentialsException: If current password is incorrect
        WeakPasswordException: If new password doesn't meet requirements
        UserNotFoundException: If user is not found
        AdminHasPermission: If user doesn't have admin permissions
    """
    return BaseResponse(
        data=await service.change_password(
            request=request, **body.model_dump(), user=user.id
        )
    )