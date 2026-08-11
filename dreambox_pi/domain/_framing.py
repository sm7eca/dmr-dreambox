"""Shared byte-oriented frame-reading loop for dmr_protocol.read_frame() and
nextion_protocol.read_event(). Both are deterministic ports of a firmware
function that waits for a first byte, then waits between subsequent bytes,
until a protocol-specific completion check succeeds. This module owns that
polling loop once; each protocol module supplies only its own completion
predicate and timeout constants.
"""

from __future__ import annotations

from typing import Callable

Transport = object  # duck-typed: needs read(size) -> bytes and wait_for_data(timeout) -> bool


def read_until(
    transport: Transport,
    is_complete: Callable[[bytes], bool],
    first_byte_timeout: float,
    inter_byte_timeout: float,
    max_len: int,
) -> bytes:
    """Read one byte at a time from `transport` until `is_complete(buf)` is
    True, `max_len` bytes have been captured, or a wait times out.

    Returns whatever bytes were captured -- possibly empty (nothing arrived
    within `first_byte_timeout`) or incomplete (cut short by a later timeout
    or the length cap). Callers are responsible for deciding what an
    incomplete result means for their protocol.
    """
    if not transport.wait_for_data(first_byte_timeout):
        return b""
    buf = bytearray()
    while len(buf) < max_len:
        chunk = transport.read(1)
        if not chunk:
            if not transport.wait_for_data(inter_byte_timeout):
                return bytes(buf)
            continue
        buf.append(chunk[0])
        if is_complete(bytes(buf)):
            return bytes(buf)
    return bytes(buf)
