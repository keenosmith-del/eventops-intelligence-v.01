from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.models.conversation import (
    Conversation,
    ConversationMessage,
)

CONVERSATION_COLUMNS = """
    id,
    title,
    created_at,
    updated_at
"""

MESSAGE_COLUMNS = """
    id,
    conversation_id,
    role,
    kind,
    content,
    query_plan,
    evidence,
    created_at
"""


class ConversationRepository:
    """Manage persistent RAG conversations and messages."""

    def __init__(self, connection: psycopg.Connection):
        self.connection = connection

    def create_conversation(
        self,
        title: str | None = None,
    ) -> Conversation:
        if title is not None:
            if not isinstance(title, str):
                raise ValueError("Conversation title must be text")

            title = title.strip()

            if not title or len(title) > 120:
                raise ValueError(
                    "Conversation title must contain " "between 1 and 120 characters"
                )

        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                f"""
                INSERT INTO rag_conversations (title)
                VALUES (%s)
                RETURNING {CONVERSATION_COLUMNS}
                """,
                (title,),
            )

            row = cursor.fetchone()

        return Conversation.model_validate(row)

    def get_conversation(
        self,
        conversation_id: UUID,
    ) -> Conversation | None:
        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                f"""
                SELECT {CONVERSATION_COLUMNS}
                FROM rag_conversations
                WHERE id = %s
                """,
                (conversation_id,),
            )

            row = cursor.fetchone()

        if row is None:
            return None

        return Conversation.model_validate(row)

    def list_recent_conversations(
        self,
        limit: int = 20,
    ) -> list[Conversation]:
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("Limit must be an integer between 1 and 100")

        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                f"""
                SELECT {CONVERSATION_COLUMNS}
                FROM rag_conversations
                ORDER BY updated_at DESC, id DESC
                LIMIT %s
                """,
                (limit,),
            )

            rows = cursor.fetchall()

        return [Conversation.model_validate(row) for row in rows]

    def list_messages(
        self,
        conversation_id: UUID,
    ) -> list[ConversationMessage]:
        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                f"""
                SELECT {MESSAGE_COLUMNS}
                FROM rag_messages
                WHERE conversation_id = %s
                ORDER BY id ASC
                """,
                (conversation_id,),
            )

            rows = cursor.fetchall()

        return [ConversationMessage.model_validate(row) for row in rows]

    def append_retrieval_exchange(
        self,
        conversation_id: UUID,
        question: str,
        query_plan: dict[str, Any],
        evidence: list[dict[str, Any]],
    ) -> list[ConversationMessage]:
        """
        Store a user question and its retrieval result.

        Both messages participate in the caller's
        database transaction.
        """

        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question cannot be empty")

        if not isinstance(query_plan, dict):
            raise ValueError("Query plan must be an object")

        if not isinstance(evidence, list) or len(evidence) > 20:
            raise ValueError("Evidence must be a list of at most 20 records")

        for item in evidence:
            if (
                not isinstance(item, dict)
                or not item.get("record_id")
                or not item.get("source_reference")
            ):
                raise ValueError(
                    "Evidence must contain a record ID " "and source reference"
                )

        question = question.strip()

        count = len(evidence)

        retrieval_summary = (
            f"Retrieved {count} evidence " f"{'record' if count == 1 else 'records'}."
        )

        messages = []

        with self.connection.cursor(row_factory=dict_row) as cursor:
            # Lock this conversation during the exchange.
            cursor.execute(
                """
                SELECT id
                FROM rag_conversations
                WHERE id = %s
                FOR UPDATE
                """,
                (conversation_id,),
            )

            if cursor.fetchone() is None:
                raise LookupError(f"Conversation not found: {conversation_id}")

            # Store the original user question.
            cursor.execute(
                f"""
                INSERT INTO rag_messages (
                    conversation_id,
                    role,
                    kind,
                    content
                )
                VALUES (%s, 'user', 'question', %s)
                RETURNING {MESSAGE_COLUMNS}
                """,
                (
                    conversation_id,
                    question,
                ),
            )

            messages.append(ConversationMessage.model_validate(cursor.fetchone()))

            # Store the retrieval result and its evidence.
            cursor.execute(
                f"""
                INSERT INTO rag_messages (
                    conversation_id,
                    role,
                    kind,
                    content,
                    query_plan,
                    evidence
                )
                VALUES (
                    %s,
                    'assistant',
                    'retrieval',
                    %s,
                    %s,
                    %s
                )
                RETURNING {MESSAGE_COLUMNS}
                """,
                (
                    conversation_id,
                    retrieval_summary,
                    Jsonb(query_plan),
                    Jsonb(evidence),
                ),
            )

            messages.append(ConversationMessage.model_validate(cursor.fetchone()))

            cursor.execute(
                """
                UPDATE rag_conversations
                SET updated_at = NOW()
                WHERE id = %s
                """,
                (conversation_id,),
            )

        return messages
