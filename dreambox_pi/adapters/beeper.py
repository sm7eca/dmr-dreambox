"""Beeper/indicator adapter (milestone 3 of
doc/akb/raspberry-pi-port-plan.md) -- optional GPIO.

The ESP32 firmware drives a beeper on a hardcoded GPIO 14
(`sketch_dreambox.ino:43-44`'s `beepPin`). The port plan's hardware-mapping
table marks the Pi equivalent explicitly optional: "Configurable libgpiod
output or disabled adapter" -- electrical driver and active level need a
bench check before use (milestone 4), so NullBeeper is the safe default and
GpioBeeper only imports `gpiod` lazily, so its absence never breaks anything
when the beeper is disabled (the common case until that bench check happens).
"""

from __future__ import annotations

from typing import Protocol


class BeeperPort(Protocol):
    def set(self, on: bool) -> None: ...


class NullBeeper:
    """Default: no GPIO access at all. Safe on any host, including one with
    no GPIO chip -- e.g. a dev machine, or a Pi before the beeper wiring has
    been bench-verified."""

    def set(self, on: bool) -> None:
        return None


class GpioBeeper:
    """Real beeper via libgpiod. `chip`/`line`/`active_high` are
    configuration, never source constants -- and must be verified against
    the actual wiring on a bench (milestone 4) before use; this class does
    not guess a safe default line."""

    def __init__(self, chip: str, line: int, active_high: bool = True):
        import gpiod  # imported lazily: only required if GpioBeeper is actually constructed

        self._active_high = active_high
        self._chip = gpiod.Chip(chip)
        self._line = self._chip.get_line(line)
        self._line.request(consumer="dreambox_pi", type=gpiod.LINE_REQ_DIR_OUT)

    def set(self, on: bool) -> None:
        value = 1 if (on == self._active_high) else 0
        self._line.set_value(value)

    def close(self) -> None:
        self._chip.close()
