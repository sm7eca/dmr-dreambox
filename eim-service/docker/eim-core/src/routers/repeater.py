"""Implement Repeater routers"""

import os
from fastapi import APIRouter, Response, status, Query, Path
from common.definitions import Repeater, RepeaterItem
from common.logger import get_logger
from common.tools import compute_end_index
from db.mongodb import MongoDB
from typing import Optional, List


logger = get_logger("routers.repeater", log_level=os.getenv("EIM_LOG_LEVEL", "INFO"))

router = APIRouter(
    prefix="/repeater",
    tags=["repeater"],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Not found"},
        status.HTTP_501_NOT_IMPLEMENTED: {"description": "Endpoint not implemented yet"},
        status.HTTP_204_NO_CONTENT: {"description": "No entry found in DB"}
    }
)

query_limit = Query(20, le=20, example=5, description="limit number of items returned")
query_skip = Query(0, ge=0, example=0, description="skip N items")
query_longitude = Query(..., ge=-180, le=180, example="12.4605814", description="longitude as float")
query_latitude = Query(..., ge=-90, le=90, example="56.8984846", description="latitude as float")
query_distance = Query(30, ge=1, example=30, description="distance in km")

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
        start, end = compute_end_index(length, skip, limit)
    else:
        response.status_code = status.HTTP_204_NO_CONTENT
        start = end = 0

    logger.info(f"received {length} repeater from DB")
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
        start, end = compute_end_index(length, skip, limit)
    else:
        start = end = 0
        response.status_code = status.HTTP_204_NO_CONTENT

    logger.info(f"received {length} repeater from DB")
    return repeaters[start:end]


@router.get("/location", response_model=List[RepeaterItem], status_code=status.HTTP_200_OK)
async def repeater_location(
        longitude: float = query_longitude,
        latitude: float = query_latitude,
        distance: Optional[int] = query_distance,
        limit: Optional[int] = query_limit,
        skip: Optional[int] = query_skip,
        response: Response = Response()
):

    db = MongoDB()
    repeaters = db.get_repeater_by_location(long=longitude, lat=latitude, distance_km=distance)
    length = len(repeaters)

    if repeaters:
        start, end = compute_end_index(length, skip, limit)
        logger.debug(f"received {length} repeater from DB")
    else:
        start = end = 0
        response.status_code = status.HTTP_204_NO_CONTENT

    return repeaters[start:end]
