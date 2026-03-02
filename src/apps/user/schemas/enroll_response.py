from uuid import UUID
from typing import List
from core.utils import CamelCaseModel
from pydantic import BaseModel


class EnrollStudentsToCourseResponse(BaseModel):
    """
    Response model returned after enrolling students to a course.

    Attributes:
        id (UUID): Identifier of the affected course.
        course_name (str): Name of the course.
        students (List[UUID]): List of student IDs enrolled.
    """
    id: UUID
    course_name: str
    students: List[UUID] = []