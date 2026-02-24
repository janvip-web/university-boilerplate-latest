from uuid import UUID
from typing import List

from core.utils import CamelCaseModel

class AssignFacultyRequest(CamelCaseModel):
    faculty_id: UUID
    course_id: List[UUID]