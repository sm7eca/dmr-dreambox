"""Nextion HMI protocol: encode/decode plus a deterministic event reader.

Ports the outbound command shape and inbound event dispatch in
sketch_dreambox/A40Nextion_HMI.ino. See doc/akb/nextion-protocol.md for the
full source-derived inventory, including the deliberately-preserved
case-0x31-falls-through-into-0x32 dispatch quirk implemented in dispatch()
below, and the cumulative (not consecutive) 0xFF-counting quirk implemented
in read_event()/split_terminator(). Encode/decode functions here have no
I/O; read_event() drives a duck-typed transport (see
dreambox_pi/adapters/fake_serial.py) but performs no I/O of its own -- the
actual polling loop lives in domain/_framing.py, shared with
dmr_protocol.read_frame().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from dreambox_pi.domain import _framing

TERMINATOR = b"\xff\xff\xff"
MAX_EVENT_BYTES = 39  # NXlisten's read cap (A40Nextion_HMI.ino:1639), regardless of NXbuff's size

FIRST_BYTE_TIMEOUT = 0.5  # seconds; NXlisten's wait for the first byte (A40Nextion_HMI.ino:1635)
INTER_BYTE_TIMEOUT = 10.0  # seconds; NXlisten's wait between subsequent bytes (A40Nextion_HMI.ino:1652)

NUMERIC_FIELD = 0x31
TEXT_FIELD = 0x32
BUTTON = 0x33
PAGE = 0x34
TOUCH_STANDARD = 0x65
ERROR_INVALID_VARIABLE = 0x1A
ERROR_GENERIC = 0x00


def build_command(command_text: str) -> bytes:
    """Outbound Nextion command: ASCII text + three 0xFF bytes (NXend,
    A40Nextion_HMI.ino:1678-1691)."""
    return command_text.encode("ascii") + TERMINATOR


def split_terminator(buf: bytes) -> Optional[bytes]:
    """Return the received frame up to its completion point, or None if fewer
    than three 0xFF bytes appear within the first MAX_EVENT_BYTES bytes.

    Mirrors NXlisten's ffcount==3 termination and 39-byte read cap
    (A40Nextion_HMI.ino:1627-1676) -- including a verified firmware quirk:
    `ffcount` is never reset on a non-0xFF byte, so this triggers on the 3rd
    cumulative 0xFF byte value, not the 3rd *consecutive* one (see
    doc/akb/nextion-protocol.md). For a well-formed frame (payload followed by
    a genuine trailing FF FF FF) this strips exactly that terminator. If the
    3rd occurrence was reached via non-adjacent 0xFF bytes, there is no clean
    terminator to strip -- NXbuff isn't stripped in the real firmware either
    -- so the full captured frame is returned as-is.
    """
    limit = min(len(buf), MAX_EVENT_BYTES)
    ff_count = 0
    complete_at = None
    for i in range(limit):
        if buf[i] == 0xFF:
            ff_count += 1
            if ff_count == 3:
                complete_at = i
                break
    if complete_at is None:
        return None
    frame = bytes(buf[: complete_at + 1])
    if frame[-3:] == TERMINATOR:
        return frame[:-3]
    return frame


def read_event(
    transport,
    first_byte_timeout: float = FIRST_BYTE_TIMEOUT,
    inter_byte_timeout: float = INTER_BYTE_TIMEOUT,
    max_len: int = MAX_EVENT_BYTES,
) -> bytes:
    """Deterministic port of NXlisten (A40Nextion_HMI.ino:1627-1676).

    `transport` needs only `read(size) -> bytes` and `wait_for_data(timeout)
    -> bool` (see dreambox_pi/adapters/fake_serial.py for the milestone-1 test
    double).

    Waits up to `first_byte_timeout` for the first byte, then up to
    `inter_byte_timeout` between subsequent bytes, until the 3rd cumulative
    0xFF byte is read (see split_terminator()'s docstring -- this does NOT
    require the three to be consecutive, matching a verified firmware quirk),
    `max_len` is reached, or a wait times out. Returns whatever bytes were
    captured -- possibly incomplete; use split_terminator() on the result to
    check whether a full frame arrived. The actual read/timeout loop is
    shared with dmr_protocol.read_frame() via domain/_framing.py.
    """
    return _framing.read_until(
        transport,
        is_complete=lambda buf: sum(1 for b in buf if b == 0xFF) >= 3,
        first_byte_timeout=first_byte_timeout,
        inter_byte_timeout=inter_byte_timeout,
        max_len=max_len,
    )


@dataclass
class NextionEvent:
    kind: str
    page: Optional[int]
    field_or_button: Optional[int]
    activity: Optional[int]
    raw: bytes


def parse_event(payload: bytes) -> NextionEvent:
    """Decode an inbound event payload (post split_terminator, terminator not
    included). Field layout per the NXhandler comment table
    (A40Nextion_HMI.ino:1579-1595):
      0x31 PP FF <number>   numeric field
      0x32 PP FF <text>     text field
      0x33 PP BB AA         button: page, button, activity (1=press, 0=release)
      0x34 PP                page
      0x65 PP CC AA          Nextion standard touch event
      0x1A                   error: invalid variable/attribute
      0x00                   error
    """
    if not payload:
        return NextionEvent("unknown", None, None, None, payload)
    leading = payload[0]
    page = payload[1] if len(payload) > 1 else None
    second = payload[2] if len(payload) > 2 else None
    third = payload[3] if len(payload) > 3 else None

    if leading == NUMERIC_FIELD:
        return NextionEvent("numeric_field", page, second, None, payload)
    if leading == TEXT_FIELD:
        return NextionEvent("text_field", page, second, None, payload)
    if leading == BUTTON:
        return NextionEvent("button", page, second, third, payload)
    if leading == PAGE:
        return NextionEvent("page", page, None, None, payload)
    if leading == TOUCH_STANDARD:
        return NextionEvent("touch_standard", page, second, third, payload)
    if leading == ERROR_INVALID_VARIABLE:
        return NextionEvent("error_invalid_variable", None, None, None, payload)
    if leading == ERROR_GENERIC:
        return NextionEvent("error", None, None, None, payload)
    return NextionEvent("unknown", None, None, None, payload)


def dispatch(payload: bytes) -> List[str]:
    """Return the handler names NXhandler's switch would invoke, IN ORDER, for
    this raw event payload (A40Nextion_HMI.ino:1579-1620).

    Deliberately preserves a verified source quirk: `case 0x31` has no
    `break`, so it falls through into `case 0x32`'s body -- every numeric-field
    event also runs the text-field handler immediately after. This is
    reproduced here rather than "fixed", per doc/akb/nextion-protocol.md;
    change it only as an explicit, documented decision.
    """
    if not payload:
        return []
    leading = payload[0]
    if leading == NUMERIC_FIELD:
        return ["NX_numfield_touched", "NX_txtfield_touched"]
    if leading == TEXT_FIELD:
        return ["NX_txtfield_touched"]
    if leading == BUTTON:
        return ["NX_button_pressed"]
    if leading == PAGE:
        return ["NX_page_init"]
    # 0x65, 0x1A, and any other leading byte are logged only in source, no handler runs.
    return []
