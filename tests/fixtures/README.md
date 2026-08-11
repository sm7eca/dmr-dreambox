# Protocol fixture skeletons

These are **skeletons for milestone 1** of
[raspberry-pi-port-plan.md](../../doc/akb/raspberry-pi-port-plan.md) ("Build a
host-side protocol harness"), not bench captures. Milestone 0 item 3
([session-capture-status.md](../../doc/akb/session-capture-status.md))
found no hardware available in this environment to capture real traffic, so
these fixtures encode what source analysis
([dmr-protocol.md](../../doc/akb/dmr-protocol.md),
[nextion-protocol.md](../../doc/akb/nextion-protocol.md)) predicts for each
named flow. **Every frame here must be checked against a real bench capture
before the port trusts it.** That's what the `confidence` field on each frame
is for.

## Layout

- `sessions/*.json` — one file per named flow from the port plan's milestone
  0 item 3: `startup`, `idle_ts_scan`, `tx_ptt`, `rx_voice_call`,
  `channel_change`, `sms_send` (bonus — a fully-specified command not in the
  original 6, kept because it's a good test case for the SMS-quirks noted in
  dmr-protocol.md), `error_paths`.
- `tools/pc_checksum.py` — a standalone Python port of `PcCheckSum`/
  `CheckCkSum` (`sketch_dreambox/A20Communication.ino`), used to generate and
  verify the checksum bytes in every DMR frame below. Run it directly
  (`python3 tools/pc_checksum.py`) to self-check.

## Schema

Each session file is a JSON object:

```jsonc
{
  "flow": "tx_ptt",
  "description": "...",
  "source_refs": ["A30Main_State_Handling.ino:11-18", "..."],
  "frames": [
    {
      "seq": 1,
      "bus": "dmr" | "nextion",
      "direction": "host_to_module" | "module_to_host" | "host_to_display" | "display_to_host",
      "command": "SET_TRANSMIT_INFORMATION / FUNC_ENABLE",
      "confidence": "computed" | "computed-assuming-natural-alignment" | "known-partial" | "synthetic-malformed" | "assumption",
      "bytes_hex": "68 26 01 01 95 C7 00 01 01 10",
      "ascii": null,
      "known_fields": null,
      "notes": "..."
    }
  ]
}
```

- `bytes_hex` is set when the frame's bytes are fully determined by source
  (fixed-length commands) or explicitly computed with a documented checksum
  tool. `ascii` is used instead for outbound Nextion text commands (append
  `FF FF FF` to get the wire bytes — that terminator is never repeated in the
  JSON to avoid clutter).
- `known_fields` is set instead of `bytes_hex`/`ascii` when only *part* of the
  frame is knowable from source (most module replies — the header shape and
  one or two payload bytes are documented, but total length and the rest of
  the payload are not). Treat these as decode assertions to write in
  milestone 1's harness tests, not literal bytes to replay.
- `confidence` values:
  - `computed` — fixed-length command, byte-for-byte determined by source,
    checksum computed with `tools/pc_checksum.py`.
  - `computed-assuming-natural-alignment` — struct-based command
    (`SET_DIGITAL_CHANNEL`) where the byte layout was derived assuming the C
    struct has no compiler-inserted padding (verified by hand for this one
    field order — every multi-byte field happens to land on a natural
    alignment boundary). Not confirmed against an actual compiled
    `sizeof()` or a bench capture. See "Open items" in dmr-protocol.md.
  - `known-partial` — only some fields are knowable; `bytes_hex` is absent.
  - `synthetic-malformed` — deliberately constructed to exercise an error
    path (truncated frame, bad checksum), not a prediction of real traffic.
  - `assumption` — inferred from a comment or convention, not from code that
    executes the exact byte sequence.

## Sanitization

Two real identifiers appear in the firmware source as literal example bytes
(a maintainer callsign in `DMRsendSMS`'s hardcoded message text, and a real
DMR contact ID). Neither is reproduced here — `sms_send.json` uses the
fictional callsign `EX1AMP` and DMR ID `2400011` instead, keeping the same
byte lengths/structure so the checksum math stays representative. This
follows the same rule as
[eim-examples.md](../../doc/akb/eim-examples.md#credentials-and-pii-handling-for-the-port).

## Using these in milestone 1

1. Write the DMR/Nextion decoders first against the `computed` frames — those
   are trustworthy today.
2. For `known-partial` frames, write the decoder to assert only the known
   fields, and leave the rest as an explicit `TODO` tied to a bench capture.
3. Once real bench captures exist (see session-capture-status.md), diff them
   against these skeletons, fix whatever assumptions were wrong (expect at
   least the `SET_DIGITAL_CHANNEL` struct layout and all reply shapes to need
   correction), and update `confidence` to `bench-verified`.
