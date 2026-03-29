from uuid import UUID
from pydantic import BaseModel
from core.utils import CamelCaseModel


class BaseUserResponse(BaseModel):
    """
    Base response object for user information.

    Attributes:
        id (UUID): The user's unique identifier.
        first_name (str): The user's first name.
        last_name (str): The user's last name.
        role (str): The user's role.
    """

    id: UUID
    first_name: str
    last_name: str
    role: str

class GetSelfResponse(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    birthday_message: str | None = None
