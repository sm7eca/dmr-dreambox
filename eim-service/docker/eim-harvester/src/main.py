
import os
import signal
import sys
from time import sleep

from common.logger import harvester_logger, harvester_config_root_logger
from db.mongo import MongoDB, MongoDbError
from dmr.brandmeister import Brandmeister


logger = harvester_logger("main")


def receive_signal(signalNumber, frame):
	logger.debug(f"Received: {signalNumber}")
	sys.exit()


def reload_configuration(signalNumber, frame):
	logger.debug(f"Received SIGHUP, {signalNumber}")
	return


def main():

	signal.signal(signal.SIGTERM, receive_signal)
	signal.signal(signal.SIGHUP, reload_configuration)

	harvester_config_root_logger()

	if "EIM_HARVESTER_PERIODICITY_SEC" in os.environ.keys():
		periodicity = int(os.environ['EIM_HARVESTER_PERIODICITY_SEC'])
	else:
		periodicity = 30

	mongodb_host = os.getenv("EIM_DB_HOST", "localhost")
	mongodb_port = os.getenv("EIM_DB_PORT", "27017")
	mongodb_name = os.getenv("EIM_DB_NAME", "eim")

	logger.debug("preparation done, entering WHILE loop")
	try:
		db = MongoDB(host=mongodb_host, port=mongodb_port, db_name=mongodb_name)
	except MongoDbError as ex:
		logger.critical(f"failed with message: {ex.msg}")
		sys.exit(1)

	db.cache_warming()

	while True:

		b = Brandmeister(url="https://api.brandmeister.network")

		repeater = b.get_all_repeater()

		db.update_repeater(repeater)

		logger.debug(f"received {len(repeater)} repeater definitions")

		del repeater
		sleep(periodicity)


if __name__ == '__main__':
	main()
