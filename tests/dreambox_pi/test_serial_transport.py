"""Adapter tests for dreambox_pi.adapters.serial_transport, against real
pseudo-terminals (Python's pty module) rather than the in-memory
FakeSerialTransport -- this is milestone 3's explicit exit criterion
("passes adapter tests with pseudo-terminals"), giving confidence in the
actual pyserial/OS I/O path without needing physical hardware.
"""

import os
import pty
import sys
import time
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from dreambox_pi.adapters.serial_transport import SerialTransport
from dreambox_pi.domain import dmr_protocol as dmr
from dreambox_pi.domain import nextion_protocol as nx


@pytest.fixture
def pty_pair():
    master_fd, slave_fd = pty.openpty()
    slave_name = os.ttyname(slave_fd)
    transport = SerialTransport(port=slave_name, baudrate=57600)
    yield master_fd, transport
    transport.close()
    os.close(master_fd)


def test_read_returns_bytes_written_to_the_master_end(pty_pair):
    master_fd, transport = pty_pair
    os.write(master_fd, b"hello")
    time.sleep(0.05)

    assert transport.in_waiting == 5
    assert transport.read(5) == b"hello"
    assert transport.read(1) == b""  # nothing left, non-blocking


def test_write_reaches_the_master_end(pty_pair):
    master_fd, transport = pty_pair
    transport.write(b"world")
    assert os.read(master_fd, 5) == b"world"


def test_wait_for_data_true_when_already_queued(pty_pair):
    master_fd, transport = pty_pair
    os.write(master_fd, b"x")
    time.sleep(0.05)
    assert transport.wait_for_data(1.0) is True


def test_wait_for_data_times_out_when_nothing_arrives(pty_pair):
    _master_fd, transport = pty_pair
    start = time.monotonic()
    assert transport.wait_for_data(0.2) is False
    assert time.monotonic() - start >= 0.2


def test_partial_delivery_across_multiple_writes(pty_pair):
    """Simulates a real UART delivering a frame a few bytes at a time --
    exactly the scenario fake_serial.FakeSerialTransport.feed(chunk_size=...)
    models in memory, now exercised over a real pty."""
    master_fd, transport = pty_pair
    os.write(master_fd, bytes([0x68, 0x27]))
    time.sleep(0.02)
    os.write(master_fd, bytes([0x01, 0x01, 0x95, 0xC6, 0x00, 0x01, 0x01, 0x10]))
    time.sleep(0.05)

    assert transport.in_waiting == 10
    assert transport.read(10).hex(" ").upper() == "68 27 01 01 95 C6 00 01 01 10"


def test_dmr_read_frame_over_a_real_pty(pty_pair):
    master_fd, transport = pty_pair
    frame = dmr.build_simple_command(dmr.QUERY_INIT_FINISHED, dmr.FUNC_ENABLE)

    for byte in frame:
        os.write(master_fd, bytes([byte]))
        time.sleep(0.005)  # force several separate reads, not one big one

    result = dmr.read_frame(transport)

    assert result == frame
    assert dmr.is_well_formed(result)


def test_dmr_read_frame_times_out_on_a_real_pty_with_no_data(pty_pair):
    _master_fd, transport = pty_pair
    result = dmr.read_frame(transport, first_byte_timeout=0.1, inter_byte_timeout=0.1)
    assert result == b""


def test_nextion_read_event_over_a_real_pty(pty_pair):
    master_fd, transport = pty_pair
    frame = bytes.fromhex("33000001") + nx.TERMINATOR

    os.write(master_fd, frame)
    time.sleep(0.05)

    result = nx.read_event(transport)

    assert result == frame
    payload = nx.split_terminator(result)
    parsed = nx.parse_event(payload)
    assert parsed.kind == "button"
    assert (parsed.page, parsed.field_or_button, parsed.activity) == (0, 0, 1)
