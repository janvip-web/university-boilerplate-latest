from typing import Any

from core.utils.schema import CamelCaseModel


class AllEnumResponse(CamelCaseModel):
    """
    Response model for fetching all master details.

    Attributes:
        enums (Dict[str, Any]): Dictionary containing all master details loaded from JSON.
    """

    enums: dict[str, Any]
