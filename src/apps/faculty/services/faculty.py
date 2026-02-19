from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only
from sqlalchemy import and_, or_, select
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

from core.db import db_session
from apps.user.exceptions import (
    DuplicateEmailException,
    InvalidCredentialsException,
    UserNotFoundException,
)
from apps.faculty.schemas.request import FacultyRequest
from apps.faculty.models.faculty import FacultyModel
from core.common_helpers import validate_input_fields, create_tokens
from core.utils.hashing import hash_password

class FacultyService:
    
    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)])->None:
        self.session = session

    async def login_faculty(self, request: Request, email:str, password:str):
        
        faculty = await self.session.scalar(
            select(FacultyModel).where(
                and_(FacultyModel.email == email, FacultyModel.password == password)
            )
        )
        if not faculty:
            raise InvalidCredentialsException
        
        # return {
        #     "id": student.id,
        #     "email": student.email,
        #     "first_name": student.first_name,
        #     "last_name": student.last_name
        # }
        return await create_tokens(user_id=faculty.id, role=faculty.role)

    async def create_faculty(self, faculty_request: FacultyRequest)->FacultyModel:

        first_name = faculty_request.first_name
        last_name = faculty_request.last_name
        email = faculty_request.email
        phone = faculty_request.phone
        password = faculty_request.password
        dept_name = faculty_request.dept_name

        validate_input_fields(first_name=first_name,
                              email=email,
                              phone=phone,
                              password=password)
        
        faculty = await self.session.scalar(
            select(FacultyModel)
            .options(load_only(FacultyModel.email))
            .where(or_(FacultyModel.email==email, FacultyModel.phone==phone))
        )
        if faculty:
            raise DuplicateEmailException
        
        faculty = FacultyModel.create(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            hashed_pass=await hash_password(password),
            password=password,
            email=email,
            dept_name=dept_name
        )
        self.session.add(faculty)
        return faculty
    
    async def get_all_faculties(self, param: Params) -> Page[FacultyModel]:
        stmt = select(FacultyModel).options(
            load_only(
                FacultyModel.first_name,
                FacultyModel.last_name,
                FacultyModel.email,
                FacultyModel.dept_name
            )
        )
        return await paginate(self.session, stmt, param)
        
    
    async def get_faculty_by_id(self, faculty_id:UUID):
        searched_faculty = await self.session.scalar(
            select(FacultyModel)
            .options(
                load_only(
                    FacultyModel.id,
                    FacultyModel.first_name,
                    FacultyModel.last_name,
                    FacultyModel.email,
                    FacultyModel.dept_name
                )
            )
            .where(FacultyModel.id == faculty_id)
        )

        if not searched_faculty:
            raise UserNotFoundException
        return searched_faculty


    async def delete_faculty_by_id(self, faculty_id:UUID):
        searched_faculty = await self.session.scalar(
            select(FacultyModel)
            .where(FacultyModel.id == faculty_id)
        )

        if not searched_faculty:
            raise UserNotFoundException
        
        return await self.session.delete(searched_faculty)