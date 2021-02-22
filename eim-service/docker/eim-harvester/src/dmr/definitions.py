from typing import Dict
from common.time import timestr_to_timestamp


class Repeater:
    """Repeater Data object"""

    repeaterid: str
    callsign: str
    hardware: str
    firmware: str
    tx: str
    rx: str
    colorcode: str
    status: str
    lastKnownMaster: str
    lat: str
    lng: str
    city: str
    website: str
    pep: str
    gain: str
    agl: str
    priorityDescription: str
    description: str
    last_updated: str
    last_updated_ts: int

    def __init__(self, _dict: Dict):
        self.__dict__.update(_dict)
        if "last_updated" in _dict.keys() and self.last_updated:
            self.last_updated_ts = timestr_to_timestamp(self.last_updated)

    def dict(self):
        return self.__dict__
