from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from apps.enroll.schemas.request import EnrollStudentsToCourseRequest
from apps.course.models.course import CourseModel
from apps.student.models.student import StudentModel
from apps.user.exceptions import (
    DuplicateEmailException,
    InvalidCredentialsException,
    UserNotFoundException,
    CourseNotFoundException
)


from core.db import db_session



class EnrollService:
    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)])->None:
        self.session = session
        
    async def enroll_students_to_course(self, req: EnrollStudentsToCourseRequest)->JSONResponse:
        result = await self.session.execute(
            select(CourseModel).options(selectinload(CourseModel.students))
            .where(CourseModel.id==req.course_id)
        )
        course = result.scalar_one_or_none()

        if not course:
            raise CourseNotFoundException
        
        result = await self.session.execute(
            select(StudentModel).where(StudentModel.id.in_(req.student_ids))
        )
        students = result.scalars().all()

        if not students:
            raise UserNotFoundException
        
        for student in students:
            if student not in course.students:
                course.students.append(student)

        return {"message": "Students enrolled successfully"}
    
    
    async def get_course_with_students(self, course_id: UUID):
        result = await self.session.execute(
            select(CourseModel).options(selectinload(CourseModel.students))
            .where(CourseModel.id==course_id)
        )
        course = result.scalar_one_or_none()

        if not course:
            raise CourseNotFoundException
        
        return course


    #     student = await self.session.get(StudentModel, student_id)
    #     course = await self.session.get(CourseModel, course_id)

    #     if not student or not course:
    #         raise ValueError("Invalid student or course ID")

    #     student.courses.append(course)

    #     await self.session.flush()

    #     return {"message": "Student enrolled successfully"}

