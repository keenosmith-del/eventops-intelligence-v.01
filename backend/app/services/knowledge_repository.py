from collections.abc import Sequence

import numpy as np
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.models.domain import KnowledgeRecord

# This SQL statement performs an upsert operation on the knowledge_records table. It inserts a new record if it doesn't
# exist, or updates the existing record if it does. The update is conditional, only changing the embedding to NULL if the
# content or source_sha256 has changed, ensuring that embeddings are recalculated when necessary.
UPSERT_SQL = """
INSERT INTO knowledge_records (
    document_id,
    record_id,
    content,
    event_id,
    record_type,
    metadata,
    source_sha256
)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (document_id, record_id)
DO UPDATE SET
    content = EXCLUDED.content,
    event_id = EXCLUDED.event_id,
    record_type = EXCLUDED.record_type,
    metadata = EXCLUDED.metadata,
    source_sha256 = EXCLUDED.source_sha256,
    embedding = CASE
        WHEN knowledge_records.content
             IS DISTINCT FROM EXCLUDED.content
          OR knowledge_records.source_sha256
             IS DISTINCT FROM EXCLUDED.source_sha256
        THEN NULL
        ELSE knowledge_records.embedding
    END,
    updated_at = NOW()
WHERE
    knowledge_records.content
        IS DISTINCT FROM EXCLUDED.content
    OR knowledge_records.event_id
        IS DISTINCT FROM EXCLUDED.event_id
    OR knowledge_records.record_type
        IS DISTINCT FROM EXCLUDED.record_type
    OR knowledge_records.metadata
        IS DISTINCT FROM EXCLUDED.metadata
    OR knowledge_records.source_sha256
        IS DISTINCT FROM EXCLUDED.source_sha256
"""


SELECT_COLUMNS = """
    document_id,
    record_id,
    content,
    event_id,
    metadata
"""


class KnowledgeRepository:
    """Persist and retrieve RAG knowledge in PostgreSQL."""

    def __init__(self, connection: psycopg.Connection):
        self.connection = connection

    def upsert_records(
        self,
        records: Sequence[KnowledgeRecord],
    ) -> int:
        identities = [(record.document_id, record.record_id) for record in records]

        if len(identities) != len(set(identities)):
            raise ValueError("Duplicate knowledge records in input batch")

        required_metadata = {
            "record_type",
            "source_sha256",
        }

        for record in records:
            if not required_metadata.issubset(record.metadata):
                raise ValueError(f"Incomplete metadata for {record.record_id}")

        changed = 0

        with self.connection.cursor() as cursor:
            for record in records:
                metadata = record.metadata

                cursor.execute(
                    UPSERT_SQL,
                    (
                        record.document_id,
                        record.record_id,
                        record.content,
                        record.event_id,
                        metadata["record_type"],
                        Jsonb(metadata),
                        metadata["source_sha256"],
                    ),
                )

                changed += cursor.rowcount

        return changed

    def get_record(
        self,
        document_id: str,
        record_id: str,
    ) -> KnowledgeRecord | None:
        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                f"""
                SELECT {SELECT_COLUMNS}
                FROM knowledge_records
                WHERE document_id = %s
                  AND record_id = %s
                """,
                (document_id, record_id),
            )

            row = cursor.fetchone()

        if row is None:
            return None

        return KnowledgeRecord.model_validate(row)

    def count_records(self) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM knowledge_records")

            return cursor.fetchone()[0]

    def list_unembedded_records(
        self,
    ) -> list[KnowledgeRecord]:
        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(f"""
                SELECT {SELECT_COLUMNS}
                FROM knowledge_records
                WHERE embedding IS NULL
                ORDER BY document_id, record_id
                """)

            rows = cursor.fetchall()

        return [KnowledgeRecord.model_validate(row) for row in rows]

    def save_embedding(
        self,
        document_id: str,
        record_id: str,
        embedding: Sequence[float] | np.ndarray,
    ) -> None:
        vector = np.asarray(
            embedding,
            dtype=np.float32,
        )

        if vector.shape != (384,):
            raise ValueError("Embedding must contain exactly 384 dimensions")

        if not np.isfinite(vector).all():
            raise ValueError("Embedding contains non-finite values")

        if np.linalg.norm(vector) == 0:
            raise ValueError("Embedding cannot be a zero vector")

        vector_literal = "[" + ",".join(str(float(value)) for value in vector) + "]"

        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE knowledge_records
                SET embedding = %s::vector(384),
                    updated_at = NOW()
                WHERE document_id = %s
                  AND record_id = %s
                """,
                (
                    vector_literal,
                    document_id,
                    record_id,
                ),
            )

            if cursor.rowcount != 1:
                raise ValueError(
                    f"Knowledge record not found: " f"{document_id}/{record_id}"
                )
