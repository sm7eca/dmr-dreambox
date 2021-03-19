from pydantic import BaseModel, Field
from typing import Optional, List


field_user_dmr_id = Field(..., example=2400011, description="user's DMR ID")

field_dmr = Field(..., example=204342, description="DMR ID for a given repeater/hotspot")
field_tx = Field(..., example=436800000, description="repeater/hotspot TX frequency in Hz")
field_rx = Field(..., example=430700000, description="repeater/hotspot RX frequency in Hz")
field_ts = Field(..., example=1, description="DMR time slot")
field_cc = Field(..., example=4, description="DMR color code")
field_callsign = Field(..., example="PI1SPA", description="repeater callsign/owners callsign when hotspot")
field_location = Field(..., example="59.426891,24.819180", description="lat, long if provided")
field_city = Field(..., example="Varberg, SE", description="city, country string provided by owner")
field_max_ts = Field(..., example="2", description="number of time slots used by the repeater/hotspot")
field_maintainer = Field(..., example="Max Mustermann", description="Maintainer of this service")
field_git_commit = Field(..., example="5cebad", description="short GIT hash")
field_num_user = Field(..., example=202000, description="number of DMR users stored in DB")
field_num_repeater = Field(..., example=66440, description="number of receiver items stored in DB")
field_release_name = Field(..., example="dmr_dreambox_SM7ECA-210302-2S", description="EIM release name")
field_uptime = Field(..., example="800s", description="uptime in seconds")
field_tg_id = Field(..., example=2401, description="DMR talk group ID")
field_is_dynamic = Field(..., example=True, description="whether this TG is dynamic")
field_num_tg = Field(..., example=3, description="number of TGs in list of talk groups")
field_name = Field(..., example="Sven Svensson", description="human readable name, surname")
field_country = Field(..., example="Sweden", description="country, human readable")
field_state = Field(..., example="Skåne", description="national state, human readable")


class TalkGroup(BaseModel):
    tg_id: int = field_tg_id
    ts: int = field_ts
    is_dynamic: bool = field_is_dynamic


class Repeater(BaseModel):
    """
    Detailed information for a Repeater, including talk groups
    """
    dmr_id: int = field_dmr
    tx: int = field_tx
    rx: int = field_rx
    cc: int = field_cc
    max_ts: int = field_max_ts
    name: str = field_callsign
    location: str = field_location
    city: str = field_city
    num_tg: int = field_num_tg
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
    uptime: str = field_uptime
    release: str = field_release_name
    git_commit: str = field_git_commit
    maintainer: str = field_maintainer
    user: int = field_num_user
    repeater: int = field_num_repeater


class DmrUser(BaseModel):
    """
    DMR User information
    """
    dmr_id: int = field_user_dmr_id
    call_sign: str = field_callsign
    name: str = field_name
    city: str = field_city
    state: str = field_state
    country: str = field_country
