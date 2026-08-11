
# Issue

- [raspberry-pi-port-plan.md](../akb/raspberry-pi-port-plan.md) milestone 3
  ("Add Linux adapters") is done: `dreambox_pi/adapters/serial_transport.py`
  (real pyserial transport), `settings_store.py`, `eim_client.py`, and
  `beeper.py` all exist and pass their adapter tests. Milestone 2's
  `StateMachine` (`dreambox_pi/application/state_machine.py`) is transport-
  agnostic by design: it takes explicit events and a clock value, and returns
  a list of `Effect` objects, never performing I/O itself.
- What is still undecided is how a real service composes these pieces: who
  calls `dmr_protocol.read_frame()` on the DMR UART, who calls
  `nextion_protocol.read_event()` on the Nextion UART, who calls
  `EimClient.lookup_user()`, and how their results reach the single
  `StateMachine` instance. No `dreambox_pi/service` main loop exists yet.
- The duck-typed transport interface (`read(size)`, `write(data)`,
  `in_waiting`, `wait_for_data(timeout)`) was carried over unchanged from the
  milestone-1 fake transport, which was itself a deterministic stand-in for
  the ESP32 firmware's `available()`-polling loops in `DMRreceive` and
  `NXlisten` (`A20Communication.ino`, `A40Nextion_HMI.ino`). Two consequences
  of that carry-over need an explicit decision now, before a main loop is
  built on top of them:
  1. `SerialTransport.wait_for_data()` (`serial_transport.py:45-53`) is a
     busy-poll: it checks `in_waiting` and sleeps 5 ms in a loop, up to the
     caller's timeout. On the ESP32 that is the only option; on Linux it
     wakes the process ~200 times/second per open port for the entire
     duration of any wait (DMR: up to 1 s first-byte / 10 s inter-byte;
     Nextion: up to 0.5 s / 10 s), instead of blocking in the kernel until
     data actually arrives.
  2. `read_frame()` / `read_event()` / `EimClient.lookup_user()` each block
     their calling thread for up to their own timeout. If a single loop
     calls them one after another ("service DMR, then service Nextion, then
     check EIM"), a slow or silent DMR module can stall Nextion touchscreen
     handling for over a second, and a slow EIM server can stall both UARTs
     for up to 5 s. The ESP32 main loop never had this problem because its
     `available()` checks are non-blocking; porting the blocking-wait
     primitives without also deciding how they run concurrently would be a
     behavioral regression, not just a style mismatch.

# Decision

- Each blocking I/O source gets its own OS thread:
  - one reader thread per UART (DMR, Nextion), each running a tight loop of
    `read_frame()` / `read_event()` against its own transport and pushing
    decoded frames/events onto a single thread-safe `queue.Queue`;
  - EIM lookups (`RequestCallerLookup` effects) are dispatched to a small
    worker thread (or single-slot thread pool), not run on a UART reader
    thread or the main thread, and post their result back onto the same
    queue.
  - GPIO (`BeeperPort.set()`) stays synchronous and is called directly from
    the main thread — it is a non-blocking local call, not an I/O wait.
- A single main thread owns the one `StateMachine` instance: it blocks on
  `queue.get()`, translates each queued item into the matching
  `StateMachine.on_*()` call, and executes the returned `Effect`s (UART
  writes, GPIO, or enqueuing a new EIM lookup) synchronously before going
  back to `queue.get()`. `StateMachine` itself is never called from more than
  one thread, so it keeps needing no locking.
- Threads over `asyncio`: the codebase and [ADR 03](03_adr_dreambox_pi_language_choice.md)
  are built on `pyserial`, a blocking API; adopting `asyncio` here would mean
  either a second async serial dependency (`pyserial-asyncio`) or wrapping
  every blocking call in an executor, for a service with a handful of
  low-throughput I/O sources. A thread per source plus one queue is simpler
  to reason about and debug for this shape of workload, and keeps the
  domain/application layers, which know nothing about threads or asyncio,
  unchanged.
- `SerialTransport.wait_for_data()` stops busy-polling and blocks instead,
  using `select.select([self._serial.fileno()], [], [], timeout)` to sleep in
  the kernel until data is available or the timeout elapses. This is an
  internal change to the real adapter only: the duck-typed transport
  interface (`read`, `write`, `in_waiting`, `wait_for_data`) is unchanged, so
  `domain/_framing.py`, `dmr_protocol.read_frame()`,
  `nextion_protocol.read_event()`, and every existing test against
  `FakeSerialTransport` are unaffected.
- `_framing.read_until()` keeps reading one byte at a time. This is not a
  concurrency concern (each UART already has its own thread), and changing
  it would touch the frame-boundary logic that is already tested against
  captured fixtures; it is left as a possible follow-up, not part of this
  decision.
- Each reader thread must catch and log transport failures (UART unplugged,
  read error) rather than let the thread die silently, and must push a
  distinguishable "transport lost" event onto the queue so the main thread
  can drive the `StateMachine` to a safe receive-only state, per the port
  plan's safety gate ("A lost UI or DMR connection must release PTT and
  return to a safe state").

# Consequences

- A new `dreambox_pi/service/runtime.py` (or similar) module is needed to
  own the queue, the three worker threads, and the main dispatch loop; this
  is the first piece of code that assembles adapters, the state machine, and
  effect execution together, and is a natural place for the milestone-6
  systemd entry point to call into.
- `SerialTransport` needs a `select`-based `wait_for_data()` plus tests
  (e.g. over a `socket.socketpair()` or `pty`) proving it unblocks promptly
  on data arrival and honors its timeout; the fake transport used by
  existing domain/state-machine tests does not need to change.
- Because UART reads and EIM lookups now run off the main thread, thread
  shutdown/join order needs to be defined (e.g. a stop `Event` each reader
  thread checks around its blocking call) so the service can exit cleanly
  during milestone 4 bench testing and milestone 6 systemd stop/restart —
  this should be covered when `runtime.py` is built, not deferred silently.
- No change to `dreambox_pi/domain/` or `dreambox_pi/application/
  state_machine.py`: both stay free of threading concerns, matching ADR 03's
  reasoning that only the adapter/service layers should need to change for a
  different I/O or performance model.
