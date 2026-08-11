"""Tests for dreambox_pi.adapters.settings_store: atomic writes, round-trip
fidelity, and graceful fallback to defaults on a missing/corrupt file
(milestone 3's "uses atomic settings writes" exit criterion).
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from dreambox_pi.adapters import settings_store
from dreambox_pi.domain.dmr_protocol import DigitalChannel


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


def test_save_then_load_round_trips_exactly(tmp_path):
    path = tmp_path / "settings.json"
    original = settings_store.PersistedSettings(channel=make_channel(), ts_scan_enabled=False)

    settings_store.save(path, original)
    loaded = settings_store.load(path, default_channel_factory=make_channel)

    assert loaded.ts_scan_enabled is False
    assert loaded.channel == original.channel


def test_save_leaves_no_temp_file_behind(tmp_path):
    path = tmp_path / "settings.json"
    settings_store.save(path, settings_store.PersistedSettings(channel=make_channel()))

    assert path.exists()
    assert not (tmp_path / "settings.json.tmp").exists()
    assert list(tmp_path.iterdir()) == [path]


def test_save_creates_parent_directories(tmp_path):
    path = tmp_path / "nested" / "dir" / "settings.json"
    settings_store.save(path, settings_store.PersistedSettings(channel=make_channel()))
    assert path.exists()


def test_load_unreadable_file_falls_back_to_default(tmp_path):
    """A permission error (or a file deleted/permissions-changed between an
    existence check and the read -- the TOCTOU this used to be vulnerable
    to) must degrade to defaults like any other configuration error, not
    raise."""
    path = tmp_path / "settings.json"
    path.write_text('{"schema_version": 1, "channel": {}}')
    path.chmod(0o000)

    try:
        loaded = settings_store.load(path, default_channel_factory=lambda: make_channel(tx_contact=7777))
        assert loaded.channel.tx_contact == 7777
    finally:
        path.chmod(0o644)  # restore so tmp_path cleanup can remove it


def test_load_missing_file_falls_back_to_default():
    used_default = False

    def default_channel_factory():
        nonlocal used_default
        used_default = True
        return make_channel(tx_contact=9999)

    loaded = settings_store.load(pathlib.Path("/nonexistent/settings.json"), default_channel_factory)

    assert used_default
    assert loaded.channel.tx_contact == 9999


def test_load_corrupt_json_falls_back_to_default(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{not valid json")

    loaded = settings_store.load(path, default_channel_factory=lambda: make_channel(tx_contact=1234))

    assert loaded.channel.tx_contact == 1234


def test_load_wrong_schema_version_falls_back_to_default(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text('{"schema_version": 999, "channel": {}}')

    loaded = settings_store.load(path, default_channel_factory=lambda: make_channel(tx_contact=4321))

    assert loaded.channel.tx_contact == 4321


def test_load_missing_channel_key_falls_back_to_default(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text('{"schema_version": 1, "ts_scan_enabled": true}')

    loaded = settings_store.load(path, default_channel_factory=lambda: make_channel(tx_contact=5555))

    assert loaded.channel.tx_contact == 5555


def test_channel_to_dict_from_dict_round_trip():
    channel = make_channel(encrypt_key=bytes(range(8)))
    data = settings_store.channel_to_dict(channel)
    restored = settings_store.channel_from_dict(data)
    assert restored == channel
