"""Settings persistence adapter (milestone 3 of
doc/akb/raspberry-pi-port-plan.md).

Replaces the ESP32 EEPROM-backed settings (`EepromSettings`,
`A60PersistentSettings.ino`) with a versioned JSON file, atomic writes, and
graceful fallback to defaults on a missing or corrupt file -- per the port
plan's migration guidance ("Export settings into a documented, versioned
schema rather than copying the ESP32 EEPROM image") and its safety gate
("Default to receive-only after startup, configuration errors, ... or
process restart"): a corrupt settings file is a configuration error, and
must not crash the service or block it from reaching a safe default state.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict

from dreambox_pi.domain.dmr_protocol import DigitalChannel

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class PersistedSettings:
    channel: DigitalChannel
    ts_scan_enabled: bool = True


def channel_to_dict(channel: DigitalChannel) -> Dict[str, Any]:
    """Derived from dataclasses.fields(), not a hand-enumerated field list --
    a future field added to DigitalChannel is included automatically instead
    of being silently dropped from every saved settings.json. Only
    encrypt_key needs a special case, since JSON has no bytes type."""
    data = dataclasses.asdict(channel)
    data["group_list"] = list(data["group_list"])
    data["encrypt_key"] = bytes(data["encrypt_key"]).hex()
    return data


def channel_from_dict(data: Dict[str, Any]) -> DigitalChannel:
    fields = dict(data)
    fields["encrypt_key"] = bytes.fromhex(fields["encrypt_key"])
    return DigitalChannel(**fields)


def save(path: Path, settings: PersistedSettings) -> None:
    """Atomic write: write to a sibling temp file with a unique name, fsync,
    then os.replace() (atomic on POSIX when source and destination are on
    the same filesystem, which a sibling temp file guarantees). The temp
    name is unique per call (tempfile.mkstemp) rather than a fixed
    "<name>.tmp" -- two overlapping save() calls must not be able to write
    into the same temp file and interleave a corrupted payload before either
    rename happens."""
    payload = {
        "schema_version": SCHEMA_VERSION,
        "ts_scan_enabled": settings.ts_scan_enabled,
        "channel": channel_to_dict(settings.channel),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(payload, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        os.unlink(tmp_name)
        raise


def load(path: Path, default_channel_factory: Callable[[], DigitalChannel]) -> PersistedSettings:
    """Never raises for a missing, unreadable, or corrupt file -- falls back
    to a fresh default channel instead, logging a warning for anything past
    "simply doesn't exist yet" (the normal first-run case). Reads the file
    directly rather than checking path.exists() first, to avoid a race where
    the file is deleted or its permissions change between the check and the
    read (a concurrent settings reset, a flaky mount, ...) -- that must
    degrade to defaults too, not raise, per the same contract."""
    try:
        raw = path.read_text()
    except FileNotFoundError:
        return PersistedSettings(channel=default_channel_factory())
    except OSError as error:
        logger.warning("settings file %s could not be read (%s); using defaults", path, error)
        return PersistedSettings(channel=default_channel_factory())

    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("settings file does not contain a JSON object")
        if data.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version {data.get('schema_version')!r}")
        return PersistedSettings(
            channel=channel_from_dict(data["channel"]),
            ts_scan_enabled=bool(data.get("ts_scan_enabled", True)),
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        logger.warning("settings file %s is corrupt or incompatible (%s); using defaults", path, error)
        return PersistedSettings(channel=default_channel_factory())
