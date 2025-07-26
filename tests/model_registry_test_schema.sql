-- SQLite DB for model registry audit log export test
-- This file is created by test_admin_agent for use as a valid SQLite DB.
-- Table: audit_events
CREATE TABLE IF NOT EXISTS audit_events (
    sequence_number INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_id TEXT UNIQUE NOT NULL,
    action_name TEXT NOT NULL,
    status TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    risk_tier TEXT NOT NULL,
    requires_approval BOOLEAN NOT NULL,
    human_decision TEXT,
    sop_reference TEXT NOT NULL,
    primary_hash TEXT,
    chain_hash TEXT,
    tamper_seal TEXT,
    signature BLOB,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
