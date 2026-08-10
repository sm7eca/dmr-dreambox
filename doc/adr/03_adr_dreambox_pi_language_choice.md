
# Issue

- [raspberry-pi-port-plan.md](../akb/raspberry-pi-port-plan.md) requires the
  language/runtime choice for the new `dreambox_pi` host-side controller to
  be recorded here before milestone 1 (protocol harness) implementation
  starts.
- The plan already suggests Python 3 with `pyserial` as "a practical first
  option because the repository already uses Python and UART throughput is
  low", conditional on the protocol fixtures and boundaries staying
  runtime-neutral.
- `requirements.pip.txt` already lists `pyserial` (currently used for
  `esptool.py erase_flash` in the ESP32 workflow), and `requirements-test.txt`
  already lists `pytest`/`pytest-mock` from the EIM service tooling. No new
  dependency category is needed to start.

# Decision

- `dreambox_pi/` is implemented in Python 3 (matching the EIM service's
  existing 3.x baseline).
- `dreambox_pi/domain/` (packet encode/decode, framing, state machine) has
  **zero** dependency on `pyserial` or any I/O library — pure functions over
  `bytes`/dataclasses, so it can be unit-tested without a serial port and
  ported to a different runtime later without touching protocol logic.
- `dreambox_pi/adapters/` is where `pyserial` (or a fake transport for tests)
  is introduced. The adapter boundary is a small duck-typed interface
  (`read(size) -> bytes`, `write(data) -> int`, `in_waiting` property) that
  both `serial.Serial` and the milestone-1 fake transport satisfy, so
  swapping one for the other requires no domain code changes.
- Protocol fixtures (`tests/fixtures/sessions/*.json`) stay plain JSON with
  hex-string byte payloads — no Python-specific types — so they remain usable
  even if a later milestone changes the implementation language.
- Test runner is `pytest`, consistent with the existing EIM service tests
  (`eim-service/docker/eim-core/src`, `eim-service/docker/eim-harvester/src`);
  `dreambox_pi` tests live under `tests/dreambox_pi/` per the layout in
  raspberry-pi-port-plan.md.

# Consequences

- No new tooling to install for milestone 1; `make unit-test` gains one more
  `pytest` invocation over `tests/dreambox_pi`.
- The domain/adapter split means milestone 1 (protocol harness) and
  milestone 3 (Linux adapters: real serial devices, settings persistence,
  EIM HTTP) can be built and tested independently, matching the plan's
  target boundaries diagram.
- If a future milestone needs different performance characteristics (e.g.
  hard real-time UART handling), only `dreambox_pi/adapters/` and the
  application-level event loop should need to change — the protocol codecs
  in `domain/` are not tied to Python's I/O model.
