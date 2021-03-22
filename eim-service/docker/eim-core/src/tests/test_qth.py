import pytest
from common.qth import qth_2_location, QthLocatorE


def test_square_to_location():

    # call uut
    lon1, lat1 = qth_2_location("Jo67AP18")
    lon2, lat2 = qth_2_location("jo67ap18")
    lon3, lat3 = qth_2_location("jo76ap")
    assert (lon1, lat1) == (12.008333, 57.658333)
    assert lat1 == lat2
    assert lon1 == lon2
    assert lon3 != lon2
    assert lat3 != lat2
    print(f"{lon1}, {lat1}, A")


@pytest.mark.parametrize(
    argnames="qth_string",
    argvalues=[
        "jo7",
        "jo76a",
        "jo76ap886",
        678.88
    ],
    ids=[
        "invalid length,3",
        "invalid_length,5",
        "invalid_length,9",
        "invalid_type_float"
    ]
)
def test_qth_location_invalid(qth_string):

    with pytest.raises(QthLocatorE) as error:
        actual = qth_2_location(qth_string)
