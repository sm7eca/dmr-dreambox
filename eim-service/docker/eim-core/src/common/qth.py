
import re

from math import floor
# Constants
ASCII_0 = 48
ASCII_A = 65


class QthLocatorE(BaseException):

    def __init__(self, msg):
        self.msg = msg


def _assert_qth_is_valid(qth_locator: str) -> None:
    # Validate input
    if not isinstance(qth_locator, str):
        raise QthLocatorE("expected string")

    if not 4 <= len(qth_locator) <= 8:
        raise QthLocatorE(f"invalid length {len(qth_locator)}, expected 4..8")

    if not len(qth_locator) % 2 == 0:
        raise QthLocatorE(f"length must be multiple of 2, got {len(qth_locator)}")


def qth_2_location(qth_locator: str) -> tuple:
    '''Converts QTH locator to latitude and longitude in decimal format.
    Gets QTH locator as string.
    Returns Tuple containing latitude and longitude as floats.'''

    _assert_qth_is_valid(qth_locator)

    qth_locator = qth_locator.upper()

    # Separate fields, squares and subsquares
    # Fields
    lon_field = ord(qth_locator[0]) - ASCII_A
    lat_field = ord(qth_locator[1]) - ASCII_A

    # Squares
    lon_sq = ord(qth_locator[2]) - ASCII_0
    lat_sq = ord(qth_locator[3]) - ASCII_0

    # Subsquares
    if len(qth_locator) >= 6:
        lon_sub_sq = ord(qth_locator[4]) - ASCII_A
        lat_sub_sq = ord(qth_locator[5]) - ASCII_A
    else:
        lon_sub_sq = 0
        lat_sub_sq = 0

    # Extended squares
    if len(qth_locator) == 8:
        lon_ext_sq = ord(qth_locator[6]) - ASCII_0
        lat_ext_sq = ord(qth_locator[7]) - ASCII_0
    else:
        lon_ext_sq = 0
        lat_ext_sq = 0

    # Calculate latitude and longitude
    lon = -180.0
    lat = -90.0

    lon += 20.0 * lon_field
    lat += 10.0 * lat_field

    lon += 2.0 * lon_sq
    lat += 1.0 * lat_sq

    lon += 5.0 / 60 * lon_sub_sq
    lat += 2.5 / 60 * lat_sub_sq

    lon += 0.5 / 60 * lon_ext_sq
    lat += 0.25 / 60 * lat_ext_sq

    return round(lon, 6), round(lat, 6)
