from apps.course.schemas.response import CourseResponse, StudentCourseResponse
from core.utils import CamelCaseModel

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