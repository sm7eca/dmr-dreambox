"""Structured logging setup (milestone 3 of
doc/akb/raspberry-pi-port-plan.md).

Enforces the port plan's safety gate: "Never log Wi-Fi credentials or
unredacted personal identifiers." The ESP32 firmware's Debug.print() calls
have no such filtering at all (current-system.md flags this as a verified
risk); this adapter adds a redaction filter rather than trusting every call
site to remember not to log sensitive data.

Convention: callers must pass anything identifying via the logging `extra=`
dict using one of the known sensitive keys below, never interpolated
directly into the message string -- a filter can redact a structured field
by name, but it cannot reliably scrub free-form text.

Important stdlib logging limitation: a `logging.Filter` only runs on the
specific `Logger`/`Handler` object it's attached to -- attaching it to the
root logger does NOT make it apply to records logged through a *different*
logger (e.g. `logging.getLogger("eim")`), and there is no hook that applies
a filter across every handler in the hierarchy automatically. That means any
handler added later -- for remote log shipping, a file handler, etc. -- MUST
be added via add_handler() below, not `logger.addHandler()` directly, or
redaction silently will not apply to it.
"""

from __future__ import annotations

import logging
from typing import Iterable, Set

REDACTED = "***"

DEFAULT_SENSITIVE_KEYS = (
    "wifi_ssid",
    "wifi_password",
    "caller_name",
    "caller_city",
    "caller_state",
    "caller_country",
)


class RedactSensitiveFields(logging.Filter):
    def __init__(self, sensitive_keys: Iterable[str]):
        super().__init__()
        self._sensitive_keys: Set[str] = set(sensitive_keys)

    def filter(self, record: logging.LogRecord) -> bool:
        for key in self._sensitive_keys:
            if hasattr(record, key):
                setattr(record, key, REDACTED)
        return True


def add_handler(
    handler: logging.Handler,
    sensitive_keys: Iterable[str] = DEFAULT_SENSITIVE_KEYS,
    logger: logging.Logger = None,
) -> None:
    """The only sanctioned way to attach a handler after configure_logging()
    has run -- e.g. adding a second destination (remote log shipping, a file
    handler) later. Attaches the redaction filter to `handler` itself, since
    (see module docstring) there is no way to make a logger-level filter
    apply to a handler transitively."""
    handler.addFilter(RedactSensitiveFields(sensitive_keys))
    (logger or logging.getLogger()).addHandler(handler)


def configure_logging(
    level: int = logging.INFO,
    sensitive_keys: Iterable[str] = DEFAULT_SENSITIVE_KEYS,
    handler: logging.Handler = None,
) -> logging.Logger:
    """Configures the root logger. Pass `handler` in tests to capture output
    without touching real stdout/stderr; defaults to a StreamHandler."""
    if handler is None:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    add_handler(handler, sensitive_keys, logger=root)
    return root
