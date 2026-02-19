from typing import Annotated

from fastapi import APIRouter, Depends, status

from apps.master.schemas import AllEnumResponse
from apps.master.services import MasterService
from core.utils import BaseResponse

router = APIRouter(prefix="/master", tags=["Master"])


@router.get(
    "/enums",
    status_code=status.HTTP_200_OK,
    description="Get All enum Masters Details",
    operation_id="get_master_details",
)
async def get_all_master_details(
    service: Annotated[MasterService, Depends()]
) -> BaseResponse[AllEnumResponse]:
    """
    Retrieve all master details including enums and other master data.

    This endpoint fetches various master data categories such as enums and returns
    them in a structured response.

    Returns:
        BaseResponse[AllMasterResponse]: A response containing all master details.
    """
    return BaseResponse(data=await service.get_all_enmus())
