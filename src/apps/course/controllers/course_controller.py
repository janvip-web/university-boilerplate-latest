from typing import Annotated
from uuid import UUID

from fastapi_pagination import Page, Params
from fastapi import APIRouter, Depends, status, Body, Path

from apps.course.models.course import CourseModel
from apps.course.schemas.request import CourseRequest
from apps.course.schemas.response import CourseResponse
from apps.course.services.course import CourseService
from core.utils.schema import BaseResponse
from core.auth import AdminHasPermission
from core.types import RoleType

router = APIRouter(prefix="/course", tags=["Course"])

@router.get("")
async def root_course():
    return {"messge": "Course panel"}

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    name="Create course",
    description="Create course",
    operation_id="create_course"
)
async def create_student(
    body: Annotated[CourseRequest, Body()],
    service: Annotated[CourseService, Depends()],
)->BaseResponse[CourseResponse]:
    return BaseResponse(
        data= await service.create_course(body)
    )


@router.get(
        "/courses",
        status_code=status.HTTP_200_OK,
        # dependencies=[Depends]
        name="get all courses",
        description="get all courses",
        operation_id="get_all_courses"
)
async def get_all_students(
    page_params: Annotated[Params, Depends()],
    service: Annotated[CourseService, Depends()]
) -> BaseResponse[Page[CourseResponse]]:
    return BaseResponse(data = await service.get_all_courses(param=page_params))

@router.get(
    "/{course_id}",
    status_code=status.HTTP_200_OK,
    # dependencies=[Depends(AdminHasPermission)],
    name="get course by id",
    description="get coruse by id",
    operation_id="get_course_by_id",
)
async def get_student_by_id(
    course_id: Annotated[UUID, Path()],
    service: Annotated[CourseService, Depends()]
) -> BaseResponse[CourseResponse]:
    return BaseResponse(
        data= await service.get_course_by_id(course_id=course_id)
    )

#  gpt..............................................................
# @router.post("/enroll")
# async def enroll_student(
#     student_id: UUID,
#     course_id: UUID,
#     service: CourseService = Depends(),
# ):
#     return await service.enroll_student(
#         student_id=student_id,
#         course_id=course_id,
#     )
