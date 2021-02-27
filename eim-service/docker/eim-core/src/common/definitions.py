from pydantic import BaseModel, Field
from typing import Optional, List


class TalkGroup(BaseModel):
    tg_id: int
    ts: int


class Repeater(BaseModel):
    dmr_id: int
    tx: int
    rx: int
    cc: int
    ts: int
    max_ts: int
    name: str
    location: str
    tg: Optional[List[TalkGroup]]


class SysInfo(BaseModel):
    uptime: str
    release: str
    git_commit: str
    maintainer: str
    repeater: int
