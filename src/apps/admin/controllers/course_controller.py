from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, Request, status, Query
from fastapi.responses import JSONResponse
from fastapi_pagination import Page, Params

from apps.admin.schemas.admin_user_response import AdminListUsersResponse
from apps.course.schemas.request import CourseRequest, CourseTranslationRequest
from apps.course.schemas.response import CourseResponse, CourseTranslationResponse
from apps.admin.services import AdminCourseService
from core.auth import AdminHasPermission
from core.utils.schema import BaseResponse


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
) -> BaseResponse[CourseResponse]:
    """
    Create a new course.

    Args:
        body (CourseRequest): The request object containing course information.
        service (AuthService): The authentication service.

    Returns:
        BaseResponse[CourseResponse]: The response containing the created course information.
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
async def tanslator(
    course_id: Annotated[UUID, Query()],
    request: Annotated[CourseTranslationRequest, Body()],
    service: Annotated[AdminCourseService, Depends()]
)-> BaseResponse[CourseTranslationResponse]:
    return BaseResponse(
        data = await service.add_course_translation(course_id=course_id, request=request)
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
    service: Annotated[AdminCourseService, Depends()]
) -> BaseResponse[Page[CourseResponse]]:
    return BaseResponse(data = await service.get_all_courses(param=page_params))

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
) -> BaseResponse[CourseResponse]:
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
    course = await service.delete_course_by_id(course_id=course_id)
    return BaseResponse(data=course)