from uuid import UUID

from core.utils import CamelCaseModel

class CourseRequest(CamelCaseModel):
    course_name: str
    course_credit: int
    faculty_id: UUID | None = None