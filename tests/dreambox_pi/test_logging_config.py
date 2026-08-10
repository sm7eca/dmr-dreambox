"""Tests for dreambox_pi.service.logging_config's redaction filter -- the
port plan's safety gate ("Never log Wi-Fi credentials or unredacted
personal identifiers.") enforced as code, not just a convention to remember.
"""

import logging
import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from dreambox_pi.service.logging_config import REDACTED, add_handler, configure_logging


class CapturingHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


@pytest.fixture
def root_logger_sandbox():
    root = logging.getLogger()
    saved_handlers = list(root.handlers)
    saved_level = root.level
    yield
    root.handlers = saved_handlers
    root.setLevel(saved_level)


def test_sensitive_fields_are_redacted(root_logger_sandbox):
    handler = CapturingHandler()
    configure_logging(handler=handler)
    logger = logging.getLogger("test.eim")

    logger.info(
        "call received",
        extra={"caller_name": "Real Person", "caller_city": "Real City", "dmr_id": 2400011},
    )

    record = handler.records[0]
    assert record.caller_name == REDACTED
    assert record.caller_city == REDACTED
    assert record.dmr_id == 2400011  # non-sensitive field passes through untouched
    assert record.getMessage() == "call received"


def test_custom_sensitive_keys_are_honored(root_logger_sandbox):
    handler = CapturingHandler()
    configure_logging(handler=handler, sensitive_keys=("secret_field",))
    logger = logging.getLogger("test.custom")

    logger.info("event", extra={"secret_field": "hide-me", "caller_name": "not redacted here"})

    record = handler.records[0]
    assert record.secret_field == REDACTED
    assert record.caller_name == "not redacted here"  # not in this call's custom key set


def test_records_without_sensitive_fields_are_unaffected(root_logger_sandbox):
    handler = CapturingHandler()
    configure_logging(handler=handler)
    logger = logging.getLogger("test.plain")

    logger.info("startup complete")

    assert handler.records[0].getMessage() == "startup complete"


def test_add_handler_redacts_a_second_destination_added_later(root_logger_sandbox):
    """The sanctioned way to add a handler after configure_logging() has
    already run -- e.g. a second log destination -- still gets redaction,
    unlike a bare logger.addHandler() call (see the module docstring's note
    on why a logger-level filter can't cover this automatically)."""
    first_handler = CapturingHandler()
    configure_logging(handler=first_handler)

    second_handler = CapturingHandler()
    add_handler(second_handler)

    logging.getLogger("test.second").info("call", extra={"caller_name": "Real Person"})

    assert first_handler.records[0].caller_name == REDACTED
    assert second_handler.records[0].caller_name == REDACTED


def test_level_filters_below_threshold(root_logger_sandbox):
    handler = CapturingHandler()
    configure_logging(level=logging.WARNING, handler=handler)
    logger = logging.getLogger("test.level")

    logger.info("should not appear")
    logger.warning("should appear")

    messages = [r.getMessage() for r in handler.records]
    assert messages == ["should appear"]
