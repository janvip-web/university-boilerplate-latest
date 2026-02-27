from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi_pagination import Page, Params

import constants
from apps.admin.schemas.admin_user_response import AdminListUsersResponse
from apps.admin.schemas.request import EncryptedRequest
from apps.admin.services.user import AdminUserService
from apps.user.models.user import UserModel
from apps.user.schemas.response import BaseUserResponse
from core.auth import AdminHasPermission
from core.exceptions import UnauthorizedError
from constants.roles import Roles
from core.utils.schema import BaseResponse
from core.utils.set_cookies import set_auth_cookies

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post(
    "/sign-in",
    status_code=status.HTTP_200_OK,
    name="sign-in",
    description="sign-in",
    operation_id="sign_in_admin",
)
async def sign_in(
    request: Request,
    body: Annotated[EncryptedRequest, Body()],
    service: Annotated[AdminUserService, Depends()],
) -> JSONResponse:
    """
    Authenticate an admin user and generate access tokens.

    This endpoint handles admin login with encrypted credentials. Upon successful
    authentication, it returns access tokens and sets authentication cookies.

    Args:
        request: The FastAPI request object containing application state
        body: Encrypted request containing admin credentials
        service: AdminUserService instance for business logic

    Returns:
        JSONResponse: Response with authentication tokens and cookies

    Raises:
        InvalidCredentialsException: If credentials are invalid
        BadRequestError: If required fields are missing
    """
    res = await service.login_admin(request=request, **body.model_dump())
    if "access_token" in res and res.get("access_token"):
        data = {"status": constants.SUCCESS, "code": status.HTTP_200_OK, "data": res}
        response = JSONResponse(content=data)
        response = set_auth_cookies(response, res, Roles.ADMIN)
        return response
    else:
        # Handle case where login fails but doesn't raise an exception
        raise UnauthorizedError(constants.UNAUTHORIZED)


@router.get(
    "/self",
    status_code=status.HTTP_200_OK,
    name="get self",
    description="Get Self",
    operation_id="get_self_admin",
)
async def get_self_handler(
    user: Annotated[UserModel, Depends(AdminHasPermission())],
    service: Annotated[AdminUserService, Depends()],
) -> BaseResponse[BaseUserResponse]:
    """
    Retrieve the current admin user's profile information.

    This endpoint returns the authenticated admin's profile data including
    basic user information like name, email, and role.

    Args:
        user: Authenticated admin user from token
        service: AdminUserService instance for business logic

    Returns:
        BaseResponse[BaseUserResponse]: Admin user profile data

    Raises:
        AdminHasPermission: If user doesn't have admin permissions
    """
    return BaseResponse(data=await service.get_self_admin(user_id=user.id))


@router.patch(
    "/change-password",
    name="change password",
    description="Change Password",
    operation_id="change_password",
    status_code=status.HTTP_200_OK,
)
async def change_password(
    request: Request,
    user: Annotated[UserModel, Depends(AdminHasPermission())],
    body: Annotated[EncryptedRequest, Body()],
    service: Annotated[AdminUserService, Depends()],
) -> BaseResponse[BaseUserResponse]:
    """
    Change the password for the authenticated admin user.

    This endpoint allows admins to update their password. The request must
    include the current password for verification and a new password that
    meets security requirements.

    Args:
        request: The FastAPI request object
        user: Authenticated admin user from token
        body: Encrypted request containing current and new passwords
        service: AdminUserService instance for business logic

    Returns:
        BaseResponse[BaseUserResponse]: Updated admin user data

    Raises:
        InvalidCredentialsException: If current password is incorrect
        WeakPasswordException: If new password doesn't meet requirements
        UserNotFoundException: If user is not found
        AdminHasPermission: If user doesn't have admin permissions
    """
    return BaseResponse(
        data=await service.change_password(
            request=request, **body.model_dump(), user=user.id
        )
    )

@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    name="logout",
    description="Logout",
    operation_id="logout",
)
async def logout(
    request: Request,
    # user: Annotated[UserModel, Depends(AdminHasPermission())],
    service: Annotated[AdminUserService, Depends()],
) -> BaseResponse[BaseUserResponse]:
    """
    Logout the authenticated admin user.

    This endpoint invalidates the admin's session and removes authentication cookies.

    Args:
        request: The FastAPI request object
        user: Authenticated admin user from token
        service: AdminUserService instance for business logic

    Returns:
        BaseResponse[BaseUserResponse]: Empty response indicating successful logout

    Raises:
        AdminHasPermission: If user doesn't have admin permissions
    """
    return await service.logout(request=request)
