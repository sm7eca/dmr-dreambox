
from fastapi import APIRouter
from common.definitions import Repeater, TalkGroup
from common.logger import get_logger
from typing import Optional

logger = get_logger("routers.hotspot")

router = APIRouter(
    prefix="/hotspot",
    tags=["hotspot"],
    responses={404: {"description": "Not found"}}
)


@router.get("/callsign/{callsign}", response_model=Repeater, description="Retrieve hotspots based on callsign")
async def hotspot(callsign: str):
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
