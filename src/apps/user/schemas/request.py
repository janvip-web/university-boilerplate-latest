from core.utils import CamelCaseModel


class EncryptedRequest(CamelCaseModel):
    """
    request model for encrypted data
    """

    encrypted_data: str
    encrypted_key: str
    iv: str
