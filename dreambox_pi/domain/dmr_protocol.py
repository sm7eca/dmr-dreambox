"""DMR module protocol: encode/decode plus a deterministic frame reader.

Ports sketch_dreambox/A20Communication.ino and the command table in
sketch_dreambox/sketch_dreambox.ino:11-32. See doc/akb/dmr-protocol.md for the
full source-derived inventory this module implements, including open items
not yet confirmed against a bench capture (struct padding, reply shapes).
Encode/decode functions here have no I/O; read_frame() below drives a
duck-typed transport (see dreambox_pi/adapters/fake_serial.py) but performs
no I/O of its own -- the actual polling loop lives in domain/_framing.py,
shared with nextion_protocol.read_event().
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import List, Optional

from dreambox_pi.domain import _framing

HEAD = 0x68
TAIL = 0x10

SET_DIGITAL_CHANNEL = 0x22
SET_ANALOG_CHANNEL = 0x23
GET_DIGITAL_CHANNEL = 0x24
GET_ANALOG_CHANNEL = 0x25
SET_TRANSMIT_INFORMATION = 0x26
QUERY_INIT_FINISHED = 0x27
SET_ENHANCED_FUNCTION = 0x28
SET_ENCRYPTION_FUNCTION = 0x29
SET_MIC_GAIN = 0x2A
QUERY_DIGITAL_VOICE_INFO = 0x2B
SEND_SMS = 0x2C
GET_SMS = 0x2D
SET_VOLUME = 0x2E
SET_MONITOR = 0x2F
SET_SQUELCH = 0x30
SET_POWER_MODE = 0x31
QUERY_SIGNAL_STRENGTH = 0x32
SET_RELAY_DISCONNECT_NET_MODE = 0x33
QUERY_VERSION = 0x34

FUNC_ENABLE = 0x01
FUNC_DISABLE = 0x02

VOICE_CALL_EVENT = 0x3D
SMS_RECEIVED_EVENT = 0x2D  # shares its byte with GET_SMS; ambiguous per source, see dmr-protocol.md

FIRST_BYTE_TIMEOUT = 1.0  # seconds; DMRreceive's wait for the first byte (A20Communication.ino:170)
INTER_BYTE_TIMEOUT = 10.0  # seconds; DMRreceive's wait between subsequent bytes (A20Communication.ino:187)
MAX_FRAME_LEN = 256  # buff[256], the shared global receive buffer (sketch_dreambox.ino:71)


def pc_checksum(buf: bytes) -> bytes:
    """Port of PcCheckSum (A20Communication.ino:2-27). Returns buf with the
    checksum bytes at offset 4-5 filled in (they are zeroed first)."""
    out = bytearray(buf)
    out[4] = 0
    out[5] = 0
    total = 0
    idx = 0
    remaining = len(out)
    while remaining > 1:
        total += 0xFFFF & (out[idx] << 8 | out[idx + 1])
        idx += 2
        remaining -= 2
    if remaining:
        total += (0xFF & out[idx]) << 8
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    cksum = (0xFFFF & total) ^ 0xFFFF
    out[5] = cksum & 0xFF
    out[4] = (cksum >> 8) & 0xFF
    return bytes(out)


def check_checksum(buf: bytes) -> bool:
    """Port of CheckCkSum (A20Communication.ino:29-53). Not currently called by
    the firmware on receive -- DMRreceive/DMRreceiveReply only check the tail
    byte and the SR field. Provided for a port that chooses to enforce it
    strictly (recommended; see dmr-protocol.md 'open items')."""
    if len(buf) < 6:
        return False
    received = (buf[4] << 8) | buf[5]
    recomputed = pc_checksum(buf)
    return received == ((recomputed[4] << 8) | recomputed[5])


def build_simple_command(cmd: int, mode: int) -> bytes:
    """10-byte frame built by DMRTransmit(mode, CMD) (A20Communication.ino:260-283).
    Used for QUERY_INIT_FINISHED, SET_TRANSMIT_INFORMATION, SET_VOLUME,
    SET_MIC_GAIN, QUERY_SIGNAL_STRENGTH, QUERY_VERSION, GET_DIGITAL_CHANNEL,
    QUERY_DIGITAL_VOICE_INFO -- any command whose payload is a single byte."""
    frame = bytes([HEAD, cmd, 0x01, 0x01, 0x00, 0x00, 0x00, 0x01, mode, TAIL])
    return pc_checksum(frame)


@dataclass
class DigitalChannel:
    """Mirrors db_digital_info (sketch_dreambox.ino:180-207)."""

    rx_freq: int
    tx_freq: int
    local_id: int
    group_list: List[int]
    tx_contact: int
    contact_type: int
    power: int = 0
    cc: int = 0
    inbound_slot: int = 0
    outbound_slot: int = 0
    channel_mode: int = 0
    encrypt_sw: int = 2  # 1=enable 2=disable; firmware always sends 2
    encrypt_key: bytes = bytes(8)  # immutable, so a plain default (not default_factory) is safe
    pwrsave: int = 2  # 1=enable 2=disable
    volume: int = 4
    mic: int = 15
    relay: int = 2  # 1=enable 2=disable


def build_set_digital_channel(channel: DigitalChannel) -> bytes:
    """Encode db_digital_info as DMRupdateDigChannel sends it: a raw memcpy of
    the C struct (A20Communication.ino:360-377). Byte layout below assumes the
    struct has no compiler-inserted padding -- verified by hand that every
    multi-byte field lands on a natural alignment boundary for this field
    order, but NOT confirmed against a compiled sizeof() or a bench capture.
    See doc/akb/dmr-protocol.md 'open items' before trusting this against
    real hardware."""
    if len(channel.group_list) != 32:
        raise ValueError("group_list must have exactly 32 entries")
    encrypt_key = bytes(channel.encrypt_key).ljust(8, b"\x00")[:8]

    body = bytearray()
    body += struct.pack("<I", channel.rx_freq)
    body += struct.pack("<I", channel.tx_freq)
    body += struct.pack("<I", channel.local_id)
    for group_id in channel.group_list:
        body += struct.pack("<I", group_id)
    body += struct.pack("<I", channel.tx_contact)
    body += bytes(
        [
            channel.contact_type,
            channel.power,
            channel.cc,
            channel.inbound_slot,
            channel.outbound_slot,
            channel.channel_mode,
            channel.encrypt_sw,
        ]
    )
    body += encrypt_key
    body += bytes([channel.pwrsave, channel.volume, channel.mic, channel.relay, TAIL])

    total_len = 8 + len(body)
    header = bytes([HEAD, SET_DIGITAL_CHANNEL, 0x01, 0x01, 0x00, 0x00, 0x00, total_len - 9])
    return pc_checksum(header + bytes(body))


def build_send_sms(contact_id: int, text: str) -> bytes:
    """Encode SEND_SMS reproducing DMRsendSMS's literal byte layout
    (A20Communication.ino:454-527), including two documented quirks:
    - contact_id is 3 bytes, little-endian, not 4 (source comment: "callnum
      ar 3 byte!! took a hell of a time to find out").
    - a stray extra 0x00 byte precedes the tail, after the last UCS-2
      character, that isn't part of a clean code unit -- present in source,
      cause unconfirmed. Preserved here rather than silently dropped."""
    if not (0 <= contact_id < 2**24):
        raise ValueError("contact_id must fit in 3 bytes")
    if any(ord(char) > 0xFF for char in text):
        raise ValueError("only single-byte characters are supported (matches firmware's byte-per-char encoding)")
    max_text_len = (MAX_FRAME_LEN - 18) // 2  # total frame length is 18 + 2*len(text); see body layout below
    if len(text) > max_text_len:
        raise ValueError(
            f"text too long ({len(text)} chars): SEND_SMS frame would exceed the "
            f"{MAX_FRAME_LEN}-byte shared DMR buffer (buff[256], sketch_dreambox.ino:71); "
            f"max supported length is {max_text_len} characters"
        )

    body = bytearray()
    body.append(0x01)  # msg_type = 1 (IP with confirm)
    body += contact_id.to_bytes(4, "little")[:3]
    body += bytes([0x00, 0x0D, 0x00, 0x0A])  # undocumented header filler, CRLF as UCS-2BE
    for char in text:
        body += bytes([0x00, ord(char)])
    body += bytes([0x00])  # stray byte, see docstring
    body += bytes([TAIL])

    total_len = 8 + len(body)
    header = bytes([HEAD, SEND_SMS, 0x01, 0x01, 0x00, 0x00, 0x00, total_len - 9])
    return pc_checksum(header + bytes(body))


def is_well_formed(buf: bytes) -> bool:
    """Frame-boundary check only: head byte and tail byte present. This is all
    DMRreceive checks structurally before inspecting SR (A20Communication.ino:163-219)."""
    return len(buf) >= 10 and buf[0] == HEAD and buf[-1] == TAIL


def is_success_reply(buf: bytes) -> bool:
    """Mirrors DMRreceive's only success check: buff[3] == 0
    (A20Communication.ino:180-182). Deliberately does not check the checksum --
    the firmware doesn't either. Use check_checksum() separately if the port
    decides to enforce it."""
    return is_well_formed(buf) and buf[3] == 0x00


def decode_unsolicited_event(buf: bytes) -> Optional[str]:
    """Return "voice_call_start", "voice_call_end", "sms_received", or None.
    Mirrors DMRhandler's dispatch (A20Communication.ino:55-85)."""
    if len(buf) < 9 or buf[0] != HEAD:
        return None
    if buf[1] == VOICE_CALL_EVENT:
        return "voice_call_start" if buf[8] == 0x00 else "voice_call_end"
    if buf[1] == SMS_RECEIVED_EVENT:
        return "sms_received"
    return None


def decode_voice_info(buf: bytes) -> tuple[int, int]:
    """Mirrors DMRqueryReceived's decode of a QUERY_DIGITAL_VOICE_INFO reply
    (A20Communication.ino:648-686): rx_contact is a little-endian uint32 at
    offset 9, rx_group is a little-endian uint32 at offset 13."""
    if len(buf) < 17:
        raise ValueError("frame too short to contain voice info")
    rx_contact = struct.unpack_from("<I", buf, 9)[0]
    rx_group = struct.unpack_from("<I", buf, 13)[0]
    return rx_contact, rx_group


def voice_info_valid(buf: bytes) -> bool:
    """Mirrors the acceptance guard in DMRqueryReceived: buff[12] == 0
    (A20Communication.ino:654). Note byte 12 is simultaneously the high byte
    of rx_contact as decoded by decode_voice_info() -- this double-use is
    verified in source, not obviously intentional. See dmr-protocol.md."""
    return len(buf) > 12 and buf[12] == 0x00


def decode_signal_strength(buf: bytes) -> int:
    """Mirrors DMRcheckRSSI: RSSI value is buff[8], 0 = no signal
    (A20Communication.ino:611-621)."""
    if len(buf) < 9:
        raise ValueError("frame too short to contain a signal-strength byte")
    return buf[8]


def read_frame(
    transport,
    first_byte_timeout: float = FIRST_BYTE_TIMEOUT,
    inter_byte_timeout: float = INTER_BYTE_TIMEOUT,
    max_len: int = MAX_FRAME_LEN,
) -> bytes:
    """Deterministic port of DMRreceive (A20Communication.ino:163-219).

    `transport` needs only `read(size) -> bytes` and `wait_for_data(timeout)
    -> bool` (see dreambox_pi/adapters/fake_serial.py for the milestone-1 test
    double; a real adapter would implement wait_for_data by polling
    in_waiting against a real clock).

    Waits up to `first_byte_timeout` for the first byte, then up to
    `inter_byte_timeout` between subsequent bytes, until a TAIL byte is read,
    `max_len` is reached, or a wait times out. Returns whatever bytes were
    captured -- possibly empty (nothing arrived) or incomplete (cut short by a
    timeout). Check is_well_formed() on the result rather than assuming a
    complete frame. The actual read/timeout loop is shared with
    nextion_protocol.read_event() via domain/_framing.py.
    """
    return _framing.read_until(
        transport,
        is_complete=lambda buf: buf[-1] == TAIL,
        first_byte_timeout=first_byte_timeout,
        inter_byte_timeout=inter_byte_timeout,
        max_len=max_len,
    )


def decode_sms_received(buf: bytes) -> tuple[int, str]:
    """Mirrors DMRcheckSMSRec (A20Communication.ino:623-647): sender contact ID
    is a 3-byte little-endian value at offset 9, message text starts at offset
    15 and takes only odd-indexed bytes up to `11 + buf[7] - 4` -- i.e. only
    the low byte of each UCS-2 code unit. This drops the high byte of every
    character, so only ASCII-range text survives intact; verified quirk, not
    corrected here."""
    if len(buf) < 16:
        raise ValueError("frame too short to contain an SMS payload")
    sender_id = buf[9] | (buf[10] << 8) | (buf[11] << 16)
    length_field = buf[7]
    end = 11 + length_field - 4
    chars = [chr(buf[i]) for i in range(15, min(end, len(buf) - 1) + 1) if i % 2 == 1]
    return sender_id, "".join(chars)
