from fastapi import FastAPI
from routes import repeater
from common.definitions import Repeater, TalkGroup

app = FastAPI(
    title="DMR Dreambox - EIM",
    description="External Information Management for DMR dreambox",
    version="0.1.1"
)


@app.get("/repeater", response_model=Repeater)
async def repeater(master: int):
    tg = {"dmr_id": 24006, "ts": 1}
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


@app.get("/hotspot", response_model=Repeater)
async def hotspot(callsign: str):
    tg = {"dmr_id": 24006, "ts": 1}
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
