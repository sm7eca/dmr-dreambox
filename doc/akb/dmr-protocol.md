# DMR module protocol (source inventory)

Status: **Verified** from `sketch_dreambox/A20Communication.ino`,
`sketch_dreambox/sketch_dreambox.ino`, `sketch_dreambox/A05Init.ino`, and
`sketch_dreambox/A30Main_State_Handling.ino` unless marked otherwise. This is
milestone 0, item 1 of the [Raspberry Pi port plan](raspberry-pi-port-plan.md):
a protocol inventory derived from source, not yet from a bench capture.

## Transport

- UART, `Serial2` on the ESP32 (`sketch_dreambox.ino:64-65`, `RXD2=16`, `TXD2=17`),
  57600 baud, 8N1, RX buffer sized to at least 264 bytes
  (`sketch_dreambox.ino:327-328`).
- All commands, replies, and unsolicited events share one framing rule: a
  leading `0x68` header byte and a trailing `0x10` byte. There is no other
  in-band escaping; a `0x10` inside payload data is possible in principle but
  not observed in the commands below (**Assumption** — not verified against a
  bus capture).
- `buff[256]` (`sketch_dreambox.ino:71`) is the single shared send/receive
  buffer for the whole DMR link. Only one request/reply exchange can be in
  flight at a time.

## Packet layout

Every packet observed follows the same header shape (byte offsets):

| Offset | Field | Notes |
| --- | --- | --- |
| 0 | `head` | Always `0x68` |
| 1 | `CMD` | Command ID, see table below |
| 2 | `RW` | Operation type (1 in all observed sends) |
| 3 | `SR` | Set/response flag; `0x00` on a successful reply (`DMRreceive`, `A20Communication.ino:180-182`) |
| 4–5 | `CKSUM` | Big-endian 16-bit checksum, computed and inserted by `PcCheckSum` (`A20Communication.ino:2-27`) |
| 6 | `LEN_dummy` | Always `0` |
| 7 | `LEN` | Data length: total packet length minus 9 |
| 8… | payload | Command-specific |
| last | `tail` | Always `0x10` |

Three concrete payload layouts are defined as C structs and reused for both
send and (implicitly) receive framing:

- `db_digital_info` (`sketch_dreambox.ino:180-207`) — digital channel set,
  command `0x22`. Fixed fields: `rx_freq`, `tx_freq`, `localID`,
  `GroupList[32]` (monitored talk groups), `tx_contact`, `ContactType`,
  `power`, `cc` (color code), `InboundSlot`/`OutboundSlot` (time slot − 1),
  `ChannelMode`, `EncryptSw` (always disabled = `2`), `EncryptKey[8]` (always
  zero), `pwrsave`, `volume`, `mic`, `relay`.
- `db_analog_info` (`sketch_dreambox.ino:211-234`) — analog channel set,
  command `0x23`. Fields: `rx_freq`, `tx_freq`, `band`, `power`, `sq`
  (squelch), `rx_type`/`rx_subcode`, `tx_type`/`tx_subcode` (CTCSS/DCS
  selection), `pwrsave`, `volume`, `monitor`, `relay`.
- `db_SMSsend_info` / `db_SMSget_info` (`sketch_dreambox.ino:239-268`) — SMS
  send/receive. Message text is UCS-2 (2 bytes per character), and the
  contact/call number field is **3 bytes**, not 4 — a documented gotcha
  (`A20Communication.ino:459` comment: "callnum är 3 byte!! took a hell of a
  time to find out").

## Checksum algorithm

`PcCheckSum` (`A20Communication.ino:2-27`):

1. Sum the buffer as big-endian 16-bit words (`(*buf<<8 | *(buf+1))`), for
   `len` bytes; if `len` is odd, add the final byte shifted left 8.
2. Fold carries: `while (sum>>16) sum = (sum & 0xFFFF) + (sum>>16)`.
3. Checksum = `(uint16_t)sum XOR 0xFFFF`.
4. Written back into the buffer at offset 4 (high byte) and 5 (low byte) —
   i.e. the checksum field itself is zeroed conceptually before the sum, since
   `CheckCkSum` clears bytes 4–5 before recomputing.

`CheckCkSum` (`A20Communication.ino:29-53`) verifies an inbound frame by
saving the received checksum bytes, zeroing them, recomputing, and comparing.
Note this verification function exists but `DMRreceive`/`DMRreceiveReply` do
not currently call it — only the `0x10` tail byte and (for `DMRTransmit`
replies) `buff[3]==0` are checked. Checksum verification on receive is
**not** part of the current runtime behavior, even though the algorithm
itself is implemented. A Raspberry Pi port must decide explicitly whether to
add strict inbound checksum verification (recommended) or preserve the
lenient legacy behavior.

## Command table

Defined in `sketch_dreambox.ino:11-32`:

| Command | Value | Direction | Purpose |
| --- | --- | --- | --- |
| `SET_DIGITAL_CHANNEL` | `0x22` | Host → module | Configure digital channel (see `db_digital_info`) |
| `SET_ANALOG_CHANNEL` | `0x23` | Host → module | Configure analog channel (see `db_analog_info`) |
| `GET_DIGITAL_CHANNEL` | `0x24` | Host → module | Read back digital channel config; used only to verify after set (`A05Init.ino:25`) |
| `GET_ANALOG_CHANNEL` | `0x25` | Host → module | Read back analog channel config (defined, not called elsewhere in current sketch) |
| `SET_TRANSMIT_INFORMATION` | `0x26` | Host → module | PTT control: `FUNC_ENABLE` on PTT down, `FUNC_DISABLE` on PTT up (`A30Main_State_Handling.ino:14,45`) |
| `QUERY_INIT_FINISHED` | `0x27` | Host → module | Startup poll: retried every 1 s until the module answers (`A05Init.ino:17-20`) |
| `SET_ENHANCED_FUNCTION` | `0x28` | Host → module | Defined, not called in current sketch |
| `SET_ENCHRYPTION_FUNKTION` | `0x29` | Host → module | Defined, not called (encryption is always disabled via `EncryptSw=2` in channel structs) |
| `SET_MIC_GAIN` | `0x2A` | Host → module | `DMRsetMicVolume` (`A20Communication.ino:606-609`) |
| `QUERY_DIGITAL_VOICE_INFO` | `0x2B` | Host → module | Poll for current RX contact/group/timeslot during a call (`DMRqueryReceived`, `A20Communication.ino:648-686`) |
| `SEND_SMS` | `0x2C` | Host → module | `DMRsendSMS` (`A20Communication.ino:454-527`) |
| `GET_SMS` | `0x2D` | Both | Ambiguous in this codebase: used both as a "send variant" (`DMRsendSMS_2D`, poorly understood per source comment) **and** as the unsolicited "SMS received" event code checked in `DMRhandler`/`DMRlisten`. Treat `0x2D` as the SMS-received event for port purposes; the send-side use is marked with a code comment admitting it's not understood ("don´t know how to use this command") — **Assumption**, needs bench verification before reuse. |
| `SET_VOLUME` | `0x2E` | Host → module | `DMRsetaudioVolume` (`A20Communication.ino:599-604`) |
| `SET_MONITOR` | `0x2F` | Host → module | Defined, not called in current sketch |
| `SET_SQUELCH` | `0x30` | Host → module | Defined, not called in current sketch |
| `SET_POWER_MODE` | `0x31` | Host → module | Defined, not called in current sketch |
| `QUERY_SIGNAL_STRENGTH` | `0x32` | Host → module | `DMRcheckRSSI` (`A20Communication.ino:611-621`); response byte 8 is RSSI, `0` = no signal |
| `SET_RELAY_DISCONNECT_NET_MODE` | `0x33` | Host → module | Defined, not called in current sketch |
| `QUERY_VERSION` | `0x34` | Host → module | `DMRgetVersion` (`A20Communication.ino:697-704`) |
| — | `0x3D` | Module → host (unsolicited) | Voice-call event: payload byte 8 `== 0` is call start, `== 1` is call end (`DMRhandler`, `A20Communication.ino:59-75`) |

`FUNC_ENABLE` = `0x01`, `FUNC_DISABLE` = `0x02` (`sketch_dreambox.ino:31-32`) —
used as the "mode" byte for simple enable/disable commands via the generic
`DMRTransmit(mode, CMD)` helper.

## Unsolicited events

The module can push two message types at any time, independent of the last
command sent:

- **`0x3D` voice call event** — byte 8 `0x00` = call start, `0x01` = call end.
  On start: `UnitState = REC_DMR_STATE`, an RSSI query is issued, and the RSSI
  timer is armed. On end: display is cleared, RSSI reset to 0, and state
  returns to idle if it was `REC_DMR_STATE` (`DMRvoicemessageStart`/`End`,
  `A20Communication.ino:87-121`).
- **`0x2D` SMS received event** — `DMRcheckSMSRec` extracts the sender's
  3-byte contact ID from bytes 9–11 and the UCS-2 message text starting at
  byte 15, taking only odd-indexed bytes (low bytes of each UCS-2 code unit)
  — i.e. this implementation assumes ASCII-range characters and drops the
  high byte (`A20Communication.ino:623-647`). Non-Latin text would be
  corrupted; **Assumption** this is acceptable for the current user base.

Both event types can also arrive interleaved with an expected reply: if a
`DMRTransmit` reply doesn't match the command just sent, `DMRreceiveReply`
checks for `0x3D`/`0x2D` as an unsolicited message, sets a flag
(`bRecVoicemessageStart`/`End`, `bSMSmessageReceived` — declared but not
consumed elsewhere in the current sketch, **dead flags**), then tries to read
one more message before giving up (`A20Communication.ino:221-258`). A port
must model this as: every read from the DMR UART can yield either the
expected reply or an out-of-band event, and the reply for a sent command may
arrive after up to one unrelated event.

## Timeouts

All from `DMRreceive` (`A20Communication.ino:163-219`):

- Wait up to **1000 ms** for the first byte of a reply to arrive.
- Once a message has started, wait up to **10000 ms** between bytes (comment
  says "5s" but the code uses 10000; treat the code as authoritative) before
  giving up on the rest of the frame.
- A frame is complete when a `0x10` byte is read; success (`rcode=true`) only
  if `buff[3]==0` (the `SR` field) at that point.
- `DMRlisten` (`A20Communication.ino:285-306`) also self-throttles: it will
  not attempt a new receive within 1 ms of the last one (guards against a
  tight polling loop, not a protocol timeout).

No retry/backoff exists beyond the "try one more message" logic above.
`DMRTransmit` returns whatever `DMRreceiveReply` returns; callers largely
ignore the boolean (exception: `QUERY_INIT_FINISHED` at startup, which loops
with a 1 s delay until true).

## Send path

`DMRsendTo` (`A20Communication.ino:122-161`) writes `buff[0..len)` byte by
byte to `DmrCmd` and stops early if it encounters `0x10` before `len` bytes
— i.e. it trusts the caller to have placed the tail byte at the correct
length and does not necessarily send a short buffer's unused trailing bytes.
This is only compiled when `INC_DMR_CALLS` is defined (it always is, in
`sketch_dreambox.ino:7`).

## State-machine touchpoints

From `A30Main_State_Handling.ino` and `A05Init.ino`:

- **Startup**: poll `QUERY_INIT_FINISHED` until true → `DMRinitChannel` (sends
  `SET_DIGITAL_CHANNEL`) → `GET_DIGITAL_CHANNEL` to verify → idle.
- **Idle**: if talk-group scanning (`ts_scan`) is enabled, every
  `tsSwitchInterval` (2000 ms) the code flips `InboundSlot`/`OutboundSlot`
  between 0 and 1 and re-sends the full digital channel config
  (`DMRupdateDigChannel`) — i.e. time-slot scanning is implemented as a full
  channel re-set every 2 s, not a lightweight mode switch.
- **PTT down** → `SET_TRANSMIT_INFORMATION` with `FUNC_ENABLE`; **PTT up** →
  same command with `FUNC_DISABLE`.
- **Receiving** (`REC_DMR_STATE`): every 5000 ms, `DMRcheckRSSI` re-polls
  signal strength; RSSI `0` is treated as "lost the call" and forces a return
  to idle even without an explicit `0x3D` end event.

## Open items for the port (not yet verified)

- Whether `CheckCkSum` should be enforced on receive (currently unused).
- Exact byte-for-byte behavior of `0x2D` as a *send* command — source comment
  admits it isn't understood.
- Behavior when a `0x10` byte legitimately appears inside a payload (framing
  ambiguity) — no case found in current commands, but not proven absent for
  all DMR module firmware revisions.
- Real bench captures for milestone 0 item 3 (see
  [session-capture-status.md](session-capture-status.md)) are required to
  confirm all of the above against actual hardware before the protocol
  harness (milestone 1) is considered validated.
