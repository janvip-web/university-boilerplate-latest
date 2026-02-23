from apps.course.schemas.response import CourseResponse
from core.utils import CamelCaseModel

class StudentCourseResponse(CamelCaseModel):
    id: str
    first_name: str
    last_name: str
    courses: list[CourseResponse]

class FacultyCourseResponse(CamelCaseModel):
    id: str
    first_name: str
    last_name: str
    faculty_courses: list[CourseResponse]