"""Implement Repeater routers"""

from fastapi import APIRouter, HTTPException
from common.definitions import Repeater, TalkGroup
from common.logger import get_logger
from common.tools import compute_end_index
from db.mongodb import MongoDB, MongoDbError
from typing import Optional, List


logger = get_logger("routers.repeater")

router = APIRouter(
    prefix="/repeater",
    tags=["repeater"],
    responses={404: {"description": "Not found"}}
)


@router.get("/master/{master_id}", response_model=List[Repeater])
async def repeater_master(master_id: int, limit: int = 0, skip: int = 0):

    db = MongoDB()
    repeaters = db.get_repeater_by_master(master_id=master_id)
    length = len(repeaters)

    if repeaters:
        logger.debug(f"received {length} repeater from DB")

    start, end = compute_end_index(length, skip, limit)
    return repeaters[start:end]


@router.get("/callsign/{callsign}", response_model=List[Repeater])
async def repeater_master_callsign(call_sign: str, limit: int = 0, skip: int = 0):

    db = MongoDB()
    repeaters = db.get_repeater_by_callsign(call_sign)
    length = len(repeaters)
    if repeaters:
        logger.debug(f"received {length} repeater from DB")

    start, end = compute_end_index(length, skip, limit)

    return repeaters[start:end]


@router.get("/dmr/{dmr_id}", response_model=List[Repeater])
async def repeater_master_dmrid(dmr_id: int):

    db = MongoDB()
    repeaters = db.get_repeater_by_dmrid(dmr_id)
    length = len(repeaters)
    if repeaters:
        logger.debug(f"received {length} repeater from DB")

    if length > 1:
        logger.critical(f"unexpected number of results for DMR_ID: {dmr_id}, expected 0/1")

    return repeaters[0:1]


@router.get("/location", response_model=Repeater)
async def repeater_location(city: str, country: str, distance: Optional[int] = 30, limit: int = 0, skip: int = 0):
    tg = {"tg_id": 24006, "ts": 1}
    response = {
        "dmr_id": 24060811,
        "tx": 436600000,
        "rx": 432600000,
        "cc": 4,
        "ts": 1,
        "max_ts": 1,
        "name": "SQ7JSK",
        "location": "Falkenberg",
        "tg": [TalkGroup(**tg)]
    }

    return Repeater(**response)
