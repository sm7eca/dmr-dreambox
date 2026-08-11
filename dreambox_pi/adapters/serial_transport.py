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

wait_for_data() blocks in the kernel via select() rather than sleep-polling
in_waiting -- see doc/adr/04_adr_dreambox_pi_io_concurrency_model.md. This
matters because dreambox_pi/service/runtime.py runs one reader thread per
UART, each spending most of its life inside wait_for_data(): a sleep-poll
loop would wake every thread on a fixed interval for as long as the port is
idle, for no reason, instead of the kernel waking exactly the thread whose
fd became readable.

select() reports a fd "readable" both when there is data to read AND when
the peer has hung up (EOF) -- read() then returns b"" forever instead of
ever raising, which without the in_waiting check below would make
domain/_framing.py's read loop spin at 100% CPU indefinitely rather than
time out. Checking in_waiting after select() distinguishes the two cases and
raises OSError for a hangup, so it surfaces the same way any other transport
failure does to callers (dreambox_pi/service/runtime.py's reader loops
already catch OSError and report it as a lost connection).
"""

from __future__ import annotations

import select
from typing import List

import serial
import serial.tools.list_ports


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
        readable, _, _ = select.select([self._serial.fileno()], [], [], timeout)
        if not readable:
            return False
        if self._serial.in_waiting == 0:
            raise OSError("serial transport closed (fd readable but no data pending -- peer hung up)")
        return True

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
