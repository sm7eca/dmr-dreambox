
import pytest
from common.tools import compute_end_index
from common.tools import uptime_2_human_string


@pytest.mark.parametrize(
    argnames="length, skip, limit, expected",
    argvalues=[
        (0, 0, 0, (0, 0)),
        (5, 0, 10, (0, 5)),
        (15, 0, 10, (0, 10)),
        (15, 0, 15, (0, 15)),
        (15, 5, 5, (5, 10)),
        (15, 10, 5, (10, 15)),
        (15, 15, 5, (15, 15)),
        (15, 0, 0, (0, 15))

    ],
    ids=[
        "all_zero",
        "len<limit",
        "len>limit",
        "len=limit",
        "skip=limit",
        "skip>limit",
        "no_items_left",
        "0=skip=limit"
    ]
)
def test_compute_end_index(length, skip, limit, expected):

    test_list = [
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15
    ]

    start, end = compute_end_index(length, skip, limit)
    # print(f"{len}:{skip}:{limit} ==> {test_list[start:end]}")

    assert (start, end) == expected


@pytest.mark.parametrize(
    argnames="uptime, expected",
    argvalues=[
        (100, "0:01:40 (d, h:m:s)"),
        (0, "0:00:00 (d, h:m:s)"),
        (3600, "1:00:00 (d, h:m:s)"),
        (86402, "1 day, 0:00:02 (d, h:m:s)"),
        (172804, "2 days, 0:00:04 (d, h:m:s)")
    ],
    ids=[
        "100s->1min",
        "0s -> 0min",
        "3600s -> 1h",
        "86402 -> 1d, 2s",
        "172804 -> 2d, 4s"
    ]
)
def test_uptime_2_human_string(uptime, expected):

    # call UUT
    actual = uptime_2_human_string(uptime)

    # asserts
    assert expected == actual, "unexpected result"
