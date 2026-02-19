from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

import constants
from apps.user.exceptions import (
    DuplicateEmailException,
    InvalidCredentialsException,
    UserNotFoundException,
)
from core.db import db_session
from apps.student.schemas.request import StudentRequest
from apps.student.models.student import StudentModel
from core.common_helpers import create_tokens, validate_input_fields
from core.utils.hashing import hash_password

class StudentService:
    
    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)])->None:
        self.session = session

    async def login_student(self, request: Request, email:str, password:str):
        
        student = await self.session.scalar(
            select(StudentModel).where(
                and_(StudentModel.email == email, StudentModel.password == password)
            )
        )
        if not student:
            raise InvalidCredentialsException
        
        # return {
        #     "id": student.id,
        #     "email": student.email,
        #     "first_name": student.first_name,
        #     "last_name": student.last_name
        # }
        return await create_tokens(user_id=student.id, role=student.role)



    async def create_student(self, student_request: StudentRequest)->StudentModel:

        first_name = student_request.first_name
        last_name = student_request.last_name
        email = student_request.email
        phone = student_request.phone
        password = student_request.password
        dob = student_request.dob

        validate_input_fields(
            first_name=first_name,
            email=email,
            phone=phone,
            password=password
        )

        #  generate error if email or phone is same
        student = await self.session.scalar(
            select(StudentModel)
            .options(load_only(StudentModel.email))
            .where(or_(StudentModel.email==email, StudentModel.phone==phone))
        )
        if student:
            raise DuplicateEmailException
        
        student = StudentModel.create(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            hashed_pass=await hash_password(password),
            password=password,
            email=email,
            dob=dob,
        )
        self.session.add(student)
        return student
    
    async def get_all_students(self, param: Params) -> Page[StudentModel]:
        stmt = select(StudentModel).options(
            load_only(
                StudentModel.first_name,
                StudentModel.last_name,
                StudentModel.email,
                StudentModel.dob
            )
        )
        return await paginate(self.session, stmt, param)
    
    async def get_student_by_id(self, student_id:UUID):
        searched_student = await self.session.scalar(
            select(StudentModel)
            .options(
                load_only(
                    StudentModel.id,
                    StudentModel.first_name,
                    StudentModel.last_name,
                    StudentModel.email,
                    StudentModel.dob
                )
            )
            .where(StudentModel.id == student_id)
        )

        if not searched_student:
            raise UserNotFoundException
        return searched_student
    
    async def delete_student_by_id(self, student_id:UUID):
        searched_student = await self.session.scalar(
            select(StudentModel)
            .where(StudentModel.id == student_id)
        )

        if not searched_student:
            raise UserNotFoundException
        
        return await self.session.delete(searched_student)
