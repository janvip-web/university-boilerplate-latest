from io import BytesIO
import json
from typing import Annotated
from uuid import UUID
from datetime import datetime, time, timedelta
import pytz

IST = pytz.timezone("Asia/Kolkata")
from core.db import redis
from fastapi import Depends, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from openpyxl import Workbook
from sqlalchemy import and_, or_, select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, selectinload

import constants
from apps.user.exceptions import (
    InvalidCredentialsException,
    UserNotFoundException,
    InvalidRequestException, 
    WeakPasswordException,
    UserNotStudent,
    CourseNotFoundException,
    EmailFieldRequired,
    PasswordFieldRequired
)
from apps.user.schemas.response import GetSelfResponse
from apps.user.models.user import UserModel, RoleModel
from apps.course.models.course import CourseModel, CourseTranslationModel, Association
from apps.course.schemas.response import StudentCourseResponse
from config import settings
from core.common_helpers import create_tokens, decrypt, validate_input_fields
from core.db import db_session
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

    async def get_self(self, user_id: UUID) -> GetSelfResponse:
        """
        Retrieve user profile information and birthday greeting.

        Fetches the authenticated user's profile information including email, name,
        and date of birth. Checks if today is the user's birthday based on the cron job
        having set the Redis key, and includes a birthday greeting message shown only
        once per day after the cron job runs.

        Args:
            user_id (UUID): The ID of the user.

        Returns:
            GetSelfResponse: Response schema containing user profile information
                and optional birthday greeting message (shown only once per day after
                the birthday cron job has run).

        Raises:
            UserNotFoundException: If the user with the given ID is not found.
        """
        user = await self.session.scalar(
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

        if not user:
            raise UserNotFoundException
        
        birthday_message = None

        today = datetime.now(IST).date()
        redis_key = f"birthday_sent:{user.id}:{today}"

        # Check if cron job has set the key (indicating birthday and cron run)
        if await redis.get(redis_key):
            api_shown_key = f"birthday_api_shown:{user.id}:{today}"

            # Show message only if not already shown via API today
            if not await redis.get(api_shown_key):
                birthday_message = "🎉 Happy Birthday!"
                
                # Expire at midnight
                midnight = IST.localize(
                    datetime.combine(today + timedelta(days=1), datetime.min.time())
                )
                now = datetime.now(IST)
                seconds_left = int((midnight - now).total_seconds())
                
                await redis.set(api_shown_key, "shown", ex=seconds_left)

        return GetSelfResponse(
                    id=user.id,
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    birthday_message=birthday_message,
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
            EmailFieldRequired: If email is missing from decrypted credentials.
            PasswordFieldRequired: If password is missing from decrypted credentials.
            InvalidCredentialsException: If email not found, user role is not
                STUDENT/FACULTY, or password does not match.
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
            raise EmailFieldRequired

        if password is None:
            raise PasswordFieldRequired

        user = await self.session.scalar(
            select(UserModel)
            .options(selectinload(UserModel.role_ref))
            .where(
                and_(UserModel.email == email,)
                    #  RoleModel.role.in_([Roles.STUDENT,Roles.FACULTY]))  
            )
        )
        if not user:
            raise InvalidCredentialsException
        
        # Only allow students and faculty to login
        user_role = user.role_ref.role
        if user_role not in [Roles.STUDENT, Roles.FACULTY] :
            raise InvalidCredentialsException

        verify = await verify_password(
            hashed_password=user.password, plain_password=password
        )
        if not verify:
            raise InvalidCredentialsException
        
        return await create_tokens(user)

    async def _get_user_with_courses(self, user_id: UUID):
        """
        Internal helper to fetch a user along with their course relationships.

        Ensures the user exists and has a student role before returning. Used by
        several public methods to avoid repeating query logic.

        Args:
            user_id: UUID of the user to retrieve.

        Raises:
            UserNotFoundException: If the user cannot be found in the database.
            UserNotStudent: If the user is not assigned a student role.
        """

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
            raise UserNotStudent
        
        return user

    async def get_my_courses(self, user_id: UUID):
        """
        Retrieve enrolled courses for a student.

        Fetches all courses the student is enrolled in with translated course names
        based on the user's preferred language. Falls back to English translation
        if the preferred language is unavailable.

        Args:
            user_id (UUID): The ID of the student user.

        Returns:
            List[StudentCourseResponse]: List of enrolled courses with translated
                names and credit information.

        Raises:
            UserNotFoundException: If the user cannot be found.
            UserNotStudent: If the user does not have a student role.
        """
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
                    translated_name=translation.course_name if translation else course.course_name,
                    course_credit=course.course_credit,
                )
            )

        return response_courses
    
    async def get_recent_course(self, user_id, limit: int = 5):
        """
        Fetch recently created courses that the user has not enrolled in.

        Args:
            user_id (UUID): The ID of the student user.
            limit (int): Maximum number of courses to return. Defaults to 5.

        Returns:
            List[StudentCourseResponse]: Recently created courses with translated
                names and credit information, excluding already enrolled courses.

        Raises:
            UserNotFoundException: If the user cannot be found.
            UserNotStudent: If the user does not have a student role.
        """
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

        result = await self.session.scalars(stmt)
        courses = result.all()

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
            InvalidRequestException: If current or new password is missing from data.
            WeakPasswordException: If the new password does not meet strength requirements.
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
        """
        Search for courses by name or translation.

        Args:
            search: Term to match against course names or their translations.

        Returns:
            List[CourseModel]: Matching course records.

        Raises:
            CourseNotFoundException: If no courses match the search term.
        """
          
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

        result = await self.session.scalars(stmt)
        courses = result.all()

        if not courses:
            raise CourseNotFoundException

        return courses


    async def export_my_courses(self, user_id: UUID)-> StreamingResponse:
        """
        Export the authenticated user's courses as an Excel workbook.

        Args:
            user_id: UUID of the student user.

        Returns:
            bytes: Binary content of the generated Excel file.
        """
        user = await self._get_user_with_courses(user_id = user_id)

        preferred_language = user.preferred_language
        print("preferred_lang", preferred_language)
        courses = user.courses

        wb = Workbook()
        ws = wb.active
        ws.title="My courses"
        ws.append(["id","course_name","course_credit"])
        for c in courses:
            print("Course:", c.id)
            print("Available translations:",[t.language_code for t in c.translations])
                    # 1️⃣ Find translation in preferred language
            translation = next(
                (t for t in c.translations if t.language_code == preferred_language),
                None
            ) or next(
                # 2️⃣ Fallback to English
                (t for t in c.translations if t.language_code == "en"),
                None
            )

            # 3️⃣ Final fallback to base course name
            course_name = (
                translation.course_name
                if translation
                else c.course_name
            )

            ws.append([str(c.id),
                       course_name,
                       c.course_credit])
            
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()