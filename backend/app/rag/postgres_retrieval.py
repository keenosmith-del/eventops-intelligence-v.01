import numpy as np
import psycopg
from psycopg.rows import dict_row

from app.models.domain import KnowledgeRecord
from app.rag.retrieval import (
    POLICY_CATEGORIES,
    EmbeddingProvider,
    SearchHit,
)


class PostgresSemanticRetriever:
    """Search persistent pgvector embeddings using cosine distance."""

    def __init__(
        self,
        connection: psycopg.Connection,
        embedding_model: EmbeddingProvider,
    ):
        self.connection = connection
        self.embedding_model = embedding_model

    def _event_exists(self, event_id: str) -> bool:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM knowledge_records
                    WHERE record_type = 'event'
                      AND event_id = %s
                )
                """,
                (event_id,),
            )

            return bool(cursor.fetchone()[0])

    @staticmethod
    def _vector_literal(vector: np.ndarray) -> str:
        array = np.asarray(vector, dtype=np.float32)

        if array.shape != (384,):
            raise ValueError("Query embedding must contain 384 dimensions")

        if not np.isfinite(array).all():
            raise ValueError("Query embedding contains non-finite values")

        if np.linalg.norm(array) == 0:
            raise ValueError("Query embedding cannot be a zero vector")

        return "[" + ",".join(str(float(value)) for value in array) + "]"

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

            if not self._event_exists(event_id):
                return []

        query_vector = self.embedding_model.embed_query(query)

        vector_literal = self._vector_literal(query_vector)

        conditions = ["embedding IS NOT NULL"]
        parameters = [vector_literal]

        if record_type is not None:
            conditions.append("record_type = %s")
            parameters.append(record_type)

        if participant_status is not None:
            conditions.append(
                "record_type = 'participant' "
                "AND metadata->>'participant_status' = %s"
            )
            parameters.append(participant_status)

        if policy_category is not None:
            conditions.append(
                "record_type = 'policy' " "AND metadata->>'policy_category' = %s"
            )
            parameters.append(policy_category)

        if event_id is not None:
            conditions.append("""
                (
                    event_id = %s

                    OR (
                        record_type = 'policy'
                        AND event_id IS NULL
                    )

                    OR (
                        record_type = 'participant'
                        AND %s = ANY(
                            string_to_array(
                                COALESCE(
                                    metadata->>'event_ids',
                                    ''
                                ),
                                ','
                            )
                        )
                    )
                )
                """)

            parameters.extend([event_id, event_id])

        where_clause = " AND ".join(conditions)

        statement = f"""
            SELECT
                document_id,
                record_id,
                content,
                event_id,
                metadata,
                1 - (embedding <=> %s::vector) AS score
            FROM knowledge_records
            WHERE {where_clause}
            ORDER BY
                embedding <=> %s::vector ASC,
                document_id ASC,
                record_id ASC
            LIMIT %s
        """

        parameters.extend([vector_literal, top_k])

        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(statement, parameters)
            rows = cursor.fetchall()

        results: list[SearchHit] = []

        for row in rows:
            score = float(row.pop("score"))

            record = KnowledgeRecord.model_validate(row)

            results.append(
                SearchHit(
                    record=record,
                    score=score,
                )
            )

        return results
