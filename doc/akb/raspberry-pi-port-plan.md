# Raspberry Pi port plan

Status: proposed. Each milestone requires its exit criteria before the next one.

## Goal

Run the DMR Dreambox controller on a Raspberry Pi while initially retaining the
DMR radio module, Nextion display, EIM API, and observable user behavior. The port
should improve testability and operations without changing radio behavior as a
side effect.

## Non-goals for the first release

- Replacing the DMR module or Nextion HMI.
- Redesigning the EIM API or database.
- Changing DMR packet formats or talk-group behavior.
- Importing the ESP32 EEPROM image directly.
- Adding remote transmit control before access control and safety behavior are
  explicitly designed.

## Target boundaries

Use a small Linux service with platform-independent application logic and narrow
adapters:

```text
Nextion UART ─┐
              ├─ I/O adapters ─ application/state machine ─ settings store
DMR UART ─────┘                         │
                                       └─ EIM HTTP client
```

Recommended initial layout:

```text
dreambox_pi/
  domain/          # states, commands, settings models; no GPIO or serial calls
  application/     # startup and state-machine orchestration
  adapters/        # DMR UART, Nextion UART, EIM HTTP, settings, GPIO
  service/         # configuration, lifecycle, logging, systemd integration
tests/
  fixtures/        # sanitized UART and HTTP captures
  dreambox_pi/     # unit, contract, and replay tests
```

Record the language/runtime choice in an ADR before implementation. Python 3 with
`pyserial` is a practical first option because the repository already uses Python
and UART throughput is low, but the protocol fixtures and boundaries must remain
runtime-neutral.

## Hardware mapping to verify

| Existing function | Raspberry Pi candidate | Verification required |
| --- | --- | --- |
| Nextion `Serial1` | Dedicated USB-UART or `/dev/serial0` | Voltage level, device identity, boot-console conflict, 57600 8N1 |
| DMR `Serial2` | Separate USB-UART | Voltage level, flow control, 264+ byte bursts, reconnect behavior |
| Debug `Serial` | Structured logs/journald | Log redaction and useful protocol trace levels |
| GPIO 14 beeper | Configurable `libgpiod` output or disabled adapter | Electrical driver, active level, safe default |
| ESP32 EEPROM | Versioned JSON or SQLite file | Atomic write, permissions, migration, backup, corruption recovery |
| ESP32 Wi-Fi/time | Linux networking and system clock | Offline startup and network-change behavior |

Prefer two uniquely identifiable USB-UART adapters for the prototype. Do not wire
the radio or display directly to Raspberry Pi GPIO until electrical levels and
grounding have been measured and documented.

## Milestones

### 0. Freeze observable contracts

1. Inventory DMR commands, replies, unsolicited events, lengths, checksum rules,
   and timeouts from `A20Communication.ino`.
2. Inventory Nextion commands and events from `A40Nextion_HMI.ino`.
3. Capture sanitized startup, idle, RX, TX, channel-change, and error sessions.
4. Snapshot EIM request/response examples without personal data or credentials.

Exit criteria: reviewed protocol notes and replay fixtures reproduce all named
flows without hardware.

### 1. Build a host-side protocol harness

Implement pure DMR packet encode/decode and Nextion framing with fixture-based
tests. Add fake serial transports supporting partial reads, timeouts, malformed
frames, disconnects, and reconnects.

Exit criteria: all captured frames round-trip or decode as expected; malformed
input fails safely and never triggers transmit.

### 2. Extract application state

Model startup, idle, RX, TX, SMS, and channel changes without Linux or hardware
calls. Keep side effects behind interfaces and drive them with deterministic
events and a controllable clock.

Exit criteria: state-transition tests cover normal and failure paths, including
PTT release, UART loss, EIM timeout, and restart during an active operation.

### 3. Add Linux adapters

Add serial device discovery/configuration, settings persistence, EIM HTTP access,
structured logging, and optional GPIO. Device paths, baud rates, endpoints, and
timeouts must be configuration—not source constants.

Exit criteria: the service runs unprivileged where practical, restarts cleanly,
uses atomic settings writes, and passes adapter tests with pseudo-terminals.

### 4. Bench integration

Connect one peripheral at a time through verified electrical interfaces. Start
with receive-only DMR operations; enable transmit only after framing, timeout,
and safe-state behavior are observed.

Exit criteria: a documented bench checklist passes startup, display navigation,
channel selection, RX, controlled TX/PTT release, network loss, peripheral loss,
and power-cycle recovery.

### 5. Parallel field trial

Run the Raspberry Pi controller alongside a known-good ESP32 unit using the same
configuration and a controlled test matrix. Compare user-visible behavior and
protocol traces.

Exit criteria: no unresolved safety or compatibility differences; settings
backup/restore and rollback have been exercised.

### 6. Package and operate

Provide a systemd unit, example configuration, dependency lock, installation and
upgrade instructions, health checks, log rotation, and a release artifact.

Exit criteria: a clean Raspberry Pi OS installation can be provisioned and
rolled back using only the documented procedure.

## Safety gates

- Default to receive-only after startup, configuration errors, UART reconnect,
  or process restart.
- A lost UI or DMR connection must release PTT and return to a safe state.
- Never log Wi-Fi credentials or unredacted personal identifiers.
- Bind any management endpoint to localhost until authentication and authorization
  are explicitly designed.
- Require a manual bench check before changes affecting TX, PTT, power, frequency,
  colour code, time slot, or contact type are field-tested.

## Migration and rollback

Export settings into a documented, versioned schema rather than copying the
ESP32 EEPROM image. Keep the ESP32 firmware and its last working settings intact
during the trial. Hardware cabling should be reversible, and every Raspberry Pi
release should identify the compatible protocol-fixture and settings-schema
versions.

## First implementation slice

The first PR after this plan should contain only:

1. the DMR framing/checksum library;
2. sanitized fixtures for a query and response;
3. unit tests for valid, partial, malformed, and timeout cases;
4. no GPIO, EIM, UI rewrite, or transmit orchestration.

This slice validates the highest-risk reusable boundary before committing to the
full runtime.
