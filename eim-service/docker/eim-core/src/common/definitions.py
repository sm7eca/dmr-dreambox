from pydantic import BaseModel, Field
from typing import Optional, List


class TalkGroup(BaseModel):
    tg_id: int
    ts: int


class Repeater(BaseModel):
    """
    Detailed information for a Repeater, including talk groups
    """
    dmr_id: int
    tx: int
    rx: int
    cc: int
    ts: int
    max_ts: int
    name: str
    location: str
    tg: Optional[List[TalkGroup]]


class RepeaterItem(BaseModel):
    """
    A short version of data stored in DB. Returned DMR ID can be used
    to fetch more detailed information.
    """
    dmr_id: int
    tx: int
    rx: int
    cc: int
    name: str
    location: str


class SysInfo(BaseModel):
    """
    SysInfo describing the installation
    """
    uptime: str
    release: str
    git_commit: str
    maintainer: str
    repeater: int
