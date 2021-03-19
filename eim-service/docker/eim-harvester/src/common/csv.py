"""
Provide functions for handling CSV translations
"""

import csv
from pathlib import Path
from typing import Dict
from enum import Enum

from common.logger import harvester_logger

logger = harvester_logger("csv")


class DmrUserSource(Enum):

    SDCL = 1        # Sveriges Digital Contact List
    RADIOID = 2     # RadioID.net


def csv_2_dict(csv_path: Path, file_format: DmrUserSource) -> Dict:
    """
    Parse a CSV file, ensure that each element is unique by using Dict
    """
    _support_formats = [DmrUserSource.SDCL, DmrUserSource.RADIOID]

    if file_format not in _support_formats:
        raise Exception(f"invalid format: {type}, supported: {_support_formats}")

    logger.debug("translate file")
    db_dict = {}
    encoding = 'latin-1'

    with open(csv_path, newline='', encoding=encoding) as csv_file:
        reader = csv.DictReader(csv_file)
        logger.debug(f"header: {reader.fieldnames}")

        for line in reader:

            if file_format == DmrUserSource.SDCL:

                dmr_id = line['Radio ID'].strip()
                if dmr_id not in db_dict.keys():
                    _user = {
                        "dmr_id": int(dmr_id),
                        "call_sign": line['Callsign'].strip().encode("utf-8"),
                        "name": line['Name'].strip().encode("utf-8"),
                        "city": line['City'].strip().encode("utf-8"),
                        "state": line['State'].strip().encode("utf-8"),
                        "country": line['Country'].strip().encode("utf-8")
                    }

            elif file_format == DmrUserSource.RADIOID:

                dmr_id = line['RADIO_ID'].strip()
                if dmr_id not in db_dict.keys():
                    _user = {
                        "dmr_id": int(dmr_id),
                        "call_sign": line['CALLSIGN'].strip().encode("utf-8"),
                        "name": (line['FIRST_NAME'].strip() + " " + line['LAST_NAME'].strip()).strip().encode("utf-8"),
                        "city": line['CITY'].strip().encode("utf-8"),
                        "state": line['STATE'].strip().encode("utf-8"),
                        "country": line['COUNTRY'].strip().encode("utf-8")
                    }

            db_dict[dmr_id] = _user
            del _user

    logger.info(f"SDCL: read {len(db_dict.keys())} entries from: {csv_path}")
    return db_dict
