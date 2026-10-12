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

        # Validate that the embedding has the correct shape and contains valid values
        if array.shape != (384,):
            raise ValueError("Query embedding must contain 384 dimensions")

        # Validate that the embedding contains finite values and is not a zero vector
        if not np.isfinite(array).all():
            raise ValueError("Query embedding contains non-finite values")

        # Validate that the embedding is not a zero vector
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

        # Validate that top_k is a positive integer
        if type(top_k) is not int or top_k < 1:
            raise ValueError("top_k must be a positive integer")

        # Validate that record_type, participant_status, and policy_category are valid if provided
        if record_type is not None and record_type not in {
            "event",
            "policy",
            "participant",
        }:
            raise ValueError("Unknown record type")

        # Validate that participant_status and policy_category are valid if provided
        if participant_status is not None and participant_status not in {
            "active",
            "inactive",
        }:
            raise ValueError("Unknown participant status")

        # Validate that policy_category is valid if provided
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

        # Validate that the record_type, participant_status, policy_category, and event_id filters are applied correctly
        if record_type is not None:
            conditions.append("record_type = %s")
            parameters.append(record_type)

        # Validate that the participant_status filter is applied correctly
        if participant_status is not None:
            conditions.append(
                "record_type = 'participant' "
                "AND metadata->>'participant_status' = %s"
            )
            parameters.append(participant_status)

        # Validate that the policy_category filter is applied correctly
        if policy_category is not None:
            conditions.append(
                "record_type = 'policy' " "AND metadata->>'policy_category' = %s"
            )
            parameters.append(policy_category)

        # Validate that the event_id filter is applied correctly
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

        # Validate that the SQL query is executed correctly and returns the expected results
        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(statement, parameters)
            rows = cursor.fetchall()

        results: list[SearchHit] = []

        # Validate that the retrieved rows are processed correctly into SearchHit objects
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
