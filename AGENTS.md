# DMR Dreambox agent guide

This repository contains three related systems:

- ESP32/Arduino controller firmware in `sketch_dreambox/`
- Nextion display sources and binaries in `hmi/`
- Python/Docker EIM services in `eim-service/`

Read `doc/akb/README.md` before making architectural changes. The current system
map is in `doc/akb/current-system.md`; the proposed Raspberry Pi migration is in
`doc/akb/raspberry-pi-port-plan.md`.

## Working rules

- Preserve the DMR and Nextion UART wire protocols unless a change is explicitly
  documented and tested against real hardware.
- Keep radio control, UI, persistence, networking, and hardware I/O separated in
  new code. Do not introduce new platform calls into domain logic.
- Treat the persisted `DmrSettingsS` layout as a compatibility boundary. Any
  format change needs an explicit migration and rollback plan.
- Keep credentials, Wi-Fi passwords, callsigns, DMR IDs, and production endpoints
  out of fixtures, logs, commits, and pull-request descriptions.
- Add or update an ADR under `doc/adr/` when a decision changes a protocol,
  persistence format, deployment model, or supported hardware.
- Mark uncertain hardware or protocol details as assumptions. Do not turn them
  into facts without a code reference, protocol capture, or bench test.

## Validation

Run the narrowest relevant checks first:

```sh
make unit-test
make function-test
make esp-binary
```

The Docker-backed function tests and ESP32 build require their documented local
dependencies. Documentation-only changes should at minimum be checked for valid
links, paths, and consistency with the source tree.

## Raspberry Pi work

Follow the milestones and exit criteria in
`doc/akb/raspberry-pi-port-plan.md`. The first implementation milestone is a
host-side protocol harness with recorded, sanitized fixtures; it is not a direct
rewrite of the Arduino sketch.
