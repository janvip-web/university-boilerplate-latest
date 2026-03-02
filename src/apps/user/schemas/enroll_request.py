from uuid import UUID
from typing import List
from core.utils import CamelCaseModel
from pydantic import BaseModel

class EnrollStudentsToCourseRequest(BaseModel):
    """
    Schema for admin enrolling multiple students into a single course.

    Attributes:
        course_id (UUID): The course to enroll students in.
        student_ids (List[UUID]): List of student UUIDs to enroll.
    """
    course_id: UUID
    student_ids: List[UUID]

class SelfEnrollRequest(BaseModel):
    """
    Schema for a student enrolling themselves in one or more courses.

    Attributes:
        course_ids (List[UUID]): List of course UUIDs to enroll in.
    """
    course_ids: List[UUID]