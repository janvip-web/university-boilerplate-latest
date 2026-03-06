from typing import Annotated
from uuid import uuid4

from openpyxl.workbook.defined_name import DefinedName
from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.datavalidation import DataValidation
from io import BytesIO
from fastapi import Depends, UploadFile
from sqlalchemy import insert, select
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
import constants
from core.db import db_session
from constants.roles import Roles
from core.utils.schema import SuccessResponse



class EnrollService:
    """
    Service responsible for student enrollment operations.

    Provides methods for admins to enroll students in courses, allow individual
    students to self-enroll, and export/import enrollment data via spreadsheets.
    """
    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)])->None:
        """
        Initialize the enrollment service with a database session.

        Args:
            session: An asynchronous SQLAlchemy session.
        """
        self.session = session
        
    async def enroll_students_to_course(self, req: EnrollStudentsToCourseRequest)->JSONResponse:
        """
        Enroll a list of students into a specific course (admin-only operation).

        Args:
            req: Request object containing course ID and student IDs.

        Returns:
            JSONResponse: Confirmation message on successful enrollment.

        Raises:
            CourseNotFoundException: If the specified course does not exist.
            UserNotFoundException: If none of the provided students exist.
            UserNotStudent: If any provided user is not a student.
        """
        course = await self.session.scalar(
            select(CourseModel).options(selectinload(CourseModel.students))
            .where(CourseModel.id==req.course_id)
        )

        if not course:
            raise CourseNotFoundException
        
        result = await self.session.scalars(
            select(UserModel)
            .options(selectinload(UserModel.role_ref)).where(UserModel.id.in_(req.student_ids))
        )
        students = result.all()

        if not students:
            raise UserNotFoundException
        
        for student in students:
            if student.role_ref.role != Roles.STUDENT:
                raise UserNotStudent

            if student not in course.students:
                course.students.append(student)

        return SuccessResponse(message=constants.STUDENT_ENROL)
    

    async def   self_enroll_to_course(self, req: SelfEnrollRequest, current_user:UserModel)->JSONResponse:
        """
        Allow a student to enroll themselves in one or more courses.

        Args:
            req: Request containing list of course IDs.
            current_user: The student performing the enrollment.

        Returns:
            JSONResponse: Confirmation of successful enrollment.

        Raises:
            UserNotStudent: If the current user isn't a student.
            CourseNotFoundException: If none of the specified courses exist.
        """

        if current_user.role_ref.role != Roles.STUDENT:
            raise UserNotStudent
        
        result = await self.session.scalars(
            select(CourseModel).options(selectinload(CourseModel.students))
            .where(CourseModel.id.in_(req.course_ids))
        )
        courses = result.all()

        if not courses:
            raise CourseNotFoundException
        
        for course in courses:
            if current_user not in course.students:
                course.students.append(current_user)

        return SuccessResponse(message=constants.STUDENT_ENROL)
    
    async def export_enrollment_template(self) -> StreamingResponse:
        """
        Generate an Excel template for bulk student enrollment.

        The template includes dropdowns populated with current students and courses.

        Returns:
            StreamingResponse: The Excel workbook bytes as a downloadable stream.
        """

        # 1️⃣ Fetch students properly
        result = await self.session.scalars(
            select(UserModel)
            .options(selectinload(UserModel.role_ref))
            .where(
                UserModel.role_ref.has(RoleModel.role == Roles.STUDENT),
                UserModel.is_deleted == False
            )
        )
        students = result.all()

        # 2️⃣ Fetch courses properly
        result = await self.session.scalars(
            select(CourseModel)
        )
        courses = result.all()

        enrollments = (
            await self.session.scalars(
                select(Association.user_id, Association.course_id)
            )
        ).all()

            # Map student -> enrolled course ids
        enrollment_map = {}
        for user_id, course_id in enrollments:
            enrollment_map.setdefault(user_id, set()).add(course_id)

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

            # 6️⃣ Create Dynamic Course Lists Per Student
        start_col = 2  # Column B onward

        for index, student in enumerate(students):
            col_index = start_col + index
            col_letter = ws_ref.cell(row=1, column=col_index).column_letter

            safe_name = student.first_name.replace(" ", "_")

            ws_ref.cell(row=1, column=col_index).value = safe_name

            enrolled_ids = enrollment_map.get(student.id, set())
            row_cursor = 2

            for course in courses:
                if course.id not in enrolled_ids:
                    ws_ref.cell(row=row_cursor, column=col_index).value = course.course_name
                    row_cursor += 1

            # 🔥 CREATE NAMED RANGE HERE
            end_row = row_cursor - 1

            if end_row >= 2:
                range_str = f"Reference!${col_letter}$2:${col_letter}${end_row}"

                defined_name = DefinedName(
                    name=safe_name,
                    attr_text=range_str
                )

                wb.defined_names.add(defined_name)

            # 7️⃣ Add Student Dropdown
        student_range = f"Reference!$A$2:$A${len(students)+1}"
        dv_student = DataValidation(type="list", formula1=f"={student_range}")
        ws_main.add_data_validation(dv_student)
        dv_student.add("A2:A100")

        # 8️⃣ Add Dynamic Course Dropdown using INDIRECT
        dv_course = DataValidation(
            type="list",
            formula1="=INDIRECT($A2)"
        )

        ws_main.add_data_validation(dv_course)
        dv_course.add("B2:B100")

        # Hide reference sheet
        ws_ref.sheet_state = "hidden"

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        return buffer.getvalue()



    async def import_enrollment(self, file: UploadFile):
        """
        Import enrollment data from an uploaded Excel file (admin only).

        Args:
            file: UploadFile containing the enrollment spreadsheet.

        Returns:
            dict: Summary of import results including inserted record count.

        Raises:
            InvalidFileType: If the provided file is not an .xlsx document.
        """

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

        # 🔥 Return proper response
        if inserted == 0:
            return SuccessResponse(
                message=constants.NO_NEW_ENROLLMENT,
            )

        return SuccessResponse(
            message= constants.ENROLLMENT_IMPORTED,
        )

            

