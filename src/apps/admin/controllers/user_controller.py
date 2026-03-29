from typing import Annotated, Optional, List
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, Request, status, Query, UploadFile, File
from fastapi_pagination import Page, Params


from apps.admin.schemas.admin_user_response import AdminListUsersResponse
from apps.admin.schemas.assign_faculty_request import AssignFacultyRequest
from apps.course.schemas.filter import Language
from apps.user.schemas.request import EncryptedRequest, CreateUserRequest
from apps.user.schemas.response import BaseUserResponse
from apps.admin.services import AdminUserService
from core.auth import AdminHasPermission
from core.utils.schema import BaseResponse
from apps.admin.schemas.student_course_response import StudentWithCourseResponse, FacultyCourseResponse, StudentRankResponse


router = APIRouter(prefix="/admin/user", tags=["User Control by Admin"], dependencies=[Depends(AdminHasPermission())])

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    name="Create user by admin",
    description="Create user by admin",
    operation_id="create_user_by_admin",
)
async def create_user(
    # admin: Annotated[UserModel, Depends(AdminHasPermission())],
    request: Request,
    body: Annotated[CreateUserRequest, Body()],
    service: Annotated[AdminUserService, Depends()],
) -> BaseResponse:
    """
    Create a new user.

    This endpoint allows admins to create a new user with user information
    such as email, password, first name, last name, phone number, user role and user's preferred language.

    Args:
        request: The FastAPI request object
        body: CreateUserRequest containing user information
        service: AdminUserService instance for business logic

    Returns:
        BaseResponse[BaseUserResponse]: Response containing the created user information

    Raises:
        DuplicateEmailException: If a user with the given email already exists
        BadRequestError: If required fields are missing or invalid
        AdminHasPermission: If user doesn't have admin permissions
    """
    return BaseResponse(
        data=await service.create_user(request=request, **body.model_dump())
    )

@router.put(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    name="Update user admin side",
    description="Update user admin side",
    operation_id="update_user_admin_side",
)
async def update_user(
    user_id: UUID,
    request: Request,
    body: Annotated[EncryptedRequest, Body()],
    service: Annotated[AdminUserService, Depends()],
) -> BaseResponse:
    """
    Update an existing user's information.

    This endpoint allows admins to modify user details such as first name, last name,
    phone number, and preferred language.

    Args:
        user_id: The UUID of the user to update
        request: The FastAPI request object
        body: EncryptedRequest containing updated user information
        service: AdminUserService instance for business logic

    Returns:
        BaseResponse[BaseUserResponse]: Response containing the updated user information

    Raises:
        UserNotFoundException: If the user with the given UUID is not found
        BadRequestError: If required fields are missing or invalid
        AdminHasPermission: If user doesn't have admin permissions
    """
    return BaseResponse(
        data=await service.update_user(user_id=user_id, request=request, **body.model_dump())
    )


@router.get(
    "/users",
    status_code=status.HTTP_200_OK,
    name="Admin get all users",
    description="Admin get all users",
    operation_id="admin_get_users",
)
async def get_users(
    page_params: Annotated[Params, Depends()],
    service: Annotated[AdminUserService, Depends()],
    role_id: Optional[int] = Query(default=None),
) -> BaseResponse[Page[AdminListUsersResponse]]:
    """
    Retrieve a paginated list of all users for admin management.

    This endpoint allows administrators to view all registered users with
    pagination support. Only admin users can access this endpoint.

    Args:
        page_params: Pagination parameters (page size, page number)
        service: AdminUserService instance for business logic

    Returns:
        BaseResponse[Page[AdminListUsersResponse]]: Paginated list of users

    Raises:
        AdminHasPermission: If user doesn't have admin permissions
    """
    return BaseResponse(data=await service.get_users(params=page_params, role_id=role_id))

@router.get(
    "/students-with-courses",  
    status_code=status.HTTP_200_OK,
    name="get students with their courses",
    description="Get a list of students along with the courses they are enrolled in",
    operation_id="get_students_with_courses",
)
async def get_student_with_courses(
    service: Annotated[AdminUserService, Depends()],
    language: Annotated[Language, Query()]
) -> BaseResponse[List[StudentWithCourseResponse]]:
    """
    Retrieve a list of students with their enrolled courses.

    This endpoint returns all students along with the courses they are enrolled in,
    with course names translated to the specified language.

    Args:
        service: AdminUserService instance for business logic
        language: The language code for course name translations

    Returns:
        BaseResponse[List[StudentWithCourseResponse]]: List of students with their enrolled courses

    Raises:
        AdminHasPermission: If user doesn't have admin permissions
    """
    return BaseResponse(data=await service.get_student_with_courses(language))

@router.get(
    "/course-with-more-student",  
    status_code=status.HTTP_200_OK,
    name="get course with more than one student",
    description="Get a list of courses in which more than one student ",
    operation_id="get_course_with_condition",
)
async def get_students_with_condition(
    service: Annotated[AdminUserService, Depends()],
) -> BaseResponse[List[StudentWithCourseResponse]]:
    """
    Retrieve a list of courses with more than one student enrolled.

    This endpoint returns courses that have multiple students enrolled in them,
    useful for identifying popular or in-demand courses.

    Args:
        service: AdminUserService instance for business logic

    Returns:
        BaseResponse[List[str]]: List of course names with multiple students

    Raises:
        AdminHasPermission: If user doesn't have admin permissions
    """
    return BaseResponse(data=await service.get_course_with_more_than_one_student())

@router.get(
    "/faculty-with-courses",  
    status_code=status.HTTP_200_OK,     
    name="get faculty with their courses",
    description="Get a list of faculty along with the courses they are teaching",
    operation_id="get_faculty_with_courses",
)
async def get_faculty_with_courses(
    service: Annotated[AdminUserService, Depends()],
    language: Annotated[Language, Query()]
) -> BaseResponse[List[FacultyCourseResponse]]:
    """
    Retrieve a list of faculty members with their assigned courses.

    This endpoint returns all faculty members along with the courses they are teaching,
    with course names translated to the specified language.

    Args:
        service: AdminUserService instance for business logic
        language: The language code for course name translations

    Returns:
        BaseResponse[List[FacultyCourseResponse]]: List of faculty with their teaching courses

    Raises:
        AdminHasPermission: If user doesn't have admin permissions
    """
    return BaseResponse(data=await service.get_faculty_with_courses(language))

@router.get(
    "/student-rank",
    status_code=status.HTTP_200_OK,
    name="Rank students by course count",
    operation_id="rank_students",
)
async def rank_students(
    page_params: Annotated[Params, Depends()],
    service: Annotated[AdminUserService, Depends()],
) -> BaseResponse[Page[StudentRankResponse]]:
    """
    Retrieve a paginated list of students ranked by course enrollment count.

    This endpoint returns students ranked based on the number of courses they are
    enrolled in, with pagination support. Useful for identifying active or engaged students.

    Args:
        page_params: Pagination parameters for page size and number
        service: AdminUserService instance for business logic

    Returns:
        BaseResponse[Page[StudentRankResponse]]: Paginated list of ranked students with their course counts

    Raises:
        AdminHasPermission: If user doesn't have admin permissions
    """
    return BaseResponse(
        data=await service.rank_student(params=page_params)
    )

@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    name="get user by id to admin",
    description="Get User By Id to admin",
    operation_id="get_user_by_id_to_admin",
)
async def get_user_by_id(
    user_id: Annotated[UUID, Path()], service: Annotated[AdminUserService, Depends()]
) -> BaseResponse[BaseUserResponse]:
    """
    Retrieve a specific user by their ID.

    This endpoint returns detailed information for a single user identified by their UUID.

    Args:
        user_id: The UUID of the user to retrieve
        service: AdminUserService instance for business logic

    Returns:
        BaseResponse[BaseUserResponse]: User response containing user information

    Raises:
        UserNotFoundException: If the user with the given UUID is not found
        AdminHasPermission: If user doesn't have admin permissions
    """
    return BaseResponse(data=await service.get_user_by_id(user_id=user_id))


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    name="delete user by id and admin",
    description="delete user by id and admin",  
    operation_id="delete_user_by_id_and_admin",
    )
async def soft_delete_user_by_id(
    user_id: Annotated[UUID, Path()],
    service: Annotated[AdminUserService, Depends()]
) -> BaseResponse:
    """
    Soft delete a user by marking them as deleted.

    This endpoint allows admins to soft delete a user, preserving their data
    in the system while marking them as inactive/deleted.

    Args:
        user_id: The UUID of the user to delete
        service: AdminUserService instance for business logic

    Returns:
        BaseResponse: Response confirming successful deletion

    Raises:
        UserNotFoundException: If the user with the given UUID is not found
        AdminHasPermission: If user doesn't have admin permissions
    """
    return BaseResponse(data=await service.soft_delete_user(user_id=user_id))
    

@router.patch(
    "/{user_id}/restore",
    status_code=status.HTTP_200_OK,
    name="restore user by admin",
    description="Restore a deleted user by admin",
    operation_id="restore_user_by_admin",
)
async def restore_user_by_admin(
    user_id: Annotated[UUID, Path()],
    service: Annotated[AdminUserService, Depends()]
) -> BaseResponse:
    """
    Restore a soft-deleted user.

    This endpoint allows admins to restore a previously deleted user,
    reactivating their account in the system.

    Args:
        user_id: The UUID of the user to restore
        service: AdminUserService instance for business logic

    Returns:
        BaseResponse[BaseUserResponse]: Response containing the restored user information

    Raises:
        UserNotFoundException: If the user with the given UUID is not found
        AdminHasPermission: If user doesn't have admin permissions
    """
    return BaseResponse(
        data=await service.restore_user(user_id=user_id)
    )

@router.patch(
    "/{user_id}/status",
    status_code=status.HTTP_200_OK,
    name="is active status set by admin",
    description="Set is_active status for a user by admin",  
    operation_id="set_user_is_active_status_by_admin",
)
async def update_user_status(
    user_id: Annotated[UUID, Path()],
    is_activated: Annotated[bool, Body()],
    service: Annotated[AdminUserService, Depends()]
) -> BaseResponse:
    """
    Update the activation status of a user.

    This endpoint allows admins to activate or deactivate a user account,
    controlling whether the user can access the system.

    Args:
        user_id: The UUID of the user whose status is to be updated
        is_activated: Boolean value indicating the desired activation status
        service: AdminUserService instance for business logic

    Returns:
        BaseResponse[BaseUserResponse]: Response containing the updated user information

    Raises:
        UserNotFoundException: If the user with the given UUID is not found
        AdminHasPermission: If user doesn't have admin permissions
    """
    return BaseResponse(
        data=await service.update_user_status(user_id=user_id, is_activated=is_activated)
    )

@router.post(
    "/assign-faculty",
    status_code=status.HTTP_200_OK,
    name="assign faculty to course",
    description="Assign faculty to course",
    operation_id="assign_faculty_to_course",
)
async def assign_faculty_to_course(
    req: Annotated[AssignFacultyRequest, Body()],
    service: Annotated[AdminUserService, Depends()]
) -> BaseResponse:
    """
    Assign a faculty member to one or more courses.

    This endpoint allows admins to assign faculty members as instructors for
    specific courses.

    Args:
        req: AssignFacultyRequest containing faculty_id and list of course IDs
        service: AdminUserService instance for business logic

    Returns:
        BaseResponse[None]: Response confirming successful faculty assignment

    Raises:
        UserNotFoundException: If the faculty member is not found
        CourseNotFoundException: If any of the specified courses are not found
        BadRequestError: If the user is not a faculty member
        AdminHasPermission: If user doesn't have admin permissions
    """
    result = await service.assign_faculty_to_course(req)
    return BaseResponse(data=result)

