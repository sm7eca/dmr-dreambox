
import pytest
from pathlib import Path
from dmr.dmr_user_info import DmrUserSource, DmrUserInfo
from dmr.definitions import DmrUser


@pytest.mark.parametrize(
    argnames="source_type",
    argvalues=[
        DmrUserSource.SDCL,
        DmrUserSource.RADIOID
    ]
)
def test_sdcl(source_type):

    s = DmrUserInfo(source=source_type)

    actual = s.get_users()

    assert isinstance(actual, list), "expected list, received"
    assert len(actual) > 0
    assert isinstance(actual[0], DmrUser)
    assert not Path('tmp/dmr_user.csv').exists()
