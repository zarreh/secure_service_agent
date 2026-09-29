"""Qdrant-backed policy search plus the embedder seam.

The embedder is injected. Production wires a real embedding model; tests and the
offline demo use `HashingEmbedder`, a deterministic bag-of-words hash. It is
lexical, not semantic, and is labelled as such: retrieval-quality claims would
need a real embedder and are not made here.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Sequence
from typing import Protocol

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from secureagent.retrieval.search import PolicyPassage
from secureagent.store.policy_docs import PolicyDoc

_TOKEN = re.compile(r"[a-z0-9]+")


class Embedder(Protocol):
    dimension: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class HashingEmbedder:
    """Deterministic, offline, lexical. Same text always yields the same vector."""

    def __init__(self, dimension: int = 256) -> None:
        self.dimension = dimension

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._one(text) for text in texts]

    def _one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        for token in _TOKEN.findall(text.lower()):
            bucket = int.from_bytes(hashlib.sha256(token.encode()).digest()[:4], "big")
            vector[bucket % self.dimension] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]


class QdrantPolicySearcher:
    """Read path over an indexed policy corpus. Passages are returned as data;
    wrapping them as untrusted content is the caller's job (graph layer)."""

    def __init__(
        self,
        client: QdrantClient,
        embedder: Embedder,
        collection: str = "policy",
    ) -> None:
        self._client = client
        self._embedder = embedder
        self._collection = collection

    def index(self, docs: Sequence[PolicyDoc]) -> None:
        if self._client.collection_exists(self._collection):
            self._client.delete_collection(self._collection)
        self._client.create_collection(
            self._collection,
            vectors_config=VectorParams(size=self._embedder.dimension, distance=Distance.COSINE),
        )
        vectors = self._embedder.embed([f"{d.title}\n{d.body}" for d in docs])
        self._client.upsert(
            self._collection,
            points=[
                PointStruct(
                    id=i,
                    vector=vector,
                    payload={"doc_id": d.doc_id, "title": d.title, "text": d.body},
                )
                for i, (d, vector) in enumerate(zip(docs, vectors, strict=True))
            ],
        )

    def search(self, query: str, *, limit: int) -> list[PolicyPassage]:
        [vector] = self._embedder.embed([query])
        result = self._client.query_points(self._collection, query=vector, limit=limit)
        return [
            PolicyPassage(
                doc_id=str(p.payload["doc_id"]),
                title=str(p.payload["title"]),
                text=str(p.payload["text"]),
                score=float(p.score),
            )
            for p in result.points
            if p.payload is not None
        ]
