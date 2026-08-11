"""Shared helpers for loading tests/fixtures/sessions/*.json in dreambox_pi tests."""

import json
import pathlib

FIXTURES_DIR = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "sessions"


def load_session(name: str) -> dict:
    path = FIXTURES_DIR / f"{name}.json"
    return json.loads(path.read_text())


def get_frame(session: dict, seq: int) -> dict:
    for frame in session["frames"]:
        if frame["seq"] == seq:
            return frame
    raise KeyError(f"no frame with seq={seq} in flow {session.get('flow')!r}")


def frame_bytes(frame: dict) -> bytes:
    return bytes.fromhex(frame["bytes_hex"].replace(" ", ""))
