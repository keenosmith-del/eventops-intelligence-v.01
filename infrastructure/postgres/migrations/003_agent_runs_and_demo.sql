-- Additive migration: persisted orchestration, results, demo isolation and quotas.
CREATE TABLE IF NOT EXISTS demo_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token_hash TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL DEFAULT NOW() + INTERVAL '24 hours'
);
CREATE TABLE IF NOT EXISTS demo_objects (
    object_id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES demo_sessions(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('conversation', 'run'))
);
CREATE INDEX IF NOT EXISTS idx_demo_objects_session ON demo_objects(session_id);
CREATE TABLE IF NOT EXISTS demo_usage (
    bucket TEXT NOT NULL,
    day DATE NOT NULL DEFAULT CURRENT_DATE,
    requests INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (bucket, day)
);
CREATE TABLE IF NOT EXISTS agent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id TEXT NOT NULL,
    max_records INTEGER NOT NULL CHECK (max_records BETWEEN 1 AND 30),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','running','completed','partial','failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    error TEXT,
    results JSONB NOT NULL DEFAULT '[]'::jsonb,
    summary JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE TABLE IF NOT EXISTS agent_steps (
    run_id UUID NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    node_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','running','completed','failed','skipped')),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    inputs JSONB NOT NULL DEFAULT '{}'::jsonb,
    outputs JSONB NOT NULL DEFAULT '{}'::jsonb,
    error TEXT,
    PRIMARY KEY (run_id, node_id)
);
CREATE INDEX IF NOT EXISTS idx_agent_runs_created ON agent_runs(created_at DESC);
