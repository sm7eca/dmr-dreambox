

import requests
from common.logger import harvester_logger
from typing import List
from dmr.definitions import Repeater

logger = harvester_logger(__name__)


class Brandmeister:

    def __init__(self, url: str):

        self._url = url
        self._session = requests.Session()
        logger.debug("created instance of Brandmeister API")

    def get_all_repeater(self) -> List[Repeater]:

        s = self._session
        repeater = []

        response = s.get(url="https://api.brandmeister.network/v1.0/repeater/?action=LIST")

        if not (200 <= response.status_code < 300):
            logger.error("BM: failed to fetch the list of receivers "
                         f"from url: {self._url}, status: {response.status_code}")
            return repeater

        for r in response.json():
            repeater.append(Repeater(r))

        logger.debug(f"BM, received {len(repeater)} repeater from: {self._url}")

        return repeater

    def __enter__(self):
        logger.debug("__enter__")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.debug("__exit__")
        self._session.close()
