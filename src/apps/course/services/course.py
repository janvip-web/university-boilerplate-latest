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
    CourseNotFoundException
)
from core.db import db_session
from apps.course.schemas.request import CourseRequest
from apps.course.models.course import CourseModel
from apps.student.models.student import StudentModel
from apps.faculty.models.faculty import FacultyModel
from core.common_helpers import validate_input_fields
from core.utils.hashing import hash_password

class CourseService:
    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)])->None:
        self.session = session


    async def create_course(self, course_request: CourseRequest)->CourseModel:

        course_name = course_request.course_name
        course_credit = course_request.course_credit
        faculty_id = course_request.faculty_id

        # faculty = await self.session.get(FacultyModel, faculty_id)

        # if faculty == None:
        #     raise UserNotFoundException

        # validate_input_fields(
        #     course_name = course_name,
        #     course_credit = course_credit
        # )
        
        course = CourseModel.create(
            course_name=course_name,
            course_credit=course_credit,
            faculty_id=faculty_id
        )
        self.session.add(course)
        return course
    
    
    async def get_all_courses(self, param: Params) -> Page[CourseModel]:
        stmt = select(CourseModel)
        return await paginate(self.session, stmt, param)
    
    async def get_course_by_id(self, course_id:UUID):
        searched_course = await self.session.scalar(
            select(CourseModel)
            .where(CourseModel.id == course_id)
        )

        if not searched_course:
            raise CourseNotFoundException
        return searched_course
    


# gpt.......................................................................
    # async def enroll_student(
    # self,
    # student_id: UUID,
    # course_id: UUID,
    # ):
    #     student = await self.session.get(StudentModel, student_id)
    #     course = await self.session.get(CourseModel, course_id)

    #     if not student or not course:
    #         raise ValueError("Invalid student or course ID")

    #     student.courses.append(course)

    #     await self.session.flush()

    #     return {"message": "Student enrolled successfully"}

