"""Composition root and process entrypoint (milestone 3 of
doc/akb/raspberry-pi-port-plan.md): wires the real adapters -- two
SerialTransport instances, EimClient over a real requests.Session, and the
persisted DigitalChannel -- to a fresh StateMachine and a Runtime, then runs
it until SIGTERM/SIGINT.

Deliberately does not invent a default DigitalChannel: rx_freq, tx_freq,
local_id (DMR ID), group_list/tx_contact (talkgroups), and contact_type are
operator-specific amateur-radio license data, not something this port can
guess a safe value for (AGENTS.md: keep callsigns/DMR IDs out of the repo;
raspberry-pi-port-plan.md's config-loading precedent: "no safe universal
default ... failing loudly is better than guessing wrong"). If
settings_path has no file yet, build_runtime() raises ConfigError rather
than starting on a synthesized channel -- a settings.json must be
provisioned once (e.g. via adapters.settings_store.save()) before the
service can run for the first time.

Packaging (a console-script entry point, a systemd unit) is milestone 6
("package and operate") -- this module is invoked directly for now:
    python3 -m dreambox_pi.service.main --config /path/to/config.json
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
from pathlib import Path

import requests

from dreambox_pi.adapters.eim_client import EimClient
from dreambox_pi.adapters.serial_transport import SerialTransport
from dreambox_pi.adapters.settings_store import load as load_settings
from dreambox_pi.application.state_machine import StateMachine
from dreambox_pi.domain.dmr_protocol import DigitalChannel
from dreambox_pi.service import config as config_module
from dreambox_pi.service.config import AppConfig, ConfigError
from dreambox_pi.service.logging_config import configure_logging
from dreambox_pi.service.runtime import Runtime

logger = logging.getLogger(__name__)


def _require_provisioned_settings(settings_path: Path):
    """default_channel_factory for settings_store.load(): raises instead of
    returning a synthesized DigitalChannel. Only called by load() when
    settings_path is missing/corrupt -- see this module's docstring for why
    that must fail loudly here rather than fall back to a guessed default."""

    def factory() -> DigitalChannel:
        raise ConfigError(
            f"no usable settings file at {settings_path}: provision one "
            "(channel, frequencies, DMR ID, talkgroups) with "
            "adapters.settings_store.save() before starting the service -- "
            "this port never invents default radio/callsign parameters"
        )

    return factory


def build_runtime(config: AppConfig) -> Runtime:
    """Composition root: the one place real adapters, persisted settings,
    and a fresh StateMachine are wired together into a Runtime. Raises
    ConfigError if settings_path has no usable settings file yet (see
    _require_provisioned_settings) -- every other failure (a bad serial
    device path, an unreachable EIM host) surfaces later, from inside
    Runtime's reader threads/EIM worker, not here."""
    settings_path = Path(config.settings_path)
    persisted = load_settings(settings_path, _require_provisioned_settings(settings_path))

    dmr_transport = SerialTransport(port=config.dmr_serial.port, baudrate=config.dmr_serial.baudrate)
    nextion_transport = SerialTransport(port=config.nextion_serial.port, baudrate=config.nextion_serial.baudrate)
    eim_client = EimClient(config.eim, requests.Session())
    state_machine = StateMachine(channel=persisted.channel, ts_scan_enabled=persisted.ts_scan_enabled)

    return Runtime(config, dmr_transport, nextion_transport, eim_client, state_machine)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="dreambox-pi", description="DMR Dreambox Raspberry Pi controller service")
    parser.add_argument("--config", required=True, type=Path, help="path to the service JSON config file")
    args = parser.parse_args(argv)

    try:
        config = config_module.load(args.config)
    except ConfigError as error:
        print(f"dreambox-pi: {error}", file=sys.stderr)
        return 1

    configure_logging(level=getattr(logging, config.log_level.upper(), logging.INFO))

    try:
        runtime = build_runtime(config)
    except ConfigError as error:
        logger.error("startup failed: %s", error)
        return 1

    def handle_stop_signal(signum, _frame):
        logger.info("received %s, stopping", signal.Signals(signum).name)
        runtime.stop()

    signal.signal(signal.SIGTERM, handle_stop_signal)
    signal.signal(signal.SIGINT, handle_stop_signal)

    logger.info("starting dreambox-pi service")
    runtime.start()
    runtime.run()  # blocks until a stop signal calls runtime.stop()
    logger.info("dreambox-pi service stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
