from core.utils import CamelCaseModel


class EncryptedRequest(CamelCaseModel):
    """
    request model for encrypted data
    """

    encrypted_data: str
    encrypted_key: str
    iv: str

class CreateUserRequest(CamelCaseModel):
    """
    request model for creating user
    """
    encrypted_data: str
    encrypted_key: str
    iv: str
    # role_name: str
