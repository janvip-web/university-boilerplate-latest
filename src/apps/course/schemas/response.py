from uuid import UUID

from pydantic import ConfigDict, Field
from core.utils import CamelCaseModel

class CourseResponse(CamelCaseModel):
    id: UUID
    course_name: str
    course_credit: int
    course_description: str | None = None
