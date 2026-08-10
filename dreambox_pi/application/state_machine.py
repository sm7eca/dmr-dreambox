"""Application-level state machine (milestone 2 of
doc/akb/raspberry-pi-port-plan.md): models startup, idle, transmit, receive,
SMS-send, and channel-change transitions, plus this port's safety gates --
all without any GPIO/serial/HTTP calls of its own.

Every method takes an explicit event (and, where timing matters, an explicit
`now` clock value) and returns a list of Effect objects (effects.py) describing
what should happen next -- it never performs I/O and never reads a real
clock. That is what makes this module unit-testable without a transport: see
tests/dreambox_pi/test_state_machine.py.

Legacy behavior ported from sketch_dreambox/A05Init.ino and
A30Main_State_Handling.ino; see states.py for which legacy states/behaviors
are intentionally out of scope for this slice, and dmr-protocol.md/
eim-examples.md for the source-derived quirks referenced below.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import List, Optional

from dreambox_pi.application.effects import (
    Effect,
    RequestCallerLookup,
    SendDigitalChannel,
    SendDmrCommand,
    SendSms,
    UpdateNextionDisplay,
)
from dreambox_pi.domain import dmr_protocol as dmr
from dreambox_pi.domain.dmr_protocol import DigitalChannel
from dreambox_pi.domain.states import UnitState

TS_SWITCH_INTERVAL = 2.0  # seconds; do_idle's TS re-send interval (A30Main_State_Handling.ino:19)
RSSI_POLL_INTERVAL = 5.0  # seconds; do_RecDMR's RSSI poll interval (A30Main_State_Handling.ino:57)


@dataclass
class CallerInfo:
    callsign: str
    name: str
    city: str


class StateMachine:
    def __init__(self, channel: DigitalChannel, ts_scan_enabled: bool = True, now: float = 0.0):
        self.state = UnitState.SYSTEM_STARTING
        self.channel = channel
        self.ts_scan_enabled = ts_scan_enabled
        self.caller_info: Optional[CallerInfo] = None
        self.active_contact_id: Optional[int] = None
        self._ts_switch_last = now
        self._rssi_timer = now

    # ---- startup ----

    def on_module_init_poll(self) -> List[Effect]:
        """Call on every startup tick until on_module_init_reply(True) arrives.
        Mirrors A05Init.ino's `while (not DMRTransmit(...)) delay(1000)` --
        legacy has no give-up bound; preserved here (open item in
        dmr-protocol.md) rather than inventing a timeout the firmware never
        had."""
        if self.state != UnitState.SYSTEM_STARTING:
            return []
        return [SendDmrCommand(dmr.QUERY_INIT_FINISHED, dmr.FUNC_ENABLE)]

    def on_module_init_reply(self, success: bool, now: float = 0.0) -> List[Effect]:
        if self.state != UnitState.SYSTEM_STARTING or not success:
            return []
        self.state = UnitState.IDLE
        self._ts_switch_last = now  # mirrors IN_NormalStartup's tsSwitchLast=millis() (A05Init.ino:40)
        return [
            SendDigitalChannel(self.channel),
            SendDmrCommand(dmr.GET_DIGITAL_CHANNEL, dmr.FUNC_ENABLE),
        ]

    # ---- idle / PTT ----

    def on_ptt_pressed(self) -> List[Effect]:
        """Guarded to IDLE only -- PTT presses during startup, an active
        receive, SMS send, or a lost link are silently ignored. This is a
        safety property in its own right: it makes accidental transmission
        during startup/link-loss structurally impossible, not just
        discouraged."""
        if self.state != UnitState.IDLE:
            return []
        self.state = UnitState.TRANSMIT
        return [
            SendDmrCommand(dmr.SET_TRANSMIT_INFORMATION, dmr.FUNC_ENABLE),
            UpdateNextionDisplay("transmit_on", {}),
        ]

    def on_ptt_released(self) -> List[Effect]:
        if self.state != UnitState.TRANSMIT:
            return []
        self.state = UnitState.IDLE
        return [
            SendDmrCommand(dmr.SET_TRANSMIT_INFORMATION, dmr.FUNC_DISABLE),
            UpdateNextionDisplay("transmit_off", {}),
        ]

    def tick(self, now: float) -> List[Effect]:
        """Call periodically (any interval shorter than the constants above)
        with the current time. `now` is caller-supplied so tests can drive it
        deterministically instead of sleeping."""
        effects: List[Effect] = []

        if self.state == UnitState.IDLE and self.ts_scan_enabled:
            if now - self._ts_switch_last >= TS_SWITCH_INTERVAL:
                new_slot = 1 - self.channel.inbound_slot
                # Rebind to a new DigitalChannel rather than mutating self.channel in
                # place: SendDigitalChannel below captures self.channel by reference,
                # so an in-place mutation on the NEXT tick would silently corrupt this
                # effect's snapshot if it hadn't been consumed yet.
                self.channel = replace(self.channel, inbound_slot=new_slot, outbound_slot=new_slot)
                self._ts_switch_last = now
                effects.append(SendDigitalChannel(self.channel))
                effects.append(UpdateNextionDisplay("ts_slot", {"slot": new_slot + 1}))

        if self.state == UnitState.REC_DMR:
            if now - self._rssi_timer >= RSSI_POLL_INTERVAL:
                self._rssi_timer = now
                effects.append(SendDmrCommand(dmr.QUERY_SIGNAL_STRENGTH, dmr.FUNC_ENABLE))

        return effects

    # ---- receive ----

    def on_voice_call_started(self, now: float) -> List[Effect]:
        """Legacy sets UnitState=REC_DMR_STATE unconditionally, from any prior
        state (DMRvoicemessageStart, A20Communication.ino:87-100) -- ported
        the same way, with one deliberate exception: LINK_LOST is a port-only
        safety state (see on_dmr_link_lost()) that must only be left via
        on_dmr_link_restored()'s reconnect handshake, never implicitly by any
        other event, or the mandated "return to a safe state" gate would be
        bypassable by a well-timed voice-call event.

        If this fires while TRANSMIT (a half-duplex DMR module shouldn't
        realistically report an RX call while we're keying up, but the
        protocol doesn't rule it out), account for the abandoned transmit
        explicitly rather than letting an unconditional overwrite silently
        drop the PTT-release effect every other path out of TRANSMIT emits.
        """
        if self.state == UnitState.LINK_LOST:
            return []
        effects: List[Effect] = []
        if self.state == UnitState.TRANSMIT:
            effects.append(SendDmrCommand(dmr.SET_TRANSMIT_INFORMATION, dmr.FUNC_DISABLE))
            effects.append(UpdateNextionDisplay("transmit_off", {}))
        self.state = UnitState.REC_DMR
        self._rssi_timer = now
        self.caller_info = None
        self.active_contact_id = None
        effects += [
            SendDmrCommand(dmr.QUERY_DIGITAL_VOICE_INFO, dmr.FUNC_ENABLE),
            SendDmrCommand(dmr.QUERY_SIGNAL_STRENGTH, dmr.FUNC_ENABLE),
        ]
        return effects

    def on_voice_info_reply(self, rx_contact: int, rx_group: int) -> List[Effect]:
        """Mirrors DMRqueryReceived's decode of a QUERY_DIGITAL_VOICE_INFO
        reply (A20Communication.ino:648-686): records which station is
        calling and requests an EIM lookup for it. on_eim_lookup_result()
        correlates against active_contact_id so a slow/stale reply from a
        previous call can't overwrite the currently active call's
        caller_info."""
        if self.state != UnitState.REC_DMR:
            return []
        self.active_contact_id = rx_contact
        return [RequestCallerLookup(rx_contact)]

    def _clear_receive_state(self) -> None:
        """Shared by every path that leaves REC_DMR (on_voice_call_ended,
        on_signal_strength_reply's rssi==0 branch, on_dmr_link_lost), so a
        future new exit path can't forget to clear these the way
        on_dmr_link_lost originally did."""
        self.caller_info = None
        self.active_contact_id = None

    def on_voice_call_ended(self, now: float = 0.0) -> List[Effect]:
        if self.state != UnitState.REC_DMR:
            return []
        self.state = UnitState.IDLE
        self._clear_receive_state()
        # "wait at this ts one extra scan cycle -- maybe response is coming"
        self._ts_switch_last = now  # DMRvoicemessageEnd, A20Communication.ino:109
        return [UpdateNextionDisplay("receive_off", {})]

    def on_signal_strength_reply(self, rssi: int, now: float = 0.0) -> List[Effect]:
        """rssi == 0 while receiving means the call was lost without an
        explicit end event -- do_RecDMR forces idle in that case
        (A30Main_State_Handling.ino:61-65); modeled identically here.
        Ignored outside REC_DMR: a late reply for an already-ended call must
        not paint a stale RSSI value over whatever the display has since
        moved on to."""
        if self.state != UnitState.REC_DMR:
            return []
        effects: List[Effect] = [UpdateNextionDisplay("rssi", {"value": rssi})]
        if rssi == 0:
            self.state = UnitState.IDLE
            self._clear_receive_state()
            self._ts_switch_last = now  # same reasoning as on_voice_call_ended
            effects.append(UpdateNextionDisplay("receive_off", {}))
        return effects

    def on_eim_lookup_result(self, dmr_id: int, caller: Optional[CallerInfo]) -> List[Effect]:
        """caller=None models a failed or timed-out EIM lookup (see
        doc/akb/eim-examples.md) -- must never raise or block the receive
        flow. Legacy falls back to a "--" placeholder rather than blocking
        (NX_P0_DisplayReceive, A40Nextion_HMI.ino:297-311); modeled the same
        way by simply passing caller=None through to the display effect.

        Ignored unless `dmr_id` matches the currently active call
        (active_contact_id, set by on_voice_info_reply): a lookup started for
        an earlier call that only resolves after that call ended and a new
        one started must not overwrite the new call's caller_info."""
        if self.state != UnitState.REC_DMR or dmr_id != self.active_contact_id:
            return []
        self.caller_info = caller
        return [UpdateNextionDisplay("caller_info", {"caller": caller, "dmr_id": dmr_id})]

    # ---- SMS ----

    def on_sms_send_requested(self, contact_id: int, text: str) -> List[Effect]:
        if self.state != UnitState.IDLE:
            return []
        self.state = UnitState.SMS_SEND
        return [SendSms(contact_id, text)]

    def on_sms_send_completed(self, success: bool) -> List[Effect]:
        """Legacy discards DMRreceiveReply's return value here
        (DMRsendSMS, A20Communication.ino:454-527) -- the port surfaces
        `success` in the display effect instead of silently dropping it, but
        the state transition itself doesn't depend on it, matching legacy."""
        if self.state != UnitState.SMS_SEND:
            return []
        self.state = UnitState.IDLE
        return [UpdateNextionDisplay("sms_sent", {"success": success})]

    def on_sms_received(self, sender_id: int, text: str) -> List[Effect]:
        """Legacy doesn't force a UnitState transition on SMS receipt
        (DMRcheckSMSRec just updates the display, A20Communication.ino:623-647)
        -- modeled the same way: no state change, any current state."""
        return [UpdateNextionDisplay("sms_received", {"sender": sender_id, "text": text})]

    # ---- channel change ----

    def on_channel_selected(self, channel: DigitalChannel) -> List[Effect]:
        if self.state != UnitState.IDLE:
            return []
        self.channel = channel
        return [SendDigitalChannel(channel), UpdateNextionDisplay("channel_changed", {})]

    # ---- safety gates ----

    def on_dmr_link_lost(self) -> List[Effect]:
        """Safety gate (raspberry-pi-port-plan.md): "A lost UI or DMR
        connection must release PTT and return to a safe state." Not present
        in the ESP32 firmware examined -- legacy has no link-loss detection
        at all, only per-command timeouts. This is new behavior required by
        the port plan, not a literal port.

        Whatever operation was active gets accounted for explicitly rather
        than silently abandoned: TRANSMIT releases PTT, REC_DMR clears the
        now-stale caller info (via the same helper on_voice_call_ended uses,
        so this can't drift out of sync the way it once did), and SMS_SEND
        reports the send as failed rather than leaving the UI showing nothing
        about whether it went out."""
        effects: List[Effect] = []
        if self.state == UnitState.TRANSMIT:
            effects.append(SendDmrCommand(dmr.SET_TRANSMIT_INFORMATION, dmr.FUNC_DISABLE))
        elif self.state == UnitState.REC_DMR:
            self._clear_receive_state()
        elif self.state == UnitState.SMS_SEND:
            effects.append(UpdateNextionDisplay("sms_sent", {"success": False}))
        self.state = UnitState.LINK_LOST
        effects.append(UpdateNextionDisplay("link_lost", {}))
        return effects

    def on_dmr_link_restored(self) -> List[Effect]:
        """Safety gate: "Default to receive-only after ... UART reconnect."
        Re-runs the startup handshake rather than jumping straight back to
        IDLE, so a reconnect is indistinguishable from a cold boot from the
        state machine's point of view -- it can only reach IDLE (receive-only)
        again via on_module_init_reply(True), never straight back into
        TRANSMIT."""
        if self.state != UnitState.LINK_LOST:
            return []
        self.state = UnitState.SYSTEM_STARTING
        return self.on_module_init_poll()
