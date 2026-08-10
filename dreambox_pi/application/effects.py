"""Side effects the state machine (state_machine.py) wants performed, as
plain, inert data -- never executed by the state machine itself. A later
milestone's adapters (or a test) are responsible for turning these into real
DMR/Nextion frames and I/O calls. Keeping effects as data, rather than
callbacks or direct calls, is what makes the state machine testable without
any transport: a test just asserts on the returned list.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Union

from dreambox_pi.domain.dmr_protocol import DigitalChannel


@dataclass(frozen=True)
class SendDmrCommand:
    """A fixed 10-byte DMR command (dmr_protocol.build_simple_command)."""

    cmd: int
    mode: int


@dataclass(frozen=True)
class SendDigitalChannel:
    """A full SET_DIGITAL_CHANNEL frame (dmr_protocol.build_set_digital_channel)."""

    channel: DigitalChannel


@dataclass(frozen=True)
class SendSms:
    """A SEND_SMS frame (dmr_protocol.build_send_sms)."""

    contact_id: int
    text: str


@dataclass(frozen=True)
class UpdateNextionDisplay:
    """An opaque hint for a Nextion adapter to render, tagged by `kind`.

    Kept coarse-grained on purpose: milestone 2 is about state transitions,
    not re-implementing every NX_P0_*/NX_P9_* display routine from
    A40Nextion_HMI.ino. An adapter maps `kind` to the specific
    nextion_protocol.build_command() calls needed.
    """

    kind: str
    data: Dict[str, Any]


@dataclass(frozen=True)
class RequestCallerLookup:
    """Ask the application layer to perform an EIM lookup for `dmr_id`
    (an HTTP call, so it stays outside the state machine) and report the
    result back via StateMachine.on_eim_lookup_result()."""

    dmr_id: int


Effect = Union[SendDmrCommand, SendDigitalChannel, SendSms, UpdateNextionDisplay, RequestCallerLookup]
