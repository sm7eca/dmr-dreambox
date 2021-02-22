import os
import sys
from urllib.parse import quote_plus

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure

from common.logger import get_logger
from common.definitions import Repeater
from typing import List, Optional

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
            sys.exit(f"Failed to connect to MongoDB at {host}:{port}")

        logger.info(f"successfully connected to MongoDB at {host}:{port}")

        eim = client.get_database(db_name)

        self._db = Database(client, name=db_name)

    def get_repeater(self, master_id: int, limit: int = 0, skip: int = 0) -> Optional[List[Repeater]]:
        """
        Return a list of Repeater objects for a given master ID.
        :param master_id: DMR master ID
        :param limit: limit number of items returned
        :param skip:
        :return: List[Repeater]
        """

        col = self._db.get_collection("repeater")
        timestamp_now = datetime.now().timestamp()

        # try to find all repeater (status == 3) for a given master
        query = {
            "lastKnownMaster": str(master_id),
            "status": "3"
        }

        docs = col.find(filter=query, limit=0)
        logger.debug(f"received {docs.count()} items from DB")

        list_repeater = []

        for record in docs:
            logger.debug(f"item received: {repr(record)}")

        return list_repeater
