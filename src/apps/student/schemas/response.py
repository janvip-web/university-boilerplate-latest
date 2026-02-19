from uuid import UUID
from core.utils import CamelCaseModel
from pydantic import Field

class StudentResponse(CamelCaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str
    dob: str

class StudentListResponse(CamelCaseModel):
    id: UUID = Field(alias="student_id")
    first_name: str
    last_name: str



    