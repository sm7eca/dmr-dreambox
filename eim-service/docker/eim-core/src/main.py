import os
from fastapi import FastAPI
from typing import Optional
from datetime import datetime
import pathlib
from common.definitions import Repeater, TalkGroup, SysInfo


eim_git_hash = os.environ['EIM_GIT_HASH']
dmr_release = os.environ['DMR_RELEASE_NAME']
github_ref = "https://github.com/sm7eca/dmr-dreambox"

app = FastAPI(
    title="DMR Dreambox - EIM",
    description=f'External Information Management for DMR dreambox<br>'
                f'DMR version: <a target="_blank" href={github_ref}/releases>{dmr_release}</a><br>'
                f'Commit at Github: <a target="_blank" href="{github_ref}/commit/{eim_git_hash}">{eim_git_hash[:6]}</a>',
    version=f"0.1.{eim_git_hash[:6]}"
)


@app.get("/repeater/master", response_model=Repeater, tags=['repeater'])
async def repeater_master(master: int):
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


@app.get("/repeater/location", response_model=Repeater, tags=['repeater'])
async def repeater_location(city: str, country: str, distance: Optional[int] = 30):
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


@app.get("/hotspot", response_model=Repeater, description="Retrieve hotspots based on callsign", tags=["hotspot"])
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


@app.get("/info", response_model=SysInfo, tags=["system"])
async def get_sys_info():
    fname = pathlib.Path('/proc/1/cmdline')
    uptime = None
    if fname.exists():
        uptime = int(datetime.now().timestamp() - fname.stat().st_ctime)
    info = {"uptime": f"{uptime}s", "version": "0.1.1", "maintainer": "Arne Nilsson", "repeater": 15431}

    return SysInfo(**info)
