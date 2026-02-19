from uuid import UUID
from typing import List
from core.utils import CamelCaseModel
from apps.student.schemas.response import StudentListResponse

class EnrollStudentsToCourseResponse(CamelCaseModel):
    id: UUID
    course_name: str
    students: List[StudentListResponse] = []