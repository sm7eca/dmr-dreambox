"""Tests for dreambox_pi.service.config: device paths, endpoints, and
timeouts must come from a config file, not source constants (milestone 3's
explicit requirement) -- and a missing/malformed file must fail loudly
rather than silently binding to a guessed device.
"""

import json
import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from dreambox_pi.service import config


MINIMAL = {
    "dmr_serial": {"port": "/dev/ttyUSB0"},
    "nextion_serial": {"port": "/dev/ttyUSB1"},
}


def test_from_dict_applies_defaults_for_optional_fields():
    cfg = config.from_dict(MINIMAL)
    assert cfg.dmr_serial == config.SerialConfig(port="/dev/ttyUSB0", baudrate=57600)
    assert cfg.nextion_serial == config.SerialConfig(port="/dev/ttyUSB1", baudrate=57600)
    assert cfg.eim.base_url == "http://dmrdream.com/api/v1"
    assert cfg.settings_path == config.AppConfig.settings_path


def test_from_dict_overrides_are_honored():
    data = dict(MINIMAL)
    data["dmr_serial"] = {"port": "/dev/ttyUSB5", "baudrate": 115200}
    data["eim"] = {"base_url": "http://example.test", "timeout": 2.0}
    data["timeouts"] = {"dmr_first_byte": 3.0}
    data["settings_path"] = "/tmp/settings.json"
    data["log_level"] = "DEBUG"

    cfg = config.from_dict(data)

    assert cfg.dmr_serial == config.SerialConfig(port="/dev/ttyUSB5", baudrate=115200)
    assert cfg.eim == config.EimHttpConfig(base_url="http://example.test", timeout=2.0)
    assert cfg.timeouts.dmr_first_byte == 3.0
    assert cfg.timeouts.dmr_inter_byte == config.TimeoutConfig().dmr_inter_byte  # untouched default
    assert cfg.settings_path == "/tmp/settings.json"
    assert cfg.log_level == "DEBUG"


@pytest.mark.parametrize("missing_key", ["dmr_serial", "nextion_serial"])
def test_from_dict_requires_both_serial_ports(missing_key):
    data = {k: v for k, v in MINIMAL.items() if k != missing_key}
    with pytest.raises(config.ConfigError):
        config.from_dict(data)


def test_from_dict_requires_port_within_serial_block():
    data = dict(MINIMAL)
    data["dmr_serial"] = {"baudrate": 9600}  # no "port"
    with pytest.raises(config.ConfigError):
        config.from_dict(data)


def test_load_missing_file_raises_config_error(tmp_path):
    with pytest.raises(config.ConfigError):
        config.load(tmp_path / "does-not-exist.json")


def test_load_malformed_json_raises_config_error(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{not valid json")
    with pytest.raises(config.ConfigError):
        config.load(path)


def test_load_non_object_json_raises_config_error(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("[1, 2, 3]")
    with pytest.raises(config.ConfigError):
        config.load(path)


def test_load_valid_file_round_trips(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(MINIMAL))

    cfg = config.load(path)

    assert cfg.dmr_serial.port == "/dev/ttyUSB0"
    assert cfg.nextion_serial.port == "/dev/ttyUSB1"
