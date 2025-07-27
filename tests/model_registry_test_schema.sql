-- SQLite DB for model registry audit log export test
-- This file is created by test_admin_agent for use as a valid SQLite DB.
DROP TABLE IF EXISTS audit_events;
CREATE TABLE audit_events (
    sequence_number INTEGER PRIMARY KEY,
    event_type TEXT NOT NULL,
    event_data TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
