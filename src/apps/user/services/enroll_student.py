from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from apps.user.schemas.enroll_request import EnrollStudentsToCourseRequest, SelfEnrollRequest
from apps.course.models.course import CourseModel
from apps.user.models.user import UserModel, RoleModel
from apps.user.exceptions import (
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
            select(UserModel).where(UserModel.id.in_(req.student_ids))
        )
        students = result.scalars().all()

        if not students:
            raise UserNotFoundException
        
        for student in students:
            if student.role_id != 2:
                raise HTTPException(
                    status_code=400,
                    detail=f"User {student.id} is not a student"
            )
            if student not in course.students:
                course.students.append(student)

        return {"message": "Students enrolled successfully"}
    

    async def   self_enroll_to_course(self, req: SelfEnrollRequest, current_user:UserModel)->JSONResponse:

        if current_user.role_id != 2:
            raise HTTPException(
                status_code=400,
                detail=f"User {current_user.id} is not a student"
            )
        
        result = await self.session.execute(
            select(CourseModel).options(selectinload(CourseModel.students))
            .where(CourseModel.id.in_(req.course_ids))
        )
        courses = result.scalars().all()

        if not courses:
            raise CourseNotFoundException
        
        for course in courses:
            if current_user not in course.students:
                course.students.append(current_user)

        return {"message": "Student enrolled in selected courses"}
    
    

    

