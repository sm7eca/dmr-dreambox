
import pytest
from common.tools import compute_end_index


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
