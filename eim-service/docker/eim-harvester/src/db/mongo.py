import os

from pymongo import MongoClient, DESCENDING, InsertOne, UpdateOne, ReplaceOne, DeleteOne
from pymongo.errors import ConnectionFailure, BulkWriteError
from pymongo.database import Database
from pymongo.results import BulkWriteResult
from pymongo.collection import Collection
from dmr.definitions import Repeater
from datetime import datetime
from urllib.parse import quote_plus
from common.logger import harvester_logger
from typing import List, Optional


logger = harvester_logger("mongodb")

class MongoDbError(BaseException):

    def __init__(self, msg):
        self.msg = msg


class MongoDB:

    def __init__(self, host: str, port: str, db_name: str = "eim"):
        """Instantiate a DB entity"""

        self._repeater_log = {}

        if "EIM_DB_USER" not in os.environ.keys():
            raise MongoDbError("missing ENV variable EIM_DB_USER")

        if "EIM_DB_PASSWORD" not in os.environ.keys():
            raise MongoDbError("missing ENV variable EIM_DB_PASSWORD")

        user = quote_plus(os.environ["EIM_DB_USER"])
        password = quote_plus(os.environ["EIM_DB_PASSWORD"])

        uri = f"mongodb://{user}:{password}@{host}:{port}/?authSource=admin"

        logger.debug(f"MDB: prepare {host}:{port}")
        client = MongoClient(uri)
        logger.info(f"successfully connected to MongoDB at {host}:{port}")

        eim = client.get_database("eim")

        if "repeater" not in eim.collection_names():
            r = eim.create_collection("repeater")
            index = ("repeaterid", DESCENDING)
            r.create_index([index], unique=True)
            logger.debug("Collection: repeater created")

        logger.debug(f"{eim.repeater.index_information()}")

        self._db = Database(client, name=db_name)

    @staticmethod
    def _str_to_timestamp(time_str: str) -> float:
        """Convert a timestring in Brandmeister entry to EPOCH"""
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S").timestamp()

    @staticmethod
    def _bulk_write(col: Collection, bulk_requests: List) -> Optional[BulkWriteResult]:
        if not bulk_requests or len(bulk_requests) == 0:
            return None
        try:
            bulk_response = col.bulk_write(bulk_requests, ordered=False)
        except BulkWriteError as ex:
            raise MongoDbError("failed to sent bulk_write request")

        # logger.debug(f"successfully sent {len(bulk_requests)} items")
        return bulk_response

    def cache_warming(self):
        """Sync with database and build internal cache to avoid DB requests"""
        col = Collection(database=self._db, name="repeater")
        repeater = col.find(filter={})
        logger.debug(f"found {repeater.count()} repeater in DB")
        self._repeater_log.clear()
        for r in repeater:
            if r['repeaterid'] not in self._repeater_log.keys():
                self._repeater_log[r['repeaterid']] = {"timestamp": self._str_to_timestamp(r['last_updated'])}

    def update_repeater(self, repeater: List[Repeater]):
        """
            Insert, Update repeater documents into the Mongo DB.

            Using an internal dictionary we are trying to reduce the number of
            requests towards MongoDB. All required requests are transferred
            to MongoDB using a bulk request.
        """
        col = Collection(database=self._db, name="repeater")
        timestamp = datetime.now().timestamp()

        bulk_requests = []
        batch_size = 500
        counter = 0
        inserted = 0
        updated = 0
        repeater_types = {}

        logger.debug(f"start updating {len(repeater)} repeater in DB, batch size: {batch_size}")
        status_list = []
        for r in repeater:
            counter += 1
            query = {"repeaterid": r.repeaterid}

            if r.status not in repeater_types.keys():
                repeater_types[r.status] = {"count": 0, "active": 0}

            repeater_types[r.status]["count"] += 1

            if (timestamp - self._str_to_timestamp(r.last_updated)) < 86400:
                repeater_types[r.status]["active"] += 1

            if r.repeaterid not in self._repeater_log.keys():
                # identified a new repeater, ID is added to local cache
                self._repeater_log[r.repeaterid] = {"timestamp": self._str_to_timestamp(r.last_updated)}
                # add an insert request
                bulk_requests.append(InsertOne(r.dict()))
            else:
                # this is a known fellow, check timestamp and decide what to do
                last_updated = self._str_to_timestamp(r.last_updated)

                if last_updated > self._repeater_log[r.repeaterid]["timestamp"]:
                    # Houston, someone updated the flight plan
                    bulk_requests.append(ReplaceOne(filter=query, replacement=r.dict()))

            if len(bulk_requests) % batch_size == 0:

                bulk_response = self._bulk_write(col, bulk_requests)

                if bulk_response:
                    inserted += bulk_response.inserted_count
                    updated += bulk_response.modified_count

                bulk_requests.clear()

        if len(bulk_requests) > 0:
            try:
                bulk_response = self._bulk_write(col, bulk_requests)
            except BulkWriteError as ex:
                raise MongoDbError(f"failed to sent {len(bulk_requests)} bulk_write requests")

            if bulk_response:
                inserted += bulk_response.inserted_count
                updated += bulk_response.modified_count

            bulk_requests.clear()

        items_deleted = [r for r in repeater if r.repeaterid not in self._repeater_log.keys()]

        if len(items_deleted) > 0:
            logger.debug(f"found deleted items: {repr([r.repeaterid for r in items_deleted])}")
            for r in items_deleted:
                bulk_requests.append(DeleteOne(filter={"repeaterid": r.repeaterid}))

            self._bulk_write(col, bulk_requests)
            bulk_requests.clear()

        logger.debug(f"cache size: {len(self._repeater_log)}")
        logger.debug(f"done updating {len(repeater)}")
        logger.debug(f"added: {inserted}, updated: {updated}")
        logger.debug(f"found {col.count_documents(filter={})} documents in collection: {col.name}")
        logger.debug(f"status list: {repr(repeater_types)}")
