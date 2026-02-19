from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status, Body, Path, Request
from fastapi.responses import JSONResponse
from fastapi_pagination import Page, Params

import constants
from apps.student.models.student import StudentModel
from apps.student.schemas.request import StudentRequest, StudentLoginRequest
from apps.student.schemas.response import StudentResponse
from apps.student.services.student import StudentService
from core.utils.schema import BaseResponse
from core.auth import HasPermission
from core.types import RoleType
from apps.user.schemas.request import EncryptedRequest
from core.utils.set_cookies import set_auth_cookies

router = APIRouter(prefix="/student", tags=["Student"])

@router.get("")
async def root_student():
    return {"messge": "Student panel"}


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    name="student login",
    description="student login",
    operation_id="student_login"
)
async def student_login(
    request: Request,
    body: Annotated[StudentLoginRequest, Body()],
    service: Annotated[StudentService, Depends()],
) -> JSONResponse:
    res = await service.login_student(request=request, **body.model_dump())
    if "access_token" in res and res.get("access_token"):
        data = {"status": constants.SUCCESS, "code": status.HTTP_200_OK, "data": res}
        response = JSONResponse(content=data)
        return set_auth_cookies(response, res, RoleType.STUDENT)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    name="Create student",
    description="Create student",
    operation_id="create_student"
)
async def create_student(
    body: Annotated[StudentRequest, Body()],
    service: Annotated[StudentService, Depends()],
)->BaseResponse[StudentResponse]:
    return BaseResponse(
        data= await service.create_student(body)
    )


@router.get(
        "/students",
        status_code=status.HTTP_200_OK,
        dependencies=[Depends(HasPermission(RoleType.STUDENT))],
        name="get all students",
        description="get all students",
        operation_id="get_all_students"
)
async def get_all_students(
    page_params: Annotated[Params, Depends()],
    service: Annotated[StudentService, Depends()]
) -> BaseResponse[Page[StudentResponse]]:
    return BaseResponse(data = await service.get_all_students(param=page_params))

@router.get(
    "/{student_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(HasPermission(RoleType.STUDENT))],
    name="get student by id",
    description="get student by id",
    operation_id="get_student_by_id",
)
async def get_student_by_id(
    student_id: Annotated[UUID, Path()],
    service: Annotated[StudentService, Depends()]
) -> BaseResponse[StudentResponse]:
    return BaseResponse(
        data= await service.get_student_by_id(student_id=student_id)
    )

@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(HasPermission(RoleType.STUDENT))],
    name="delete student by id",
    description="delete student by id",
    operation_id="delete_student_by_id",
)
async def delete_student_by_id(
    student_id: Annotated[UUID, Path()],
    service: Annotated[StudentService, Depends()]
):
    await service.delete_student_by_id(student_id=student_id)