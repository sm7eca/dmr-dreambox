"""Reference port of PcCheckSum/CheckCkSum from sketch_dreambox/A20Communication.ino.

Used to generate and verify the DMR frame bytes in tests/fixtures/sessions/*.json.
Not part of the application runtime — this is a fixture-authoring/verification
tool for milestone 0/1 of doc/akb/raspberry-pi-port-plan.md, kept dependency-free
so it can run standalone.
"""


def pc_checksum(buf: bytes) -> bytes:
    """Return buf with checksum bytes (offset 4-5) filled in, per PcCheckSum."""
    buf = bytearray(buf)
    buf[4] = 0
    buf[5] = 0
    total = 0
    idx = 0
    remaining = len(buf)
    while remaining > 1:
        total += 0xFFFF & (buf[idx] << 8 | buf[idx + 1])
        idx += 2
        remaining -= 2
    if remaining:
        total += (0xFF & buf[idx]) << 8
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    cksum = (0xFFFF & total) ^ 0xFFFF
    buf[5] = cksum & 0xFF
    buf[4] = (cksum >> 8) & 0xFF
    return bytes(buf)


def check_cksum(buf: bytes) -> bool:
    """Return True if buf's checksum bytes (offset 4-5) match PcCheckSum, per CheckCkSum."""
    buf = bytearray(buf)
    received = (buf[4] << 8) | buf[5]
    buf[4] = 0
    buf[5] = 0
    recomputed = pc_checksum(buf)
    recomputed_value = (recomputed[4] << 8) | recomputed[5]
    return received == recomputed_value


if __name__ == "__main__":
    # Sanity-check against the fixed 10-byte DMRTransmit(mode, CMD) frames
    # documented in doc/akb/dmr-protocol.md.
    known = {
        (0x27, 0x01): "68 27 01 01 95 C6 00 01 01 10",  # QUERY_INIT_FINISHED
        (0x26, 0x01): "68 26 01 01 95 C7 00 01 01 10",  # SET_TRANSMIT_INFORMATION / PTT down
    }
    for (cmd, mode), expected_hex in known.items():
        frame = bytes([0x68, cmd, 0x01, 0x01, 0x00, 0x00, 0x00, 0x01, mode, 0x10])
        got = pc_checksum(frame)
        expected = bytes.fromhex(expected_hex.replace(" ", ""))
        assert got == expected, f"mismatch for cmd={cmd:#x} mode={mode:#x}: {got.hex()} != {expected.hex()}"
        assert check_cksum(got)
    print("pc_checksum self-check OK")
