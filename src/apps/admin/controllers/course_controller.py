from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, Request, status, Query, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi_pagination import Page, Params
import io

from apps.admin.schemas.admin_user_response import AdminListUsersResponse
from apps.course.schemas.request import CourseRequest, CourseTranslationRequest
from apps.course.schemas.response import CourseResponse, CourseTranslationResponse
from apps.admin.services import AdminCourseService
from core.auth import AdminHasPermission
from core.utils.schema import BaseResponse
from apps.course.schemas.filter import CourseSortField, SortOrder


router = APIRouter(prefix="/admin/course", tags=["Course Control by Admin"], dependencies=[Depends(AdminHasPermission())])

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    name="Create course by admin",
    description="Create course by admin ",
    operation_id="create_course_by_admin",
)
async def create_course(
    body: Annotated[CourseRequest, Body()],
    service: Annotated[AdminCourseService, Depends()],
) -> BaseResponse:
    """
    Create a new course.

    This endpoint allows admins to create a new course with course information
    such as course name, credit, and description.

    Args:
        body: The request object containing course information
        service: AdminCourseService instance for business logic

    Returns:
        BaseResponse[CourseResponse]: Response containing the created course information

    Raises:
        BadRequestError: If required fields are missing or invalid
        AdminHasPermission: If user doesn't have admin permissions
    """
    return BaseResponse(
        data=await service.create_course(body)
    )

@router.post(
        "/translation",
        name="Translator",
        description="hindi translation",
        operation_id="hindi_translation",
        status_code=status.HTTP_200_OK
)
async def translator(
    course_id: Annotated[UUID, Query()],
    request: Annotated[CourseTranslationRequest, Body()],
    service: Annotated[AdminCourseService, Depends()]
)-> BaseResponse:
    """
    Add a translation for a course in a different language.

    This endpoint allows admins to add translated content for a course,
    such as course names and descriptions in different languages.

    Args:
        course_id: The UUID of the course to add translation for
        request: CourseTranslationRequest containing translated course information
        service: AdminCourseService instance for business logic

    Returns:
        BaseResponse[CourseTranslationResponse]: Response containing the added translation

    Raises:
        CourseNotFoundException: If the course is not found
        BadRequestError: If required fields are missing or invalid
        AdminHasPermission: If user doesn't have admin permissions
    """

    return BaseResponse(
        data = await service.add_course_translation(course_id=course_id, **request.model_dump())
    )


@router.get(
    "/export",
    status_code=status.HTTP_200_OK,
    name="Export courses to Excel",
    description="Download course data as an Excel file",
    operation_id="export_courses",
)
async def export_courses(
    service: Annotated[AdminCourseService, Depends()],
    course_name: Annotated[Optional[str], Query()] = None,
    course_credit: Annotated[Optional[int], Query()] = None,
    search: Annotated[Optional[str], Query()] = None,
    sort_by: Annotated[CourseSortField, Query()] = CourseSortField.created_at,
    order: Annotated[SortOrder, Query()] = SortOrder.desc,
):
    """
    Export courses to an Excel spreadsheet.

    This endpoint streams an Excel (.xlsx) file containing course data filtered by
    optional parameters. If the openpyxl package is not available, returns CSV format
    which Excel can still open.

    Args:
        service: AdminCourseService instance for business logic
        course_name: Optional filter for course name
        course_credit: Optional filter for course credit 
        search: Optional search term for course information
        sort_by: Field to sort results by (default: created_at)
        order: Sort order - ascending or descending (default: desc)

    Returns:
        StreamingResponse: Excel file as a streaming response

    Raises:
        AdminHasPermission: If user doesn't have admin permissions
    """
    data = await service.export_courses_excel(course_name=course_name,
                                              course_credit=course_credit,
                                              search=search,
                                              sort_by=sort_by,
                                              order=order)
    # choose a filename depending on bytes format
    fname = "courses.xlsx"
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )

@router.get(
    "/courses",
    status_code=status.HTTP_200_OK,
    name="get all courses to admin",
    description="get all courses to admin",
    operation_id="get_all_courses_to_admin",
)
async def get_all_courses_to_admin(
    page_params: Annotated[Params, Depends()],
    service: Annotated[AdminCourseService, Depends()],
    course_name: Annotated[Optional[str], Query()] = None,
    course_credit: Annotated[Optional[int], Query()] = None,
    search: Annotated[Optional[str], Query()] = None,
    sort_by: Annotated[CourseSortField, Query()] = CourseSortField.created_at,
    order: Annotated[SortOrder, Query()] = SortOrder.desc,
) -> BaseResponse[Page[CourseResponse]]:
    """
    Retrieve all courses with pagination and filtering options.

    This endpoint returns a paginated list of all courses with optional filtering
    by course name, credit hours, and search terms, as well as sorting capabilities.

    Args:
        page_params: Pagination parameters for page size and number
        service: AdminCourseService instance for business logic
        course_name: Optional filter for course name
        course_credit: Optional filter for course credit 
        search: Optional search term for course information
        sort_by: Field to sort results by (default: created_at)
        order: Sort order - ascending or descending (default: desc)

    Returns:
        BaseResponse[Page[CourseResponse]]: Paginated list of course responses

    Raises:
        AdminHasPermission: If user doesn't have admin permissions
    """
    return BaseResponse(
        data = await service.get_all_courses(param=page_params, 
                                             course_name=course_name, 
                                             course_credit=course_credit,
                                             search=search,
                                             sort_by=sort_by, 
                                             order=order))

@router.get(
    "/courses/search-combined",
    status_code=status.HTTP_200_OK,
    name="search courses by name and credit",
)
async def search_courses_combined(
    page_params: Annotated[Params, Depends()],
    service: Annotated[AdminCourseService, Depends()],
    course_name: Annotated[Optional[str], Query()] = None,
    course_credit: Annotated[Optional[int], Query()] = None,
    sort_by: Annotated[CourseSortField, Query()] = CourseSortField.created_at,
    order: Annotated[SortOrder, Query()] = SortOrder.desc,
)->BaseResponse[Page[CourseResponse]]:
    """
    Search courses by name and credit hours with pagination.

    This endpoint provides a combined search functionality to filter courses
    by both course name and credit hours simultaneously, with pagination support.

    Args:
        page_params: Pagination parameters for page size and number
        service: AdminCourseService instance for business logic
        course_name: Optional filter for course name
        course_credit: Optional filter for course credit 
        sort_by: Field to sort results by (default: created_at)
        order: Sort order - ascending or descending (default: desc)

    Returns:
        BaseResponse[Page[CourseResponse]]: Paginated list of matching course responses

    Raises:
        BadRequestError: If search parameters are invalid
        AdminHasPermission: If user doesn't have admin permissions
    """
    return BaseResponse(
        data=await service.search_courses_by_name_and_credit(
            param=page_params,
            course_name=course_name,
            course_credit=course_credit,
            sort_by=sort_by,
            order=order,
        )
    )

@router.get(
    "/{course_id}",
    status_code=status.HTTP_200_OK,
    name="get course by id to admin",
    description="get course by id to admin",
    operation_id="get_course_by_id_to_admin",
)
async def get_course_by_id(
    course_id: Annotated[UUID, Path()],
    service: Annotated[AdminCourseService, Depends()]
) -> BaseResponse[CourseResponse]:
    """
    Retrieve a specific course by its ID.

    This endpoint returns detailed information for a single course identified
    by its UUID.

    Args:
        course_id: The UUID of the course to retrieve
        service: AdminCourseService instance for business logic

    Returns:
        BaseResponse[CourseResponse]: Course response containing detailed course information

    Raises:
        CourseNotFoundException: If the course with the given ID is not found
        AdminHasPermission: If user doesn't have admin permissions
    """
    return BaseResponse(data = await service.get_course_by_id(course_id=course_id))


@router.put(
    "/{course_id}",
    status_code=status.HTTP_200_OK,
    name="update course by id and admin",
    description="update course by id and admin",
    operation_id="update_course_by_id_and_admin",
)
async def update_course_by_id(
    course_id: Annotated[UUID, Path()],
    body: Annotated[CourseRequest, Body()],
    service: Annotated[AdminCourseService, Depends()]
) -> BaseResponse:
    """
    Update an existing course by its ID.

    This endpoint allows admins to modify course information such as course name,
    credit hours, and description for an existing course.

    Args:
        course_id: The UUID of the course to update
        body: CourseRequest containing updated course information
        service: AdminCourseService instance for business logic

    Returns:
        BaseResponse[CourseResponse]: Response containing the updated course information

    Raises:
        CourseNotFoundException: If the course with the given ID is not found
        BadRequestError: If required fields are missing or invalid
        AdminHasPermission: If user doesn't have admin permissions
    """
    return BaseResponse(data = await service.update_course_by_id(course_id=course_id, course_req=body))

@router.delete(
    "/{course_id}",
    status_code=status.HTTP_200_OK,
    name="delete course by id and admin",
    description="delete course by id and admin",
    operation_id="delete_course_by_id_and_admin",
)
async def delete_course_by_id(
    course_id: Annotated[UUID, Path()],
    service: Annotated[AdminCourseService, Depends()]
) -> BaseResponse:
    """
    Delete a course by its ID.

    This endpoint allows admins to delete a course from the system. This operation
    may soft-delete the course to preserve historical data.

    Args:
        course_id: The UUID of the course to delete
        service: AdminCourseService instance for business logic

    Returns:
        BaseResponse: Response confirming successful deletion

    Raises:
        CourseNotFoundException: If the course with the given ID is not found
        AdminHasPermission: If user doesn't have admin permissions
    """
    course = await service.delete_course_by_id(course_id=course_id)
    return BaseResponse(data=course)

