from enum import Enum

class LanguageEnum(str, Enum):
    """
    Enumeration for supported language codes in the application.

    Attributes:
        EN: English language code.
        HI: Hindi language code.
    """
    EN = "en"
    HI = "hi"