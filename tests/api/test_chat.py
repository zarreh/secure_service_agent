"""Chat endpoints: create a run, read its durable record and cost, and
stream its events to completion (docs/PLAN.md Phase 4). The graph is stubbed
offline and always passes review, so the happy path lands on a completed
run with the specialist's draft as its response."""

from __future__ import annotations

import json
from pathlib import Path

from tests.api._sentinel_client import build_sentinel_test_context


def test_create_then_get_returns_completed_record(tmp_path: Path) -> None:
    ctx = build_sentinel_test_context(tmp_path)
    create = ctx.client.post(
        "/chat",
        json={"question": "Why is my bill higher?", "account_id": ctx.account_id, "pin": ctx.pin},
    )
    assert create.status_code == 202
    payload = create.json()
    assert payload["status"] == "running"
    run_id = payload["id"]

    record = ctx.client.get(f"/chat/{run_id}").json()
    assert record["status"] == "completed"
    assert record["question"] == "Why is my bill higher?"
    assert record["account_id"] == ctx.account_id
    assert record["response"] == "Here is your answer."
    assert "total_cost_usd" in record
    assert isinstance(record["costs"], list)


def test_get_unknown_chat_is_404(tmp_path: Path) -> None:
    ctx = build_sentinel_test_context(tmp_path)
    assert ctx.client.get("/chat/nope").status_code == 404


def test_create_response_never_echoes_the_pin(tmp_path: Path) -> None:
    ctx = build_sentinel_test_context(tmp_path)
    create = ctx.client.post(
        "/chat",
        json={"question": "What's my plan?", "account_id": ctx.account_id, "pin": ctx.pin},
    )
    assert ctx.pin not in create.text


def test_events_replay_to_end(tmp_path: Path) -> None:
    ctx = build_sentinel_test_context(tmp_path)
    run_id = ctx.client.post(
        "/chat",
        json={"question": "Why is my bill higher?", "account_id": ctx.account_id, "pin": ctx.pin},
    ).json()["id"]

    resp = ctx.client.get(f"/chat/{run_id}/events")
    assert resp.status_code == 200
    events = [
        json.loads(line.removeprefix("data:").strip())
        for line in resp.text.splitlines()
        if line.startswith("data:")
    ]
    nodes = [e["node"] for e in events]
    assert "guardrail" in nodes
    assert "identity_gate" in nodes
    assert "publish" in nodes
    assert nodes[-1] == "__end__"
    assert events[-1]["output"]["status"] == "completed"


def test_events_never_persist_the_pin(tmp_path: Path) -> None:
    ctx = build_sentinel_test_context(tmp_path)
    run_id = ctx.client.post(
        "/chat",
        json={"question": "Why is my bill higher?", "account_id": ctx.account_id, "pin": ctx.pin},
    ).json()["id"]

    resp = ctx.client.get(f"/chat/{run_id}/events")
    assert ctx.pin not in resp.text


def test_events_for_unknown_chat_is_404(tmp_path: Path) -> None:
    ctx = build_sentinel_test_context(tmp_path)
    assert ctx.client.get("/chat/nope/events").status_code == 404


def test_wrong_pin_completes_with_a_verification_required_response(tmp_path: Path) -> None:
    ctx = build_sentinel_test_context(tmp_path)
    run_id = ctx.client.post(
        "/chat",
        json={"question": "What's my plan?", "account_id": ctx.account_id, "pin": "0000000"},
    ).json()["id"]

    record = ctx.client.get(f"/chat/{run_id}").json()
    assert record["status"] == "completed"
    assert "verify" in record["response"].lower()


def test_a_blocked_leak_is_not_quoted_anywhere_the_client_can_read(tmp_path: Path) -> None:
    """A guardrail verdict is streamed to the client, so its reason must not repeat
    the very value it blocked (another customer's id or name)."""
    from sentinel.schemas.specialist import SpecialistResponse

    class _LeakyChain:
        def __init__(self, text: str) -> None:
            self._text = text

        def invoke(self, input: dict[str, object]) -> SpecialistResponse:
            return SpecialistResponse(draft=self._text, citations=[])

    (tmp_path / "probe").mkdir()
    probe = build_sentinel_test_context(tmp_path / "probe")
    other_id = next(i for i in probe.account_store.account_ids() if i != probe.account_id)
    other = probe.account_store.get_account(other_id)
    assert other is not None

    for index, leak in enumerate(
        (f"This matches {other_id}.", f"{other.customer_name} has the same plan.")
    ):
        workdir = tmp_path / f"leak{index}"
        workdir.mkdir()
        ctx = build_sentinel_test_context(workdir, specialist_chain=_LeakyChain(leak))
        run_id = ctx.client.post(
            "/chat",
            json={"question": "Compare my plan", "account_id": ctx.account_id, "pin": ctx.pin},
        ).json()["id"]

        everything = (
            ctx.client.get(f"/chat/{run_id}/events").text + ctx.client.get(f"/chat/{run_id}").text
        )
        assert '"blocked": true' in everything or "blocked=True" in everything
        assert other_id not in everything
        assert other.customer_name not in everything
