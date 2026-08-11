"""Application configuration (milestone 3 of doc/akb/raspberry-pi-port-plan.md).

Device paths, baud rates, EIM endpoint, and protocol timeouts must be
configuration, not source constants -- the ESP32 firmware hardcodes all of
these (`sketch_dreambox.ino:61-65`'s pin assignments, `A70EIMintegration.ino`'s
`http://dmrdream.com/...` string literals), which is exactly what this
milestone's goal says to stop doing.

Loaded from a plain JSON file (same format choice as adapters/settings_store.py
for consistency, not a new decision needing its own ADR). Unlike
settings_store.load() -- which holds recoverable operational radio state and
must degrade gracefully -- a missing or malformed config file here raises a
clear error at startup: there is no safe universal default for which UART
device is the DMR module vs. the Nextion display, so guessing wrong and
silently binding to the wrong port is worse than failing loudly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

from dreambox_pi.domain import dmr_protocol as dmr
from dreambox_pi.domain import nextion_protocol as nx


class ConfigError(Exception):
    """Raised for a missing, malformed, or incomplete config file."""


@dataclass(frozen=True)
class SerialConfig:
    port: str
    baudrate: int = 57600  # sketch_dreambox.ino:324,327 -- both UARTs run at this rate today


@dataclass(frozen=True)
class EimHttpConfig:
    base_url: str = "http://dmrdream.com/api/v1"
    timeout: float = 5.0


@dataclass(frozen=True)
class TimeoutConfig:
    dmr_first_byte: float = dmr.FIRST_BYTE_TIMEOUT
    dmr_inter_byte: float = dmr.INTER_BYTE_TIMEOUT
    nextion_first_byte: float = nx.FIRST_BYTE_TIMEOUT
    nextion_inter_byte: float = nx.INTER_BYTE_TIMEOUT


@dataclass(frozen=True)
class AppConfig:
    dmr_serial: SerialConfig
    nextion_serial: SerialConfig
    eim: EimHttpConfig = field(default_factory=EimHttpConfig)
    timeouts: TimeoutConfig = field(default_factory=TimeoutConfig)
    settings_path: str = "/var/lib/dreambox-pi/settings.json"
    log_level: str = "INFO"


def _require(data: Dict[str, Any], key: str, context: str) -> Any:
    if key not in data:
        raise ConfigError(f"missing required config key {key!r} in {context}")
    return data[key]


def from_dict(data: Dict[str, Any]) -> AppConfig:
    dmr_serial_data = _require(data, "dmr_serial", "config")
    nextion_serial_data = _require(data, "nextion_serial", "config")

    dmr_serial = SerialConfig(
        port=_require(dmr_serial_data, "port", "dmr_serial"),
        baudrate=dmr_serial_data.get("baudrate", SerialConfig.baudrate),
    )
    nextion_serial = SerialConfig(
        port=_require(nextion_serial_data, "port", "nextion_serial"),
        baudrate=nextion_serial_data.get("baudrate", SerialConfig.baudrate),
    )

    eim_data = data.get("eim", {})
    eim = EimHttpConfig(
        base_url=eim_data.get("base_url", EimHttpConfig.base_url),
        timeout=eim_data.get("timeout", EimHttpConfig.timeout),
    )

    timeouts_data = data.get("timeouts", {})
    defaults = TimeoutConfig()
    timeouts = TimeoutConfig(
        dmr_first_byte=timeouts_data.get("dmr_first_byte", defaults.dmr_first_byte),
        dmr_inter_byte=timeouts_data.get("dmr_inter_byte", defaults.dmr_inter_byte),
        nextion_first_byte=timeouts_data.get("nextion_first_byte", defaults.nextion_first_byte),
        nextion_inter_byte=timeouts_data.get("nextion_inter_byte", defaults.nextion_inter_byte),
    )

    return AppConfig(
        dmr_serial=dmr_serial,
        nextion_serial=nextion_serial,
        eim=eim,
        timeouts=timeouts,
        settings_path=data.get("settings_path", AppConfig.settings_path),
        log_level=data.get("log_level", AppConfig.log_level),
    )


def load(path: Path) -> AppConfig:
    if not path.exists():
        raise ConfigError(f"config file not found: {path}")
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        raise ConfigError(f"config file {path} is not valid JSON: {error}") from error
    if not isinstance(data, dict):
        raise ConfigError(f"config file {path} must contain a JSON object")
    return from_dict(data)
