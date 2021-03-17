
import datetime


def compute_end_index(len: int, skip: int = 0, limit: int = 0) -> (int, int):

    end = len
    if len > (skip + limit):
        end = skip + limit
    if limit == 0:
        end = len
    return skip, end


def uptime_2_human_string(uptime: int) -> str:
    """
    converts number of seconds into x days, x hours, x minutes
    2d:2m
    """

    return str(datetime.timedelta(seconds=uptime)) + " (d, h:m:s)"

