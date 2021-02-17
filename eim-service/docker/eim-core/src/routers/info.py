
from fastapi import APIRouter
from common.definitions import SysInfo
from common.logger import get_logger
from datetime import datetime
import pathlib


router = APIRouter(
    prefix="/info",
    tags=["system"],
    responses={404: {"description": "Not found"}}
)


@router.get("/", response_model=SysInfo)
async def get_sys_info():
    fname = pathlib.Path('/proc/1/cmdline')
    uptime = None
    if fname.exists():
        uptime = int(datetime.now().timestamp() - fname.stat().st_ctime)
    info = {"uptime": f"{uptime}s", "version": "0.1.1", "maintainer": "Arne Nilsson", "repeater": 15431}

    return SysInfo(**info)
