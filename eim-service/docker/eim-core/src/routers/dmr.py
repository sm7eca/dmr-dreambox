
import os
from fastapi import APIRouter, Path, status, Response
from common.definitions import Repeater
from common.logger import get_logger
from common.brandmeister import Brandmeister
from db.mongodb import MongoDB
from typing import Optional

logger = get_logger("routers.dmr", log_level=os.getenv("EIM_LOG_LEVEL", "INFO"))

router = APIRouter(
    prefix="/dmr",
    tags=["dmr"],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Not found"},
        status.HTTP_501_NOT_IMPLEMENTED: {"description": "Endpoint not implemented yet"},
        status.HTTP_204_NO_CONTENT: {"description": "No entry found in DB"}
    }
)

path_dmr_id = Path(..., gt=0, example=240701, description="unique DMR ID, > 0")


@router.get(
    "/{dmr_id}",
    response_model=Optional[Repeater],
    status_code=status.HTTP_200_OK,
    description="Retrieve detailed DMR endpoint information for given DMR ID"
)
async def repeater_dmrid(
        dmr_id: int = path_dmr_id,
        response: Response = Response()
):

    db = MongoDB()

    list_repeater = db.get_repeater_by_dmrid(dmr_id)
    length = len(list_repeater)
    if list_repeater:
        logger.debug(f"received {length} repeater from DB")

        bm = Brandmeister()
        if length > 1:
            logger.critical(f"unexpected number of results for DMR_ID: {dmr_id}, expected 0/1")

        # fetch talk groups
        tgs = bm.get_talk_groups(dmr_id=dmr_id)

        list_repeater[0].tg = tgs
        list_repeater[0].max_ts = len(set([tg.ts for tg in tgs]))

        return_data = list_repeater[0]
        logger.info(f"received {len(tgs)} talk groups for DMR: {dmr_id}")
    else:
        response.status_code = status.HTTP_204_NO_CONTENT
        return_data = None

    return return_data
