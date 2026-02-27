from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends,status, Body, UploadFile, File
from fastapi.responses import StreamingResponse

from apps.user.schemas.enroll_request import EnrollStudentsToCourseRequest, SelfEnrollRequest
from apps.user.services.enroll_student import EnrollService
from apps.user.schemas.enroll_response import EnrollStudentsToCourseResponse
from core.auth import AdminHasPermission, HasPermission
from core.utils.schema import BaseResponse
from apps.user.models.user import UserModel
from io import BytesIO

router = APIRouter(prefix="/enroll", tags=["Enrollment"])

@router.get("")
async def root_course():
    return {"messge": "Enrollment panel"}

@router.post(
        "/course/enroll-students",
        status_code=status.HTTP_200_OK,
        dependencies=[Depends(AdminHasPermission())],
        name="Enroll students to course",
        description="Enroll students to course",
        operation_id="enroll_students_to_course"
             )
async def enroll_students_self(
    request:Annotated[EnrollStudentsToCourseRequest, Body()],
    service: Annotated[EnrollService, Depends()],
):
    return await service.enroll_students_to_course(request)


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
):
    return await service.self_enroll_to_course(request, current_user)
    

@router.get("/export-template",
            name = "Enrollment template",
            operation_id="enrol_template",
            dependencies=[Depends(AdminHasPermission())],
            )
async def export_template(
    service: Annotated[EnrollService, Depends()])-> StreamingResponse:
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
    result = await service.import_enrollment(file)
    return BaseResponse(data=result)


