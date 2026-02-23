from uuid import UUID
from typing import List
from core.utils import CamelCaseModel


class EnrollStudentsToCourseResponse(CamelCaseModel):
    id: UUID
    course_name: str
    students: List[UUID] = []