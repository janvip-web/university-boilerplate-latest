from uuid import UUID
from core.enum import LanguageEnum
from core.utils import CamelCaseModel
from pydantic import BaseModel

class CourseRequest(BaseModel):
    """
    Schema used when creating or updating a course.

    Attributes:
        course_name (str): Name of the course.
        course_credit (int): Credit value for the course.
        course_description (Optional[str]): Description text (optional).
    """
    course_name: str
    course_credit: int
    course_description: str | None = None
    # faculty_id: UUID | None = None

class CourseTranslationRequest(BaseModel):
    """
    Schema for adding a translated version of a course name.

    Attributes:
        course_name (str): Translated course name.
        language_code (LanguageEnum): Language of the translation.
    """
    course_name:str
    language_code: LanguageEnum