"""Real serial transport adapter (milestone 3 of
doc/akb/raspberry-pi-port-plan.md), built on pyserial.

Implements the same duck-typed interface as
fake_serial.FakeSerialTransport (`read(size)`, `write(data)`, `in_waiting`,
`wait_for_data(timeout)`), so dreambox_pi.domain.dmr_protocol.read_frame()
and dreambox_pi.domain.nextion_protocol.read_event() work completely
unchanged against a real UART -- only the transport passed to them differs.
Device path and baud rate come from dreambox_pi.service.config, never from
source constants.

Note: pyserial is opened with timeout=0 (non-blocking reads) unconditionally.
That is an internal implementation detail of satisfying this class's
non-blocking read() contract, not a device/protocol behavior choice -- the
actual "how long to wait for data" behavior is entirely handled by
wait_for_data(), matching first_byte_timeout/inter_byte_timeout at the
protocol layer (service/config.py's TimeoutConfig).
"""

from __future__ import annotations

import time
from typing import List

import serial
import serial.tools.list_ports

_POLL_INTERVAL = 0.005  # seconds; how often wait_for_data re-checks in_waiting


class SerialTransport:
    def __init__(self, port: str, baudrate: int):
        self._serial = serial.Serial(port=port, baudrate=baudrate, timeout=0)

    @property
    def in_waiting(self) -> int:
        return self._serial.in_waiting

    def read(self, size: int = 1) -> bytes:
        return self._serial.read(size)

    def write(self, data: bytes) -> int:
        return self._serial.write(data)

    def wait_for_data(self, timeout: float) -> bool:
        if self._serial.in_waiting > 0:
            return True
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            time.sleep(_POLL_INTERVAL)
            if self._serial.in_waiting > 0:
                return True
        return False

    def close(self) -> None:
        self._serial.close()


def list_available_ports() -> List[str]:
    """Serial device discovery, for setup/diagnostics -- not used by the
    protocol readers themselves, which always take an explicit configured
    port. Returns device paths only; matching a specific port to "the DMR
    module" vs. "the Nextion display" by USB vendor/product ID is not
    implemented here (see raspberry-pi-port-plan.md's hardware-mapping table:
    "Prefer two uniquely identifiable USB-UART adapters")."""
    return [info.device for info in serial.tools.list_ports.comports()]
