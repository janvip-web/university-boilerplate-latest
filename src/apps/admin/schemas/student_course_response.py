from apps.course.schemas.response import CourseResponse, StudentCourseResponse
from core.utils import CamelCaseModel
from pydantic import BaseModel

class StudentWithCourseResponse(CamelCaseModel):
    id: str
    first_name: str
    last_name: str
    courses: list[StudentCourseResponse]

class FacultyCourseResponse(CamelCaseModel):
    id: str
    first_name: str
    last_name: str
    faculty_courses: list[StudentCourseResponse]

class StudentRankResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    total_courses: int
    rank: int