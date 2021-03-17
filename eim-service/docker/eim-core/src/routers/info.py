import os
from fastapi import APIRouter
from common.definitions import SysInfo
from common.tools import uptime_2_human_string
from db.mongodb import MongoDB
from datetime import datetime
import pathlib


router = APIRouter(
    prefix="/system",
    tags=["system"],
    responses={404: {"description": "Not found"}}
)


@router.get(
    "/info",
    response_model=SysInfo,
    summary="Provides a summary about the system health."
)
async def get_sys_info():
    fname = pathlib.Path('/proc/1/cmdline')
    dmr_release_name = os.getenv("DMR_RELEASE_NAME", "UNKOWN")
    git_hash = os.getenv("EIM_GIT_HASH", "ERROR, no hash found")

    uptime = None
    if fname.exists():
        uptime = int(datetime.now().timestamp() - fname.stat().st_ctime)

    db = MongoDB()
    num_repeater: int = db.count_docs(collection="repeater")

    info = {
        "uptime": uptime_2_human_string(uptime),
        "git_commit": git_hash,
        "release": dmr_release_name,
        "maintainer": "Arne Nilsson (SM7ECA), Sebastian Mangelsen (SM6-8506)",
        "repeater": num_repeater}

    return SysInfo(**info)
