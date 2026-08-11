"""Tests for dreambox_pi.service.main -- the composition root that wires
real adapters (milestone 3) into a running Runtime, and the process
entrypoint's config-error handling.
"""

import json
import os
import pty
import sys
import time
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from dreambox_pi.adapters.serial_transport import SerialTransport
from dreambox_pi.adapters.settings_store import PersistedSettings, save as save_settings
from dreambox_pi.domain import dmr_protocol as dmr
from dreambox_pi.domain.dmr_protocol import DigitalChannel
from dreambox_pi.domain.states import UnitState
from dreambox_pi.service.config import ConfigError
from dreambox_pi.service.main import build_runtime, main


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


def write_config(path, **overrides):
    data = {
        "dmr_serial": {"port": "unused-dmr"},
        "nextion_serial": {"port": "unused-nextion"},
    }
    data.update(overrides)
    path.write_text(json.dumps(data))


def test_build_runtime_raises_config_error_without_a_provisioned_settings_file(tmp_path):
    """The service must never invent a default DigitalChannel (frequencies,
    DMR ID, talkgroups are operator-specific) -- see main.py's docstring."""
    from dreambox_pi.service.config import AppConfig, SerialConfig

    config = AppConfig(
        dmr_serial=SerialConfig(port="unused-dmr"),
        nextion_serial=SerialConfig(port="unused-nextion"),
        settings_path=str(tmp_path / "settings.json"),  # deliberately does not exist
    )

    with pytest.raises(ConfigError, match="provision one"):
        build_runtime(config)


def test_build_runtime_wires_real_adapters_over_ptys_and_reaches_idle(tmp_path):
    from dreambox_pi.service.config import AppConfig, SerialConfig, TimeoutConfig

    settings_path = tmp_path / "settings.json"
    save_settings(settings_path, PersistedSettings(channel=make_channel()))

    dmr_master, dmr_slave = pty.openpty()
    nx_master, nx_slave = pty.openpty()
    try:
        config = AppConfig(
            dmr_serial=SerialConfig(port=os.ttyname(dmr_slave)),
            nextion_serial=SerialConfig(port=os.ttyname(nx_slave)),
            timeouts=TimeoutConfig(
                dmr_first_byte=0.2, dmr_inter_byte=0.2, nextion_first_byte=0.2, nextion_inter_byte=0.2
            ),
            settings_path=str(settings_path),
        )

        runtime = build_runtime(config)
        assert isinstance(runtime._dmr_transport, SerialTransport)
        assert isinstance(runtime._nextion_transport, SerialTransport)
        assert runtime._state_machine.channel.local_id == 2400011
        assert runtime._state_machine.state == UnitState.SYSTEM_STARTING

        import threading

        runtime.start()
        threading.Thread(target=runtime.run, daemon=True).start()
        try:
            outgoing = os.read(dmr_master, 10)
            assert outgoing == dmr.build_simple_command(dmr.QUERY_INIT_FINISHED, dmr.FUNC_ENABLE)
            success_reply = bytes([0x68, dmr.QUERY_INIT_FINISHED, 0, 0, 0, 0, 0, 0, 0, 0x10])
            os.write(dmr_master, success_reply)

            deadline = time.monotonic() + 2.0
            while runtime._state_machine.state == UnitState.SYSTEM_STARTING and time.monotonic() < deadline:
                time.sleep(0.02)

            assert runtime._state_machine.state == UnitState.IDLE
        finally:
            runtime.stop(join_timeout=2.0)
    finally:
        os.close(dmr_master)
        os.close(nx_master)


def test_main_returns_1_and_reports_a_missing_config_file(tmp_path, capsys):
    exit_code = main(["--config", str(tmp_path / "does-not-exist.json")])

    assert exit_code == 1
    assert "does-not-exist.json" in capsys.readouterr().err


def test_main_returns_1_when_settings_are_not_provisioned(tmp_path):
    config_path = tmp_path / "config.json"
    write_config(config_path, settings_path=str(tmp_path / "settings.json"))

    exit_code = main(["--config", str(config_path)])

    assert exit_code == 1
