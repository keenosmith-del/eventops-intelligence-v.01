-- Server-to-server delivery ledger. Never stores credentials or reviewer tokens.
CREATE TABLE IF NOT EXISTS n8n_deliveries (
    idempotency_key UUID PRIMARY KEY,
    payload_hash TEXT NOT NULL,
    run_id UUID NOT NULL UNIQUE REFERENCES agent_runs(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
