"""Tests for dreambox_pi.adapters.eim_client, using a fake HTTP session --
no real network access, and directly exercises the "EIM timeout must never
raise" contract that dreambox_pi.application.state_machine relies on.
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from dreambox_pi.adapters.eim_client import EimClient
from dreambox_pi.application.state_machine import CallerInfo
from dreambox_pi.service.config import EimHttpConfig


class FakeResponse:
    def __init__(self, status_code: int, body=None, json_raises: bool = False):
        self.status_code = status_code
        self._body = body
        self._json_raises = json_raises

    def json(self):
        if self._json_raises:
            raise ValueError("invalid JSON")
        return self._body


class FakeSession:
    def __init__(self, response=None, raises: Exception = None):
        self._response = response
        self._raises = raises
        self.requested_url = None
        self.requested_timeout = None

    def get(self, url, timeout):
        self.requested_url = url
        self.requested_timeout = timeout
        if self._raises:
            raise self._raises
        return self._response


def make_client(session) -> EimClient:
    config = EimHttpConfig(base_url="http://example.test/api/v1", timeout=3.0)
    return EimClient(config, session)


def test_successful_lookup_returns_caller_info():
    body = {"dmr_id": 2400011, "call_sign": "EX1AMP", "name": "Example Person", "city": "Example City",
            "state": "", "country": "Exampleland"}
    session = FakeSession(response=FakeResponse(200, body))
    client = make_client(session)

    result = client.lookup_user(2400011)

    assert result == CallerInfo(callsign="EX1AMP", name="Example Person", city="Example City")
    assert session.requested_url == "http://example.test/api/v1/user/2400011"
    assert session.requested_timeout == 3.0


def test_trailing_slash_in_base_url_does_not_produce_a_double_slash():
    session = FakeSession(response=FakeResponse(204))
    config = EimHttpConfig(base_url="http://example.test/api/v1/", timeout=3.0)
    client = EimClient(config, session)

    client.lookup_user(123)

    assert session.requested_url == "http://example.test/api/v1/user/123"


def test_response_object_that_raises_on_status_code_returns_none():
    class ExplodingResponse:
        @property
        def status_code(self):
            raise RuntimeError("misbehaving session")

    session = FakeSession(response=ExplodingResponse())
    client = make_client(session)
    assert client.lookup_user(1) is None


def test_non_200_status_returns_none():
    session = FakeSession(response=FakeResponse(204))  # EIM's "no entry found" status
    client = make_client(session)
    assert client.lookup_user(1) is None


def test_network_error_returns_none_and_does_not_raise():
    session = FakeSession(raises=ConnectionError("boom"))
    client = make_client(session)
    assert client.lookup_user(1) is None


def test_timeout_returns_none_and_does_not_raise():
    session = FakeSession(raises=TimeoutError("timed out"))
    client = make_client(session)
    assert client.lookup_user(1) is None


def test_malformed_json_body_returns_none():
    session = FakeSession(response=FakeResponse(200, {"unexpected": "shape"}))
    client = make_client(session)
    assert client.lookup_user(1) is None


def test_json_decode_error_returns_none():
    session = FakeSession(response=FakeResponse(200, json_raises=True))
    client = make_client(session)
    assert client.lookup_user(1) is None
