from email import message
from typing import Annotated, Optional
from uuid import UUID
import csv
from io import StringIO
from io import BytesIO
from openpyxl import Workbook

from fastapi import Depends, status
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import and_, select, or_, update, delete, desc, asc, cast, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, selectinload

from apps.course.models.course import CourseModel, CourseTranslationModel
from apps.course.schemas.request import CourseRequest, CourseTranslationRequest
from apps.user.exceptions import (
    CourseNotFoundException,
    InvalidRequestException,
    TranslationExists,
    CourseAlreadyExistsException
)

import constants
from core.db import db_session
from core.enum import LanguageEnum
from core.utils.schema import SuccessResponse


class AdminCourseService:
    """
    Service providing methods for managing admin-related course operations.
    """

    def __init__(self, session:Annotated[AsyncSession, Depends(db_session)]):
        """
        Initialize the AdminCourseService with an asynchronous database session.

        Args:
            session (AsyncSession): Asynchronous database session injected via dependency.
        """
        self.session = session

    async def create_course(self, course_req: CourseRequest):
        """
        Create a new course record in the database.

        Args:
            course_req (CourseRequest): Pydantic schema containing course name, credit,
                and description.

        Returns:
            CourseModel: The newly created course model instance.

        Raises:
            Error: If provided data is invalid or missing required fields.
        """

                # 1️⃣ Check if course already exists
        existing_course = await self.session.scalar(
            select(CourseModel).where(
                CourseModel.course_name == course_req.course_name,
            )
        )

        if existing_course:
            raise CourseAlreadyExistsException 
        
        course_name = course_req.course_name
        course_credit = course_req.course_credit
        course_description = course_req.course_description

        course = CourseModel.create(
            course_name=course_name,
            course_credit=course_credit,
            course_description=course_description,
        )
        self.session.add(course)

        course.translations = [
            CourseTranslationModel(
                language_code = LanguageEnum.EN,
                course_name = course_req.course_name
            )
        ]
         # suceess response
        return SuccessResponse(message=constants.COURSE_CREATED)
    
    async def add_course_translation(self, course_id:UUID, course_name: str, language_code: str):
        """
        Add a translation entry for an existing course.

        Args:
            course_id (UUID): Identifier of the course to translate.
            request (CourseTranslationRequest): Schema containing language_code and
                translated course_name.

        Returns:
            CourseTranslationModel: The newly created translation record.

        Raises:
            CourseNotFoundException: If no course exists with the given ID.
            Error: If a translation for the specified language already exists.
        """
        course = await self.session.scalar(
            select(CourseModel).where(CourseModel.id == course_id)
        )
        
        if not course:
            raise CourseNotFoundException
        
        existing_translations = await self.session.scalar(
            select(CourseTranslationModel).where(
            CourseTranslationModel.course_id == course_id,
            CourseTranslationModel.language_code == language_code
            )
        )
        if existing_translations:
            raise TranslationExists
        
        translation = CourseTranslationModel(
            course_id=course_id,
            language_code = language_code,
            course_name = course_name
        )
        self.session.add(translation)
        return SuccessResponse(message=constants.COURE_TRANSLATION_CREATED)


    
    def _build_course_query(
        self,
        course_name: str | None,
        course_credit: int | None,
        search: str | None,
        sort_by: str,
        order: str,
        ):
        """
        Construct a base SQLAlchemy query for courses with filtering and sorting.

        This internal helper centralizes logic used across several public methods
        to filter by course name, credit, search terms, and sort order.

        Args:
            course_name: Optional substring to match course names.
            course_credit: Optional exact credit value to filter by.
            search: Optional global search term matching name, description, or credit.
            sort_by: Field name used for ordering results.
            order: "asc" or "desc" specifying sort direction.

        Returns:
            sqlalchemy.sql.Select: The constructed query object.
        """

        stmt = select(CourseModel)

        # Filter by course name
        if course_name:
            stmt = stmt.where(
                CourseModel.course_name.ilike(f"%{course_name}%")
            )

        # Filter by course credit
        if course_credit is not None:
            stmt = stmt.where(
                CourseModel.course_credit == course_credit
            )

        # Global search
        if search:
            stmt = stmt.where(
                or_(
                    CourseModel.course_name.ilike(f"%{search}%"),
                    CourseModel.course_description.ilike(f"%{search}%"),
                    cast(CourseModel.course_credit, String).ilike(f"%{search}%")
                )
            )

        # Sorting
        if sort_by == "created_at":
            column = CourseModel.created_at
        elif sort_by == "course_name":
            column = CourseModel.course_name
        elif sort_by == "course_credit":
            column = CourseModel.course_credit
        else:
            column = CourseModel.created_at

        if order == "desc":
            stmt = stmt.order_by(desc(column))
        else:
            stmt = stmt.order_by(asc(column))

        return stmt
    

    async def get_all_courses(self, param: Params, course_name:str|None, course_credit:int|None, search: str|None,
                              sort_by:str, order:str
                              
                              ) -> Page[CourseModel]:
        """
        Retrieve a paginated list of courses with optional filters.

        Args:
            param: Pagination parameters (page size, number).
            course_name: Optional filter for a substring match on course names.
            course_credit: Optional filter for exact credit value.
            search: Optional global search term.
            sort_by: Field name to sort results by.
            order: "asc" or "desc" sort direction.

        Returns:
            Page[CourseModel]: Paginated page of courses matching criteria.
        """
        
        stmt = self._build_course_query(course_name=course_name,
                                        course_credit=course_credit,
                                        search=search,
                                        sort_by=sort_by,
                                        order=order)

        return await paginate(self.session, stmt, param)
    


    async def search_courses_by_name_and_credit(
        self,
        param: Params,
        course_name: str | None,
        course_credit: int | None,
        sort_by: str,
        order: str,
    ) -> Page[CourseModel]:
        """
        Retrieve courses matching both name and credit filters, with pagination.

        Returns an empty paginated result if no courses match the criteria or
        if required parameters are missing.

        Args:
            param: Pagination parameters (page size, number).
            course_name: Substring to match against course names (optional).
            course_credit: Exact credit value to match (optional).
            sort_by: Field name to sort results by.
            order: "asc" or "desc" sort direction.

        Returns:
            Page[CourseModel]: Paginated list of matching courses, empty if no matches.
        """

        stmt = select(CourseModel)

        # If both not provided → return empty result
        if not course_name or course_credit is None:
            return await paginate(self.session, stmt, param)

        # Apply BOTH filters together
        stmt = stmt.where(
            and_(
                CourseModel.course_name.ilike(f"%{course_name}%"),
                CourseModel.course_credit == course_credit
            )
        )

        # Sorting (same logic as before)
        if sort_by == "created_at":
            column = CourseModel.created_at
        elif sort_by == "course_name":
            column = CourseModel.course_name
        elif sort_by == "course_credit":
            column = CourseModel.course_credit
        else:
            column = CourseModel.created_at

        stmt = stmt.order_by(column.desc() if order == "desc" else column.asc())

        result = await paginate(self.session, stmt, param)
        # Return result even if empty
        return result

    async def get_course_by_id(self, course_id:UUID):
        """
        Retrieve a single course by its unique identifier.

        Args:
            course_id (UUID): The ID of the course to fetch.

        Returns:
            CourseModel: The requested course model.

        Raises:
            CourseNotFoundException: If no course exists with the provided ID.
        """
        course = await self.session.scalar(
            select(CourseModel).where(CourseModel.id == course_id)
        )
        if not course:
            raise CourseNotFoundException
        return course
    
    async def update_course_by_id(self, course_id:UUID, course_req:CourseRequest):
        """
        Update an existing course's details.

        Args:
            course_id (UUID): The ID of the course to update.
            course_req (CourseRequest): Schema containing updated course information.

        Returns:
            CourseModel: The updated course model instance.

        Raises:
            CourseNotFoundException: If the course with the given ID does not exist.
        """
        # on do conflit update
        stmt = (update(CourseModel).where(CourseModel.id == course_id)
                .values(
                    course_name = course_req.course_name,
                    course_credit = course_req.course_credit,
                    course_description = course_req.course_description
                )
                .returning(CourseModel))
        
        updated_course = await self.session.scalar(stmt)

        if not updated_course :
            raise CourseNotFoundException
        
        return SuccessResponse(message=constants.COURSE_UPDATED)
    
    
    async def delete_course_by_id(self, course_id:UUID):
        """
        Delete a course by its identifier.

        Args:
            course_id (UUID): The ID of the course to delete.

        Returns:
            dict: A message confirming successful deletion.

        Raises:
            CourseNotFoundException: If no course exists with the provided ID.
        """

        stmt = delete(CourseModel).where(CourseModel.id == course_id)
        course = await self.session.execute(stmt)
        if course.rowcount == 0:
            raise CourseNotFoundException

        return SuccessResponse(message=constants.COURSE_DELETED)

    

    async def export_courses_excel(self, course_name:str|None, course_credit:int|None, search: str|None,
                              sort_by:str, order:str) -> bytes:
        """Return an Excel workbook as bytes containing course rows.

        If ``course_name`` is supplied the result will be filtered by that term.
        """
        stmt = self._build_course_query(course_name=course_name,
                                        course_credit=course_credit,
                                        search=search,
                                        sort_by=sort_by,
                                        order=order)
        
        result = await self.session.scalars(stmt)
        courses = result.all()

        wb = Workbook()
        ws = wb.active
        ws.append(["id", "course_name", "course_credit", "course_description", "created_at"])
        for c in courses:
            ws.append([
                str(c.id),
                c.course_name,
                c.course_credit,
                c.course_description,
                c.created_at.isoformat(),
            ])
        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf.getvalue()