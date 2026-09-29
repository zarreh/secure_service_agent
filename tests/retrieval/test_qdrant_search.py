from pathlib import Path

from qdrant_client import QdrantClient

from secureagent.retrieval.qdrant_search import HashingEmbedder, QdrantPolicySearcher
from secureagent.store.policy_docs import load_policy_docs

POLICY_DIR = Path(__file__).parents[2] / "data" / "policy"


def _searcher() -> QdrantPolicySearcher:
    searcher = QdrantPolicySearcher(QdrantClient(":memory:"), HashingEmbedder())
    searcher.index(load_policy_docs(POLICY_DIR))
    return searcher


def test_embedder_is_deterministic_and_unit_length() -> None:
    embedder = HashingEmbedder()
    [a] = embedder.embed(["roaming charges abroad"])
    [b] = embedder.embed(["roaming charges abroad"])
    assert a == b
    assert abs(sum(v * v for v in a) - 1.0) < 1e-9


def test_search_returns_ranked_passages_up_to_limit() -> None:
    passages = _searcher().search("roaming charges when travelling abroad", limit=3)
    assert 0 < len(passages) <= 3
    scores = [p.score for p in passages]
    assert scores == sorted(scores, reverse=True)


def test_search_finds_the_relevant_document() -> None:
    docs = load_policy_docs(POLICY_DIR)
    target = next(d for d in docs if "roaming" in d.doc_id)
    passages = _searcher().search(f"{target.title} {target.body[:80]}", limit=3)
    assert target.doc_id in {p.doc_id for p in passages}


def test_reindexing_replaces_rather_than_duplicates() -> None:
    searcher = _searcher()
    searcher.index(load_policy_docs(POLICY_DIR))
    ids = [p.doc_id for p in searcher.search("billing", limit=50)]
    assert len(ids) == len(set(ids))
