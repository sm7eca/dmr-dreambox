# Hardware spec: Raspberry Pi 4 replacing the ESP32

Status: mixed — connector pinouts and electrical ratings marked **Verified**
come from the DMR module's own datasheet or official Raspberry Pi
specifications; everything about how those connect to a Pi 4 (voltage
compatibility, GPIO choice, driver reuse) is an **Assumption** pending a
bench check, per the safety-critical caution already recorded in
[raspberry-pi-port-plan.md](raspberry-pi-port-plan.md#hardware-mapping-to-verify).
This document elaborates that table into a specific Pi 4 wiring plan; it
does not supersede its "do not wire directly to GPIO until verified"
instruction.

## Scope

Replace the ESP32 Dev Board with a Raspberry Pi 4 (any RAM variant) as the
host controller. The DMR module, Nextion display, and beeper are unchanged
hardware — only what they plug into changes. Sourced from
[current-system.md](current-system.md)'s verified ESP32 interface table, the
hand-annotated pinout in `doc/hw/ESP32-DMR-NX-SD-connect.pdf`, and the
DMR-5WUF module datasheet (`doc/specs/DMR-5WUF-english.pdf`).

## Power distribution

| Rail | Consumer | Source |
| --- | --- | --- |
| 9–18 V DC, 12 V typical | DMR-5WUF module (`VBAT`, pins 1–2 of J1) | **Verified** — datasheet §5.1 "Electrical Characteristics" table: Power Supply min 9 V, typical 12 V, max 18 V. Matches the "12V" hand-written annotation on the existing ESP32 diagram. |
| 5 V, 3 A (official Pi 4 requirement) | Raspberry Pi 4, via USB-C | **Verified** — [Raspberry Pi 4 official power specification]; not sourced from project docs. |
| 5 V | Nextion display | **Assumption** — matches the "5V" annotation on the ESP32 diagram for the existing display; not independently re-verified for this port. |

These are three independent supplies, not one shared rail — the DMR module's
12 V requirement is well outside both the Pi 4's and the Nextion's 5 V
range. **Common ground between all three supplies is required** for the
UART signaling below to work; this is asserted here as a basic electrical
requirement, not something the port plan's open items list separately, but
it should be confirmed on the bench alongside the other grounding checks
already called for in raspberry-pi-port-plan.md.

## DMR-5WUF module connector (J1)

**Verified** from the datasheet's "Module size and pin assignment" table
(page 3) — this supersedes guessing from the ESP32 sketch alone, since the
sketch only proves which two pins (`Serial2` RX/TX) the firmware happens to
use, not the full connector:

| Pin | Name | Type | Description |
| --- | --- | --- | --- |
| 1–2 | `VBAT` | POWER | DC power, 9–18 V (see above) |
| 3–4 | `GND` | GND | |
| 5 | `UART_TX` | DO | TX from the module — wire to the host's RX |
| 6 | `UART_RX` | DI | RX to the module — wire to the host's TX |
| 7 | `HANGUP` | DI | Accept/end call; low pulse > 20 ms |
| 8 | `CALL` | DI | Initiate call; low pulse > 20 ms |
| 9–12 | `CTRL_D0`–`D3` | DIO | Reserved |
| 13 | `GND` | GND | |
| 14 | — | NC | Not connected |
| 15 | `MIC_IN` | AI | Microphone input |
| 16 | `GND` | GND | |
| 17 | `LINEOUT` | AO | Audio output |
| 18–20 | `GND` | GND | |

**Datasheet note 1 (verbatim): "when power on, CALL, HANGUP pin must be pull
high."** Neither `A20Communication.ino` nor any other firmware source file
reviewed for [dmr-protocol.md](dmr-protocol.md) ever drives GPIO pins named
CALL/HANGUP — the firmware only ever talks to the module over UART (e.g.
`SET_TRANSMIT_INFORMATION`, `0x26`, for PTT). This means the existing ESP32
board almost certainly ties CALL/HANGUP high with a passive pull-up
resistor at the module/interconnect level, not through firmware GPIO
control — **Assumption, needs a continuity check on the existing hardware**
before building a new interconnect for the Pi, since if the Pi port omits
this pull-up the module may not behave the same way it does today.

**Baud rate discrepancy, unresolved:** the datasheet's electrical table
lists "Series Baut Rate: 56700 bps" (page 4), but the shipped ESP32 firmware
opens the port at 57600 baud (`DmrCmd.begin(57600, ...)`,
`sketch_dreambox.ino:327`, already verified in current-system.md) and this
is what actually works today. 56700 is not a standard UART baud rate and is
almost certainly a typo in the vendor document (`Baut` for `Baud` in the
same table supports that reading). Treat 57600 as authoritative; flagged
here only so a future reader of the datasheet doesn't "correct" the working
config to match the typo.

**UART logic level: unverified.** The datasheet doesn't state
`UART_TX`/`UART_RX`'s logic voltage directly — the circuit diagram on page 4
shows a `VDD3V` rail feeding the microphone bias circuit, which is
suggestive of a 3.3 V logic domain (matching both the ESP32's and the Pi
4's own 3.3 V GPIO), but that is not the same as a stated UART I/O voltage.
This is exactly the "Voltage level" verification item already listed in
raspberry-pi-port-plan.md's hardware-mapping table — still open.

## Connecting the DMR module and Nextion display to a Pi 4

Per raspberry-pi-port-plan.md's existing instruction, **do not wire either
device directly to Pi 4 GPIO** until the voltage-level and grounding checks
above are done. Two options, in order of preference:

### Recommended for the prototype: two USB-to-TTL-serial adapters

**UART connections always cross over — do not pair same-named pins.** Per
the connector table above: the DMR module's `UART_TX` (pin 5, an output)
goes to the adapter's **RX**, and the module's `UART_RX` (pin 6, an input)
goes to the adapter's **TX**. The Nextion display's TX goes to the
adapter's RX and its RX to the adapter's TX, the same way.

- One adapter: its RX to the DMR module's `UART_TX` (pin 5), its TX to the
  module's `UART_RX` (pin 6), GND to GND (pins 3-4).
- A second adapter: its RX to the Nextion display's TX, its TX to the
  display's RX, GND to GND.
- Both enumerate as separate `/dev/ttyUSB*` (or stable `/dev/serial/by-id/*`)
  devices on the Pi 4 — a direct match for
  [`SerialConfig.port`](../../dreambox_pi/service/config.py) in the config
  already built for milestone 3, and for the pseudo-terminal-tested
  [`SerialTransport`](../../dreambox_pi/adapters/serial_transport.py)
  adapter.
- Isolates the Pi's 3.3 V GPIO domain from both devices entirely until their
  logic levels are confirmed — most USB-UART adapters are 3.3 V/5V
  switchable or available in a 3.3 V-only variant, so pick one that matches
  once the DMR module's actual level is measured.
- Downside: two USB ports consumed, and USB-serial adapters add their own
  (usually negligible) latency/jitter versus a hardware UART.

### Future option, gated on bench verification: native Pi 4 GPIO UARTs

The Pi 4 (unlike the Pi Zero/3, which have only one easily available extra
UART) exposes several additional hardware UARTs via GPIO alt-functions and
`dtoverlay` entries in `/boot/config.txt` (e.g. `uart2` on GPIO 0/1, `uart3`
on GPIO 4/5, `uart4` on GPIO 8/9, `uart5` on GPIO 12/13), alongside the
primary UART on GPIO 14/15. In principle this could give the DMR module and
Nextion display each their own dedicated hardware UART with no USB adapters
at all. **Do not use this until:**

1. The DMR module's UART logic level is measured and confirmed 3.3 V-safe
   (see above) — a 5 V logic signal into Pi 4 GPIO can damage it permanently,
   unlike a USB-UART adapter which isolates that risk.
2. The CALL/HANGUP pull-up question above is resolved, so the new
   interconnect (if any) preserves it.
3. `raspberry-pi-port-plan.md` is updated to record this as a deliberate
   decision, not a default — the plan currently prefers USB adapters
   specifically to avoid the risk this option reintroduces.

## Beeper (optional)

Per [beeper.py](../../dreambox_pi/adapters/beeper.py) (already built,
untested against real hardware): `GpioBeeper` takes a configurable
`chip`/`line`, deliberately not defaulting to a specific pin, since:

- The ESP32 used a fixed `GPIO 14` (`sketch_dreambox.ino:43-44`) — there is
  no requirement to reuse that BCM number on the Pi, and GPIO 14 is one of
  the pins the "native UART" option above would need, so picking a
  different, currently-unused Pi 4 GPIO (e.g. BCM 17, physical pin 11, as a
  placeholder — not yet chosen) avoids a future conflict.
- The driver circuit behind the ESP32's beeper pin (transistor-driven piezo
  or LED — not documented in any file reviewed here) needs to be inspected
  on the physical board before assuming it's safe to drive from a Pi 4 GPIO
  at the same logic level, per the same "Electrical driver, active level,
  safe default" item already listed in raspberry-pi-port-plan.md.
- `NullBeeper` (also already built) is the correct default until that check
  happens — the beeper is cosmetic, not safety-critical, so shipping without
  it is a reasonable fallback, unlike the DMR/Nextion links.

## Not needed on the Pi 4: SD card reader

The hand-annotated ESP32 diagram (`doc/hw/ESP32-DMR-NX-SD-connect.pdf`)
shows a "SD KORT LÄSARE" (SD card reader) label with a CS/SCK/MISO/MOSI
annotation that, from the diagram's own column labels, appears to align
with the board's **VSPI** pins (GPIO 5/18/19/23) rather than HSPI — but
reading exact pin alignment off a hand-drawn sketch is inherently
imprecise, so treat the specific bus as an unconfirmed detail; it doesn't
change the conclusion below. No `.ino` file reviewed for this project
(`sketch_dreambox.ino`, `A05`–`A70`) includes `SD.h` or otherwise reads from
an SD card at runtime — the only documented SD-card use anywhere in this
repository is flashing the *Nextion display's own* firmware from a microSD
card inserted into the display itself
([development.md](../development.md)'s "Prepare HW" section), which is a
manual, display-side process unrelated to the ESP32/host controller.

**Assumption:** this SD reader wiring is either vestigial, was for a
feature not present in the current firmware, or serves a purpose not
covered by the source files reviewed. Either way, the Pi 4 needs no
equivalent: it boots from and persists to its own SD card or eMMC already,
and radio settings now live in
[`settings_store.py`](../../dreambox_pi/adapters/settings_store.py)'s JSON
file on that same filesystem (milestone 3). Do not carry this wiring forward
without first confirming what it was for.

## Not applicable on the Pi 4: Wi-Fi module wiring

The ESP32's Wi-Fi is on-chip; the Pi 4 also has on-chip Wi-Fi (plus
Ethernet), so there is no equivalent *wiring* concern either way — this is
purely a Linux-networking/software question, already captured as its own
row in raspberry-pi-port-plan.md's hardware-mapping table ("ESP32 Wi-Fi/time
→ Linux networking and system clock").

## Open items before this spec can be trusted on a bench

1. DMR module `UART_TX`/`UART_RX` logic voltage — measure directly.
2. Whether CALL/HANGUP are pulled high on the existing interconnect board,
   and how (resistor value, to which rail).
3. Nextion display's actual supply voltage and UART logic level for the
   specific unit in use — the "5 V" figure here is carried over from the
   ESP32 diagram's handwriting, not independently re-measured.
4. Beeper driver circuit — transistor/LED type, active-high or active-low,
   drive current — before choosing `GpioBeeper`'s `active_high` config or
   assuming the ESP32's driver circuit can be reused unmodified.
5. Confirm 57600 baud (not the datasheet's likely-typo 56700) against the
   physical module, not just the working ESP32 firmware's configuration.

None of these are new risks — they were already implicit in
raspberry-pi-port-plan.md's "Prefer two uniquely identifiable USB-UART
adapters... do not wire directly to GPIO until measured" instruction. This
document just makes each item concrete enough to check off on a bench,
which milestone 4 (bench integration) will need to do before enabling any
of this for real.
