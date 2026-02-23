from uuid import UUID

from core.utils import CamelCaseModel

class AssignFacultyRequest(CamelCaseModel):
    faculty_id: UUID
    course_id: UUID 