# API Versioning in FastAPI

## Structure

- Versioned routes are stored under `apps/<module>/vX/controllers`, `schemas`, `services`, and `models`.
- Each version folder has proper `__init__.py` files that export the routers and services with versioned names.
- No `common/` folder is used; all version-specific logic is isolated under its version folder.

## Import Structure

Each version module exports its components with versioned names:

```python
# apps/user/v1/controllers/__init__.py
from apps.user.v1.controllers.user_controller import router as user_router_v1
__all__ = ["user_router_v1"]

# apps/user/v1/services/__init__.py
from apps.user.v1.services.user import UserService_v1
__all__ = ["UserService_v1"]
```

## Access

- v1: /api/v1/user, /api/v1/admin, /api/v1/student
- v2: /api/v2/user, /api/v2/admin, /api/v2/student

## Principles

- Each version must be backward compatible
- Shared logic can be refactored into utilities/services if needed, but not in a `common/` folder
- Swagger UI clearly distinguishes v1/v2 using tags
- Do not mix versioned and shared logic; keep each version isolated
- All v2 endpoints return simple success messages for now

## Router Registration Example

```python
from fastapi import FastAPI
from apps.user.v1.controllers import user_router_v1
from apps.user.v2.controllers import user_router_v2
from apps.admin.controllers import admin_router
from apps.admin.v1.controllers import admin_router_v1
from apps.student.v1.controllers import student_router_v1
from apps.student.v2.controllers import student_router_v2

app = FastAPI(title="Naagmani API", version="2.0")

# Versioned router registration
app.include_router(user_router_v1, tags=["V1 - User"])
app.include_router(user_router_v2, tags=["V2 - User"])
app.include_router(admin_router_v1, tags=["V1 - Admin"])
app.include_router(admin_router_v2, tags=["V2 - Admin"])
app.include_router(student_router_v1, tags=["V1 - Student"])
app.include_router(student_router_v2, tags=["V2 - Student"])
```

## Service Naming Convention

- v1 services: `UserService_v1`, `AdminUserService_v1`
- v2 services: `UserService_v2`, `AdminUserService_v2` (when implemented)

## Router Prefixes

- v1 routers: `prefix="/api/v1/user"`, `prefix="/api/v1/admin"`, `prefix="/api/v1/student"`
- v2 routers: `prefix="/api/v2/user"`, `prefix="/api/v2/admin"`, `prefix="/api/v2/student"`
