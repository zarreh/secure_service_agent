"""The PIN must not reach any tracing callback, the run store, or the audit trail
(D-A4-9).

A LangSmith tracer records the root run's inputs, and the initial graph state is
the root run's input — so a PIN carried in graph state is sent to the tracing
vendor in plaintext. This test drives the real `POST /chat` path with a recording
callback installed where `build_tracing_callbacks` would install the tracer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from langchain_core.callbacks import BaseCallbackHandler

from sentinel.api import run_executor
from tests.api._sentinel_client import build_sentinel_test_context


class _Recorder(BaseCallbackHandler):
    def __init__(self) -> None:
        self.seen: list[str] = []

    def on_chain_start(self, serialized: Any, inputs: Any, **kwargs: Any) -> None:
        self.seen.append(json.dumps(inputs, default=str))

    def on_chain_end(self, outputs: Any, **kwargs: Any) -> None:
        self.seen.append(json.dumps(outputs, default=str))


def test_the_pin_reaches_no_tracer_and_no_stored_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    recorder = _Recorder()
    monkeypatch.setattr(run_executor, "build_tracing_callbacks", lambda *_: [recorder])
    ctx = build_sentinel_test_context(tmp_path)

    run_id = ctx.client.post(
        "/chat",
        json={"question": "Why is my bill higher?", "account_id": ctx.account_id, "pin": ctx.pin},
    ).json()["id"]

    # Non-vacuous: the recorder really did see the run's inputs and outputs.
    assert any(ctx.account_id in entry for entry in recorder.seen)
    assert any('"identity"' in entry for entry in recorder.seen)
    assert not [e[:120] for e in recorder.seen if f'"{ctx.pin}"' in e]

    stored = " ".join(ev.payload_json for ev in ctx.run_store.get_events(run_id))
    assert f'"{ctx.pin}"' not in stored
