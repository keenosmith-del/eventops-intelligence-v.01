
-- EventOps Intelligence
-- Migration 001: Persistent structured knowledge records

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS knowledge_records (
    document_id TEXT NOT NULL,
    record_id TEXT NOT NULL,

    content TEXT NOT NULL,
    event_id TEXT,

    record_type TEXT NOT NULL,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    source_sha256 CHAR(64) NOT NULL,

    embedding VECTOR(384),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (document_id, record_id),

    CONSTRAINT valid_record_type CHECK (
        record_type IN (
            'event',
            'policy',
            'participant'
        )
    ),

    CONSTRAINT valid_source_fingerprint CHECK (
        source_sha256 ~ '^[0-9a-f]{64}$'
    ),

    CONSTRAINT non_empty_content CHECK (
        LENGTH(TRIM(content)) > 0
    )
);

CREATE INDEX IF NOT EXISTS idx_knowledge_event
ON knowledge_records (event_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_record_type
ON knowledge_records (record_type);

CREATE INDEX IF NOT EXISTS idx_knowledge_metadata
ON knowledge_records USING GIN (metadata);
