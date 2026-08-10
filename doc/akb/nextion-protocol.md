# Nextion HMI protocol (source inventory)

Status: **Verified** from `sketch_dreambox/A40Nextion_HMI.ino` and
`sketch_dreambox/sketch_dreambox.ino` unless marked otherwise. This is
milestone 0, item 2 of the [Raspberry Pi port plan](raspberry-pi-port-plan.md).

## Transport

- UART, `Serial1` on the ESP32 (`sketch_dreambox.ino:61-62`, `RXD1=2`,
  `TXD1=4`), 57600 baud, 8N1.
- Outbound (host → display): ASCII Nextion Instruction Set commands, each
  terminated by three `0xFF` bytes (`NXend`, `A40Nextion_HMI.ino:1678-1691`).
  This is the standard Nextion protocol convention, not a custom framing.
- Inbound (display → host): binary event messages, nominally terminated by
  three `0xFF` bytes, but `NXlisten`'s `ffcount` counter is **never reset** on
  a non-`0xFF` byte (`A40Nextion_HMI.ino:1642-1650`) — it terminates on the
  3rd `0xFF` byte value seen anywhere in the message, not the 3rd
  *consecutive* one. In practice this only differs from "three consecutive"
  when an isolated `0xFF` appears earlier in the payload (e.g. as part of a
  numeric/text field value), which would end the read early. Receive buffer
  `NXbuff[100]` (`sketch_dreambox.ino:72`), but `NXlisten` caps reads at
  `i < 39` bytes regardless of buffer size.

## Outbound command shape

All outbound traffic is built with `NextionCmd.print(...)` calls followed by
`NXend(n)`, where `n` is an arbitrary debug/trace tag (not part of the wire
protocol — purely for matching Serial-monitor log lines to source, see
`lastNXtrans`). Typical forms seen throughout the file:

- Page navigation: `"page <name-or-number>"` e.g. `"page main"`, `"page 13"`.
- Attribute set: `"<object>.<attr>=<value>"` e.g. `"main.t0.txt=\"...\""`,
  `"bt2.val=1"`.
- Global display attribute: `"dim=25"` / `"dim=100"` for backlight dimming
  (`NXdimdisplay`, `A40Nextion_HMI.ino:29-44`).

There is no custom checksum or length prefix on the outbound side — safety
relies entirely on the Nextion firmware parsing ASCII commands and the
triple-`0xFF` terminator.

## Inbound event shape

Documented directly in the `NXhandler` switch comment
(`A40Nextion_HMI.ino:1579-1595`):

| Leading byte | Meaning | Payload layout |
| --- | --- | --- |
| `0x31` | Numeric field event | `PP FF <number>` (page, field, value) |
| `0x32` | Text field event | `PP FF <text>` (page, field, text) |
| `0x33` | Button event | `PP BB AA` (page, button, activity: 1=press, 0=release) |
| `0x34` | Page event | `PP` (page number) |
| `0x65` | Nextion standard touch event | `PP CC AA` (page, component ID, activity) — received but currently a no-op (`case 0x65: break;`) |
| `0x1A` | Nextion error: invalid variable name/attribute | — |
| `0x00` | Nextion error | — |

`NXhandler` (`A40Nextion_HMI.ino:1566-1623`) dispatches on `NXbuff[0]`:

- `0x31` → `NX_numfield_touched()` — **falls through** into `0x32`'s handler
  (`A40Nextion_HMI.ino:1597-1599` has no `break` after `case 0x31`). This
  means every numeric-field event currently also runs the text-field handler
  immediately after. This looks unintentional but is the current verified
  behavior — flag it explicitly in the port rather than "fixing" it silently,
  since downstream logic may depend on it.
- `0x32` → `NX_txtfield_touched()`
- `0x33` → `NX_button_pressed()`
- `0x34` → `NX_page_init()`
- `0x65`, `0x1A`, default → logged only, no state change.

## Page map (from `NX_page_init`, `A40Nextion_HMI.ino:1448-1562`, and page
constants used elsewhere)

| Page | Name/purpose | On-enter action |
| --- | --- | --- |
| 0 (`main`) | Main operating screen | Re-send digital channel config, refresh display (`DMRupdateDigChannel`, `NX_P0_DisplayCurrent`) |
| 1 | Start/splash page | Show call sign |
| 3 | Status/boot log page | Used only during `NXinitDisplay` at startup |
| 4 | Repeater/channel select list | `NX_P4_displayChannels`, paginated (`p4_*` state) |
| 5 | Talk-group select list (RX) | `NX_P5_displayTGlist`, paginated (`p5_*` state) |
| 6 | Talk-group select (TX) | `NX_P6_displayTG`, paginated (`p6_*` state) |
| 7 | Send SMS | Triggers `DMRsendSMS()` directly on page-init event |
| 8 | View received SMS | `NX_P8_viewSMS` |
| 9 | Setup: Wi-Fi SSID, volume, mic, version, channel info | Multiple `NX_P9_*` refreshers |
| 10 | RX last-heard list | `NX_P10_rxLastHeard` |
| 11 | RX talk-group monitor toggles | Populates up to `NXmaxrxTalkgroups` (32) buttons from `dmrSettings.rxTalkGroup[]`/`rxTGStatus[]` |
| 12 | TS (time-slot) usage setup | Reflects `digData.InboundSlot` and `ts_scan` into 3 buttons |
| 13 | Initial setup entry | Shown when EEPROM is uninitialized (`INITIAL_INPUT` state) |
| 14 / event `0x0E` | Repeater DMR-ID entry / EIM lookup | `NX_P14_getRepeaterDMRid`, `NX_P14_fillRepeaterlist` |
| 15 / event `0x0F` | Location-based repeater search (lat/long) | `NX_P15_*` (get input, init, fill list, save) |

Pages 2 is not referenced in `NX_page_init`; not confirmed to exist or be
unused — **Assumption**, needs confirming against the compiled HMI project in
`hmi/`.

## Button/touch payload conventions

From `NX_button_pressed` (`A40Nextion_HMI.ino:1217-1447`) and
`NX_txtfield_touched`/`NX_numfield_touched`:

- `NXbuff[1]` is consistently the page number and `NXbuff[2]` the
  component/button ID within that page — this holds across the `0x31`,
  `0x32`, and `0x33` handlers.
- Page 0 buttons: `0x0`=PTT, `0x1`=volume down, `0x2`=volume up (plus
  scroll/back buttons `0x19`/`0x20` reused across list pages 4/5/6).
- Setup pages (9, 13, 14) reuse the same component-ID ranges for similar
  controls (SSID slots, volume, mic gain) — component IDs are **not**
  globally unique across pages; every dispatch must be scoped by page number
  first, matching the nested `switch (NXbuff[1]) { switch (NXbuff[2]) }`
  pattern already in the source.

## Known fragility for the port

- `NXlisten`'s 39-byte read cap will silently truncate any inbound event
  needing more bytes (e.g. a long text-field value) — no case currently
  requires more, but this is a latent limit, not a deliberate protocol
  maximum.
- Timeouts mirror the DMR link: wait up to 500 ms for the first byte, then up
  to 10000 ms between subsequent bytes of the same frame
  (`A40Nextion_HMI.ino:1635,1652` — note this is half the DMR link's initial
  wait).
- No checksum exists on either direction; only the cumulative-`0xFF`-count
  guards frame boundaries, and per the transport note above it doesn't even
  require the three `0xFF` bytes to be consecutive. A malformed display
  response with even one or two isolated `0xFF` bytes earlier in the payload
  (e.g. inside free text, or as a numeric field's value byte) would truncate
  the frame early on the 3rd cumulative occurrence — not observed in current
  text fields (bounded to callsigns/short strings) but implemented as a
  fixture-backed test case in milestone 1
  (`dreambox_pi/domain/nextion_protocol.py`'s `read_event`/`split_terminator`
  intentionally reproduce this cumulative-count behavior rather than the
  "three consecutive" behavior an earlier draft of this doc assumed).
- `case 0x31` fallthrough into `case 0x32` (above) should be captured as an
  explicit fixture/test case so the port either preserves or deliberately
  removes it with a documented decision.
