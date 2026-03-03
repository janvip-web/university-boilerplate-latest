import json
from typing import Annotated, Optional
from uuid import UUID
from datetime import datetime

from fastapi import Depends, Request, Query
from fastapi.responses import JSONResponse
from fastapi_pagination import Page, Params, paginate, create_page
from fastapi_pagination.ext.sqlalchemy import paginate
import jwt
from sqlalchemy import and_, select, or_ , update, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, selectinload, Load, joinedload, with_loader_criteria

from apps.course.models.course import CourseModel, Association, CourseTranslationModel
from apps.admin.schemas.admin_user_response import AdminListUsersResponse
from apps.user.schemas.response import BaseUserResponse
import constants
from constants.messages import INVALID_TOKEN_OR_PAYLOAD
from core.enum import LanguageEnum
from apps.user.exceptions import (
    DuplicateEmailException,
    InvalidCredentialsException,
    InvalidRequestException,
    UserNotFoundException,
    WeakPasswordException,
    CourseNotFoundException,
    UserNotLogginException,
    EmailFieldRequired,
    PasswordFieldRequired,
    RoleNotFoundException,
    UserNotFaculty,
    DOBValidationException
)
from apps.user.models.user import UserModel, RoleModel
from config import settings
from core.common_helpers import create_tokens, decrypt, validate_email, validate_input_fields
from core.db import db_session
from core.exceptions import InvalidJWTTokenException
from core.types import RoleType
from core.utils import strong_password
from core.utils.hashing import hash_password, verify_password
from core.utils.schema import SuccessResponse
from core.utils.set_cookies import delete_cookies
from apps.admin.schemas.assign_faculty_request import AssignFacultyRequest
from apps.admin.schemas.student_course_response import StudentRankResponse
from constants.roles import Roles


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
            raise EmailFieldRequired

        if password is None:
            raise PasswordFieldRequired

        validate_email(email=email)

        user = await self.session.scalar(
            select(UserModel)
            .options(selectinload(UserModel.role_ref))
            .where(
                and_(UserModel.email == email, )
            )
        )

        if user.role != Roles.ADMIN:
            raise InvalidCredentialsException

        if not user:
            raise InvalidCredentialsException
        
        # if user.is_deleted:
        #     raise UnauthorizedError("Account deleted")

        # if not user.is_activated:  
        #     raise UnauthorizedError("Account deactivated")
        # print("Password plain:", repr(password))
        # print("Password DB:", repr(user.password))

        verify = await verify_password(
            hashed_password=user.password, plain_password=password
        )
        if not verify:
            raise InvalidCredentialsException

        return await create_tokens(user)
    


    async def get_users(self, params: Params, role_id: int | None = None) -> Page[AdminListUsersResponse]:
        """
        Retrieve a paginated list of users.

        Args:
            params (Params): Pagination parameters to control the page size and number.

        Returns:
            Page[UserModel]: A paginated list of UserModel instances.

        Raises:
            UserNotFoundException: If the user with the given UUID is not found.
        """
        query = (select(UserModel)
                .where(UserModel.is_deleted.is_(False))
            .options(
                selectinload(UserModel.role_ref)
        ))
    
        if role_id is not None:
            query = query.where(UserModel.role_id == role_id)

        return await paginate(self.session, query, params)

    async def get_self_admin(self, user_id: UUID) -> BaseUserResponse:
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
    ) :
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
        preferred_language = decrypted_data.get("preferred_language")
        

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
            raise RoleNotFoundException

        user = UserModel.create(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            password=await hash_password(password),
            email=email,
            role_id=role.role_id,
            preferred_language=preferred_language
        )
        self.session.add(user)
        return SuccessResponse(message=constants.USER_CREATED_SUCCESS)
    

    async def update_user(
        self, user_id: UUID, request: Request, encrypted_data: str, encrypted_key: str, iv: str
    ) :
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

        allowed_fields = {"first_name", "last_name", "phone", "preferred_language","date_of_birth"}

        update_data = {}
            # key: value
        for key, value in decrypted_data.items():
            if key in allowed_fields and value is not None:
                if key == "date_of_birth":
                    try:
                        value = datetime.strptime(value, "%d/%m/%Y").date()
                    except ValueError:
                        raise DOBValidationException

            update_data[key] = value  

        if not update_data:
            None

        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(**update_data)
            .returning(UserModel)
        )
        updated_user = await self.session.scalar(stmt)

        if not updated_user:
            raise UserNotFoundException

        return SuccessResponse(message=constants.USER_UPDATED)
    
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
            .where(UserModel.id == user_id, UserModel.is_deleted.is_(False))
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
        stmt = (update(UserModel).where(UserModel.id == user_id, UserModel.is_deleted.is_(False))
                .values(is_deleted = True))

        result = await self.session.execute(stmt)
        if result.rowcount == 0:
            raise UserNotFoundException
        # return searched_user
        return SuccessResponse(message=constants.USER_DELETED)
    
    
    async def update_user_status(self, user_id: UUID, is_activated: bool):
        """
        Update the activation status of a user.

        Args:
            user_id (UUID): The ID of the user to update.
            is_activated (bool): The new activation status for the user.

        Returns:
            UserModel: The updated user model with the new activation status.

        Raises:
            UserNotFoundException: If the user with the given UUID is not found.
        """
        stmt = (update(UserModel).where(UserModel.id == user_id, UserModel.is_deleted.is_(False))
                .values(is_activated = is_activated)
                .returning(UserModel.id, UserModel.is_activated)
                )
        updated_user = await self.session.scalar(stmt)

        if not updated_user:
            raise UserNotFoundException

        return SuccessResponse(message=constants.USER_STATUS_UPDATED)
    
    
    async def restore_user(self, user_id: UUID):
        """
        Restore a soft-deleted user by marking them as not deleted.

        Args:
            user_id (UUID): The ID of the user to restore.

        Returns:
            UserModel: The restored user model.

        Raises:
            UserNotFoundException: If the user with the given UUID is not found or is not deleted.
        """
        stmt=(update(UserModel).where(UserModel.id == user_id, UserModel.is_deleted.is_(True))
             .values(is_deleted=False)
             .returning(UserModel.id)
             )
        restored_user = await self.session.scalar(stmt)

        if not restored_user:
            raise UserNotFoundException

        return SuccessResponse(message=constants.USER_RESTORED)
    

    async def logout(self, request: Request)-> JSONResponse:
        """
        Log out a user by invalidating their authentication tokens.

        Args:
            request (Request): The incoming request object containing authentication cookies.

        Returns:
            JSONResponse: A response with success message and cookies cleared.

        Raises:
            UserNotLogginException: If the user is not logged in.
            InvalidJWTTokenException: If the access token is expired or invalid.
        """
        access_token = (
        request.cookies.get("accessToken")
        or request.cookies.get("adminAccessToken")
    )
        
        if not access_token:
            raise UserNotLogginException

        try:
            payload = jwt.decode(
                access_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )

            role = payload.get("role")
            if not role:
                raise INVALID_TOKEN_OR_PAYLOAD

        except jwt.ExpiredSignatureError:
            raise InvalidJWTTokenException(constants.EXPIRED_TOKEN)

        except jwt.InvalidTokenError:
            raise INVALID_TOKEN_OR_PAYLOAD
            

        response = JSONResponse(
                        content={
                            "status": "SUCCESS",
                            "message": constants.LOG_OUT
                        }
                    )
        return delete_cookies(response=response, role=role)
    
    
    async def assign_faculty_to_course(self, req: AssignFacultyRequest):
        """
        Assign a faculty member to one or more courses.

        Args:
            req (AssignFacultyRequest): Request object containing faculty_id and list of course_ids.

        Returns:
            dict: A success message indicating faculty assignment completion.

        Raises:
            UserNotFoundException: If the faculty member with the given ID is not found.
            UserNotFaculty: If the user is not a faculty member.
            CourseNotFoundException: If any of the specified courses are not found.
        """
        faculty = await self.session.scalar(
            select(UserModel)
            .options(selectinload(UserModel.role_ref))
            .where(UserModel.id == req.faculty_id))
        
        if not faculty:
            raise UserNotFoundException
        
        if faculty.role_ref.role != Roles.FACULTY:
            raise UserNotFaculty
        
        result = await self.session.scalars(
            select(CourseModel).where(CourseModel.id.in_(req.course_id))
        )

        courses = result.all() 
        if len(courses) != len(req.course_id):
            raise CourseNotFoundException

    # 4️⃣ Assign faculty to each course
        for course in courses:
            course.faculty_id = req.faculty_id

        return SuccessResponse(message=constants.ASSIGN_COURSES_TO_FACULTY)
    


    async def get_student_with_courses(self, language: str):
        """
        Retrieve all students with their enrolled courses in a specified language.

        Args:
            language (str): The language code for course translations (e.g., 'en', 'es').

        Returns:
            list[UserModel]: A list of student users with their courses, including translated course names.
        """
        result = await self.session.scalars(
            select(UserModel)
            .options(
                selectinload(UserModel.courses).selectinload(CourseModel.translations),
                with_loader_criteria(UserModel,UserModel.is_deleted == False)
            )
            # .join(UserModel.role_ref)  # join only for filtering
            .where(UserModel.role_ref.has(RoleModel.role == Roles.STUDENT))
        )
        students = result.all()

        # add a non‑persistent attribute so we don't mutate the mapped column
        for student in students:
            for course in student.courses:
                translation = next(
                    (t for t in course.translations if t.language_code == language),
                    None,
                )
                if not translation:
                    translation = next(
                        (t for t in course.translations if t.language_code == LanguageEnum.EN),
                        None,
                    )

                course.translated_name = translation.course_name if translation else course.course_name

        return students
    
    async def get_course_with_more_than_one_student(self):
        """
        Retrieve courses that have more than one student enrolled.

        Returns:
            list[str]: A list of course names that have multiple students.
        """
        subq = (
            select(Association.course_id)
            .group_by(Association.course_id)
            .having(func.count(Association.user_id)>1)
            .subquery()
        )
        stmt = select(CourseModel.course_name).where(CourseModel.id.in_(subq))
        result = await self.session.scalars(stmt)
        students = result.all()
        return students
    

    async def get_faculty_with_courses(self, language: str):
        """
        Retrieve all faculty members with their assigned courses in a specified language.

        Args:
            language (str): The language code for course translations (e.g., 'en', 'es').

        Returns:
            list[UserModel]: A list of faculty users with their assigned courses, including translated course names.
        """
        result = await self.session.scalars(
            select(UserModel)
            .options(selectinload(UserModel.faculty_courses).selectinload(CourseModel.translations))
            .where(
                UserModel.role_ref.has(RoleModel.role == Roles.FACULTY), UserModel.is_deleted.is_(False))
        )
        faculty_members = result.all()

        for faculty in faculty_members:
            for course in faculty.faculty_courses:
                # try requested language first
                translation = next(
                    (t for t in course.translations if t.language_code == language),
                    None,
                )
                # fallback english
                if not translation:
                    translation = next(
                        (t for t in course.translations if t.language_code == LanguageEnum.EN),
                        None,
                    )
                # stash translated value, avoid mutating mapped attr
                course.translated_name = translation.course_name if translation else course.course_name
        return faculty_members
    
    async def rank_student(self, params:Params) :
        """
        Retrieve a paginated list of students ranked by the number of courses they are enrolled in.

        Args:
            params (Params): Pagination parameters to control the page size and number.

        Returns:
            Page[dict]: A paginated list of students with their rank and total course count.
        """
        stmt = (select(UserModel.id, 
                      UserModel.first_name,
                      UserModel.last_name,
                      func.count(Association.course_id).label("total_courses"),
                      func.rank()
                      .over(order_by=func.count(Association.course_id).desc())
                      .label("rank"),)
                      .join(Association, Association.user_id == UserModel.id)
                      .where(
                          UserModel.role_ref.has(RoleModel.role == Roles.STUDENT),
                          UserModel.is_deleted.is_(False)
                      )
                      .group_by(UserModel.id)
                      )
        page = await paginate(self.session, stmt, params)

    # convert Row → dict
        page.items = [dict(item._mapping) for item in page.items]

        return page

