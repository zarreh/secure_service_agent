from pathlib import Path

from zarreh_agentkit.cost import CostEntry

from sentinel.store.run_store import RunStore


def test_create_then_get_returns_a_running_record(tmp_path: Path) -> None:
    store = RunStore(tmp_path / "runs.db")
    store.create_run("run-1", "question text", "ACCT_2000")

    run = store.get_run("run-1")

    assert run is not None
    assert run.status == "running"
    assert run.question == "question text"
    assert run.account_id == "ACCT_2000"
    assert run.response is None


def test_get_unknown_run_returns_none(tmp_path: Path) -> None:
    store = RunStore(tmp_path / "runs.db")
    assert store.get_run("nope") is None


def test_complete_run_sets_status_and_response(tmp_path: Path) -> None:
    store = RunStore(tmp_path / "runs.db")
    store.create_run("run-1", "q", "ACCT_2000")

    store.complete_run("run-1", "the answer")

    run = store.get_run("run-1")
    assert run is not None
    assert run.status == "completed"
    assert run.response == "the answer"


def test_fail_run_sets_status_and_error(tmp_path: Path) -> None:
    store = RunStore(tmp_path / "runs.db")
    store.create_run("run-1", "q", "ACCT_2000")

    store.fail_run("run-1", "boom")

    run = store.get_run("run-1")
    assert run is not None
    assert run.status == "failed"
    assert run.error == "boom"


def test_events_replay_in_sequence_order(tmp_path: Path) -> None:
    store = RunStore(tmp_path / "runs.db")
    store.create_run("run-1", "q", "ACCT_2000")
    store.append_event("run-1", 0, "guardrail", '{"blocked": false}')
    store.append_event("run-1", 1, "identity_gate", '{"verified": true}')

    events = store.get_events("run-1")

    assert [e.node for e in events] == ["guardrail", "identity_gate"]


def test_events_after_sequence_only_returns_newer_events(tmp_path: Path) -> None:
    store = RunStore(tmp_path / "runs.db")
    store.create_run("run-1", "q", "ACCT_2000")
    store.append_event("run-1", 0, "guardrail", "{}")
    store.append_event("run-1", 1, "identity_gate", "{}")

    events = store.get_events("run-1", after_sequence=0)

    assert [e.node for e in events] == ["identity_gate"]


def test_costs_round_trip(tmp_path: Path) -> None:
    store = RunStore(tmp_path / "runs.db")
    store.create_run("run-1", "q", "ACCT_2000")
    store.record_costs(
        "run-1",
        [
            CostEntry(
                node="supervisor",
                model="gpt-4o-mini",
                prompt_tokens=100,
                completion_tokens=20,
                cost_usd=0.001,
            )
        ],
    )

    costs = store.get_costs("run-1")

    assert len(costs) == 1
    assert costs[0].node == "supervisor"
    assert costs[0].cost_usd == 0.001
