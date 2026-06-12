-- GigGuard Database Schema
-- SQLite 3 | Python 3.11
-- All IDs are UUIDs (TEXT)

CREATE TABLE IF NOT EXISTS sessions (
    id                   TEXT PRIMARY KEY,
    phone_number         TEXT NOT NULL UNIQUE,
    worker_name          TEXT,
    state                TEXT NOT NULL DEFAULT 'intake',
    language             TEXT NOT NULL DEFAULT 'en',
    created_at           TEXT NOT NULL,
    last_active          TEXT NOT NULL,
    conversation_history TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS cases (
    id               TEXT PRIMARY KEY,
    session_id       TEXT NOT NULL,
    platform         TEXT,
    event_type       TEXT,
    date_occurred    TEXT,
    amount_affected  REAL,
    case_status      TEXT NOT NULL DEFAULT 'open',
    filing_channel   TEXT,
    reference_id     TEXT,
    created_at       TEXT NOT NULL,
    resolved_at      TEXT,
    resolution_type  TEXT,
    outcome          TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS evidence (
    id             TEXT PRIMARY KEY,
    case_id        TEXT NOT NULL,
    evidence_type  TEXT,
    file_url       TEXT,
    extracted_data TEXT NOT NULL DEFAULT '{}',
    created_at     TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id)
);