"""Implement Repeater routers"""

from fastapi import APIRouter, Response, status, Query, Path
from common.definitions import Repeater, RepeaterItem
from common.logger import get_logger
from common.tools import compute_end_index
from db.mongodb import MongoDB
from typing import Optional, List
from common.brandmeister import BrandmeisterE, Brandmeister


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

query_limit = Query(5, lt=20, example=5, description="limit number of items returned")
query_skip = Query(0, ge=0, example=0, description="skip N items")
query_country = Query(..., min_length=2, example="SE", description="international country code")
query_city = Query(..., min_length=2, example="Gothenburg", description="human readable city, English")
query_distance = Query(..., ge=1, lt=100, example=30, description="distance in km")

path_dmr_id = Path(..., gt=0, example=2401, description="DMR ID, > 0")
path_callsign = Path(..., example="PI1SPA", description="international callsign", min_length=3)


@router.get("/master/{master_id}", response_model=List[RepeaterItem], status_code=status.HTTP_200_OK)
async def repeater_master(
        master_id: int = path_dmr_id,
        limit: Optional[int] = query_limit,
        skip: Optional[int] = query_skip,
        response: Response = Response()
):

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


@router.get("/callsign/{call_sign}", response_model=List[RepeaterItem], status_code=status.HTTP_200_OK)
async def repeater_callsign(
        call_sign: str = path_callsign,
        limit: Optional[int] = query_limit,
        skip: Optional[int] = query_skip,
        response: Response = Response()
):

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


@router.get("/location", response_model=List[RepeaterItem], status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def repeater_location(
        city: str = query_city,
        country: str = query_country,
        distance: Optional[int] = query_distance,
        response: Response = Response()
):

    repeater = {
        "dmr_id": 24060811,
        "tx": 436600000,
        "rx": 432600000,
        "cc": 4,
        "name": "SQ7JSK",
        "location": "Falkenberg, SE",
        "city": "Falkenberg"
    }

    response.status_code = status.HTTP_501_NOT_IMPLEMENTED

    return [RepeaterItem(**repeater)]
