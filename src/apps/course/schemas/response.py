from uuid import UUID

from pydantic import Field
from core.utils import CamelCaseModel

class CourseResponse(CamelCaseModel):
    id: UUID = Field(alias="course_id")
    course_name: str
    course_credit: int