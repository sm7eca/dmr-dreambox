from pydantic import BaseModel, Field
from typing import Optional, List


field_dmr = Field(..., example=204342, description="DMR ID for a given repeater/hotspot")
field_tx = Field(..., example=436800000, description="repeater/hotspot TX frequency in MHz")
field_rx = Field(..., example=430700000, description="repeater/hotspot RX frequency in MHz")
field_ts = Field(..., example=1, description="time slot")
field_cc = Field(..., example=4, description="color code")
field_callsign = Field(..., example="PI1SPA", description="repeater callsign/owners callsign when hotspot")
field_location = Field(..., example="59.426891,24.819180", description="lat, long if provided")
field_city = Field(..., example="Varberg, SE", description="city, country string provided by owner")


class TalkGroup(BaseModel):
    tg_id: int = Field(..., example=2401, description="talk group ID")
    master_id: int = Field(..., example=2401, description="current DMR ID of master handling the traffic")
    rep_id: int = Field(..., example=204342, description="DMR ID of repeater/hotspot handling this TG")
    ts: int = field_ts
    is_dynamic: bool = Field(..., example=True, description="whether this TG is dynamic")


class Repeater(BaseModel):
    """
    Detailed information for a Repeater, including talk groups
    """
    dmr_id: int = field_dmr
    tx: int = field_tx
    rx: int = field_rx
    cc: int = field_cc
    ts: int = field_ts
    max_ts: int
    name: str = field_callsign
    location: str = field_location
    city: str = field_city
    tg: Optional[List[TalkGroup]]


class RepeaterItem(BaseModel):
    """
    A short version of data stored in DB. Returned DMR ID can be used
    to fetch more detailed information.
    """
    dmr_id: int = field_dmr
    tx: int = field_tx
    rx: int = field_rx
    cc: int = field_cc
    name: str = field_callsign
    location: str = field_location
    city: str = field_city


class SysInfo(BaseModel):
    """
    SysInfo describing the installation
    """
    uptime: str = Field(..., example="800s", description="uptime in seconds")
    release: str = Field(..., example="dmr_dreambox_SM7ECA-210302-2S", description="DMR release name")
    git_commit: str = Field(..., example="5cebad", description="short GIT hash")
    maintainer: str = Field(..., example="Max Mustermann", description="Maintainer of this service")
    repeater: int = Field(..., example=66440, description="number of receiver items stored in DB")
