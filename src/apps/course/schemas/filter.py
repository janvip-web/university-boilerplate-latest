from enum import Enum

class CourseSortField(str, Enum):
    created_at = "created_at"
    course_name = "course_name"
    course_credit = "course_credit"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"

class Language(str, Enum):
    en = "en"
    hi = "hi"