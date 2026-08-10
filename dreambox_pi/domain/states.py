"""Unit states for the host-side controller (milestone 2 of
doc/akb/raspberry-pi-port-plan.md).

Modeled after the state constants in sketch_dreambox/sketch_dreambox.ino:44-53,
but not a 1:1 port -- some legacy states are intentionally out of scope for
this slice:

- INITIAL_INPUT / INITIAL_SAVE: first-run EEPROM setup. That's a settings/
  persistence concern for the Linux-adapters milestone, not a runtime state
  transition; see doc/akb/current-system.md.
- MODE_CHANGE: legacy comment marks it "not used yet" (sketch_dreambox.ino:51).
- CHAN_CHANGE: defined as a constant in source but never observed being
  assigned to UnitState in A40Nextion_HMI.ino's channel-list navigation
  (pages 4/5/6) -- channel selection there updates dmrSettings/digData
  directly without a distinct state. Modeled here as a same-state action from
  IDLE, not a separate state.
- SMS_REC: DMRcheckSMSRec (A20Communication.ino:623-647) never sets this
  state either; it just updates the Nextion display. Modeled the same way.

LINK_LOST is new: the ESP32 firmware has no link-loss detection (only
per-command timeouts), but the port plan's safety gates require it
("A lost UI or DMR connection must release PTT and return to a safe state").
"""

from enum import Enum, auto


class UnitState(Enum):
    SYSTEM_STARTING = auto()
    IDLE = auto()
    TRANSMIT = auto()
    REC_DMR = auto()
    SMS_SEND = auto()
    LINK_LOST = auto()
