
from datetime import datetime


def timestr_to_timestamp(time_str: str) -> int:
    """Convert from string to a timestamp (int)"""
    return int(datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S").timestamp())
