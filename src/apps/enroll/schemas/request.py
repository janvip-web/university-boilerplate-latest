from uuid import UUID
from typing import List
from core.utils import CamelCaseModel

class EnrollStudentsToCourseRequest(CamelCaseModel):
    course_id: UUID
    student_ids: List[UUID]