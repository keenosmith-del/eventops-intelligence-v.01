
-- EventOps Intelligence
-- Migration 002: Persistent RAG conversations

CREATE TABLE IF NOT EXISTS rag_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    title TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_conversation_title CHECK (
        title IS NULL OR LENGTH(TRIM(title)) > 0
    )
);


CREATE TABLE IF NOT EXISTS rag_messages (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    conversation_id UUID NOT NULL
        REFERENCES rag_conversations(id)
        ON DELETE CASCADE,

    role TEXT NOT NULL,
    kind TEXT NOT NULL,

    content TEXT NOT NULL,

    query_plan JSONB,
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_message_role CHECK (
        role IN ('user', 'assistant')
    ),

    CONSTRAINT valid_message_kind CHECK (
        (
            role = 'user'
            AND kind = 'question'
        )
        OR
        (
            role = 'assistant'
            AND kind IN ('retrieval', 'answer')
        )
    ),

    CONSTRAINT non_empty_message CHECK (
        LENGTH(TRIM(content)) > 0
    ),

    CONSTRAINT valid_evidence_json CHECK (
        jsonb_typeof(evidence) = 'array'
    ),

    CONSTRAINT valid_query_plan_json CHECK (
        query_plan IS NULL
        OR jsonb_typeof(query_plan) = 'object'
    )
);


CREATE INDEX IF NOT EXISTS idx_rag_messages_conversation
ON rag_messages (conversation_id, id);


CREATE INDEX IF NOT EXISTS idx_rag_conversations_updated
ON rag_conversations (updated_at DESC);
