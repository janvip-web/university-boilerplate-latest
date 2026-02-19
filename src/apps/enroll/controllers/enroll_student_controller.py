from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends,status, Body, Path

from apps.enroll.schemas.request import EnrollStudentsToCourseRequest
from apps.enroll.services.enroll_student import EnrollService
from apps.enroll.schemas.response import EnrollStudentsToCourseResponse
from core.utils.schema import BaseResponse

router = APIRouter(prefix="/enroll", tags=["Enrollment"])

@router.get("")
async def root_course():
    return {"messge": "Enrollment panel"}

@router.post(
        "/course/enroll",
        status_code=status.HTTP_200_OK,
        name="Enroll students to course",
        description="Enroll students to course",
        operation_id="enroll_students_to_course"
             )
async def enroll_students(
    request:Annotated[EnrollStudentsToCourseRequest, Body()],
    service: Annotated[EnrollService, Depends()],
):
    return await service.enroll_students_to_course(request)


@router.get(
    "/course/{course_id}",
    status_code=status.HTTP_200_OK,
    name="Get course with enrolled students",
    description="Get course with enrolled students",
    operation_id="get_course_with_students"
)
async def get_course_with_students(
    course_id: Annotated[UUID, Path()],
    service: Annotated[EnrollService, Depends()]
)->BaseResponse[EnrollStudentsToCourseResponse]:
    
    return BaseResponse(
        data=await service.get_course_with_students(course_id=course_id))





# @router.post("/")
# async def enroll_student(
#     student_id: UUID,
#     course_id: UUID,
#     service: CourseService = Depends(),
# ):
#     return await service.enroll_student(
#         student_id=student_id,
#         course_id=course_id,
#     )

