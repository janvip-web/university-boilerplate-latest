from uuid import UUID
from typing import List
from pydantic import BaseModel
from core.utils import CamelCaseModel

class AssignFacultyRequest(BaseModel):
    """
    Request schema used by admins to assign a faculty member to courses.

    Attributes:
        faculty_id (UUID): The identifier of the faculty user.
        course_id (List[UUID]): A list of course identifiers to assign to the faculty.
    """
    faculty_id: UUID
    course_id: List[UUID]