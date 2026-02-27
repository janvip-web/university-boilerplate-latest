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
    InvalidRequestException
)
from core.exceptions import BadRequestError
from core.db import db_session
from core.enum import LanguageEnum
from apps.user.models.user import UserModel


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
            course_description=course_description,
        )
        self.session.add(course)

        course.translations = [
            CourseTranslationModel(
                language_code = LanguageEnum.EN,
                course_name = course_req.course_name
            )
        ]
        self.session.add(course) # suceess response
        return course

    async def bulk_create_from_csv(self, file) -> dict:
        """Parse an uploaded CSV of courses and insert them in bulk.

        The CSV must have headers: ``course_name``, ``course_credit`` (optional) and
        ``course_description`` (optional). Rows with missing names or invalid
        credit values are skipped and reported in the returned error list.

        Returns a summary dict with ``created`` count and ``errors`` list.
        """


        content = await file.read()
        try:
            text = content.decode("utf-8")
        except Exception:
            raise BadRequestError(message="Unable to decode CSV file; ensure it is UTF-8")

        reader = csv.DictReader(StringIO(text))
        created = []
        errors = []
        row_num = 1

        for row in reader:
            row_num += 1
            name = row.get("course_name")
            credit_raw = row.get("course_credit")
            description = row.get("course_description")
            if not name:
                errors.append({"row": row_num, "error": "course_name is required"})
                continue
            try:
                credit = int(credit_raw) if credit_raw else None
            except ValueError:
                errors.append({"row": row_num, "error": "course_credit must be integer"})
                continue

                # simple duplicate check
            existing = await self.session.scalar(
                select(CourseModel).where(CourseModel.course_name == name)
            )
            if existing:
                errors.append({"row": row_num, "error": "course already exists"})
                continue

            course = CourseModel.create(
                    course_name=name,
                    course_credit=credit,
                    course_description=description,
            )
            self.session.add(course)
                # add default translation for EN
            course.translations = [
                CourseTranslationModel(
                        language_code=LanguageEnum.EN,
                        course_name=name,
                    )
                ]
            created.append(course)
        return {"created": len(created), "errors": errors}
    
    async def add_course_translation(self, course_id:UUID, request:CourseTranslationRequest):
        course = await self.session.scalar(
            select(CourseModel).where(CourseModel.id == course_id)
        )
        
        if not course:
            raise CourseNotFoundException
        
        # if request.language_code == LanguageEnum.EN:
        #     raise BadRequestError(
        #         message="Use update_course API to modify English name"
        #     )
        
        existing_translations = await self.session.scalar(
            select(CourseTranslationModel).where(
            CourseTranslationModel.course_id == course_id,
            CourseTranslationModel.language_code == request.language_code
            )
        )
        if existing_translations:
            raise BadRequestError(
            message=f"Translation already exists for language {request.language_code}"
        )
        translation = CourseTranslationModel(
            course_id=course_id,
            language_code = request.language_code,
            course_name = request.course_name
        )
        self.session.add(translation)
        return translation


    
    def _build_course_query(
        self,
        course_name: str | None,
        course_credit: int | None,
        search: str | None,
        sort_by: str,
        order: str,
        ):

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

        stmt = select(CourseModel)

        # ✅ If both not provided → return empty result
        if not course_name or course_credit is None:
            raise InvalidRequestException(message="Both course_name and course_credit are required.")

        # ✅ Apply BOTH filters together
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
            # ✅ 2️⃣ If no records found
        if not result.items:
            raise CourseNotFoundException(message="No course found matching both course_name and course_credit.")

        return result

    async def get_course_by_id(self, course_id:UUID):
        course = await self.session.scalar(
            select(CourseModel).where(CourseModel.id == course_id)
        )
        if not course:
            raise CourseNotFoundException
        return course
    
    async def update_course_by_id(self, course_id:UUID, course_req:CourseRequest):
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
        
        return updated_course
    
    
    async def delete_course_by_id(self, course_id:UUID):

        stmt = delete(CourseModel).where(CourseModel.id == course_id)
        course = await self.session.execute(stmt)
        if course.rowcount == 0:
            raise CourseNotFoundException

        return {"message": "course deleted successfully"}

    

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
        
        result = await self.session.execute(stmt)
        courses = result.scalars().all()

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