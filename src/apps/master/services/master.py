import json
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.master.schemas import AllEnumResponse
from config import settings
from core.db import db_session


class MasterService:
    """
    Service with methods to handle master authentication and information.

    This service provides methods for creating master, logging in, and retrieving master information.
    """

    def __init__(self, session: Annotated[AsyncSession, Depends(db_session)]) -> None:
        """
        Initialize masterService with a database session
        This method also calls a database connection which is injected here.

        Args:
            session (AsyncSession): An asynchronous database connection.
        """
        self.session = session

    async def get_all_enmus(self) -> AllEnumResponse:
        """
        Retrieve all enum details from a JSON file.

        Returns:
            AllEnumResponse: Response object containing all enum details.
        """
        with open(settings.MASTER_ENUM_FILE_PATH, encoding="utf-8") as file_size:
            data = json.load(file_size)

        return AllEnumResponse(enums=data)
