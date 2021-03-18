
import logging
import sys
import os


def harvester_config_root_logger():

    root = logging.getLogger()

    log_level = os.getenv("EIM_LOG_LEVEL", "INFO")

    root.setLevel(log_level.upper())

    f = logging.Formatter('%(name)s - %(levelname)s - %(message)s')

    lh = logging.StreamHandler(sys.stdout)
    lh.setLevel(logging.DEBUG)
    lh.setFormatter(f)

    root.addHandler(lh)

    if "INFO" not in log_level:
        logging.info(f"Set root log level to {log_level}")


def harvester_logger(name: str, level: str = "INFO") -> logging.Logger:

    logger = logging.getLogger(name)
    logger.setLevel(os.getenv("EIM_LOG_LEVEL", level))

    return logger
