from typing import Dict
from common.time import timestr_to_timestamp


DEFAULT_LOC = {"type": "Point", "coordinates": [0.000000, 0.000000]}


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
    loc: Dict
    loc_valid : bool
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

        self.__update_location(self.lng, self.lat)

    def __update_location(self, lng: str, lat: str):
        """
        Update the location so that we could do location searches based
        on long lat.

            - if invalid numbers are detected, set 0.00000, 0.00000
            - range check for +/-180, +/-90
            - both have to differ from 0.000000
        """
        self.loc = DEFAULT_LOC
        self.loc_valid = False

        try:
            longitude = float(lng)
            latitude = float(lat)
        except BaseException as ex:
            return

        if longitude == 0.0 and latitude == 0.0:
            return

        if not (-180 <= longitude <= 180) or not (-90 <= latitude <= 90):
            return

        self.loc = {"type": "Point", "coordinates": [longitude, latitude]}
        self.loc_valid = True

    def dict(self):
        return self.__dict__
