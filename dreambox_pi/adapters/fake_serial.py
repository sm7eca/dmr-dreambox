"""A fake, deterministic stand-in for a real serial transport (pyserial or
otherwise), for milestone 1 of doc/akb/raspberry-pi-port-plan.md ("Build a
host-side protocol harness ... fake serial transports supporting partial
reads, timeouts, malformed frames, disconnects, and reconnects").

Exposes the minimal duck-typed interface the domain-level frame readers need
(`read(size)`, `write(data)`, `in_waiting`, `wait_for_data(timeout)`), so a
real adapter built on pyserial in a later milestone can satisfy the same
interface without any change to dreambox_pi/domain code.
"""

from __future__ import annotations

from collections import deque
from typing import Optional


class TransportDisconnected(Exception):
    """Raised by write() when the transport is in a disconnected state."""


class FakeClock:
    """A manually-advanced clock, so timeout behavior is tested deterministically
    instead of by actually sleeping."""

    def __init__(self, start: float = 0.0):
        self.now = start

    def time(self) -> float:
        return self.now

    def advance(self, seconds: float) -> float:
        self.now += seconds
        return self.now


class FakeSerialTransport:
    """A queue of byte chunks that drains via read(), with disconnect/reconnect
    and a fake clock for deterministic timeout tests."""

    def __init__(self, clock: Optional[FakeClock] = None):
        self.clock = clock or FakeClock()
        self._queue: deque[bytes] = deque()
        self._connected = True
        self.written = bytearray()

    def feed(self, data: bytes, chunk_size: Optional[int] = None) -> None:
        """Queue bytes for subsequent read() calls. Pass chunk_size to force
        the data to arrive across multiple reads, simulating a partial read
        (e.g. a UART delivering a frame a few bytes at a time)."""
        data = bytes(data)
        if not data:
            return
        if chunk_size is None:
            self._queue.append(data)
            return
        for i in range(0, len(data), chunk_size):
            self._queue.append(data[i : i + chunk_size])

    def disconnect(self) -> None:
        """Simulate a lost UART: no data will ever arrive, writes raise."""
        self._connected = False

    def reconnect(self) -> None:
        self._connected = True

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def in_waiting(self) -> int:
        if not self._connected or not self._queue:
            return 0
        return len(self._queue[0])

    def read(self, size: int = 1) -> bytes:
        """Return up to `size` bytes available right now, or b"" if none.
        Never blocks -- timeout/backoff behavior lives in the domain-level
        frame readers, which call wait_for_data() between read() calls."""
        if not self._connected or not self._queue:
            return b""
        chunk = self._queue[0]
        take = chunk[:size]
        rest = chunk[size:]
        if rest:
            self._queue[0] = rest
        else:
            self._queue.popleft()
        return take

    def write(self, data: bytes) -> int:
        if not self._connected:
            raise TransportDisconnected("write on disconnected transport")
        self.written += bytes(data)
        return len(data)

    def wait_for_data(self, timeout: float) -> bool:
        """Deterministic stand-in for the busy-wait loops in DMRreceive/
        NXlisten, which poll `available() > 0` against a wall clock. Returns
        True immediately if data is already queued; otherwise advances the
        fake clock by `timeout` and returns False -- modeling a timed-out
        wait without actually sleeping in tests. A real adapter would instead
        poll `in_waiting` against `time.monotonic()` for up to `timeout`
        seconds."""
        if self.in_waiting > 0:
            return True
        self.clock.advance(timeout)
        return False
