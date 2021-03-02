"""Implement Repeater routers"""

from fastapi import APIRouter, Response, status
from common.definitions import Repeater, RepeaterItem
from common.logger import get_logger
from common.tools import compute_end_index
from db.mongodb import MongoDB
from typing import Optional, List


logger = get_logger("routers.repeater")

router = APIRouter(
    prefix="/repeater",
    tags=["repeater"],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Not found"},
        status.HTTP_501_NOT_IMPLEMENTED: {"description": "Endpoint not implemented yet"},
        status.HTTP_204_NO_CONTENT: {"description": "No entry found in DB"}
    }
)


@router.get("/master/{master_id}", response_model=List[RepeaterItem], status_code=status.HTTP_200_OK)
async def repeater_master(master_id: int, limit: int = 0, skip: int = 0, response: Response = Response()):

    db = MongoDB()
    repeaters = db.get_repeater_by_master(master_id=master_id)
    length = len(repeaters)

    if repeaters:
        logger.debug(f"received {length} repeater from DB")
        start, end = compute_end_index(length, skip, limit)
    else:
        response.status_code = status.HTTP_204_NO_CONTENT
        start = end = 0

    return repeaters[start:end]


@router.get("/callsign/{callsign}", response_model=List[RepeaterItem], status_code=status.HTTP_200_OK)
async def repeater_master_callsign(call_sign: str, limit: int = 0, skip: int = 0, response: Response = Response()):

    db = MongoDB()
    repeaters = db.get_repeater_by_callsign(call_sign)
    length = len(repeaters)
    if repeaters:
        logger.debug(f"received {length} repeater from DB")
        start, end = compute_end_index(length, skip, limit)
    else:
        start = end = 0
        response.status_code = status.HTTP_204_NO_CONTENT

    return repeaters[start:end]


@router.get("/dmr/{dmr_id}", response_model=List[Repeater], status_code=status.HTTP_200_OK)
async def repeater_master_dmrid(dmr_id: int, response: Response = Response()):

    db = MongoDB()
    repeaters = db.get_repeater_by_dmrid(dmr_id)
    length = len(repeaters)
    if repeaters:
        logger.debug(f"received {length} repeater from DB")
        if length > 1:
            logger.critical(f"unexpected number of results for DMR_ID: {dmr_id}, expected 0/1")
    else:
        response.status_code = status.HTTP_204_NO_CONTENT

    return repeaters[0:1]


@router.get("/location", response_model=List[RepeaterItem], status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def repeater_location(city: str, country: str, distance: Optional[int] = 30, response: Response = Response()):

    repeater = {
        "dmr_id": 24060811,
        "tx": 436600000,
        "rx": 432600000,
        "cc": 4,
        "name": "SQ7JSK",
        "location": "Falkenberg"
    }

    response.status_code = status.HTTP_501_NOT_IMPLEMENTED

    return [RepeaterItem(**repeater)]
