from uuid import UUID
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from apps.faculty.models.faculty import FacultyModel
from apps.user.exceptions import UserNotFoundException
from core.db import db_session


class FacultyCourseService:

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)])->None:
        self.session = session

    async def get_faculty_with_courses(self, faculty_id: UUID):
        result = await self.session.execute(
            select(FacultyModel).options(selectinload(FacultyModel.courses))
            .where(FacultyModel.id==faculty_id)
        )
        faculty = result.scalar_one_or_none()

        if not faculty:
            raise UserNotFoundException
        
        return faculty