
import logging
import sys
import os


def config_root_logger():

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


def get_logger(name: str, log_level: str = "DEBUG") -> logging.Logger:

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    return logger