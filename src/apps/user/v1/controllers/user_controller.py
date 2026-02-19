from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/user", tags=["V1 - User"])


@router.get("/")
def get_users_v1():
    """
    v1 endpoint for users - placeholder for future versioning needs.

    This endpoint is a placeholder that will be implemented when breaking changes
    are required in the user API. Currently returns a simple message indicating
    this is the v1 version.

    When v1 is actually needed:
    1. Move the current user logic from default controller to this v1 controller
    2. Update the default controller with new breaking changes
    3. Implement full user functionality here for backward compatibility

    Returns:
        dict: A simple response indicating this is the v1 endpoint

    Example:
        {
            "version": "v1",
            "message": "User v1 endpoint - placeholder"
        }
    """
    return {"version": "v1", "message": "User v1 endpoint - placeholder"}
