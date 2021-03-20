"""
Interface for Sveriges Digital Contact List for Anytone.
"""

from typing import Dict, List, Optional
from pathlib import Path
import csv
import os
from requests.exceptions import HTTPError, ConnectionError, ConnectTimeout
from common.logger import harvester_logger
from common.download import download_2_file, downloadable
from common.csv import csv_2_dict, DmrUserSource
from dmr.definitions import DmrUser

logger = harvester_logger("dmr.sdcl", level="INFO")


class DmrUserInfo:
    """
    Handle the CSV file provided by SK7HW
    """
    __URL_SDCL = "https://www.sk7hw.org/DMR/Sverige_Digital%20Contact%20list%20AnyTone%20578_868_878.csv"
    __URL_RADIOID = "https://www.radioid.net/static/user.csv"

    def __init__(self, source: DmrUserSource):
        if source == DmrUserSource.RADIOID:
            self._url = self.__URL_RADIOID
        elif source == DmrUserSource.SDCL:
            self._url = self.__URL_SDCL
        else:
            raise Exception(f"invalid format: {source}")
        self._source = source

    def get_users(self) -> Optional[List[DmrUser]]:
        """
        retrieve all users from CSV file provided at SDCL
        """

        # prepare for download
        list_users = []
        if not downloadable(self._url):
            logger.critical("not is downloadable")
            return list_users

        try:
            csv_file = download_2_file(self._url, Path('/tmp/dmr_user.csv'))
        except (HTTPError, ConnectionError, ConnectTimeout) as error:
            logger.error(f"failed to download user DB from SDCL {self._url}")
            return None

        try:
            user_db = csv_2_dict(csv_file, file_format=self._source)
        except csv.Error as error:
            logger.error(f"CSV parser failed on {csv_file}")
            return None

        os.remove(csv_file)

        return [DmrUser(v) for _k, v in user_db.items()]
