import json
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import and_, or_, select, desc, func, join
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, selectinload

import constants
from apps.user.exceptions import (
    DuplicateEmailException,
    InvalidCredentialsException,
    UserNotFoundException,
    InvalidRequestException, 
    WeakPasswordException
)
from apps.user.models.user import UserModel, RoleModel
from apps.course.models.course import CourseModel, CourseTranslationModel, Association
from apps.course.schemas.response import StudentCourseResponse
from config import settings
from core.common_helpers import create_tokens, decrypt, validate_input_fields
from core.db import db_session
from core.exceptions import BadRequestError
from core.types import RoleType
from core.utils.hashing import hash_password, verify_password
from core.utils import strong_password
from constants.roles import Roles



class UserService:
    """
    Service with methods to handle user authentication and information.

    This service provides methods for creating users, logging in, and retrieving user information.
    """

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]) -> None:
        """
        Initialize AuthService with a database session
        This method also calls a database connection which is injected here.

        Args:
            session (AsyncSession): An asynchronous database connection.
        """
        self.session = session

    async def get_self(self, user_id: UUID) -> UserModel:
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

    async def login_user(
        self, request: Request, encrypted_data: str, encrypted_key: str, iv: str
    ) -> dict[str, str]:
        """
         Log in a user and generate authentication tokens.

        Args:
             request: The FastAPI request object.
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
        print(email, password)

        if email is None:
            raise BadRequestError(message=constants.EMAIL_FIELD_REQUIRED)

        if password is None:
            raise BadRequestError(message=constants.PASSWORD_FIELD_REQUIRED)

        user = await self.session.scalar(
            select(UserModel)
            .options(selectinload(UserModel.role_ref))
            .where(
                and_(UserModel.email == email,)
                    #  RoleModel.role.in_([Roles.STUDENT,Roles.FACULTY]))  # Only allow students and faculty to login
            )
        )
        if not user:
            raise InvalidCredentialsException

        user_role = user.role_ref.role
        if user_role not in [Roles.STUDENT, Roles.FACULTY] :
            raise InvalidCredentialsException

        verify = await verify_password(
            hashed_password=user.password, plain_password=password
        )
        if not verify:
            raise InvalidCredentialsException
        
        return await create_tokens(user)

    async def _get_user_with_courses(self, user_id: UUID) -> UserModel:

        result = await self.session.scalars(
            select(UserModel)
            .options(selectinload(UserModel.role_ref),
                selectinload(UserModel.courses)
                .selectinload(CourseModel.translations)
            )
            .where(UserModel.id == user_id)
        )

        user = result.first()

        if not user:
            raise UserNotFoundException()

        if user.role_ref.role != Roles.STUDENT:
            raise HTTPException(
                status_code=400,
                detail="User is not a student"
            )

        return user

    async def get_my_courses(self, user_id: UUID):
        user = await self._get_user_with_courses(user_id=user_id)
        
        preferred_lang = user.preferred_language
        response_courses = []

        for course in user.courses:

            # find translation
            translation = next(
                (t for t in course.translations if t.language_code == preferred_lang),
                None
            ) or next(
                (t for t in course.translations if t.language_code == 'en'),
                None
            )

            response_courses.append(
                StudentCourseResponse(
                    id=course.id,
                    course_name=translation.course_name if translation else course.course_name,
                    course_credit=course.course_credit,
                )
            )

        return response_courses
    
    async def get_recent_course(self, user_id, limit: int = 5):
        user = await self._get_user_with_courses(user_id=user_id)



        preferred_lang = user.preferred_language

        enrolled_course_ids = [course.id for course in user.courses]

        stmt = (
            select(CourseModel)
            .where(~CourseModel.id.in_(enrolled_course_ids))
            .options(selectinload(CourseModel.translations))
            .order_by(desc(CourseModel.created_at))
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        courses = result.scalars().all()

        response = []

        for course in courses:

            translation = next(
                (t for t in course.translations if t.language_code == preferred_lang),
                None
            ) or next(
                (t for t in course.translations if t.language_code == "en"),
                None
            )

            response.append(
                StudentCourseResponse(
                    id=course.id,
                    course_name=translation.course_name if translation else course.course_name,
                    course_credit=course.course_credit
                )
            )

        return response
        
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
    
    async def search_course(self, search:str):
          
        stmt = (
            select(CourseModel)
            .where(
                or_(
                    CourseModel.course_name.ilike(f"%{search}%"),
                CourseModel.translations.any(CourseTranslationModel.course_name.ilike(f"%{search}%"))
                )
            )
            .options(selectinload(CourseModel.translations))
            .distinct()
        )

        result = await self.session.execute(stmt)
        courses = result.scalars().all()

        if not courses:
            raise HTTPException(
            status_code=404,
            detail="Course not present"
        )

        return courses


    
