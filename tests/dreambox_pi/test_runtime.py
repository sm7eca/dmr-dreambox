"""Tests for dreambox_pi.service.runtime.Runtime -- the threading/queue
wiring decided in doc/adr/04_adr_dreambox_pi_io_concurrency_model.md.

Most tests drive the dispatch/routing logic directly (no threads), which is
where the actual risk lives: the FIFO-based solicited-reply correlation
described in runtime.py's module docstring. One end-to-end test exercises
the real reader/worker threads over pseudo-terminals to prove start()/run()/
stop() genuinely deliver a frame from a UART to the StateMachine and back.
"""

import os
import pty
import sys
import threading
import time
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from dreambox_pi.adapters.fake_serial import FakeSerialTransport
from dreambox_pi.adapters.serial_transport import SerialTransport
from dreambox_pi.application import effects as fx
from dreambox_pi.application.state_machine import StateMachine
from dreambox_pi.domain import dmr_protocol as dmr
from dreambox_pi.domain.dmr_protocol import DigitalChannel
from dreambox_pi.domain.states import UnitState
from dreambox_pi.service.config import AppConfig, EimHttpConfig, SerialConfig, TimeoutConfig
from dreambox_pi.service.runtime import Runtime, _DmrFrame, _TransportLost


def feed_dmr(runtime: Runtime, raw: bytes) -> None:
    """Directly drive Runtime._dispatch() for a DMR frame, bypassing the
    reader thread/queue -- deterministic for testing the routing logic."""
    runtime._dispatch(_DmrFrame(raw))


def make_channel(**overrides) -> DigitalChannel:
    kwargs = dict(
        rx_freq=434587500,
        tx_freq=432587500,
        local_id=2400011,
        group_list=[2401] + [0] * 31,
        tx_contact=2401,
        contact_type=1,
        cc=7,
    )
    kwargs.update(overrides)
    return DigitalChannel(**kwargs)


def make_config(**timeout_overrides) -> AppConfig:
    return AppConfig(
        dmr_serial=SerialConfig(port="unused-dmr"),
        nextion_serial=SerialConfig(port="unused-nextion"),
        eim=EimHttpConfig(),
        timeouts=TimeoutConfig(**timeout_overrides),
    )


class RecordingRenderer:
    def __init__(self):
        self.calls = []

    def render(self, kind, data):
        self.calls.append((kind, data))


class StubEimClient:
    def __init__(self, result=None):
        self.result = result
        self.requested_ids = []

    def lookup_user(self, dmr_id):
        self.requested_ids.append(dmr_id)
        return self.result


def make_runtime(state=UnitState.SYSTEM_STARTING, clock=lambda: 0.0, eim_result=None):
    state_machine = StateMachine(channel=make_channel())
    state_machine.state = state
    renderer = RecordingRenderer()
    eim_client = StubEimClient(result=eim_result)
    runtime = Runtime(
        config=make_config(),
        dmr_transport=FakeSerialTransport(),
        nextion_transport=FakeSerialTransport(),
        eim_client=eim_client,
        state_machine=state_machine,
        nextion_renderer=renderer,
        clock=clock,
    )
    return runtime, state_machine, renderer, eim_client


# ---- solicited-reply correlation ----


def test_module_init_command_then_success_reply_reaches_idle():
    runtime, state_machine, _renderer, _eim = make_runtime()

    runtime._execute(state_machine.on_module_init_poll())
    assert bytes(runtime._dmr_transport.written) == dmr.build_simple_command(
        dmr.QUERY_INIT_FINISHED, dmr.FUNC_ENABLE
    )

    success_reply = bytes([0x68, dmr.QUERY_INIT_FINISHED, 0, 0, 0, 0, 0, 0, 0, 0x10])
    feed_dmr(runtime, success_reply)

    assert state_machine.state == UnitState.IDLE


def test_module_init_failure_reply_does_not_advance_past_starting():
    runtime, state_machine, _renderer, _eim = make_runtime()
    runtime._execute(state_machine.on_module_init_poll())

    failure_reply = bytes([0x68, dmr.QUERY_INIT_FINISHED, 0, 1, 0, 0, 0, 0, 0, 0x10])
    feed_dmr(runtime, failure_reply)

    assert state_machine.state == UnitState.SYSTEM_STARTING


def test_voice_call_start_pushes_two_pending_replies_resolved_in_send_order():
    """on_voice_call_started() emits QUERY_DIGITAL_VOICE_INFO then
    QUERY_SIGNAL_STRENGTH back-to-back, before either reply has arrived --
    the FIFO must resolve the two replies that follow in that same order,
    not just handle one pending reply at a time."""
    runtime, state_machine, renderer, eim_client = make_runtime(state=UnitState.IDLE)

    call_start = bytes([0x68, dmr.VOICE_CALL_EVENT, 0, 0, 0, 0, 0, 0, 0x00, 0x10])
    feed_dmr(runtime, call_start)

    assert state_machine.state == UnitState.REC_DMR
    assert list(runtime._pending_dmr_replies) == ["voice_info", "signal_strength"]

    voice_info_reply = bytearray([0x68, dmr.QUERY_DIGITAL_VOICE_INFO, 1, 0, 0, 0, 0, 1] + [0] * 20)
    voice_info_reply[9:13] = (2400011).to_bytes(4, "little")
    voice_info_reply[13:17] = (2401).to_bytes(4, "little")
    feed_dmr(runtime, bytes(voice_info_reply))

    assert state_machine.active_contact_id == 2400011
    # RequestCallerLookup only reaches the EIM worker's queue here -- the
    # worker thread that would actually call eim_client isn't running in
    # this synchronous test (see test_request_caller_lookup_effect_is_queued_for_the_eim_worker).
    assert runtime._eim_requests.get_nowait() == 2400011
    assert list(runtime._pending_dmr_replies) == ["signal_strength"]

    rssi_reply = bytes([0x68, dmr.QUERY_SIGNAL_STRENGTH, 1, 0, 0, 0, 0, 1, 0x2A, 0x10])
    feed_dmr(runtime, rssi_reply)

    assert ("rssi", {"value": 0x2A}) in renderer.calls
    assert list(runtime._pending_dmr_replies) == []


def test_unsolicited_events_are_recognized_even_with_replies_pending():
    """decode_unsolicited_event() must be checked before the pending-reply
    FIFO, or a genuinely unsolicited voice_call_end arriving while a
    signal_strength reply is still outstanding would be misrouted as that
    reply."""
    runtime, state_machine, _renderer, _eim = make_runtime(state=UnitState.REC_DMR)
    runtime._pending_dmr_replies.append("signal_strength")

    call_end = bytes([0x68, dmr.VOICE_CALL_EVENT, 0, 0, 0, 0, 0, 0, 0x01, 0x10])
    feed_dmr(runtime, call_end)

    assert state_machine.state == UnitState.IDLE
    assert list(runtime._pending_dmr_replies) == ["signal_strength"]  # untouched


def test_sms_send_reply_completes_the_sms_flow():
    runtime, state_machine, renderer, _eim = make_runtime(state=UnitState.IDLE)
    runtime._execute(state_machine.on_sms_send_requested(2401, "HI"))
    assert state_machine.state == UnitState.SMS_SEND
    assert list(runtime._pending_dmr_replies) == ["sms_send"]

    success_reply = bytes([0x68, dmr.SEND_SMS, 0, 0, 0, 0, 0, 0, 0, 0x10])
    feed_dmr(runtime, success_reply)

    assert state_machine.state == UnitState.IDLE
    assert ("sms_sent", {"success": True}) in renderer.calls


def test_unrouted_frame_with_empty_pending_queue_is_a_safe_no_op():
    runtime, state_machine, renderer, _eim = make_runtime(state=UnitState.IDLE)
    stray_reply = bytes([0x68, dmr.GET_DIGITAL_CHANNEL, 0, 0, 0, 0, 0, 0, 0, 0x10])

    feed_dmr(runtime, stray_reply)

    assert state_machine.state == UnitState.IDLE
    assert renderer.calls == []


def test_malformed_sms_reply_is_dropped_not_crashed():
    """decode_unsolicited_event() only needs len(buf) >= 9 to recognize an
    SMS_RECEIVED_EVENT frame, but decode_sms_received() needs len(buf) >= 16
    to actually decode one -- a short frame passes the first check and
    raises ValueError in the second."""
    runtime, state_machine, renderer, _eim = make_runtime(state=UnitState.IDLE)
    short_sms_event = bytes([0x68, dmr.SMS_RECEIVED_EVENT, 0, 0, 0, 0, 0, 0, 0, 0x10])

    feed_dmr(runtime, short_sms_event)  # must not raise

    assert renderer.calls == []


def test_malformed_voice_info_reply_is_dropped_not_crashed():
    """voice_info_valid() only needs len(buf) > 12, but decode_voice_info()
    unpacks a field at offset 13 and needs len(buf) >= 17."""
    runtime, state_machine, _renderer, _eim = make_runtime(state=UnitState.REC_DMR)
    runtime._pending_dmr_replies.append("voice_info")
    short_voice_info_reply = bytearray(14)
    short_voice_info_reply[0] = 0x68
    short_voice_info_reply[-1] = 0x10  # buf[12] stays 0 -> passes voice_info_valid()

    feed_dmr(runtime, bytes(short_voice_info_reply))  # must not raise

    assert list(runtime._pending_dmr_replies) == []  # consumed, not left dangling


def test_failed_write_does_not_leave_a_stale_pending_reply():
    """If the transport write itself fails, the command was never actually
    sent -- _note_pending_reply() must not run, or the next real reply that
    arrives would be misattributed to a command that was never transmitted."""
    runtime, state_machine, _renderer, _eim = make_runtime(state=UnitState.SYSTEM_STARTING)
    runtime._dmr_transport.disconnect()

    runtime._execute(state_machine.on_module_init_poll())  # write raises, must not propagate

    assert list(runtime._pending_dmr_replies) == []


def test_note_pending_reply_deduplicates_to_avoid_unbounded_growth():
    """A command whose reply is still outstanding can get resent (e.g.
    on_module_init_poll() every idle tick while the DMR module never
    answers) -- each resend must not add another FIFO entry."""
    runtime, _state_machine, _renderer, _eim = make_runtime()

    runtime._note_pending_reply(dmr.QUERY_INIT_FINISHED)
    runtime._note_pending_reply(dmr.QUERY_INIT_FINISHED)
    runtime._note_pending_reply(dmr.QUERY_INIT_FINISHED)

    assert list(runtime._pending_dmr_replies) == ["module_init"]


def test_stop_closes_both_transports():
    """Closing the transports is what actually unblocks a reader thread
    stuck in wait_for_data() -- see stop()'s docstring."""
    runtime, _state_machine, _renderer, _eim = make_runtime()

    runtime.stop(join_timeout=0.1)

    assert runtime._dmr_transport.connected is False
    assert runtime._nextion_transport.connected is False


# ---- transport loss ----


def test_transport_lost_drives_link_lost_and_clears_pending_replies():
    runtime, state_machine, renderer, _eim = make_runtime(state=UnitState.TRANSMIT)
    runtime._pending_dmr_replies.append("signal_strength")

    runtime._dispatch(_TransportLost("dmr"))

    assert state_machine.state == UnitState.LINK_LOST
    assert list(runtime._pending_dmr_replies) == []
    assert ("link_lost", {}) in renderer.calls


# ---- tick / idle loop ----


def test_run_once_ticks_the_state_machine_when_queue_is_idle():
    now = [0.0]
    runtime, state_machine, renderer, _eim = make_runtime(state=UnitState.IDLE, clock=lambda: now[0])
    state_machine._ts_switch_last = 0.0

    now[0] = 3.0  # past TS_SWITCH_INTERVAL (2.0s)
    runtime.run_once(timeout=0.01)

    assert any(kind == "ts_slot" for kind, _data in renderer.calls)


def test_run_once_resends_module_init_while_starting_until_the_reply_arrives():
    """Nothing else calls on_module_init_poll() -- without this, a fresh
    service would sit in SYSTEM_STARTING forever, since the DMR module is
    never asked anything."""
    runtime, state_machine, _renderer, _eim = make_runtime(state=UnitState.SYSTEM_STARTING)
    assert bytes(runtime._dmr_transport.written) == b""

    runtime.run_once(timeout=0.01)

    assert bytes(runtime._dmr_transport.written) == dmr.build_simple_command(
        dmr.QUERY_INIT_FINISHED, dmr.FUNC_ENABLE
    )

    # A second idle tick re-sends it again (no give-up bound, matches legacy).
    runtime.run_once(timeout=0.01)
    assert bytes(runtime._dmr_transport.written) == dmr.build_simple_command(
        dmr.QUERY_INIT_FINISHED, dmr.FUNC_ENABLE
    ) * 2



# ---- effect execution: RequestCallerLookup reaches the EIM worker queue ----


def test_request_caller_lookup_effect_is_queued_for_the_eim_worker():
    runtime, _state_machine, _renderer, _eim = make_runtime()
    runtime._execute([fx.RequestCallerLookup(2400011)])
    assert runtime._eim_requests.get_nowait() == 2400011


# ---- end-to-end over real pseudo-terminals ----


@pytest.fixture
def pty_transport():
    master_fd, slave_fd = pty.openpty()
    transport = SerialTransport(port=os.ttyname(slave_fd), baudrate=57600)
    yield master_fd, transport
    transport.close()
    os.close(master_fd)


def test_start_run_stop_delivers_a_real_frame_end_to_end(pty_transport):
    dmr_master_fd, dmr_transport = pty_transport
    nx_master_fd, nx_slave_fd = pty.openpty()
    nextion_transport = SerialTransport(port=os.ttyname(nx_slave_fd), baudrate=57600)
    try:
        state_machine = StateMachine(channel=make_channel())
        runtime = Runtime(
            config=make_config(dmr_first_byte=0.2, dmr_inter_byte=0.2, nextion_first_byte=0.2, nextion_inter_byte=0.2),
            dmr_transport=dmr_transport,
            nextion_transport=nextion_transport,
            eim_client=StubEimClient(),
            state_machine=state_machine,
        )
        runtime.start()
        # run() is meant to be called on the service's own main thread (a
        # real main() would do runtime.start(); runtime.run()) -- driven
        # from a background thread here so the test can drive I/O and poll
        # state concurrently.
        dispatch_thread = threading.Thread(target=runtime.run, daemon=True)
        dispatch_thread.start()
        try:
            # Wait for the runtime's own idle-tick to send the startup query
            # (see run_once()'s on_module_init_poll() call) before replying,
            # so the reply lands after "module_init" is actually pending --
            # otherwise it would race and arrive as an unrouted frame.
            outgoing = os.read(dmr_master_fd, 10)
            assert outgoing == dmr.build_simple_command(dmr.QUERY_INIT_FINISHED, dmr.FUNC_ENABLE)

            success_reply = bytes([0x68, dmr.QUERY_INIT_FINISHED, 0, 0, 0, 0, 0, 0, 0, 0x10])
            os.write(dmr_master_fd, success_reply)

            deadline = time.monotonic() + 2.0
            while state_machine.state == UnitState.SYSTEM_STARTING and time.monotonic() < deadline:
                time.sleep(0.05)

            assert state_machine.state != UnitState.SYSTEM_STARTING
        finally:
            runtime.stop(join_timeout=2.0)
            dispatch_thread.join(timeout=2.0)
            assert not dispatch_thread.is_alive()
            assert all(not t.is_alive() for t in runtime._threads)
    finally:
        os.close(nx_master_fd)
