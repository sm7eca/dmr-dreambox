"""Service runtime: assembles the DMR/Nextion UART adapters, the EIM HTTP
adapter, and the pure StateMachine (milestone 2) into a running service.

Threading model, per doc/adr/04_adr_dreambox_pi_io_concurrency_model.md: one
reader thread per UART blocks on dmr_protocol.read_frame() /
nextion_protocol.read_event() and pushes decoded frames onto a single
queue.Queue; a small EIM worker thread does the same for RequestCallerLookup
effects. A single main thread (run()/run_once()) owns the one StateMachine
instance, draining the queue and calling the matching StateMachine.on_*()
method, then executing the returned Effects -- so StateMachine is never
touched from more than one thread and needs no locking.

Solicited-reply correlation (which on_*() call a DMR frame answers) is
inferred from a FIFO of "commands sent that expect one specific reply":
_execute_one() pushes onto it whenever it sends a SendDmrCommand/SendSms
effect that the state machine cares about the reply to, and
_route_dmr_frame() pops from it for any received frame that isn't a
recognized unsolicited event. This assumes the DMR module replies in the
same order commands were sent -- inherent to how a single half-duplex UART
works, not a new byte-level protocol fact -- but the *sequencing policy*
itself (a FIFO of expected replies, unsolicited events always checked first
via dmr_protocol.decode_unsolicited_event()) is new to this port: the ESP32
firmware never had to choose, because DMRreceiveReply blocks the whole
program between sending a command and reading its one reply, so at most one
reply is ever "in flight" at a time. Treat this as a documented assumption
pending a bench check (milestone 4), not verified fact, same as the other
open items in doc/akb/dmr-protocol.md.

Nextion touch events are parsed and logged but not yet routed into the state
machine: mapping a page/button event to a specific StateMachine.on_*() call
requires reconstructing the NX_P*/button dispatch table from
A40Nextion_HMI.ino, which effects.py's UpdateNextionDisplay docstring
already flags as out of scope for the milestones done so far. Wiring that up
is a separate piece of work, not a threading concern.

No reconnect: a reader thread that hits an OSError reports _TransportLost
and exits for good (see _dmr_reader_loop/_nextion_reader_loop) -- the state
machine reaches LINK_LOST via on_dmr_link_lost() and stays there, since
nothing in this module ever calls StateMachine.on_dmr_link_restored().
Deciding how/when a dropped UART should be reopened and retried (device
rediscovery, backoff, re-arming the reader thread) is bench-integration
(milestone 4) territory, not a threading-model decision -- today, recovering
from a lost link requires restarting the process.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, List, Optional, Protocol

from dreambox_pi.application import effects as fx
from dreambox_pi.application.state_machine import CallerInfo, StateMachine
from dreambox_pi.domain import dmr_protocol as dmr
from dreambox_pi.domain import nextion_protocol as nx
from dreambox_pi.service.config import AppConfig

logger = logging.getLogger(__name__)

TICK_INTERVAL = 0.5  # seconds; how often tick() runs when the queue is idle


class NextionRenderer(Protocol):
    def render(self, kind: str, data: dict) -> None: ...


class NullNextionRenderer:
    """Default renderer: logs and drops. UpdateNextionDisplay's `kind`
    values are not yet mapped to real nextion_protocol.build_command() calls
    (see application/effects.py) -- this is the safe default until that
    mapping exists, mirroring adapters/beeper.py's NullBeeper."""

    def render(self, kind: str, data: dict) -> None:
        logger.debug("nextion display update (not yet wired): %s %r", kind, data)


@dataclass(frozen=True)
class _DmrFrame:
    raw: bytes


@dataclass(frozen=True)
class _NextionFrame:
    raw: bytes


@dataclass(frozen=True)
class _EimResult:
    dmr_id: int
    caller: Optional[CallerInfo]


@dataclass(frozen=True)
class _TransportLost:
    source: str


_QueueItem = object  # duck-typed union of the four dataclasses above


class Runtime:
    """Owns the reader/worker threads and the single-threaded dispatch loop.

    `dmr_transport`/`nextion_transport` need the duck-typed transport
    interface (see adapters/fake_serial.py); `eim_client` needs
    EimClient.lookup_user(); `nextion_renderer` defaults to
    NullNextionRenderer. Construct with real adapters for a running service,
    or fakes for tests -- the dispatch/routing logic itself has no platform
    dependency, only start()/stop() touch threads.
    """

    def __init__(
        self,
        config: AppConfig,
        dmr_transport,
        nextion_transport,
        eim_client,
        state_machine: StateMachine,
        nextion_renderer: Optional[NextionRenderer] = None,
        clock=time.monotonic,
    ):
        self._config = config
        self._dmr_transport = dmr_transport
        self._nextion_transport = nextion_transport
        self._eim_client = eim_client
        self._state_machine = state_machine
        self._nextion_renderer = nextion_renderer or NullNextionRenderer()
        self._clock = clock

        self._queue: "queue.Queue[_QueueItem]" = queue.Queue()
        self._eim_requests: "queue.Queue[Optional[int]]" = queue.Queue()
        self._stop = threading.Event()
        self._threads: List[threading.Thread] = []

        self._pending_dmr_replies: Deque[str] = deque()

    # ---- lifecycle ----

    def start(self) -> None:
        self._stop.clear()
        self._threads = [
            threading.Thread(target=self._dmr_reader_loop, name="dmr-reader", daemon=True),
            threading.Thread(target=self._nextion_reader_loop, name="nextion-reader", daemon=True),
            threading.Thread(target=self._eim_worker_loop, name="eim-worker", daemon=True),
        ]
        for thread in self._threads:
            thread.start()

    def stop(self, join_timeout: float = 5.0) -> None:
        """Signals every thread to stop and waits for them to exit.

        The EIM worker is woken immediately via its own stop sentinel, since
        queue.get() would otherwise block indefinitely. The reader threads
        are different: closing both transports here is what actually
        unblocks them, not `_stop` alone -- a reader thread is normally
        sitting inside a blocking wait_for_data() call, and _stop is only
        checked between calls to read_frame()/read_event(), i.e. after a
        complete DMR/Nextion frame's worth of waiting. Closing the transport
        makes any wait_for_data() call already in progress fail (or the very
        next one fail immediately), so a reader thread notices within
        roughly one inter_byte_timeout window -- NOT instantly, since a
        select() already blocked on the old fd when it's closed isn't
        guaranteed to wake before its own timeout elapses (this is a real
        but bounded improvement over never closing the transport at all,
        which could otherwise leave a reader blocked for a single frame's
        entire first_byte_timeout + max_len * inter_byte_timeout). Threads
        are daemons, so a `join_timeout` that elapses first does not block
        process exit; it only means stop() returns before every thread has
        fully exited.
        """
        self._stop.set()
        self._eim_requests.put(None)
        self._dmr_transport.close()
        self._nextion_transport.close()
        for thread in self._threads:
            thread.join(timeout=join_timeout)

    # ---- reader/worker threads ----

    def _dmr_reader_loop(self) -> None:
        timeouts = self._config.timeouts
        while not self._stop.is_set():
            try:
                raw = dmr.read_frame(
                    self._dmr_transport,
                    first_byte_timeout=timeouts.dmr_first_byte,
                    inter_byte_timeout=timeouts.dmr_inter_byte,
                )
            except OSError as error:
                logger.warning("DMR transport error: %s", error)
                self._queue.put(_TransportLost("dmr"))
                return
            if raw and dmr.is_well_formed(raw):
                self._queue.put(_DmrFrame(raw))

    def _nextion_reader_loop(self) -> None:
        timeouts = self._config.timeouts
        while not self._stop.is_set():
            try:
                raw = nx.read_event(
                    self._nextion_transport,
                    first_byte_timeout=timeouts.nextion_first_byte,
                    inter_byte_timeout=timeouts.nextion_inter_byte,
                )
            except OSError as error:
                logger.warning("Nextion transport error: %s", error)
                self._queue.put(_TransportLost("nextion"))
                return
            if raw:
                self._queue.put(_NextionFrame(raw))

    def _eim_worker_loop(self) -> None:
        while True:
            dmr_id = self._eim_requests.get()
            if dmr_id is None:  # stop() sentinel
                return
            caller = self._eim_client.lookup_user(dmr_id)
            self._queue.put(_EimResult(dmr_id, caller))

    # ---- main dispatch loop ----

    def run(self) -> None:
        while not self._stop.is_set():
            self.run_once()

    def run_once(self, timeout: float = TICK_INTERVAL) -> None:
        """Process exactly one queued item, or run a state-machine tick if
        the queue stays empty for `timeout` seconds. Split out from run() so
        tests can drive the loop deterministically without real threads.

        Also re-sends the startup handshake command via on_module_init_poll()
        on every idle tick: mirrors A05Init.ino's `while (not
        DMRTransmit(...)) delay(1000)` retry-with-no-give-up-bound, at
        TICK_INTERVAL's pace rather than legacy's exact 1s (on_module_init_poll
        is a no-op outside SYSTEM_STARTING, so this is harmless once past
        startup). Without this, nothing would ever send the first
        QUERY_INIT_FINISHED and the service would sit in SYSTEM_STARTING
        forever."""
        try:
            item = self._queue.get(timeout=timeout)
        except queue.Empty:
            now = self._clock()
            self._execute(self._state_machine.on_module_init_poll())
            self._execute(self._state_machine.tick(now))
            return
        self._dispatch(item)

    def _dispatch(self, item: _QueueItem) -> None:
        if isinstance(item, _DmrFrame):
            self._execute(self._route_dmr_frame(item.raw))
        elif isinstance(item, _NextionFrame):
            self._execute(self._route_nextion_frame(item.raw))
        elif isinstance(item, _EimResult):
            self._execute(self._state_machine.on_eim_lookup_result(item.dmr_id, item.caller))
        elif isinstance(item, _TransportLost):
            # Safety gate: "A lost UI or DMR connection must release PTT and
            # return to a safe state" -- covers both sources alike.
            logger.error("%s transport lost", item.source)
            self._pending_dmr_replies.clear()
            self._execute(self._state_machine.on_dmr_link_lost())

    # ---- DMR frame routing ----

    def _route_dmr_frame(self, raw: bytes) -> List[fx.Effect]:
        now = self._clock()
        event = dmr.decode_unsolicited_event(raw)
        try:
            if event == "voice_call_start":
                return self._state_machine.on_voice_call_started(now)
            if event == "voice_call_end":
                return self._state_machine.on_voice_call_ended(now)
            if event == "sms_received":
                sender_id, text = dmr.decode_sms_received(raw)
                return self._state_machine.on_sms_received(sender_id, text)

            if not self._pending_dmr_replies:
                logger.debug("unrouted DMR frame (no pending reply expected): %s", raw.hex())
                return []
            pending = self._pending_dmr_replies.popleft()
            if pending == "module_init":
                return self._state_machine.on_module_init_reply(dmr.is_success_reply(raw), now)
            if pending == "voice_info":
                if not dmr.voice_info_valid(raw):
                    return []
                rx_contact, rx_group = dmr.decode_voice_info(raw)
                return self._state_machine.on_voice_info_reply(rx_contact, rx_group)
            if pending == "signal_strength":
                return self._state_machine.on_signal_strength_reply(dmr.decode_signal_strength(raw), now)
            if pending == "sms_send":
                return self._state_machine.on_sms_send_completed(dmr.is_success_reply(raw))
            return []  # unreachable: every value pushed by _note_pending_reply is handled above
        except ValueError as error:
            # decode_unsolicited_event()/voice_info_valid() only check that a
            # frame is long enough to identify its *kind*, not long enough
            # for the matching decode_*() to read every field it needs (e.g.
            # decode_sms_received needs len>=16, but the "is this SMS"
            # check only needs len>=9) -- a short/malformed frame can pass
            # the first check and still raise here. Treat it like any other
            # malformed frame: log and drop, never crash the dispatch loop.
            logger.warning("malformed DMR frame %s: %s", raw.hex(), error)
            return []

    def _route_nextion_frame(self, raw: bytes) -> List[fx.Effect]:
        payload = nx.split_terminator(raw)
        if payload is None:
            logger.debug("incomplete nextion event: %s", raw.hex())
            return []
        event = nx.parse_event(payload)
        logger.debug("nextion event (not yet routed to a StateMachine input): %s", event)
        return []

    # ---- effect execution ----

    def _execute(self, effects: List[fx.Effect]) -> None:
        for effect in effects:
            self._execute_one(effect)

    def _execute_one(self, effect: fx.Effect) -> None:
        # Encoding errors (ValueError, e.g. an invalid group_list or SMS
        # payload) and transport errors (OSError) are both handled the same
        # way here: log and drop rather than crash the single dispatch
        # thread over one bad effect.
        try:
            if isinstance(effect, fx.SendDmrCommand):
                self._dmr_transport.write(dmr.build_simple_command(effect.cmd, effect.mode))
                self._note_pending_reply(effect.cmd)
            elif isinstance(effect, fx.SendDigitalChannel):
                self._dmr_transport.write(dmr.build_set_digital_channel(effect.channel))
            elif isinstance(effect, fx.SendSms):
                self._dmr_transport.write(dmr.build_send_sms(effect.contact_id, effect.text))
                self._note_pending_reply(dmr.SEND_SMS)
            elif isinstance(effect, fx.UpdateNextionDisplay):
                self._nextion_renderer.render(effect.kind, effect.data)
            elif isinstance(effect, fx.RequestCallerLookup):
                self._eim_requests.put(effect.dmr_id)
        except (OSError, ValueError) as error:
            # _note_pending_reply() only runs after a successful write
            # (above), specifically so a failed write can never leave a
            # pending-reply FIFO entry for a command that was never actually
            # sent -- that would desync every reply correlation after it.
            logger.warning("could not execute effect %r: %s", effect, error)

    def _note_pending_reply(self, cmd: int) -> None:
        """Only commands a StateMachine.on_*() method actually consumes the
        reply to get a FIFO entry -- e.g. GET_DIGITAL_CHANNEL's reply has no
        consumer today, so it is deliberately left untracked and will show up
        as an "unrouted" frame rather than misattributed to some later
        command's reply.

        Deduplicates against an already-pending entry of the same kind
        (rather than appending unconditionally) so a command that gets
        resent while its reply is still outstanding -- e.g.
        on_module_init_poll() retried every idle tick while the DMR module
        never answers, or QUERY_SIGNAL_STRENGTH re-polled every
        RSSI_POLL_INTERVAL during a stalled receive -- can't grow this deque
        without bound."""
        kind = {
            dmr.QUERY_INIT_FINISHED: "module_init",
            dmr.QUERY_DIGITAL_VOICE_INFO: "voice_info",
            dmr.QUERY_SIGNAL_STRENGTH: "signal_strength",
            dmr.SEND_SMS: "sms_send",
        }.get(cmd)
        if kind is not None and kind not in self._pending_dmr_replies:
            self._pending_dmr_replies.append(kind)
