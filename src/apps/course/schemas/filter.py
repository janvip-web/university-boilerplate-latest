from enum import Enum

class CourseSortField(str, Enum):
    """Fields available for sorting courses in queries.

    Attributes:
        created_at: Sort by course creation timestamp.
        course_name: Sort by the course's name.
        course_credit: Sort by credit value assigned to the course.
    """
    created_at = "created_at"
    course_name = "course_name"
    course_credit = "course_credit"


class SortOrder(str, Enum):
    """Defines order direction for sorting results.

    Values:
        asc: Ascending order.
        desc: Descending order.
    """
    asc = "asc"
    desc = "desc"

class Language(str, Enum):
    """Supported language codes for course content or localization.

    Values:
        en: English language.
        hi: Hindi language.
    """
    en = "en"
    hi = "hi"