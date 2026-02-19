from uuid import UUID
from core.utils import CamelCaseModel
from pydantic import Field
from typing import List
from apps.course.schemas.response import CourseResponse

class FacultyResponse(CamelCaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str
    dept_name: str

class FacultyWithCoursesResponse(FacultyResponse):
    id: UUID = Field(alias="faculty_id")
    first_name: str 
    last_name: str
    courses: List[CourseResponse] = []