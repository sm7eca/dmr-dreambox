
from fastapi import APIRouter
from common.definitions import Repeater, TalkGroup
from common.logger import get_logger
from db.mongodb import MongoDB
from typing import List

logger = get_logger("routers.hotspot")

router = APIRouter(
    prefix="/hotspot",
    tags=["hotspot"],
    responses={404: {"description": "Not found"}}
)


@router.get("/callsign/{callsign}", response_model=List[Repeater], description="Retrieve hotspots based on callsign")
async def hotspot(callsign: str):

    db = MongoDB()

    hotspots = db.get_hotspot(call_sign=callsign)

    if hotspots:
        logger.debug(f"Received {len(hotspots)} hotspots for callsign {callsign} from DB")

    return hotspots
