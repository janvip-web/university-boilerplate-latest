import constants
from core.exceptions import CustomException, NotFoundError, UnauthorizedError, UnprocessableEntityError, BadRequestError


class DuplicateEmailException(CustomException):
    """
    Custom exception for email duplication.
    """

    message = constants.DUPLICATE_EMAIL

class DOBValidationException(BadRequestError):
    """
    Custom exception for DOB validation
    """
    message = constants.DOB_VALIDATION


class InvalidCredentialsException(UnauthorizedError):
    """
    Custom exception to show a generic error message.
    """

    message = constants.INVALID_CREDS

class UserNotLogginException(UnauthorizedError):
    """
    Exception raised when an operation requires a logged-in user but none is found.
    """
    message = constants.USER_NOT_LOGGIN

class InvalidTokenException(UnauthorizedError):
    """
    Raised when a provided JWT token is invalid or the payload cannot be parsed.
    """
    message = constants.INVALID_TOKEN_OR_PAYLOAD



class UserNotFoundException(NotFoundError):
    """
    Custom exception to show a generic error message.
    """

    message = constants.USER_NOT_FOUND

class RoleNotFoundException(NotFoundError):
    """
    Custom exception to show a generic error message.
    """
    message = constants.ROLE_NOT_FOUND

class CourseNotFoundException(NotFoundError):
    """
    Custom exception to show a generic error message.
    """

    message = constants.COURSE_NOT_FOUND

class UserDeletedException(NotFoundError):
    """
    Exception indicating a user account has been deleted and is unavailable.
    """
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
    """
    Raised when an action requires a student role but the user is not a student.
    """
    message = constants.USER_IS_NOT_STUDENT    

class UserNotFaculty(BadRequestError):
    """
    Raised when an action requires a faculty role but the user is not a faculty.
    """
    message = constants.USER_IS_NOT_FACULTY

class TranslationExists(BadRequestError):
    """
    Custom exception for Translation already exists for given language.
    """
    message = constants.TRANSLATION_ALREDY_EXISTS

class CourseAlreadyExistsException(BadRequestError):
    message = constants.COURSE_ALREADY_EXISTS

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
    """
    Custom exception for invalid filetype.
    """
    message = constants.INVALID_FILETYPE

class EmailFieldRequired(BadRequestError):
    """
    Custom exception for email required.
    """
    message = constants.EMAIL_FIELD_REQUIRED

class PasswordFieldRequired(BadRequestError):
    """
    CUstom exception for password requirement.
    """
    message = constants.PASSWORD_FIELD_REQUIRED