
import os
from fastapi import APIRouter, Path, status, Response, Query
from common.definitions import RepeaterItem
from common.logger import get_logger
from common.tools import compute_end_index
from db.mongodb import MongoDB
from typing import List

logger = get_logger("routers.hotspot", log_level=os.getenv("EIM_LOG_LEVEL", "INFO"))

router = APIRouter(
    prefix="/hotspot",
    tags=["hotspot"],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Not found"},
        status.HTTP_501_NOT_IMPLEMENTED: {"description": "Endpoint not implemented yet"},
        status.HTTP_204_NO_CONTENT: {"description": "No entry found in DB"}
    }
)

query_limit = Query(5, lt=20, example=5, description="limit number of items returned")
query_skip = Query(0, ge=0, example=0, description="skip N items")


@router.get(
    "/callsign/{call_sign}",
    response_model=List[RepeaterItem],
    description="Retrieve hotspots based on call sign",
    status_code=status.HTTP_200_OK
)
async def hotspot(
        call_sign: str = Path(..., min_length=3, max_length=10, example="PI1SPA", description="international call sign"),
        limit: int = query_limit,
        skip: int = query_skip,
        response: Response = Response()
):

    db = MongoDB()

    hotspots = db.get_hotspot(call_sign=call_sign)

    if hotspots:
        num_hotspots = len(hotspots)
        start, end = compute_end_index(num_hotspots, 0, 0)
    else:
        response.status_code = status.HTTP_204_NO_CONTENT

    logger.info(f"Received {len(hotspots)} hotspots for callsign {call_sign} from DB")
    return hotspots[:10]
