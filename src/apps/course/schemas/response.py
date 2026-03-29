from uuid import UUID

from pydantic import ConfigDict, Field
from core.utils import CamelCaseModel
from pydantic import BaseModel

class CourseResponse(BaseModel):
    """
    Standard response model representing a course.

    Attributes:
        id (UUID): Unique identifier of the course.
        course_name (str): Name of the course.
        course_credit (int): Credit value for the course.
        course_description (Optional[str]): Optional description text.
    """
    id: UUID
    course_name: str
    course_credit: int
    course_description: str | None = None

class StudentCourseResponse(BaseModel):
    """
    Response model used when returning courses to students.

    `translated_name` may be in the student's preferred language.

    Attributes:
        id (UUID): Identifier of the course.
        translated_name (str): Course name after translation.
        course_credit (int): Credit hours of the course.
    """
    id: UUID
    translated_name: str 
    course_credit: int


class CourseTranslationResponse(BaseModel):
    """
    Response schema for a specific translation of a course.

    Attributes:
        id (UUID): Translation record identifier.
        course_id (UUID): The related course's ID.
        course_name (str): Translated course name.
        language_code (str): Language of the translation.
    """
    id:UUID
    course_id: UUID
    course_name: str
    language_code: str