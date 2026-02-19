from core.utils import CamelCaseModel

class FacultyRequest(CamelCaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    password: str
    dept_name: str

class FacultyLoginRequest(CamelCaseModel):
    email: str
    password: str