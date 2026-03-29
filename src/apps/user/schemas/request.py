from core.utils import CamelCaseModel
from pydantic import BaseModel


class EncryptedRequest(BaseModel):
    """
    request model for encrypted data
    """

    encrypted_data: str
    encrypted_key: str
    iv: str

class CreateUserRequest(BaseModel):
    """
    request model for creating user
    """
    encrypted_data: str
    encrypted_key: str
    iv: str
    # role_name: str
