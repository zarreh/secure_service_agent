from __future__ import annotations

import json
from pathlib import Path

from sentinel.api.client_view import project_for_client
from tests.api._sentinel_client import build_sentinel_test_context


def test_the_client_view_is_an_allow_list() -> None:
    projected = project_for_client(
        {
            "draft": "unvetted model text",
            "specialist_context": "account and plan record",
            "escalation": {"issue": "x"},
            "history": ["prior"],
            "a_field_added_later": "hidden until someone decides it is safe",
            "output_verdict": {"blocked": True},
            "response": "ok",
        }
    )
    assert projected == {"output_verdict": {"blocked": True}, "response": "ok"}


def test_non_dict_outputs_pass_through() -> None:
    assert project_for_client(None) is None


def test_the_replayed_stream_hides_the_draft_but_the_audit_log_keeps_it(tmp_path: Path) -> None:
    ctx = build_sentinel_test_context(tmp_path)
    run_id = ctx.client.post(
        "/chat",
        json={"question": "Why is my bill higher?", "account_id": ctx.account_id, "pin": ctx.pin},
    ).json()["id"]

    streamed = ctx.client.get(f"/chat/{run_id}/events").text
    assert '"draft"' not in streamed
    assert '"specialist_context"' not in streamed

    audit = [json.loads(e.payload_json) for e in ctx.run_store.get_events(run_id)]
    assert any(isinstance(payload, dict) and "draft" in payload for payload in audit)
