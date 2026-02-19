from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status, Body, Path, Request
from fastapi_pagination import Page, Params

import constants
from apps.faculty.schemas.request import FacultyRequest
from apps.faculty.models.faculty import FacultyModel
from apps.faculty.services.faculty import FacultyService
from apps.faculty.schemas.response import FacultyResponse
from core.utils.schema import BaseResponse
from apps.faculty.schemas.request import FacultyLoginRequest
from core.auth import HasPermission
from core.types import RoleType
from core.utils.set_cookies import set_auth_cookies
from fastapi.responses import JSONResponse




router = APIRouter(prefix="/faculty", tags=["Faculty"])

@router.get("")
async def root_faculty():
    return {"messge": "Faculty panel"}

@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    name="faculty login",
    description="faculty login",
    operation_id="faculty_login"
)
async def faculty_login(
    request: Request,
    body: Annotated[FacultyLoginRequest, Body()],
    service: Annotated[FacultyService, Depends()],
) -> JSONResponse:
    res = await service.login_faculty(request=request, **body.model_dump())
    if "access_token" in res and res.get("access_token"):
        data = {"status": constants.SUCCESS, "code": status.HTTP_200_OK, "data": res}
        response = JSONResponse(content=data)
        return set_auth_cookies(response, res, RoleType.FACULTY)

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    name="Create faculty",
    description="Create faculty",
    operation_id="create_faculty"
)
async def create_faculty(
    body: Annotated[FacultyRequest, Body()],
    service: Annotated[FacultyService, Depends()],
)->BaseResponse[FacultyResponse]:
    return BaseResponse(
        data= await service.create_faculty(body)
    )

@router.get(
        "/faculties",
        status_code=status.HTTP_200_OK,
        dependencies=[Depends(HasPermission(RoleType.FACULTY))],
        name="get all faculties",
        description="get all faculties",
        operation_id="get_all_faculties"
)
async def get_all_faculties(
    page_params: Annotated[Params, Depends()],
    service: Annotated[FacultyService, Depends()]
) -> BaseResponse[Page[FacultyResponse]]:
    return BaseResponse(data = await service.get_all_faculties(param=page_params))



@router.get(
    "/{faculty_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(HasPermission(RoleType.FACULTY))],
    name="get faculty by id",
    description="get faculty by id",
    operation_id="get_faculty_by_id",
)
async def get_faculty_by_id(
    faculty_id: Annotated[UUID, Path()],
    service: Annotated[FacultyService, Depends()]
) -> BaseResponse[FacultyResponse]:
    return BaseResponse(
        data= await service.get_faculty_by_id(faculty_id=faculty_id)
    )

@router.delete(
    "/{faculty_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(HasPermission(RoleType.FACULTY))],
    name="delete faculty by id",
    description="delete faculty by id",
    operation_id="delete_faculty_by_id",
)
async def delete_faculty_by_id(
    faculty_id: Annotated[UUID, Path()],
    service: Annotated[FacultyService, Depends()]
):
    await service.delete_faculty_by_id(faculty_id=faculty_id)