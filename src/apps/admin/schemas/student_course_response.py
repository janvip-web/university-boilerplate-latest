from apps.course.schemas.response import CourseResponse, StudentCourseResponse
from core.utils import CamelCaseModel
from pydantic import BaseModel

class StudentWithCourseResponse(BaseModel):
    """Represents a student along with their enrolled courses.

    Attributes:
        id (str): Unique identifier for the student.
        first_name (str): Student's first name.
        last_name (str): Student's last name.
        courses (list[StudentCourseResponse]): List of course details the student is enrolled in.
    """
    id: str
    first_name: str
    last_name: str
    courses: list[StudentCourseResponse]

class FacultyCourseResponse(BaseModel):
    """Response model for faculty members and the courses they teach.

    Attributes:
        id (str): Unique identifier for the faculty member.
        first_name (str): Faculty's first name.
        last_name (str): Faculty's last name.
        faculty_courses (list[StudentCourseResponse]): Courses taught by the faculty member.
    """
    id: str
    first_name: str
    last_name: str
    faculty_courses: list[StudentCourseResponse]

class StudentRankResponse(BaseModel):
    """Response schema providing a student's rank based on course count.

    Attributes:
        id (str): Unique identifier for the student.
        first_name (str): Student's first name.
        last_name (str): Student's last name.
        total_courses (int): Total number of courses the student is registered in.
        rank (int): Ranking position among peers based on course count.
    """
    id: str
    first_name: str
    last_name: str
    total_courses: int
    rank: int