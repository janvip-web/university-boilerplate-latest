from typing import Annotated
from uuid import UUID


from fastapi import APIRouter, Depends, status, Body, Path

from apps.faculty.schemas.response import FacultyWithCoursesResponse
from apps.faculty.services.faculty_courses import FacultyCourseService
from core.utils.schema import BaseResponse
from core.auth import HasPermission
from core.types import RoleType

router = APIRouter(prefix="/faculty-courses", tags=["Courses taken by Faculty"])

@router.get("")
async def root_fauclty_courses():
    return {"message": "Courses taken by faculty panel"}


@router.get(
    "/{faculty_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(HasPermission(RoleType.FACULTY))],
    name="Get courses taken by faculty",
    description="Get courses taken by faculty",
    operation_id="get_courses_taken_by_faculty"
)
async def get_courses_taken_by_faculty(
    faculty_id: Annotated[UUID, Path()],
    service: Annotated[FacultyCourseService, Depends()]
) -> BaseResponse[FacultyWithCoursesResponse]:

    return BaseResponse(data=await service.get_faculty_with_courses(faculty_id=faculty_id))