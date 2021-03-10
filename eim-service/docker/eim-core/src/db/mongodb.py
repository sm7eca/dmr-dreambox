import os
import sys
from urllib.parse import quote_plus

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure
from pymongo.collection import Collection

from common.logger import get_logger
from common.definitions import Repeater, RepeaterItem
from typing import List, Optional, Dict

from datetime import datetime

logger = get_logger("mongodb")


class MongoDbError(BaseException):

    def __init__(self, msg):
        self.msg = msg


class MongoDB:

    def __init__(self, db_name: str = "eim"):
        """Instantiate a DB entity"""

        self._repeater_log = {}

        if "EIM_DB_USER" not in os.environ.keys():
            raise MongoDbError("missing ENV variable EIM_DB_USER")

        if "EIM_DB_PASSWORD" not in os.environ.keys():
            raise MongoDbError("missing ENV variable EIM_DB_PASSWORD")

        if "EIM_DB_HOST" not in os.environ.keys():
            raise MongoDbError("missing ENV variable EIM_DB_HOST")

        if "EIM_DB_PORT" not in os.environ.keys():
            raise MongoDbError("missing ENV variable EIM_DB_PORT")

        user = quote_plus(os.getenv("EIM_DB_USER"))
        password = quote_plus(os.getenv("EIM_DB_PASSWORD"))
        host = os.getenv("EIM_DB_HOST")
        port = os.getenv("EIM_DB_PORT")

        uri = f"mongodb://{user}:{password}@{host}:{port}/?authSource=admin"

        client = MongoClient(uri)

        # ensure that we have connectivity
        try:
            client.admin.command("ismaster")
        except ConnectionFailure as ex:
            sys.exit(f"Failed to connect to MongoDB at {host}:{port} => {ex}")

        logger.info(f"successfully connected to MongoDB at {host}:{port}")

        self._db = Database(client, name=db_name)

    @staticmethod
    def _translate_db_2_repeater(db_entry: Dict) -> Repeater:
        r_object = {
            "dmr_id": db_entry["repeaterid"],
            "tx": float(db_entry["tx"]) * 1e6,
            "rx": float(db_entry["rx"]) * 1e6,
            "cc": int(db_entry["colorcode"]),
            "max_ts": 0,
            "name": db_entry["callsign"],
            "location": f"{db_entry['lng']},{db_entry['lat']}",
            "city": db_entry["city"]
        }
        r = Repeater(**r_object)
        logger.debug(f"item translated: {repr(r)}")
        return r

    @staticmethod
    def _translate_db_2_repeater_item(db_entry: Dict) -> RepeaterItem:
        """
        Translate into a shorter Repeater Item, the data can be reused
        in order to make additional calls retrieving detailed information
        using the unique DMR ID.
        """
        ri_object = {
            "dmr_id": db_entry["repeaterid"],
            "tx": float(db_entry["tx"]) * 1e6,
            "rx": float(db_entry["rx"]) * 1e6,
            "cc": int(db_entry["colorcode"]),
            "name": db_entry["callsign"],
            "location": f"{db_entry['lng']},{db_entry['lat']}",
            "city": db_entry["city"]
        }
        ri = RepeaterItem(**ri_object)
        logger.debug(f"RepeaterItem translated: {repr(ri)}")
        return ri

    def get_repeater_by_master(self, master_id: int) -> Optional[List[RepeaterItem]]:
        """
        Return a list of Repeater objects for a given master ID.
        :param master_id: DMR master ID
        :return: List[Repeater]
        """

        col = self._db.get_collection("repeater")
        timestamp_24_hours_ago = int(datetime.now().timestamp()) - 86400

        # try to find all repeater (status == 3) for a given master, updated 24 hours ago
        query = {
            "lastKnownMaster": str(master_id),
            "status": "3",
            "last_updated_ts": {"$gt": timestamp_24_hours_ago}
        }

        docs = col.find(filter=query, limit=0).sort("callsign")
        logger.debug(f"received {docs.count()} repeater from DB")

        list_repeater = [self._translate_db_2_repeater_item(record) for record in docs]
        return list_repeater

    def get_repeater_by_callsign(self, call_sign) -> Optional[List[RepeaterItem]]:

        col = self._db.get_collection("repeater")
        timestamp_24_hours_ago = int(datetime.now().timestamp()) - 86400

        query = {
            "status": "3",
            "callsign": call_sign,
            "last_updated_ts": {"$gt": timestamp_24_hours_ago}
        }

        docs = col.find(filter=query, limit=0).sort("callsign")
        logger.debug(f"received {docs.count()} repeater for callsign={call_sign} from DB")

        list_repeater = [self._translate_db_2_repeater_item(record) for record in docs]

        return list_repeater

    def get_repeater_by_dmrid(self, dmr_id: int) -> Optional[List[Repeater]]:
        """
        Here we are looking for a detailed list for each repeater, including talk groups.

        The talk groups are fetched using additional request towards the RestAPI and
        cached in the database
        """

        col = self._db.get_collection("repeater")
        timestamp_24_hours_ago = int(datetime.now().timestamp()) - 86400

        # we are looking for both repeater ("3") and hotspots ("4")
        query = {
            "status": {"$in": ["3", "4"]},
            "repeaterid": str(dmr_id)
        }

        logger.debug(f"query: {repr(query)}")

        docs = col.find(filter=query, limit=0)
        logger.debug(f"received {docs.count()} repeater for repeater_id={dmr_id} from DB")

        list_repeater = [self._translate_db_2_repeater(record) for record in docs]
        return list_repeater

    def get_hotspot(self, call_sign: str) -> Optional[List[RepeaterItem]]:
        """
        Return a list of Repeater for a given callsign
            - filter for status == 4, updated < 1 day and call sign
        """
        logger.debug(f"==> Received hotspot request, callsign: {call_sign}")
        timestamp_24_hours_ago = int(datetime.now().timestamp()) - 86400

        col = self._db.get_collection("repeater")

        query = {
            "callsign": call_sign,
            "status": "4"
        }

        docs = col.find(filter=query, limit=0).sort("repeaterid")
        logger.debug(f"received {docs.count()} hotspots from DB")
        list_hotspots = []

        for record in docs:
            list_hotspots.append(self._translate_db_2_repeater_item(record))

        return list_hotspots

    def count_docs(self, collection: str) -> int:
        """
        Return the number of documents for a given collection

        - throw an exception if collection doesn't exist

        """
        col: Collection = self._db.get_collection("repeater")
        if "repeater" not in self._db.list_collection_names():
            raise MongoDbError(f"no collection {col} found in DB")

        num_docs = col.count_documents(filter={})
        return num_docs

    def get_repeater_by_location(self, long: float, lat: float, distance_km: int) -> Optional[List[RepeaterItem]]:
        """
        Based on valid location data received from BM, query for 2d near-maxDistance
        """

        col: Collection = self._db.get_collection("repeater")

        query = {
            "status": "3",
            "loc_valid": True,
            "loc": {"$near": {"$geometry": {"type": "Point", "coordinates": [long, lat]},
                              "$maxDistance": distance_km * 1000}}
        }

        docs = col.find(filter=query, limit=0)
        logger.debug(f"received {docs.count()} repeater for {[long, lat]}, distance: {distance_km} km")

        list_repeater = []
        for record in docs:
            list_repeater.append(self._translate_db_2_repeater_item(record))

        return list_repeater
