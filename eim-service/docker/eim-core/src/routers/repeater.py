"""Implement Repeater routers"""

from fastapi import APIRouter, HTTPException
from common.definitions import Repeater, TalkGroup
from common.logger import get_logger
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
    repeaters = db.get_repeater(master_id=master_id)

    if repeaters:
        logger.debug(f"received {len(repeaters)} repeater from DB")

    return repeaters[:10]


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
