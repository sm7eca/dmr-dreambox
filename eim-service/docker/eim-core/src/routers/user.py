
import os
from fastapi import APIRouter, Path, status, Response
from common.definitions import DmrUser
from common.logger import get_logger

from db.mongodb import MongoDB
from typing import Optional

logger = get_logger("routers.user", log_level=os.getenv("EIM_LOG_LEVEL", "INFO"))


router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Not found"},
        status.HTTP_501_NOT_IMPLEMENTED: {"description": "Endpoint not implemented yet"},
        status.HTTP_204_NO_CONTENT: {"description": "No entry found in DB"}
    }
)

path_dmr_id = Path(..., gt=0, example=2400011, description="unique DMR ID, > 0")


@router.get(
    "/{dmr_id}",
    response_model=Optional[DmrUser],
    status_code=status.HTTP_200_OK,
    summary="Returns information about a user for a given DMR ID"
)
async def user_dmrid(
        dmr_id: int = path_dmr_id,
        response: Response = Response()
):

    db = MongoDB()

    user = db.get_user_by_dmrid(dmr_id)

    if not user:
        logger.debug(f"No user received for {dmr_id}")
        response.status_code = status.HTTP_204_NO_CONTENT
        return None
    else:
        return user
