from datetime import datetime, timedelta
from typing import Annotated, Any, Literal

from fastapi import Cookie, Depends, Request
from fastapi.openapi.models import HTTPBearer
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer as HTTPBearerSecurity
from fastapi.security.base import SecurityBase
from jwt import DecodeError, ExpiredSignatureError, decode, encode
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, selectinload

import constants.messages as constants
from apps.user.models.user import UserModel
# from apps.student.models.student import StudentModel
# from apps.faculty.models.faculty import FacultyModel
from config import settings
from core.db import db_session
from core.exceptions import InvalidJWTTokenException, UnauthorizedError
from core.types import RoleType


class JWToken(SecurityBase):
    """
    A class for handling JWT tokens.

    This class inherits from :class:`SecurityBase` and provides methods for encoding and decoding JWT tokens.

    Args:
        token_type (Literal["access", "refresh", "admin_access", "admin_refresh"]): The type of token.

    Attributes:
        model: The HTTPBearer model for token extraction.
        scheme_name: The name of the token scheme.
        token_type (Literal["access", "refresh", "admin_access", "admin_refresh"]): The type of token.
    """

    def __init__(
        self, token_type: Literal["access", "refresh", "admin_access", "admin_refresh"]
    ) -> None:
        """
        Initialize the JWToken with the specified token type.

        Args:
            token_type (Literal["access", "refresh", "admin_access", "admin_refresh"]): The type of token.
        """
        self.model = HTTPBearer(name=f"{token_type}Token")
        self.scheme_name = self.__class__.__name__
        self.token_type = token_type

    def encode(self, payload: dict, expire_period: int = 3600) -> str:
        """
        Encode a payload into a JWT token.

        Args:
            payload (dict): The payload to be included in the token.
            expire_period (int, optional): The expiry period of the token in seconds. Defaults to 3600.

        Returns:
            str: The encoded JWT token.
        """
        return encode(
            {
                **payload,
                "type": self.token_type,
                "exp": datetime.utcnow() + timedelta(seconds=expire_period),
            },
            key=settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

    def decode(self, token: str) -> dict[str, Any] | None:
        """
        Decode a JWT token.

        Args:
            token (str): The JWT token to decode.

        Returns:
            Union[dict[str, Any], None]: The decoded token payload.
        """
        try:
            payload = decode(
                token,
                key=settings.JWT_SECRET_KEY,
                algorithms=settings.JWT_ALGORITHM,
                option={"verify_signature": True, "verify_exp": True},
            )
            if payload.get("type") != self.token_type:
                raise UnauthorizedError(constants.UNAUTHORIZED)
            return payload
        except DecodeError:
            raise InvalidJWTTokenException(constants.INVALID_TOKEN)
        except ExpiredSignatureError:
            raise InvalidJWTTokenException(constants.EXPIRED_TOKEN)

    async def __call__(
        self,
        request: Request,
        access_token: Annotated[
            str | None, Cookie(alias="accessToken", include_in_schema=False)
        ] = None,  # type: ignore
        refresh_token: Annotated[
            str | None, Cookie(alias="refreshToken", include_in_schema=False)
        ] = None,  # type: ignore
        admin_access_token: Annotated[
            str | None, Cookie(alias="adminAccessToken", include_in_schema=False)
        ] = None,  # type: ignore
        admin_refresh_token: Annotated[
            str | None, Cookie(alias="adminRefreshToken", include_in_schema=False)
        ] = None,  # type: ignore
        authorization: Annotated[
            HTTPAuthorizationCredentials, Depends(HTTPBearerSecurity(auto_error=False))
        ] = None,
    ) -> dict[str, Any] | None:
        """
        Extract the token from the request and decode it.

        Args:
            request (Request): The incoming request.
            access_token (str | None, optional): The access token cookie. Defaults to None.
            refresh_token (str | None, optional): The refresh token cookie. Defaults to None.
            admin_access_token (str | None, optional): The admin access token cookie. Defaults to None.
            admin_refresh_token (str | None, optional): The admin refresh token cookie. Defaults to None.

        Returns:
            Union[dict[str, Any], None]: The decoded token payload or None if no token found.
        """
        if authorization:
            try:
                token = authorization.credentials
                return self.decode(token)
            except InvalidJWTTokenException:
                raise UnauthorizedError(message=constants.UNAUTHORIZED)

        token_mapping = {
            constants.ACCESS: access_token,
            constants.REFRESH: refresh_token,
            constants.ADMIN_ACCESS: admin_access_token,
            constants.ADMIN_REFRESH: admin_refresh_token,
        }

        token = token_mapping.get(self.token_type)

        if token:
            return self.decode(token)

        if self.token_type in [
            constants.ACCESS,
            constants.REFRESH,
            constants.ADMIN_ACCESS,
            constants.ADMIN_REFRESH,
        ]:
            raise UnauthorizedError(message=constants.UNAUTHORIZED)
        return None


access = JWToken("access")
refresh = JWToken("refresh")
admin_access = JWToken("admin_access")
admin_refresh = JWToken("admin_refresh")


class HasPermission:
    """
    A Dependency Injection class that checks the user's permissions.

    This class checks the user's permissions based on the provided token payload.

    """

    def __init__(self, role_name:list[str]) -> None:
        """
        Initialize the HasPermission object with the specified permission type.

        Args:
            type_ (RoleType): The type of permission to check.
        """
        self.role_name = role_name

    async def __call__(
        self,
        session: Annotated[AsyncSession, Depends(db_session)],
        payload: Annotated[dict[str, Any], Depends(access)],
    ) -> dict[str, Any] | None:
        """
        Check the user type and return the user object if authorized.

        :param session: The database session.
        :param payload: The token payload containing user information.
        :raises UnauthorizedError: If the user is not authorized.
        :return: The user object if authorized, None otherwise.
        """
        # print(payload)
        if not payload:
            # if self.role_name == RoleType.OPTIONAL:
            #     return None
            # else:
                raise UnauthorizedError(message=constants.UNAUTHORIZED)
        
        print(payload)
        print("ID FROM TOKEN:", payload.get("id"))
        # user = await session.scalar(
        #     select(UserModel).where(UserModel.id == payload.get("id"))
        # )

        # user = await session.scalar(
        #     select(StudentModel).where(StudentModel.id == payload.get("id"))
        # )

        user = await session.scalar(
            select(UserModel)
            .options(selectinload(UserModel.role_ref))
            .where(UserModel.id == payload.get("id"))  
        )

        if not user :
            raise UnauthorizedError(message=constants.UNAUTHORIZED)
        
        # allowed_roles = {
        #     RoleType.USER: [RoleType.USER],
        #     RoleType.STAFF: [RoleType.STAFF],
        #     RoleType.ADMIN: [RoleType.ADMIN],
        #     RoleType.ANY: [RoleType.USER, RoleType.ADMIN, RoleType.STUDENT],
        #     RoleType.OPTIONAL: [RoleType.USER, RoleType.STUDENT],
        #     RoleType.STUDENT: [RoleType.STUDENT],
        #     RoleType.FACULTY: [RoleType.FACULTY]
        # }

        # if user.role_id not in allowed_roles[self.type]:
        #     raise UnauthorizedError(message=constants.UNAUTHORIZED)
        if user.role_ref.role not in self.role_name:
            raise UnauthorizedError(message=constants.UNAUTHORIZED)

        return user


class AdminHasPermission:
    """
    A Dependency Injection class that checks if the user has admin permissions.
    """

    def __init__(self) -> None:
        """
        Initialize the object to check admin permissions.
        """
        self.type = RoleType.ADMIN

    async def __call__(
        self,
        session: Annotated[AsyncSession, Depends(db_session)],
        payload: Annotated[dict[str, Any], Depends(admin_access)],
    ) -> dict[str, Any]:
        """
        Check if the user has admin permissions.

        :param session: The database session.
        :param payload: The token payload.
        :raises UnauthorizedError: If the user is not authorized.
        :return: The user object if authorized.
        """
        if not payload:
            raise UnauthorizedError(message=constants.UNAUTHORIZED)

        user = await session.scalar(
            select(UserModel)
            .options(selectinload(UserModel.role_ref))
            .where(UserModel.id == payload.get("id"))
        )

        # if not user or user.role_id != RoleType.ADMIN:
        if not user or user.role_id != 1:
            raise UnauthorizedError(message=constants.UNAUTHORIZED)
        return user
