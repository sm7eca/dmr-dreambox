"""EIM HTTP client adapter (milestone 3 of doc/akb/raspberry-pi-port-plan.md).

Calls the `/user/{dmr_id}` endpoint documented in doc/akb/eim-examples.md
(response shape: `DmrUser` -- `dmr_id`, `call_sign`, `name`, `city`, `state`,
`country`), replacing the hardcoded `http://dmrdream.com/...` string literals
in sketch_dreambox/A70EIMintegration.ino and A50WIFI.ino with configuration
(dreambox_pi.service.config.EimHttpConfig).

Takes an injectable HTTP session (anything with a `.get(url, timeout=...)`
method returning an object with `.status_code` and `.json()`, matching
`requests`) rather than importing `requests` directly, so tests can supply a
fake session with no network access and no new test dependency beyond what
the EIM service already uses.
"""

from __future__ import annotations

from typing import Any, Optional, Protocol

from dreambox_pi.application.state_machine import CallerInfo
from dreambox_pi.service.config import EimHttpConfig


class HttpResponse(Protocol):
    status_code: int

    def json(self) -> Any: ...


class HttpSession(Protocol):
    def get(self, url: str, timeout: float) -> HttpResponse: ...


class EimClient:
    def __init__(self, config: EimHttpConfig, session: HttpSession):
        self._config = config
        self._session = session

    def lookup_user(self, dmr_id: int) -> Optional[CallerInfo]:
        """Returns None on ANY failure -- network error, timeout, non-200,
        a malformed response object, or an unexpected response shape.
        Deliberately never raises: the state machine's
        on_eim_lookup_result() treats caller=None as "unknown caller" and
        must not be blocked by a slow or broken EIM service (see the
        EIM-timeout coverage in tests/dreambox_pi/test_state_machine.py).
        The whole call -- including accessing response.status_code, which is
        just as capable of raising as the network call itself against a
        misbehaving session implementation -- is wrapped in one broad
        `except Exception`, intentionally, for that reason."""
        base_url = self._config.base_url.rstrip("/")
        url = f"{base_url}/user/{dmr_id}"
        try:
            response = self._session.get(url, timeout=self._config.timeout)
            if response.status_code != 200:
                return None
            data = response.json()
            return CallerInfo(
                callsign=data["call_sign"],
                name=data["name"],
                city=data["city"],
            )
        except Exception:
            return None
