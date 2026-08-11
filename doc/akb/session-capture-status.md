# Session capture status (milestone 0, item 3)

Status: **blocked — no hardware in this environment.** This tracks milestone
0 item 3 of the [Raspberry Pi port plan](raspberry-pi-port-plan.md): sanitized
startup, idle, RX, TX, channel-change, and error session captures.

## Why this is blocked here

Capturing real UART traffic requires a bench with the physical DMR module and
Nextion display attached to a listening UART (e.g. a USB-UART tapping
`Serial2`/`Serial1`, or firmware built with `DMRDebug`/`NXDebug` trace output
captured over the existing `Serial` debug port). Nothing in this repository
substitutes for that. Beyond `tests/test_eim_service.py` (Python unit tests
for the EIM service), the only DMR/Nextion material in the repository is the
source-derived fixture *skeletons* under `tests/fixtures/sessions/` described
below — synthetic predictions, not bench captures.

## What source analysis can predict about each flow

These are **assumptions to verify**, not captures. Use them to write the
first replay-fixture skeletons in milestone 1, then correct them against a
real capture:

- **Startup**: `QUERY_INIT_FINISHED` (`0x27`) sent repeatedly with 1 s
  delay until a successful reply, then `SET_DIGITAL_CHANNEL` (`0x22`, full
  channel struct), then `GET_DIGITAL_CHANNEL` (`0x24`) to verify. On the
  Nextion side: `page 3` → status text updates → `page main` once ready.
- **Idle with time-slot scanning**: every 2000 ms, a full
  `SET_DIGITAL_CHANNEL` re-send with `InboundSlot`/`OutboundSlot` toggled
  0↔1, and a Nextion time-slot indicator update.
- **RX (voice)**: unsolicited `0x3D` (byte 8 = `0`) starts the flow; host
  issues `QUERY_DIGITAL_VOICE_INFO` (`0x2B`) and `QUERY_SIGNAL_STRENGTH`
  (`0x32`) roughly every 5 s while receiving; Nextion RSSI/contact fields
  update; unsolicited `0x3D` (byte 8 = `1`) ends the flow.
- **TX (PTT)**: `SET_TRANSMIT_INFORMATION` (`0x26`) with `FUNC_ENABLE` on
  press, `FUNC_DISABLE` on release; Nextion transmit indicator toggles
  immediately, no round trip wait modeled in firmware beyond the DMR reply.
- **Channel/talk-group change**: Nextion page-4/5/6 navigation events select
  a repeater/TG, then a full `SET_DIGITAL_CHANNEL` re-send.
- **Error paths worth capturing deliberately**: DMR module not responding at
  startup (infinite retry — confirm there's truly no give-up path), a
  `0x10` byte appearing mid-payload, a reply with mismatched `CMD`, and a
  UART disconnect/reconnect during an active RX.

## What's needed to unblock

1. Bench access to a DMR Dreambox unit (or the DMR module + Nextion display
   pair) wired to a UART tap, per
   [raspberry-pi-port-plan.md](raspberry-pi-port-plan.md)'s hardware mapping
   table.
2. A capture tool (e.g. a simple Python pyserial logger, or the existing
   `DMRDebug`/`NXDebug` trace already built into the firmware, redirected to
   a log file over the `Serial` debug UART).
3. Sanitization pass on any captured DMR ID / callsign / name before the
   fixture is committed — same rule as in
   [eim-examples.md](eim-examples.md).

Until captured, milestone 0's exit criterion ("reviewed protocol notes and
replay fixtures reproduce all named flows without hardware") is **not fully
met** — the protocol notes exist ([dmr-protocol.md](dmr-protocol.md),
[nextion-protocol.md](nextion-protocol.md)) and a first pass at fixture
*skeletons* now exists too (`tests/fixtures/sessions/*.json`, one per flow
above, see `tests/fixtures/README.md`), but they encode source-derived
predictions with an explicit `confidence` rating per frame, not real captured
bytes. Treat them as the shape milestone 1's decoders should target, and the
checklist for what a bench capture needs to confirm or correct.
