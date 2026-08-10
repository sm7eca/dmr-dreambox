# Current system

Status: verified from repository sources unless marked otherwise.

## Purpose

DMR Dreambox is an ESP32-based controller for a DMR radio module and a Nextion
display. It maintains radio/user settings, drives the radio state machine, and
uses Wi-Fi to retrieve external DMR information. A separate EIM service harvests
and serves DMR-related data.

## Runtime components

| Component | Location | Responsibility |
| --- | --- | --- |
| ESP32 firmware | `sketch_dreambox/` | Startup, state machine, DMR control, Nextion UI, settings, Wi-Fi, EIM calls |
| Nextion HMI | `hmi/` | Display pages, controls, and compiled TFT image |
| EIM core | `eim-service/docker/eim-core/` | HTTP API for users, repeaters, hotspots, and system data |
| EIM harvester | `eim-service/docker/eim-harvester/` | Imports external BrandMeister and RadioID data |
| MongoDB and proxy | `eim-service/docker/` | Persistence and HTTP gateway for EIM |

## ESP32 interfaces

The interface assignments are defined in `sketch_dreambox/sketch_dreambox.ino`:

| Interface | ESP32 binding | Current settings |
| --- | --- | --- |
| Debug | `Serial` | 115200 baud |
| Nextion display | `Serial1`, RX GPIO 2, TX GPIO 4 | 57600, 8N1 |
| DMR module | `Serial2`, RX GPIO 16, TX GPIO 17 | 57600, 8N1; RX buffer at least 264 bytes |
| Beeper/indicator | GPIO 14 | Digital output |

The DMR command identifiers, packet structures, checksum handling, and receive
dispatch are in `sketch_dreambox/sketch_dreambox.ino` and
`sketch_dreambox/A20Communication.ino`. Nextion commands and events are handled
in `sketch_dreambox/A40Nextion_HMI.ino`.

## State and persistence

- `UnitState` drives the main radio states such as idle, transmit, receive, SMS,
  channel change, and initial setup.
- `DmrSettingsS` in `sketch_dreambox/Settings.h` holds Wi-Fi slots, identity,
  location, channel, talk-group, and repeater data.
- `sketch_dreambox/A60PersistentSettings.ino` stores an `EepromSettings`
  container through the ESP32 EEPROM compatibility API.
- The in-memory and persisted structures are tightly coupled. Their binary layout
  must not be assumed portable to a Raspberry Pi.

## Network boundary

The firmware uses ESP32 `WiFiMulti`, `HTTPClient`, and `ArduinoJson`. EIM calls
are concentrated in `sketch_dreambox/A70EIMintegration.ino`; user lookup and time
setup are in `sketch_dreambox/A50WIFI.ino`.

The EIM service is separately deployable through Docker Compose and Ansible.
Existing ADRs document active-record filtering and paginated API responses for a
memory-constrained embedded client.

## Build and test boundary

- `make esp-binary` compiles the ESP32 firmware with Arduino CLI.
- `make unit-test` runs Python unit tests for EIM core and harvester.
- `make function-test` starts the local EIM stack and runs functional tests.
- Hardware behavior, UART timing, and the Nextion interaction currently require
  bench validation; the repository has no automated hardware-in-the-loop suite.

## Known risks and assumptions

- **Verified:** protocol, UI, networking, and persistence concerns share global
  state across the Arduino sketch files, which increases porting risk.
- **Verified:** external service URLs in the firmware use plain HTTP in several
  paths. Security and endpoint ownership need review before a new deployment.
- **Assumption:** the Nextion display and DMR module can be retained unchanged in
  the first Raspberry Pi prototype.
- **Assumption:** their electrical UART levels are safe for the chosen Raspberry
  Pi interface. Confirm voltage, grounding, and isolation before connecting them.
- **Assumption:** 57600 baud and current timeout behavior remain valid when UART
  access moves to Linux userspace.
