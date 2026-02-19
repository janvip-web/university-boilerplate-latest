from apps.faculty.controllers.faculty_controller import router as faculty_router
from apps.faculty.controllers.faculty_course_controller import router as faculty_course_router

__all__ = ["faculty_router", "faculty_course_router"]