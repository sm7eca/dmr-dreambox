
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

    def __init__(self, _dict):
        self.__dict__.update(_dict)

    def dict(self):
        return self.__dict__
