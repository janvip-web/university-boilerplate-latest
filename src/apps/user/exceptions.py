import constants
from core.exceptions import CustomException, NotFoundError, UnauthorizedError, UnprocessableEntityError, BadRequestError


class DuplicateEmailException(CustomException):
    """
    Custom exception for email duplication.
    """

    message = constants.DUPLICATE_EMAIL


class InvalidCredentialsException(UnauthorizedError):
    """
    Custom exception to show a generic error message.
    """

    message = constants.INVALID_CREDS

class UserNotLogginException(UnauthorizedError):
    message = constants.USER_NOT_LOGGIN

class InvalidTokenException(UnauthorizedError):
    message = constants.INVALID_TOKEN_OR_PAYLOAD



class UserNotFoundException(NotFoundError):
    """
    Custom exception to show a generic error message.
    """

    message = constants.USER_NOT_FOUND

class CourseNotFoundException(NotFoundError):
    """
    Custom exception to show a generic error message.
    """

    message = constants.COURSE_NOT_FOUND

class UserDeletedException(NotFoundError):
    message = constants.USER_DELETED


class EmptyDescriptionException(UnprocessableEntityError):
    """
    Custom exception for issue with the notes create empty description.
    """

    message = constants.DESCRIPTION


class InvalidEncryptedData(BadRequestError):
    """
    Custom exception for User already assigned error.
    """

    message = constants.INVALID_ENCRYPTED_DATA

class UserNotStudent(BadRequestError):
    message = constants.USER_IS_NOT_STUDENT    

class WeakPasswordException(BadRequestError):
    """
    Custom exception for User already assigned error.
    """

    message = constants.WEAK_PASSWORD

class InvalidPhoneFormatException(BadRequestError):
    """
    Custom exception for invalid phone number format.
    """

    message = constants.INVALID_PHONE_NUMBER

class InvalidEmailException(BadRequestError):
    """
    Custom exception for invalid email.
    """

    message = constants.INVALID_EMAIL

class InvalidRequestException(BadRequestError):
    """
    Custom exception for invalid request.
    """

    message = constants.INVALID_REQUEST

class InvalidFileType(BadRequestError):
    message = constants.INVALID_FILETYPE