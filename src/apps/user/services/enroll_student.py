from typing import Annotated
from uuid import uuid4

from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.datavalidation import DataValidation
from io import BytesIO
from fastapi import Depends, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from apps.user.schemas.enroll_request import EnrollStudentsToCourseRequest, SelfEnrollRequest
from apps.course.models.course import CourseModel, Association
from apps.user.models.user import UserModel, RoleModel
from apps.user.exceptions import (
    UserNotFoundException,
    CourseNotFoundException,
    UserNotStudent,
    InvalidFileType
)
from core.db import db_session
from constants.roles import Roles



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
            select(UserModel)
            .options(selectinload(UserModel.role_ref)).where(UserModel.id.in_(req.student_ids))
        )
        students = result.scalars().all()

        if not students:
            raise UserNotFoundException
        
        for student in students:
            if student.role_ref.role != Roles.STUDENT:
                raise UserNotStudent

            if student not in course.students:
                course.students.append(student)

        return {"message": "Students enrolled successfully"}
    

    async def   self_enroll_to_course(self, req: SelfEnrollRequest, current_user:UserModel)->JSONResponse:

        if current_user.role_ref.role != Roles.STUDENT:
            raise UserNotStudent
        
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
    
    async def export_enrollment_template(self) -> StreamingResponse:

        # 1️⃣ Fetch students properly
        result = await self.session.scalars(
            select(UserModel)
            .options(selectinload(UserModel.role_ref))
            .where(
                RoleModel.role == Roles.STUDENT,
                UserModel.is_deleted == False
            )
        )
        students = result.all()

        # 2️⃣ Fetch courses properly
        result = await self.session.scalars(
            select(CourseModel)
        )
        courses = result.all()

        # 3️⃣ Create workbook
        wb = Workbook()
        ws_main = wb.active
        ws_main.title = "Enrollment"

        ws_ref = wb.create_sheet("Reference")

        # 4️⃣ Headers
        ws_main.append(["Student Name", "Course Name"])

        # 5️⃣ Fill reference sheet
        ws_ref["A1"] = "Students"
        for i, student in enumerate(students, start=2):
            ws_ref[f"A{i}"] = student.first_name

        ws_ref["B1"] = "Courses"
        for i, course in enumerate(courses, start=2):
            ws_ref[f"B{i}"] = course.course_name

        # 6️⃣ Add dropdown validation
        student_range = f"Reference!$A$2:$A${len(students)+1}"  # create drop down
        course_range = f"Reference!$B$2:$B${len(courses)+1}"

        dv_student = DataValidation(type="list", formula1=f"={student_range}")
        dv_course = DataValidation(type="list", formula1=f"={course_range}")

        ws_main.add_data_validation(dv_student)
        ws_main.add_data_validation(dv_course)

        dv_student.add("A2:A100")
        dv_course.add("B2:B100")

        # Hide reference sheet
        ws_ref.sheet_state = "hidden"

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        return buffer.getvalue()



    async def import_enrollment(self, file: UploadFile):

        if not file.filename.endswith(".xlsx"):
            raise InvalidFileType

        file_bytes = await file.read()

        wb = load_workbook(BytesIO(file_bytes))
            # DEBUG
        print("Available sheets:", wb.sheetnames)
        sheet = wb.active
        inserted = 0


        for row in sheet.iter_rows(min_row=2, values_only=True):
            student_name, course_name = row

            student = await self.session.scalar(
                select(UserModel).where(UserModel.first_name == student_name)
            )

            course = await self.session.scalar(
                select(CourseModel).where(CourseModel.course_name == course_name)
            )

            if not student or not course:
                continue

            exists = await self.session.scalar(
                select(Association).where(
                    Association.user_id == student.id,
                    Association.course_id == course.id
                )
            )

            if not exists:
                self.session.add(
                    Association.create(
                        user_id=student.id,
                        course_id=course.id
                    )
                )
                inserted += 1

        return {"message": "Enrollment imported successfully,",
                      "inserted_records": inserted}

