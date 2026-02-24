from uuid import UUID

from pydantic import ConfigDict, Field
from core.utils import CamelCaseModel
from pydantic import BaseModel

class CourseResponse(BaseModel):
    id: UUID
    course_name: str
    course_credit: int
    course_description: str | None = None

class StudentCourseResponse(BaseModel):
    id: UUID
    course_name: str
    course_credit: int


class CourseTranslationResponse(BaseModel):
    id:UUID
    course_id: UUID
    course_name: str
    language_code: str