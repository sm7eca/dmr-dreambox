"""Fixture-driven tests for dreambox_pi.domain.dmr_protocol.

Verifies the codec reproduces every "computed"/"computed-assuming-natural-
alignment" DMR frame in tests/fixtures/sessions/*.json byte-for-byte, and that
malformed/error-path frames from error_paths.json are handled the way
doc/akb/dmr-protocol.md says the firmware handles them -- notably that an
unenforced checksum is accepted (`is_success_reply`) while the stricter
`check_checksum` correctly flags it, and that a truncated frame times out
without ever synthesizing a fake "success".
"""

import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "tools"))

from dreambox_pi.adapters.fake_serial import FakeSerialTransport
from dreambox_pi.domain import dmr_protocol as dmr

import pc_checksum as fixture_pc_checksum  # tests/fixtures/tools/pc_checksum.py -- deliberately standalone, see its docstring
from _fixture_utils import load_session, get_frame, frame_bytes


def test_pc_checksum_self_consistent():
    frame = bytes([0x68, 0x27, 0x01, 0x01, 0x00, 0x00, 0x00, 0x01, 0x01, 0x10])
    out = dmr.pc_checksum(frame)
    assert out.hex(" ").upper() == "68 27 01 01 95 C6 00 01 01 10"
    assert dmr.check_checksum(out)


def test_pc_checksum_matches_standalone_fixture_tool():
    """tests/fixtures/tools/pc_checksum.py is a deliberately standalone
    duplicate (see its own docstring) of dmr_protocol.pc_checksum/
    check_checksum, kept dependency-free for fixture authoring. Nothing else
    enforces the two stay in sync, so cross-check them here against a range
    of sample buffers -- any future correction to the checksum algorithm
    applied to only one copy will fail this test."""
    samples = [
        bytes([0x68, 0x27, 0x01, 0x01, 0x00, 0x00, 0x00, 0x01, 0x01, 0x10]),
        bytes([0x68, 0x2C, 0x01, 0x01, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x10]),
        bytes([0x68, 0x22, 0x01, 0x01, 0x00, 0x00, 0x00] + list(range(160)) + [0x10]),
    ]
    for sample in samples:
        assert dmr.pc_checksum(sample) == fixture_pc_checksum.pc_checksum(sample)


def test_startup_fixture_frames():
    session = load_session("startup")

    query_init = get_frame(session, 3)
    assert dmr.build_simple_command(dmr.QUERY_INIT_FINISHED, dmr.FUNC_ENABLE) == frame_bytes(query_init)

    set_channel = get_frame(session, 5)
    channel = dmr.DigitalChannel(
        rx_freq=434587500,
        tx_freq=432587500,
        local_id=2400011,
        group_list=[2401] + [0] * 31,
        tx_contact=2401,
        contact_type=1,
        power=0,
        cc=7,
        inbound_slot=0,
        outbound_slot=0,
        channel_mode=0,
        pwrsave=2,
        volume=4,
        mic=15,
        relay=2,
    )
    encoded = dmr.build_set_digital_channel(channel)
    assert encoded == frame_bytes(set_channel)
    assert dmr.check_checksum(encoded)

    get_channel = get_frame(session, 7)
    assert dmr.build_simple_command(dmr.GET_DIGITAL_CHANNEL, dmr.FUNC_ENABLE) == frame_bytes(get_channel)


def test_idle_ts_scan_fixture_toggles_time_slot():
    session = load_session("idle_ts_scan")
    base_kwargs = dict(
        rx_freq=434587500,
        tx_freq=432587500,
        local_id=2400011,
        group_list=[2401] + [0] * 31,
        tx_contact=2401,
        contact_type=1,
        power=0,
        cc=7,
        channel_mode=0,
        pwrsave=2,
        volume=4,
        mic=15,
        relay=2,
    )

    ts1_frame = get_frame(session, 1)
    encoded_ts1 = dmr.build_set_digital_channel(dmr.DigitalChannel(inbound_slot=1, outbound_slot=1, **base_kwargs))
    assert encoded_ts1 == frame_bytes(ts1_frame)

    ts0_frame = get_frame(session, 4)
    encoded_ts0 = dmr.build_set_digital_channel(dmr.DigitalChannel(inbound_slot=0, outbound_slot=0, **base_kwargs))
    assert encoded_ts0 == frame_bytes(ts0_frame)


def test_tx_ptt_fixture_frames():
    session = load_session("tx_ptt")
    ptt_down = get_frame(session, 2)
    assert dmr.build_simple_command(dmr.SET_TRANSMIT_INFORMATION, dmr.FUNC_ENABLE) == frame_bytes(ptt_down)

    ptt_up = get_frame(session, 6)
    assert dmr.build_simple_command(dmr.SET_TRANSMIT_INFORMATION, dmr.FUNC_DISABLE) == frame_bytes(ptt_up)


def test_rx_voice_call_fixture_frames_and_decoders():
    session = load_session("rx_voice_call")

    query_voice_info = get_frame(session, 2)
    assert dmr.build_simple_command(dmr.QUERY_DIGITAL_VOICE_INFO, dmr.FUNC_ENABLE) == frame_bytes(query_voice_info)

    query_rssi = get_frame(session, 4)
    assert dmr.build_simple_command(dmr.QUERY_SIGNAL_STRENGTH, dmr.FUNC_ENABLE) == frame_bytes(query_rssi)

    call_start = bytes([0x68, dmr.VOICE_CALL_EVENT, 0, 0, 0, 0, 0, 0, 0x00, 0x10])
    call_end = bytes([0x68, dmr.VOICE_CALL_EVENT, 0, 0, 0, 0, 0, 0, 0x01, 0x10])
    assert dmr.decode_unsolicited_event(call_start) == "voice_call_start"
    assert dmr.decode_unsolicited_event(call_end) == "voice_call_end"

    voice_info_reply = bytearray([0x68, 0x2B, 1, 0, 0, 0, 0, 1] + [0] * 20)
    # byte 12 (the MSB of this 4-byte contact ID) is 0 for any value < 2**24,
    # which both satisfies voice_info_valid()'s guard and is true of any real
    # DMR ID -- no separate masking needed.
    voice_info_reply[9:13] = (2400011).to_bytes(4, "little")
    voice_info_reply[13:17] = (2401).to_bytes(4, "little")
    rx_contact, rx_group = dmr.decode_voice_info(bytes(voice_info_reply))
    assert rx_group == 2401
    assert dmr.voice_info_valid(bytes(voice_info_reply)) is True

    rssi_reply = bytes([0x68, 0x32, 1, 0, 0, 0, 0, 1, 0x2A, 0x10])
    assert dmr.decode_signal_strength(rssi_reply) == 0x2A


def test_sms_send_fixture_frame():
    session = load_session("sms_send")
    encoded = dmr.build_send_sms(2400011, "DE EX1AMP")
    assert encoded == frame_bytes(get_frame(session, 1))
    assert dmr.check_checksum(encoded)


def test_build_send_sms_rejects_text_that_would_overflow_the_shared_buffer():
    # 119 chars is the longest text whose frame still fits in MAX_FRAME_LEN (256).
    dmr.build_send_sms(2400011, "A" * 119)
    with pytest.raises(ValueError, match="too long"):
        dmr.build_send_sms(2400011, "A" * 120)


def test_decode_sms_received():
    # Mirrors DMRcheckSMSRec (A20Communication.ino:623-647): sender contact ID
    # is a 3-byte little-endian value at offset 9, message text starts at
    # offset 15 and takes only the odd-offset (low) byte of each UCS-2 unit.
    # length_field (offset 7) controls how far the text-extraction loop runs:
    # end = 11 + length_field - 4.
    buf = bytearray(19)
    buf[0] = 0x68
    buf[1] = dmr.SMS_RECEIVED_EVENT
    buf[7] = 10  # end = 11 + 10 - 4 = 17, covers offsets 15 and 17
    buf[9:12] = (2401).to_bytes(4, "little")[:3]
    buf[15], buf[16] = ord("H"), 0x00
    buf[17], buf[18] = ord("I"), 0x00

    sender_id, text = dmr.decode_sms_received(bytes(buf))

    assert sender_id == 2401
    assert text == "HI"


def test_decode_sms_received_rejects_short_frame():
    with pytest.raises(ValueError, match="too short"):
        dmr.decode_sms_received(bytes(15))


def test_error_paths_truncated_frame_times_out_without_faking_success():
    session = load_session("error_paths")
    truncated = get_frame(session, 1)
    transport = FakeSerialTransport()
    transport.feed(frame_bytes(truncated))

    result = dmr.read_frame(transport)

    assert result == frame_bytes(truncated)
    assert dmr.is_well_formed(result) is False
    assert transport.clock.time() == dmr.INTER_BYTE_TIMEOUT


def test_error_paths_unsolicited_event_instead_of_reply():
    session = load_session("error_paths")
    unsolicited = get_frame(session, 2)
    decoded = dmr.decode_unsolicited_event(frame_bytes(unsolicited))
    assert decoded == "voice_call_start"


def test_error_paths_checksum_not_enforced_by_default():
    session = load_session("error_paths")
    corrupted = frame_bytes(get_frame(session, 3))

    # Mirrors the current firmware gap documented in dmr-protocol.md: SR==0
    # is accepted as success even though the checksum bytes don't match.
    assert dmr.is_success_reply(corrupted) is True
    assert dmr.check_checksum(corrupted) is False


def test_error_paths_numeric_field_dispatch_quirk_does_not_affect_dmr_layer():
    # Sanity check that the DMR codec has no notion of the Nextion 0x31
    # fallthrough quirk (that belongs to nextion_protocol) -- included so a
    # future refactor that merges the two dispatchers would fail loudly here.
    session = load_session("error_paths")
    nextion_quirk_frame = get_frame(session, 6)
    assert nextion_quirk_frame["bus"] == "nextion"
