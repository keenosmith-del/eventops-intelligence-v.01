from dataclasses import dataclass
from typing import Protocol

import numpy as np

POLICY_CATEGORIES = frozenset(
    {
        "identity",
        "cancellation",
        "check_in",
        "eligibility",
        "transfers",
        "recording",
        "registration",
    }
)


from app.models.domain import KnowledgeRecord


# This protocol defines the interface for embedding providers. Any class that implements this protocol must
# provide methods to embed documents and queries, returning numpy arrays of embeddings.
class EmbeddingProvider(Protocol):
    def embed_documents(
        self,
        texts: list[str],
    ) -> np.ndarray: ...

    def embed_query(
        self,
        query: str,
    ) -> np.ndarray: ...


@dataclass(frozen=True)
class SearchHit:
    record: KnowledgeRecord
    score: float


class SemanticRetriever:
    """Rank structured knowledge records using cosine similarity."""

    def __init__(
        self,
        records: list[KnowledgeRecord],
        embedding_model: EmbeddingProvider,
    ):
        if not records:
            raise ValueError("Cannot build an index without knowledge records")

        self._records = [record.model_copy(deep=True) for record in records]

        self._known_event_ids = {
            record.event_id
            for record in self._records
            if record.metadata.get("record_type") == "event"
            and record.event_id is not None
        }

        identities = [
            (record.document_id, record.record_id) for record in self._records
        ]

        if len(identities) != len(set(identities)):
            raise ValueError("Duplicate knowledge record IDs")

        vectors = np.asarray(
            embedding_model.embed_documents(
                [record.content for record in self._records]
            ),
            dtype=np.float32,
        )

        if (
            vectors.ndim != 2
            or vectors.shape[0] != len(self._records)
            or vectors.shape[1] == 0
            or not np.isfinite(vectors).all()
        ):
            raise ValueError("Invalid document embeddings")

        norms = np.linalg.norm(
            vectors,
            axis=1,
            keepdims=True,
        )

        if np.any(norms == 0):
            raise ValueError("Document embeddings cannot be zero")

        self._vectors = vectors / norms
        self._embedding_model = embedding_model

    @property
    def record_count(self) -> int:
        return len(self._records)

    def _matches_filters(
        self,
        record: KnowledgeRecord,
        record_type: str | None,
        event_id: str | None,
        participant_status: str | None,
        policy_category: str | None,
    ) -> bool:
        kind = record.metadata.get("record_type")

        if record_type is not None and kind != record_type:
            return False

        if participant_status is not None:
            if (
                kind != "participant"
                or record.metadata.get("participant_status") != participant_status
            ):
                return False

        if policy_category is not None:
            if (
                kind != "policy"
                or record.metadata.get("policy_category") != policy_category
            ):
                return False

        if event_id is None:
            return True

        if record.event_id == event_id:
            return True

        if kind == "policy" and record.event_id is None:
            return True

        if kind == "participant":
            registered_events = record.metadata.get("event_ids", "").split(",")

            return event_id in registered_events

        return False

    def search(
        self,
        query: str,
        top_k: int = 5,
        record_type: str | None = None,
        event_id: str | None = None,
        participant_status: str | None = None,
        policy_category: str | None = None,
    ) -> list[SearchHit]:

        if not isinstance(query, str) or not query.strip():
            raise ValueError("Search query cannot be empty")

        if type(top_k) is not int or top_k < 1:
            raise ValueError("top_k must be a positive integer")

        if record_type is not None and record_type not in {
            "event",
            "policy",
            "participant",
        }:
            raise ValueError("Unknown record type")

        if participant_status is not None and participant_status not in {
            "active",
            "inactive",
        }:
            raise ValueError("Unknown participant status")

        if policy_category is not None and policy_category not in POLICY_CATEGORIES:
            raise ValueError("Unknown policy category")

        if event_id is not None:
            if not isinstance(event_id, str) or not event_id.strip():
                raise ValueError("event_id cannot be empty")

            event_id = event_id.strip().upper()

            if event_id not in self._known_event_ids:
                return []

        eligible_indices = [
            index
            for index, record in enumerate(self._records)
            if self._matches_filters(
                record,
                record_type,
                event_id,
                participant_status,
                policy_category,
            )
        ]

        if not eligible_indices:
            return []

        query_vector = np.asarray(
            self._embedding_model.embed_query(query),
            dtype=np.float32,
        )

        if (
            query_vector.ndim != 1
            or query_vector.shape[0] != self._vectors.shape[1]
            or not np.isfinite(query_vector).all()
        ):
            raise ValueError("Invalid query embedding")

        query_norm = np.linalg.norm(query_vector)

        if query_norm == 0:
            raise ValueError("Query embedding cannot be zero")

        normalized_query = query_vector / query_norm

        scored_records = [
            SearchHit(
                record=self._records[index].model_copy(deep=True),
                score=float(
                    np.dot(
                        self._vectors[index],
                        normalized_query,
                    )
                ),
            )
            for index in eligible_indices
        ]

        scored_records.sort(
            key=lambda hit: (
                -hit.score,
                hit.record.document_id,
                hit.record.record_id,
            )
        )

        return scored_records[:top_k]
