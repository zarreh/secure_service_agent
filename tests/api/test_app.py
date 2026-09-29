"""API skeleton: health, the walking-skeleton stream, and the two request-level
controls that exist from day one -- a body-size cap and a per-route rate limit
(OWASP LLM10)."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from secureagent.api.main import app
from secureagent.settings import get_settings


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _events(text: str) -> list[dict[str, object]]:
    return [
        json.loads(line.removeprefix("data:").strip())
        for line in text.splitlines()
        if line.startswith("data:")
    ]


def test_health(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Correlation-ID"]


def test_skeleton_streams_one_event_per_node_then_ends(client: TestClient) -> None:
    response = client.post("/conversations/stream", json={"question": "hello"})
    assert response.status_code == 200
    nodes = [e["node"] for e in _events(response.text)]
    # Only genuine node boundaries: no graph-level or routing-function events.
    assert nodes == ["echo", "done", "__end__"]


def test_empty_question_is_rejected(client: TestClient) -> None:
    assert client.post("/conversations/stream", json={"question": ""}).status_code == 422


def test_oversized_body_is_rejected_before_routing(client: TestClient) -> None:
    body = json.dumps({"question": "x" * (get_settings().max_request_body_bytes + 1)})
    response = client.post(
        "/conversations/stream", content=body, headers={"content-type": "application/json"}
    )
    assert response.status_code == 413


def test_rate_limit_is_enforced() -> None:
    limited = TestClient(app)
    limit = get_settings().rate_limit_per_minute
    app.state.limiter.reset()
    statuses = [limited.get("/healthz").status_code for _ in range(limit + 3)]
    assert 429 in statuses
    assert statuses[:limit] == [200] * limit
    app.state.limiter.reset()
