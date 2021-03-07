
import requests
from requests import Response
from requests.exceptions import ConnectionError, ConnectTimeout
from common.definitions import TalkGroup
from typing import List, Optional, Dict
from common import logger


logger = logger.get_logger("brandmeister")


class BrandmeisterE(BaseException):

    def __init__(self, msg):
        self.msg = msg


class Brandmeister:
    """
    Provide a clean interface to BM Rest API at https://api.brandmeister.network
    """
    BM_URL = "https://api.brandmeister.network/v1.0"

    def __init__(self):
        self._session = requests.session()

    @staticmethod
    def _translate_profile_2_tg_list(profile: Dict) -> List[TalkGroup]:

        logger.debug(f"translator, received profile: {repr(profile)}")

        tg_list = []
        if "staticSubscriptions" not in profile.keys():
            logger.critical("no static subscriptions found")
            raise BrandmeisterE("missing item in profile dict")

        for tg in profile.get("staticSubscriptions"):
            tg_object = {
                "tg_id": tg["talkgroup"],
                "ts": tg["slot"],
                "is_dynamic": False
            }
            tg_list.append(TalkGroup(**tg_object))
            del tg_object

        for tg in profile.get("dynamicSubscriptions"):
            tg_object = {
                "tg_id": tg["talkgroup"],
                "ts": tg["slot"],
                "is_dynamic": True
            }
            tg_list.append(TalkGroup(**tg_object))
            del tg_object

        return tg_list

    def get_talk_groups(self, dmr_id: int) -> Optional[List[TalkGroup]]:

        logger.debug(f"gather repeater profile for DMR_ID: {dmr_id}")

        profile_url = self.BM_URL + f"/repeater/?action=profile&q={dmr_id}"

        response = Response()
        response.status_code = 404

        try:
            response = self._session.get(url=profile_url)
        except (ConnectionError, ConnectTimeout) as ex:
            raise BrandmeisterE(ex)

        logger.debug(f"received {response.status_code} from {profile_url}")

        list_tg = []
        if response.status_code == 200:
            # we expect a list of talk groups from BM API
            profile = response.json()

            list_tg = self._translate_profile_2_tg_list(profile)

        return list_tg
