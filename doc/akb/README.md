# Agent Knowledge Base

This directory is the compact, repository-owned knowledge base for developers
and coding agents working on DMR Dreambox. It complements the user-facing
documentation and ADRs; it does not replace source code or bench measurements.

## Start here

- [Current system](current-system.md) — components, responsibilities, interfaces,
  constraints, and known risks derived from the repository.
- [Raspberry Pi port plan](raspberry-pi-port-plan.md) — target boundaries,
  milestones, validation gates, and rollback strategy.
- [DMR module protocol](dmr-protocol.md) — command table, checksum, framing,
  timeouts (milestone 0, item 1).
- [Nextion HMI protocol](nextion-protocol.md) — outbound commands, inbound
  event codes, page map (milestone 0, item 2).
- [Session capture status](session-capture-status.md) — bench capture
  blockers and source-derived flow predictions (milestone 0, item 3).
- [EIM request/response examples](eim-examples.md) — sanitized API shapes and
  firmware/service contract drift (milestone 0, item 4).
- [Raspberry Pi 4 hardware spec](hardware-raspberry-pi.md) — power
  distribution, DMR module connector pinout, and UART wiring options for
  replacing the ESP32 with a Pi 4; elaborates the port plan's
  hardware-mapping table with datasheet-sourced detail.
- [Architecture decisions](../adr/) — decisions that are already recorded.
- [Development workflow](../development.md) — build, test, and release workflow.

## Evidence levels

Every durable statement should be one of:

- **Verified** — supported by a source path, test, protocol capture, or bench test.
- **Assumption** — plausible but awaiting verification.
- **Decision** — accepted in an ADR or an explicitly approved plan.

Prefer links to repository paths over copied implementation details. When code
and this knowledge base disagree, verify the behavior and update the stale side
in the same change.

## Maintenance contract

Update the AKB when a change affects:

- component ownership or runtime boundaries;
- DMR, Nextion, EIM, or persistence contracts;
- supported boards and hardware connections;
- build, test, deployment, or recovery procedures;
- an assumption or risk listed in the port plan.

Keep documents short enough to review with code. Put consequential decisions in
`doc/adr/` and link them from the relevant AKB page.
