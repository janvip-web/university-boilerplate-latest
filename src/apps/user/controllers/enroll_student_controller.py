from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends,status, Body, UploadFile, File
from fastapi.responses import StreamingResponse

from apps.user.schemas.enroll_request import EnrollStudentsToCourseRequest, SelfEnrollRequest
from apps.user.services.enroll_student import EnrollService
from apps.user.schemas.enroll_response import EnrollStudentsToCourseResponse
from core.auth import AdminHasPermission, HasPermission
from core.db import Base
from core.utils.schema import BaseResponse
from apps.user.models.user import UserModel
from io import BytesIO

router = APIRouter(prefix="/enroll", tags=["Enrollment"])


@router.post(
        "/course/enroll-students",
        status_code=status.HTTP_200_OK,
        dependencies=[Depends(AdminHasPermission())],
        name="Enroll students to course",
        description="Enroll students to course",
        operation_id="enroll_students_to_course"
             )
async def enroll_students(
    request:Annotated[EnrollStudentsToCourseRequest, Body()],
    service: Annotated[EnrollService, Depends()],
)->BaseResponse:
    """
    Enroll a batch of students in a course (admin only).

    This endpoint allows administrators to enroll multiple students into a
    specified course using either a list or uploaded data.

    Args:
        request: EnrollStudentsToCourseRequest containing course_id and student ids.
        service: EnrollService instance for business logic.

    Returns:
        EnrollStudentsToCourseResponse: Result of the enrollment operation.

    Raises:
        CourseNotFoundException: If the specified course does not exist.
        BadRequestError: If request data is invalid.
        AdminHasPermission: If the caller is not an admin.
    """
    return BaseResponse(
        data = await service.enroll_students_to_course(request))


@router.post(
        "/course/self-enroll",
        status_code=status.HTTP_200_OK,
        name="Self enroll to course",
        description="Self enroll to course",        
        operation_id="self_enroll_to_course"
             )
async def self_enroll_to_course(
    request:Annotated[SelfEnrollRequest, Body()],
    service: Annotated[EnrollService, Depends()],
    current_user: Annotated[UserModel, Depends(HasPermission(role_name="STUDENT"))]
)-> BaseResponse:
    """
    Allow a student to enroll themselves in a course.

    Args:
        request: SelfEnrollRequest containing course_id to enroll in.
        service: EnrollService instance for business logic.
        current_user: The student user initiating the enrollment.

    Returns:
        dict: Confirmation or details of the enrollment.

    Raises:
        CourseNotFoundException: If the course does not exist.
        BadRequestError: If the student is already enrolled or data invalid.
        HasPermission: If the current user is not a student.
    """
    return BaseResponse(data = await service.self_enroll_to_course(request, current_user))

    

@router.get("/export-template",
            name = "Enrollment template",
            operation_id="enrol_template",
            dependencies=[Depends(AdminHasPermission())],
            )
async def export_template(
    service: Annotated[EnrollService, Depends()])-> StreamingResponse:
    """
    Download an Excel template for bulk student enrollment.

    This template can be filled out by admins and later imported using the
    corresponding import endpoint.

    Args:
        service: EnrollService instance for business logic.

    Returns:
        StreamingResponse: Excel file stream of the enrollment template.

    Raises:
        AdminHasPermission: If caller is not an admin.
    """
    file_bytes = await service.export_enrollment_template()

    return StreamingResponse(
        BytesIO(file_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=enrollment_template.xlsx"
        },
    )

@router.post("/import-enrollment",
             name= "Import enrollment",
             operation_id="import_enrollment",
             dependencies=[Depends(AdminHasPermission())]
             )
async def import_enrollment(
    file: Annotated[UploadFile, File()],
    service: Annotated[EnrollService, Depends()]
)->BaseResponse:
    """
    Import student enrollment data from an uploaded Excel file (admin only).

    The file should conform to the enrollment template structure. Records will
    be processed in bulk to enroll students into courses.

    Args:
        file: Uploaded Excel file containing enrollment rows.
        service: EnrollService instance for business logic.

    Returns:
        BaseResponse: Result summary of the import operation.

    Raises:
        BadRequestError: If the file is malformed or contains invalid data.
        AdminHasPermission: If caller is not an admin.
    """
    result = await service.import_enrollment(file)
    return BaseResponse(data=result)


