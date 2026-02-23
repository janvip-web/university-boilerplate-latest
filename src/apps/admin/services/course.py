import json
from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, Request, Query
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import and_, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from apps.course.models.course import CourseModel
from apps.course.schemas.request import CourseRequest
import constants
from apps.user.exceptions import (
    CourseNotFoundException,
)

from config import settings
from core.db import db_session
from core.exceptions import BadRequestError, UnauthorizedError



class AdminCourseService:

    def __init__(self, session:Annotated[AsyncSession, Depends(db_session)]):
        self.session = session

    async def create_course(self, course_req: CourseRequest) -> CourseModel:
        course_name = course_req.course_name
        course_credit = course_req.course_credit
        course_description = course_req.course_description

        course = CourseModel.create(
            course_name=course_name,
            course_credit=course_credit,
            course_description=course_description
        )
        self.session.add(course)
        return course
    
    async def get_all_courses(self, param: Params) -> Page[CourseModel]:
        stmt = select(CourseModel)
        return await paginate(self.session, stmt, param)
    
    
    async def get_course_by_id(self, course_id:UUID):
        course = await self.session.scalar(
            select(CourseModel).where(CourseModel.id == course_id)
        )
        if course == None:
            raise CourseNotFoundException
        return course
    
    async def update_course_by_id(self, course_id:UUID, course_req:CourseRequest):
        course = await self.session.scalar(
            select(CourseModel).where(CourseModel.id == course_id)
        )
        if course == None:
            raise CourseNotFoundException
        
        course.course_name = course_req.course_name
        course.course_credit = course_req.course_credit
        course.course_description = course_req.course_description

        self.session.add(course)
        return course
    
    async def delete_course_by_id(self, course_id:UUID):
        course = await self.session.scalar(
            select(CourseModel).where(CourseModel.id == course_id)
        )
        if course == None:
            raise CourseNotFoundException
        
        await self.session.delete(course)
        return course