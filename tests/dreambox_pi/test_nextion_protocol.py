"""Fixture-driven tests for dreambox_pi.domain.nextion_protocol.

Verifies outbound command building, inbound event parsing/dispatch (including
the deliberately-preserved 0x31-falls-through-into-0x32 quirk), and the fake
transport's timeout/partial-read behavior against tests/fixtures/sessions/*.json.
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from dreambox_pi.adapters.fake_serial import FakeSerialTransport
from dreambox_pi.domain import nextion_protocol as nx

from _fixture_utils import load_session, get_frame, frame_bytes


def test_build_command_appends_terminator():
    assert nx.build_command("page 3") == b"page 3\xff\xff\xff"
    assert nx.build_command('main.n2.val=2') == b'main.n2.val=2\xff\xff\xff'


def test_tx_ptt_fixture_button_events():
    session = load_session("tx_ptt")

    press = get_frame(session, 1)
    event = nx.parse_event(frame_bytes(press))
    assert event.kind == "button"
    assert (event.page, event.field_or_button, event.activity) == (0, 0, 1)
    assert nx.dispatch(frame_bytes(press)) == ["NX_button_pressed"]

    release = get_frame(session, 5)
    event = nx.parse_event(frame_bytes(release))
    assert (event.page, event.field_or_button, event.activity) == (0, 0, 0)


def test_idle_ts_scan_fixture_ascii_command():
    session = load_session("idle_ts_scan")
    ts_update = get_frame(session, 3)
    assert nx.build_command("main.n2.val=2") == ts_update["ascii"].encode("ascii") + nx.TERMINATOR


def test_channel_change_fixture_page_and_button_events():
    session = load_session("channel_change")

    page_event = get_frame(session, 1)
    parsed = nx.parse_event(frame_bytes(page_event))
    assert parsed.kind == "page"
    assert parsed.page == 4
    assert nx.dispatch(frame_bytes(page_event)) == ["NX_page_init"]


def test_error_paths_fixture_terminator_and_dispatch_quirk():
    session = load_session("error_paths")

    truncated = get_frame(session, 5)
    transport = FakeSerialTransport()
    transport.feed(frame_bytes(truncated))
    result = nx.read_event(transport)
    assert result == frame_bytes(truncated)
    assert nx.split_terminator(result) is None

    quirk_frame = get_frame(session, 6)
    payload = frame_bytes(quirk_frame)
    handlers = nx.dispatch(payload)
    assert handlers == ["NX_numfield_touched", "NX_txtfield_touched"], (
        "case 0x31 must fall through into 0x32's handler, per the verified "
        "missing `break` in NXhandler (A40Nextion_HMI.ino:1597-1599)"
    )


def test_ffcount_is_cumulative_not_consecutive():
    """Verified firmware quirk (A40Nextion_HMI.ino:1642-1650): NXlisten's
    ffcount is never reset on a non-0xFF byte, so three ISOLATED 0xFF bytes
    (not a run of three) still complete the frame -- earlier than a strict
    "three consecutive" reading would. This must match real hardware, not the
    more conventional interpretation."""
    # 0xFF at positions 0, 2, 4 -- never two in a row, but three occurrences total.
    isolated = bytes([0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x99, 0x99])
    transport = FakeSerialTransport()
    transport.feed(isolated)

    result = nx.read_event(transport)

    assert result == isolated[:5], result.hex()
    # No genuine trailing FF FF FF run exists, so nothing is stripped.
    assert nx.split_terminator(result) == isolated[:5]


def test_error_paths_fixture_invalid_variable_error():
    session = load_session("error_paths")
    error_frame = get_frame(session, 4)
    parsed = nx.parse_event(frame_bytes(error_frame))
    assert parsed.kind == "error_invalid_variable"
    assert nx.dispatch(frame_bytes(error_frame)) == []


def test_read_event_full_roundtrip_with_partial_reads():
    transport = FakeSerialTransport()
    full_frame = bytes.fromhex("34" "04") + nx.TERMINATOR
    transport.feed(full_frame, chunk_size=2)

    result = nx.read_event(transport)

    assert result == full_frame
    payload = nx.split_terminator(result)
    parsed = nx.parse_event(payload)
    assert parsed.kind == "page"
    assert parsed.page == 4


def test_read_event_disconnect_yields_no_data():
    transport = FakeSerialTransport()
    transport.disconnect()
    result = nx.read_event(transport)
    assert result == b""
    assert transport.clock.time() == nx.FIRST_BYTE_TIMEOUT
