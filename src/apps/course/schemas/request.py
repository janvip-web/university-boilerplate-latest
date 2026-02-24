from uuid import UUID
from core.enum import LanguageEnum
from core.utils import CamelCaseModel
from pydantic import BaseModel

class CourseRequest(BaseModel):
    course_name: str
    course_credit: int
    course_description: str | None = None
    # faculty_id: UUID | None = None

class CourseTranslationRequest(BaseModel):
    course_name:str
    language_code: LanguageEnum