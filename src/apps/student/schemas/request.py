from core.utils import CamelCaseModel

class StudentRequest(CamelCaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    password: str
    dob: str

class StudentLoginRequest(CamelCaseModel):
    email: str
    password: str