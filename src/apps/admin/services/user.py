import json
from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from fastapi_pagination import Page, Params, response
from fastapi_pagination.ext.sqlalchemy import paginate
import jwt
from sqlalchemy import and_, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, selectinload

from apps.course.models.course import CourseModel
import constants
from apps.user.exceptions import (
    DuplicateEmailException,
    InvalidCredentialsException,
    InvalidRequestException,
    UserNotFoundException,
    WeakPasswordException,
    CourseNotFoundException
)
from apps.user.models.user import UserModel, RoleModel
from config import settings
from core.common_helpers import create_tokens, decrypt, validate_email, validate_input_fields
from core.db import db_session
from core.exceptions import BadRequestError, UnauthorizedError
from core.types import RoleType
from core.utils import strong_password
from core.utils.hashing import hash_password, verify_password
from core.utils.set_cookies import delete_cookies
from apps.admin.schemas.assign_faculty_request import AssignFacultyRequest


class AdminUserService:
    """
    Service providing methods for managing admin-related user operations.
    """

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]) -> None:
        """
        Initializes the AdminUserService with an asynchronous database session.
        This method also calls a database connection which is injected here.

        :param session: an asynchronous database connection
        """
        self.session = session

    async def login_admin(
        self, request: Request, encrypted_data: str, encrypted_key: str, iv: str
    ) -> dict[str, str]:
        """
        Log in an admin and generate authentication tokens.

        Args:
            request(Request):  The incoming request object.
            encrypted_data (str): The encrypted data containing the login credentials.
            encrypted_key (str): The encrypted key used to encrypt the data.
            iv (str): The initialization vector used to encrypt the data.

        Returns:
            dict[str, str]: A dictionary containing the authentication tokens.

        Raises:
            InvalidCredentialsException: If the login credentials are invalid.
        """
        decrypted_data = await decrypt(
            rsa_key=request.app.state.rsa_key,
            enc_data=encrypted_data,
            encrypt_key=encrypted_key,
            iv_input=iv,
            time_check=settings.DECRYPT_REQUEST_TIME_CHECK or False,
            timeout=constants.PAYLOAD_TIMEOUT,
        )
        decrypted_data = json.loads(decrypted_data)

        email = decrypted_data.get("email")
        password = decrypted_data.get("password")

        if email is None:
            raise BadRequestError(message=constants.EMAIL_FIELD_REQUIRED)

        if password is None:
            raise BadRequestError(message=constants.PASSWORD_FIELD_REQUIRED)

        validate_email(email=email)

        user = await self.session.scalar(
            select(UserModel).where(
                and_(UserModel.email == email, UserModel.role_id == 1)
            )
        )

        if not user:
            raise InvalidCredentialsException
        
        if user.is_deleted:
            raise UnauthorizedError("Account deleted")

        if not user.is_activated:  
            raise UnauthorizedError("Account deactivated")
        
        verify = await verify_password(
            hashed_password=user.password, plain_password=password
        )
        if not verify:
            raise InvalidCredentialsException

        return await create_tokens(user_id=user.id, role_id=user.role_id)
    


    async def get_users(self, params: Params, role_id: int | None = None) -> Page[UserModel]:
        """
        Retrieve a paginated list of users.

        Args:
            params (Params): Pagination parameters to control the page size and number.

        Returns:
            Page[UserModel]: A paginated list of UserModel instances.

        Raises:
            UserNotFoundException: If the user with the given UUID is not found.
        """
        query = select(UserModel).where(UserModel.is_deleted == False).options(
            load_only(
                UserModel.first_name,
                UserModel.last_name,
                UserModel.email,
                UserModel.phone,
                UserModel.role_id
            )
        )

        if role_id is not None:
            query = query.where(UserModel.role_id == role_id)

        return await paginate(self.session, query, params)

    async def get_self_admin(self, user_id: UUID) -> UserModel:
        """
        Retrieve user information by user ID.

        Args:
            user_id (UUID): The ID of the user.

        Returns:
            UserModel: The user model with the user's information.
        """
        return await self.session.scalar(
            select(UserModel)
            .options(
                load_only(
                    UserModel.id,
                    UserModel.email,
                    UserModel.first_name,
                    UserModel.last_name,
                )
            )
            .where(UserModel.id == user_id)
        )

    async def change_password(
        self,
        request: Request,
        user: UUID,
        encrypted_data: str,
        encrypted_key: str,
        iv: str,
    ):
        """
        Change the password for a user.

        Args:
            user (UUID): The ID of the user.
            encrypted_data (str): The encrypted data containing the current and new passwords.
            encrypted_key (str): The encrypted key used to encrypt the data.
            iv (str): The initialization vector used to encrypt the data.

        Returns:
            UserModel: The updated user model with the new password.

        Raises:
            UserNotFoundException: If the user with the given UUID is not found.
            InvalidCredentialsException: If the current password is incorrect.
        """

        decrypted_data = await decrypt(
            rsa_key=request.app.state.rsa_key,
            enc_data=encrypted_data,
            encrypt_key=encrypted_key,
            iv_input=iv,
        )
        decrypted_data = json.loads(decrypted_data)

        current_password = decrypted_data.get("current_password")
        new_password = decrypted_data.get("new_password")

        if not current_password or not new_password:
            raise InvalidRequestException

        if not strong_password(new_password):
            raise WeakPasswordException

        current_user = await self.session.scalar(
            select(UserModel).where(UserModel.id == user)
        )

        if not current_user:
            raise UserNotFoundException

        verify = await verify_password(
            hashed_password=current_user.password, plain_password=current_password
        )

        if not verify:
            raise InvalidCredentialsException

        current_user.password = await hash_password(new_password)

        return current_user


    async def create_user(
        self, request: Request, encrypted_data: str, encrypted_key: str, iv: str
    ) -> UserModel:
        """
        Create a new user.

        Args:
            email (EmailStr): The user's email address.
            password (str): The user's password.
            first_name (str): The user's first name.
            last_name (str): The user's last name.
            phone (str): The user's phone number.

        Returns:
            UserModel: The created user model.

        Raises:
            DuplicateEmailException: If a user with the given email already exists.
        """
        decrypted_data = await decrypt(
            rsa_key=request.app.state.rsa_key,
            enc_data=encrypted_data,
            encrypt_key=encrypted_key,
            iv_input=iv,
        )
        decrypted_data = json.loads(decrypted_data)

        first_name = decrypted_data.get("first_name")
        last_name = decrypted_data.get("last_name")
        phone = decrypted_data.get("phone")
        email = decrypted_data.get("email")
        password = decrypted_data.get("password")
        role_name = decrypted_data.get("role_name")

        validate_input_fields(
            first_name=first_name, email=email, phone=phone, password=password
        )

        user = await self.session.scalar(
            select(UserModel)
            .options(load_only(UserModel.email))
            .where(or_(UserModel.email == email, UserModel.phone == phone))
        )
        if user:
            raise DuplicateEmailException
        
        role = await self.session.scalar(
            select(RoleModel).where(RoleModel.role == role_name.upper())
        )
        if not role:
            raise BadRequestError(message=constants.ROLE_NOT_FOUND)

        user = UserModel.create(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            password=await hash_password(password),
            email=email,
            role_id=role.role_id,
        )
        self.session.add(user)
        return user
    
    async def update_user(
        self, user_id: UUID, request: Request, encrypted_data: str, encrypted_key: str, iv: str
    ) -> UserModel:
        """
        Update an existing user's information.

        Args:
            user_id (UUID): The ID of the user to update.
            encrypted_data (str): The encrypted data containing the updated user information.
            encrypted_key (str): The encrypted key used to encrypt the data.
            iv (str): The initialization vector used to encrypt the data.

        Returns:
            UserModel: The updated user model.

        Raises:
            UserNotFoundException: If the user with the given UUID is not found.
        """
        decrypted_data = await decrypt(
            rsa_key=request.app.state.rsa_key,
            enc_data=encrypted_data,
            encrypt_key=encrypted_key,
            iv_input=iv,
        )
        decrypted_data = json.loads(decrypted_data)

        first_name = decrypted_data.get("first_name")
        last_name = decrypted_data.get("last_name")
        phone = decrypted_data.get("phone")

        # validate_input_fields(first_name=first_name)

        user = await self.session.scalar(
            select(UserModel).where(UserModel.id == user_id)
        )
        if not user:
            raise UserNotFoundException

        user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if phone:
            user.phone = phone

        return user
    
    async def get_user_by_id(self, user_id: UUID):
        """
        Retrieve a user by their ID.

        Args:
            user_id (UUID): The ID of the user to retrieve.

        Returns:
            UserModel: The user model with the requested user's information.
        """

        searched_user = await self.session.scalar(
            select(UserModel)
            .options(
                load_only(
                    UserModel.id,
                    UserModel.email,
                    UserModel.first_name,
                    UserModel.last_name,
                )
            )
            .where(UserModel.id == user_id, UserModel.is_deleted == False)
        )

        if not searched_user:
            raise UserNotFoundException
        return searched_user
    
    async def soft_delete_user(self, user_id: UUID):
        """
        Soft delete a user by their ID.

        Args:
            user_id (UUID): The ID of the user to soft delete.

        Returns:
            UserModel: The user model with the updated is_active status.

        Raises:
            UserNotFoundException: If the user with the given UUID is not found.
        """

        searched_user = await self.session.scalar(
            select(UserModel)
            .options(
                load_only(
                    UserModel.id,
                    UserModel.is_deleted,
                )
            )
            .where(UserModel.id == user_id)
        )

        if not searched_user or searched_user.is_deleted == True:
            raise UserNotFoundException
        
        searched_user.is_deleted = True
        return searched_user
    
    async def update_user_status(self, user_id: UUID, is_activated: bool):
        user = await self.session.scalar(
            select(UserModel)
            .options(
                load_only(
                    UserModel.id,
                    UserModel.is_activated,
                )
            )
            .where(UserModel.id == user_id, UserModel.is_deleted == False)
        )

        if not user:
            raise UserNotFoundException
        
        user.is_activated = is_activated
        return user
    
    async def restore_user(self, user_id: UUID):
        user = await self.session.scalar(
            select(UserModel)
            .options(
                load_only(
                    UserModel.id,
                    UserModel.is_deleted,
                )
            )
            .where(UserModel.id == user_id, UserModel.is_deleted == True)
        )

        if not user:
            raise UserNotFoundException
        
        if not user.is_deleted:
            raise BadRequestError(message="user is not deleted")
        
        user.is_deleted = False
        return user
    

    async def logout(self, request: Request)-> JSONResponse:
        access_token = (
        request.cookies.get("accessToken")
        or request.cookies.get("adminAccessToken")
    )
        
        if not access_token:
            raise HTTPException(
            status_code=401,
            detail="User not logged in"
        )

        try:
            payload = jwt.decode(
                access_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )

            role_id = payload.get("role_id")

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")

        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

        response = JSONResponse(
            content={
                "status": "SUCCESS",
                "message": "Logged out successfully"
            }
        )

        return delete_cookies(response=response, role_id=role_id)
    
    async def assign_faculty_to_course(self, req: AssignFacultyRequest):
        course = await self.session.scalar(
            select(CourseModel).where(CourseModel.id == req.course_id)
        )
        if not course:
            raise CourseNotFoundException
        
        faculty = await self.session.scalar(
            select(UserModel).where(UserModel.id == req.faculty_id))
        
        if not faculty:
            raise UserNotFoundException
        
        if faculty.role_id != 3:
            raise BadRequestError(message="User is not a faculty")
        
        course.faculty_id = req.faculty_id

        return {"message": "Faculty assigned to course successfully"}
    

    async def get_student_with_courses(self):
        result = await self.session.scalars(
            select(UserModel).options(selectinload(UserModel.courses))
            .where(UserModel.role_id == 2, UserModel.is_deleted == False)
        )
        students = result.all()

        return students
    

    async def get_faculty_with_courses(self):
        result =await self.session.scalars(
            select(UserModel).options(selectinload(UserModel.faculty_courses))
            .where(UserModel.role_id == 3, UserModel.is_deleted == False)
        )
        faculty = result.all()
        return faculty
    
