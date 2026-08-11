"""Tests for dreambox_pi.adapters.beeper.

GpioBeeper needs a real GPIO chip (or at least the `gpiod` library) and is
explicitly out of scope for bench-less testing per
doc/akb/raspberry-pi-port-plan.md's hardware-mapping table -- only its lazy
import behavior is checked here, not real GPIO access. See milestone 4
(bench integration) for that.
"""

import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from dreambox_pi.adapters.beeper import GpioBeeper, NullBeeper


def test_null_beeper_set_is_a_no_op():
    beeper = NullBeeper()
    beeper.set(True)  # must not raise
    beeper.set(False)


def test_gpio_beeper_fails_clearly_without_the_gpiod_library():
    with pytest.raises(ImportError):
        GpioBeeper(chip="/dev/gpiochip0", line=14)
