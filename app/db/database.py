"""
GigGuard — SQLite Database Layer
app/db/database.py

All IDs are UUID4 strings.
All timestamps are ISO 8601 UTC strings.
Connection is opened and closed per operation (safe for hackathon scale).
JSON fields (conversation_history, outcome, extracted_data) are stored
as TEXT and serialized/deserialized automatically by these functions.

Author: Person 4 (Database + Navigator + Dashboard)
"""

import sqlite3
import uuid
import json
from datetime import datetime, timezone
from pathlib import Path

# ── Path resolution ──────────────────────────────────────────────────────────
DB_PATH    = Path(__file__).parent / "gigguard.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def _get_connection() -> sqlite3.Connection:
    """Open a SQLite connection with row_factory set to Row for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _init_db() -> None:
    """Create all tables from schema.sql if they do not already exist."""
    conn = _get_connection()
    try:
        with open(SCHEMA_PATH, "r") as f:
            conn.executescript(f.read())
        conn.commit()
    finally:
        conn.close()


def _now() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row: sqlite3.Row | None) -> dict | None:
    """Convert a sqlite3.Row to a plain dict, deserializing JSON fields."""
    if row is None:
        return None
    d = dict(row)
    for field in ("conversation_history", "outcome", "extracted_data"):
        if field in d and isinstance(d[field], str):
            try:
                d[field] = json.loads(d[field])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


# ── Session functions ─────────────────────────────────────────────────────────

def get_session(phone_number: str) -> dict | None:
    """
    Retrieve a session by phone number.

    Args:
        phone_number: Worker's WhatsApp phone number (e.g. '+919876543210')

    Returns:
        Session dict with deserialized conversation_history, or None if not found.
    """
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM sessions WHERE phone_number = ?",
            (phone_number,)
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def create_session(phone_number: str) -> dict:
    """
    Create a new session for a worker.

    Args:
        phone_number: Worker's WhatsApp phone number.

    Returns:
        Newly created session dict.

    Raises:
        sqlite3.IntegrityError: If a session for this phone number already exists.
    """
    session_id = str(uuid.uuid4())
    now = _now()
    conn = _get_connection()
    try:
        conn.execute(
            """
            INSERT INTO sessions
                (id, phone_number, worker_name, state, language,
                 created_at, last_active, conversation_history)
            VALUES (?, ?, NULL, 'intake', 'en', ?, ?, '[]')
            """,
            (session_id, phone_number, now, now)
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def update_session(phone_number: str, updates: dict) -> dict:
    """
    Update one or more fields on an existing session.

    Automatically updates last_active to now.
    conversation_history is serialized to JSON if passed as a list/dict.

    Args:
        phone_number: Worker's WhatsApp phone number.
        updates: Dict of column names → new values.
                 Example: {'state': 'research', 'worker_name': 'Raju'}

    Returns:
        Updated session dict.

    Raises:
        ValueError: If no session exists for this phone number.
    """
    if not updates:
        return get_session(phone_number)

    updates["last_active"] = _now()

    # Serialize JSON fields if passed as Python objects
    if "conversation_history" in updates and not isinstance(
        updates["conversation_history"], str
    ):
        updates["conversation_history"] = json.dumps(
            updates["conversation_history"], ensure_ascii=False
        )

    columns = ", ".join(f"{k} = ?" for k in updates)
    values  = list(updates.values()) + [phone_number]

    conn = _get_connection()
    try:
        cursor = conn.execute(
            f"UPDATE sessions SET {columns} WHERE phone_number = ?",
            values
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise ValueError(f"No session found for phone_number: {phone_number}")
        row = conn.execute(
            "SELECT * FROM sessions WHERE phone_number = ?", (phone_number,)
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


# ── Case functions ─────────────────────────────────────────────────────────────

def create_case(session_id: str, case_data: dict) -> dict:
    """
    Create a new case linked to a session.

    Args:
        session_id: UUID of the parent session.
        case_data: Dict with any of:
            platform (str), event_type (str), date_occurred (str),
            amount_affected (float), filing_channel (str),
            reference_id (str), outcome (dict)

    Returns:
        Newly created case dict.
    """
    case_id = str(uuid.uuid4())
    now = _now()
    outcome = json.dumps(case_data.get("outcome", {}), ensure_ascii=False)

    conn = _get_connection()
    try:
        conn.execute(
            """
            INSERT INTO cases
                (id, session_id, platform, event_type, date_occurred,
                 amount_affected, case_status, filing_channel,
                 reference_id, created_at, resolved_at,
                 resolution_type, outcome)
            VALUES (?, ?, ?, ?, ?, ?, 'open', ?, ?, ?, NULL, NULL, ?)
            """,
            (
                case_id,
                session_id,
                case_data.get("platform"),
                case_data.get("event_type"),
                case_data.get("date_occurred"),
                case_data.get("amount_affected"),
                case_data.get("filing_channel"),
                case_data.get("reference_id"),
                now,
                outcome,
            )
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM cases WHERE id = ?", (case_id,)
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def update_case(case_id: str, updates: dict) -> dict:
    """
    Update one or more fields on an existing case.

    outcome is serialized to JSON if passed as a dict.

    Args:
        case_id: UUID of the case.
        updates: Dict of column names → new values.

    Returns:
        Updated case dict.

    Raises:
        ValueError: If no case exists for this case_id.
    """
    if not updates:
        return get_case(case_id)

    if "outcome" in updates and not isinstance(updates["outcome"], str):
        updates["outcome"] = json.dumps(updates["outcome"], ensure_ascii=False)

    columns = ", ".join(f"{k} = ?" for k in updates)
    values  = list(updates.values()) + [case_id]

    conn = _get_connection()
    try:
        cursor = conn.execute(
            f"UPDATE cases SET {columns} WHERE id = ?", values
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise ValueError(f"No case found for case_id: {case_id}")
        row = conn.execute(
            "SELECT * FROM cases WHERE id = ?", (case_id,)
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def get_cases_by_session(session_id: str) -> list:
    """
    Retrieve all cases for a given session, ordered by created_at descending.

    Args:
        session_id: UUID of the session.

    Returns:
        List of case dicts (may be empty).
    """
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM cases WHERE session_id = ? ORDER BY created_at DESC",
            (session_id,)
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def get_case(case_id: str) -> dict | None:
    """
    Retrieve a single case by its UUID.

    Args:
        case_id: UUID of the case.

    Returns:
        Case dict, or None if not found.
    """
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM cases WHERE id = ?", (case_id,)
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def get_case_by_reference(reference_id: str) -> dict | None:
    """
    Retrieve a single case by its reference_id.
    Args:
        reference_id: Reference ID of the case (e.g. GG-2026-001).
    Returns:
        Case dict, or None if not found.
    """
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM cases WHERE reference_id = ?", (reference_id,)
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()
# ── Auto-initialize DB on import ──────────────────────────────────────────────
_init_db()