from pydantic import BaseModel
from typing import Optional, List


class TalkGroup(BaseModel):
    dmr_id: int
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
