from apps.admin.controllers.admin_controller import router as admin_router
from apps.admin.controllers.user_controller import router as admin_user_router
from apps.admin.controllers.course_controller import router as admin_course_router

__all__ = ["admin_router", "admin_user_router", "admin_course_router"]
