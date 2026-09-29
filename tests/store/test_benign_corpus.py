"""The benign corpus is well formed, and free of the attacks it is measured against."""

from __future__ import annotations

from collections import Counter

from data.benign_corpus import BENIGN_CORPUS


def test_the_corpus_is_large_enough_to_measure_a_rate() -> None:
    assert len(BENIGN_CORPUS) >= 120


def test_the_documented_corpus_size_is_the_real_one() -> None:
    # docs/PLAN.md §14 quotes this figure; changing the corpus must be a
    # deliberate edit to both, not a silent drift.
    assert len(BENIGN_CORPUS) == 122


def test_messages_are_unique_and_non_empty() -> None:
    texts = [message.text for message in BENIGN_CORPUS]
    assert all(text.strip() for text in texts)
    assert len(set(texts)) == len(texts)


def test_every_category_is_represented() -> None:
    counts = Counter(message.category for message in BENIGN_CORPUS)
    assert set(counts) == {
        "billing",
        "network",
        "account",
        "policy",
        "general",
        "angry",
        "technical",
        "hard_negative",
    }
    assert counts["hard_negative"] >= 15  # the ones that expose over-blocking


def test_messages_fit_comfortably_under_the_request_size_cap() -> None:
    assert max(len(message.text) for message in BENIGN_CORPUS) < 400


def test_no_message_contains_a_credential_or_a_real_looking_identifier() -> None:
    """Benign messages must not smuggle in what the output checks look for."""
    for message in BENIGN_CORPUS:
        assert "ACCT_" not in message.text
        assert "555-" not in message.text
