"""State-transition tests for dreambox_pi.application.state_machine.

Covers milestone 2's exit criteria (doc/akb/raspberry-pi-port-plan.md):
normal paths (startup, idle, TS scan, receive, SMS, channel change) and the
required failure paths -- PTT release, UART/link loss, EIM timeout, and
restart during an active operation never resuming transmit.
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from dreambox_pi.application.effects import (
    RequestCallerLookup,
    SendDigitalChannel,
    SendDmrCommand,
    SendSms,
    UpdateNextionDisplay,
)
from dreambox_pi.application.state_machine import CallerInfo, StateMachine, TS_SWITCH_INTERVAL, RSSI_POLL_INTERVAL
from dreambox_pi.domain import dmr_protocol as dmr
from dreambox_pi.domain.dmr_protocol import DigitalChannel
from dreambox_pi.domain.states import UnitState


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


def boot_to_idle(machine: StateMachine) -> None:
    machine.on_module_init_poll()
    machine.on_module_init_reply(True)
    assert machine.state == UnitState.IDLE


# ---- startup ----

def test_fresh_instance_always_starts_in_system_starting():
    machine = StateMachine(make_channel())
    assert machine.state == UnitState.SYSTEM_STARTING


def test_startup_retries_forever_until_success():
    machine = StateMachine(make_channel())

    for _ in range(5):
        effects = machine.on_module_init_poll()
        assert effects == [SendDmrCommand(dmr.QUERY_INIT_FINISHED, dmr.FUNC_ENABLE)]
        assert machine.state == UnitState.SYSTEM_STARTING
        assert machine.on_module_init_reply(False) == []

    effects = machine.on_module_init_reply(True)
    assert machine.state == UnitState.IDLE
    assert effects == [
        SendDigitalChannel(machine.channel),
        SendDmrCommand(dmr.GET_DIGITAL_CHANNEL, dmr.FUNC_ENABLE),
    ]


# ---- idle / PTT ----

def test_ptt_press_and_release():
    machine = StateMachine(make_channel())
    boot_to_idle(machine)

    pressed = machine.on_ptt_pressed()
    assert machine.state == UnitState.TRANSMIT
    assert SendDmrCommand(dmr.SET_TRANSMIT_INFORMATION, dmr.FUNC_ENABLE) in pressed

    released = machine.on_ptt_released()
    assert machine.state == UnitState.IDLE
    assert SendDmrCommand(dmr.SET_TRANSMIT_INFORMATION, dmr.FUNC_DISABLE) in released


def test_ptt_ignored_outside_idle():
    machine = StateMachine(make_channel())  # SYSTEM_STARTING
    assert machine.on_ptt_pressed() == []
    assert machine.state == UnitState.SYSTEM_STARTING

    boot_to_idle(machine)
    machine.on_voice_call_started(now=0.0)
    assert machine.state == UnitState.REC_DMR
    assert machine.on_ptt_pressed() == []
    assert machine.state == UnitState.REC_DMR


def test_ts_scan_tick_toggles_slot_and_resends_channel():
    machine = StateMachine(make_channel(inbound_slot=0, outbound_slot=0), now=0.0)
    boot_to_idle(machine)

    assert machine.tick(now=1.0) == []  # under the 2s interval

    effects = machine.tick(now=TS_SWITCH_INTERVAL)
    assert machine.channel.inbound_slot == 1
    assert machine.channel.outbound_slot == 1
    assert SendDigitalChannel(machine.channel) in effects
    assert UpdateNextionDisplay("ts_slot", {"slot": 2}) in effects


def test_ts_scan_effect_snapshot_is_not_mutated_by_a_later_tick():
    machine = StateMachine(make_channel(inbound_slot=0, outbound_slot=0), now=0.0)
    boot_to_idle(machine)

    effects_1 = machine.tick(now=TS_SWITCH_INTERVAL)
    sent_1 = next(e for e in effects_1 if isinstance(e, SendDigitalChannel))
    assert sent_1.channel.inbound_slot == 1

    machine.tick(now=2 * TS_SWITCH_INTERVAL)  # flips the slot again

    # effect #1's snapshot must be unaffected by the later tick's mutation
    assert sent_1.channel.inbound_slot == 1


def test_delayed_startup_does_not_cause_an_immediate_ts_switch():
    machine = StateMachine(make_channel(inbound_slot=0, outbound_slot=0), now=0.0)
    # simulate a slow DMR module: startup takes 30s of real time before succeeding
    machine.on_module_init_poll()
    machine.on_module_init_reply(True, now=30.0)
    assert machine.state == UnitState.IDLE

    assert machine.tick(now=30.5) == []  # only 0.5s since entering idle, not since t=0
    effects = machine.tick(now=30.0 + TS_SWITCH_INTERVAL)
    assert any(isinstance(e, SendDigitalChannel) for e in effects)


# ---- receive ----

def test_rx_voice_call_normal_flow_and_rssi_poll_interval():
    machine = StateMachine(make_channel(), now=0.0)
    boot_to_idle(machine)

    effects = machine.on_voice_call_started(now=100.0)
    assert machine.state == UnitState.REC_DMR
    assert SendDmrCommand(dmr.QUERY_DIGITAL_VOICE_INFO, dmr.FUNC_ENABLE) in effects
    assert SendDmrCommand(dmr.QUERY_SIGNAL_STRENGTH, dmr.FUNC_ENABLE) in effects

    assert machine.tick(now=104.0) == []  # under the 5s RSSI interval
    tick_effects = machine.tick(now=100.0 + RSSI_POLL_INTERVAL)
    assert SendDmrCommand(dmr.QUERY_SIGNAL_STRENGTH, dmr.FUNC_ENABLE) in tick_effects

    end_effects = machine.on_voice_call_ended()
    assert machine.state == UnitState.IDLE
    assert UpdateNextionDisplay("receive_off", {}) in end_effects


def test_voice_call_started_while_transmitting_releases_ptt_first():
    machine = StateMachine(make_channel())
    boot_to_idle(machine)
    machine.on_ptt_pressed()
    assert machine.state == UnitState.TRANSMIT

    effects = machine.on_voice_call_started(now=0.0)

    assert machine.state == UnitState.REC_DMR
    assert SendDmrCommand(dmr.SET_TRANSMIT_INFORMATION, dmr.FUNC_DISABLE) in effects
    assert UpdateNextionDisplay("transmit_off", {}) in effects


def test_signal_strength_reply_ignored_outside_receive():
    machine = StateMachine(make_channel())
    boot_to_idle(machine)

    effects = machine.on_signal_strength_reply(rssi=42)

    assert effects == []
    assert machine.state == UnitState.IDLE


def test_rssi_zero_forces_idle_without_explicit_end_event():
    machine = StateMachine(make_channel())
    boot_to_idle(machine)
    machine.on_voice_call_started(now=0.0)

    effects = machine.on_signal_strength_reply(rssi=0)

    assert machine.state == UnitState.IDLE
    assert UpdateNextionDisplay("receive_off", {}) in effects


def test_rssi_nonzero_keeps_receiving():
    machine = StateMachine(make_channel())
    boot_to_idle(machine)
    machine.on_voice_call_started(now=0.0)

    machine.on_signal_strength_reply(rssi=42)

    assert machine.state == UnitState.REC_DMR


def test_voice_info_reply_requests_a_caller_lookup():
    machine = StateMachine(make_channel())
    boot_to_idle(machine)
    machine.on_voice_call_started(now=0.0)

    effects = machine.on_voice_info_reply(rx_contact=2400011, rx_group=2401)

    assert machine.active_contact_id == 2400011
    assert effects == [RequestCallerLookup(2400011)]


def test_eim_lookup_timeout_does_not_raise_or_block_receive_flow():
    machine = StateMachine(make_channel())
    boot_to_idle(machine)
    machine.on_voice_call_started(now=0.0)
    machine.on_voice_info_reply(rx_contact=2400011, rx_group=2401)

    effects = machine.on_eim_lookup_result(dmr_id=2400011, caller=None)

    assert machine.state == UnitState.REC_DMR
    assert machine.caller_info is None
    assert UpdateNextionDisplay("caller_info", {"caller": None, "dmr_id": 2400011}) in effects

    # a successful lookup afterward still works normally
    caller = CallerInfo(callsign="EX1AMP", name="Example Person", city="Example City")
    machine.on_eim_lookup_result(dmr_id=2400011, caller=caller)
    assert machine.caller_info is caller

    # and the call can still end normally -- the timeout didn't wedge anything
    machine.on_voice_call_ended()
    assert machine.state == UnitState.IDLE


def test_eim_lookup_result_ignored_if_stale_for_a_previous_call():
    machine = StateMachine(make_channel())
    boot_to_idle(machine)

    # Call A starts, a lookup is requested, but A ends before the lookup replies.
    machine.on_voice_call_started(now=0.0)
    machine.on_voice_info_reply(rx_contact=1111111, rx_group=2401)
    machine.on_voice_call_ended()

    # Call B starts from a different station.
    machine.on_voice_call_started(now=1.0)
    machine.on_voice_info_reply(rx_contact=2222222, rx_group=2401)

    # A's slow lookup reply finally arrives -- must not overwrite B's caller_info.
    stale_caller = CallerInfo(callsign="STALE1", name="Stale Caller", city="Nowhere")
    effects = machine.on_eim_lookup_result(dmr_id=1111111, caller=stale_caller)

    assert effects == []
    assert machine.caller_info is None
    assert machine.active_contact_id == 2222222


def test_eim_lookup_result_ignored_outside_receive():
    machine = StateMachine(make_channel())
    boot_to_idle(machine)
    assert machine.on_eim_lookup_result(dmr_id=1, caller=None) == []


# ---- SMS ----

def test_sms_send_round_trip():
    machine = StateMachine(make_channel())
    boot_to_idle(machine)

    effects = machine.on_sms_send_requested(2400011, "DE EX1AMP")
    assert machine.state == UnitState.SMS_SEND
    assert effects == [SendSms(2400011, "DE EX1AMP")]

    done_effects = machine.on_sms_send_completed(success=True)
    assert machine.state == UnitState.IDLE
    assert UpdateNextionDisplay("sms_sent", {"success": True}) in done_effects


def test_sms_received_does_not_change_state():
    machine = StateMachine(make_channel())
    boot_to_idle(machine)
    machine.on_voice_call_started(now=0.0)

    effects = machine.on_sms_received(sender_id=2401, text="HI")

    assert machine.state == UnitState.REC_DMR
    assert UpdateNextionDisplay("sms_received", {"sender": 2401, "text": "HI"}) in effects


# ---- channel change ----

def test_channel_selected_from_idle():
    machine = StateMachine(make_channel())
    boot_to_idle(machine)
    new_channel = make_channel(tx_contact=2402)

    effects = machine.on_channel_selected(new_channel)

    assert machine.channel is new_channel
    assert SendDigitalChannel(new_channel) in effects


def test_channel_selected_ignored_outside_idle():
    machine = StateMachine(make_channel())  # SYSTEM_STARTING
    original = machine.channel
    assert machine.on_channel_selected(make_channel(tx_contact=9999)) == []
    assert machine.channel is original


# ---- safety gates ----

def test_link_lost_releases_ptt_when_transmitting():
    machine = StateMachine(make_channel())
    boot_to_idle(machine)
    machine.on_ptt_pressed()
    assert machine.state == UnitState.TRANSMIT

    effects = machine.on_dmr_link_lost()

    assert machine.state == UnitState.LINK_LOST
    assert SendDmrCommand(dmr.SET_TRANSMIT_INFORMATION, dmr.FUNC_DISABLE) in effects


def test_link_lost_from_idle_does_not_fabricate_a_ptt_release():
    machine = StateMachine(make_channel())
    boot_to_idle(machine)

    effects = machine.on_dmr_link_lost()

    assert machine.state == UnitState.LINK_LOST
    assert SendDmrCommand(dmr.SET_TRANSMIT_INFORMATION, dmr.FUNC_DISABLE) not in effects
    assert UpdateNextionDisplay("link_lost", {}) in effects


def test_link_lost_from_receive_clears_caller_info():
    machine = StateMachine(make_channel())
    boot_to_idle(machine)
    machine.on_voice_call_started(now=0.0)
    machine.on_voice_info_reply(rx_contact=2400011, rx_group=2401)
    machine.on_eim_lookup_result(dmr_id=2400011, caller=CallerInfo("EX1AMP", "Example Person", "Example City"))
    assert machine.caller_info is not None

    machine.on_dmr_link_lost()

    assert machine.state == UnitState.LINK_LOST
    assert machine.caller_info is None
    assert machine.active_contact_id is None

    # reconnecting and getting a fresh call must not see the old caller's info
    machine.on_dmr_link_restored()
    machine.on_module_init_reply(True)
    assert machine.caller_info is None


def test_link_lost_from_sms_send_reports_failure():
    machine = StateMachine(make_channel())
    boot_to_idle(machine)
    machine.on_sms_send_requested(2400011, "DE EX1AMP")
    assert machine.state == UnitState.SMS_SEND

    effects = machine.on_dmr_link_lost()

    assert machine.state == UnitState.LINK_LOST
    assert UpdateNextionDisplay("sms_sent", {"success": False}) in effects


def test_voice_call_started_ignored_while_link_lost():
    machine = StateMachine(make_channel())
    boot_to_idle(machine)
    machine.on_dmr_link_lost()
    assert machine.state == UnitState.LINK_LOST

    effects = machine.on_voice_call_started(now=0.0)

    assert effects == []
    assert machine.state == UnitState.LINK_LOST


def test_link_restored_reruns_startup_and_never_resumes_transmit():
    machine = StateMachine(make_channel())
    boot_to_idle(machine)
    machine.on_ptt_pressed()
    assert machine.state == UnitState.TRANSMIT

    machine.on_dmr_link_lost()
    assert machine.state == UnitState.LINK_LOST

    restart_effects = machine.on_dmr_link_restored()
    assert machine.state == UnitState.SYSTEM_STARTING
    assert restart_effects == [SendDmrCommand(dmr.QUERY_INIT_FINISHED, dmr.FUNC_ENABLE)]

    # PTT presses are still ignored mid-restart, same as any other non-idle state
    assert machine.on_ptt_pressed() == []

    machine.on_module_init_reply(True)
    assert machine.state == UnitState.IDLE  # never TRANSMIT -- restart always lands safe


def test_link_restored_ignored_unless_link_lost():
    machine = StateMachine(make_channel())
    boot_to_idle(machine)
    assert machine.on_dmr_link_restored() == []
    assert machine.state == UnitState.IDLE
