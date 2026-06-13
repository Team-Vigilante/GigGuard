from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from app.db.database import get_session, get_cases_by_session

router = APIRouter()


def _mask_phone(phone: str) -> str:
    """Mask middle digits of phone number for privacy."""
    clean = phone.replace("whatsapp:", "")
    if len(clean) >= 6:
        return clean[:3] + "****" + clean[-3:]
    return "****"


def _days_pending(created_at: str) -> int:
    """Calculate days since case was created."""
    try:
        created = datetime.fromisoformat(created_at)
        now = datetime.now(timezone.utc)
        return (now - created).days
    except Exception:
        return 0


def _build_timeline(case: dict) -> list:
    """Build timeline of case events."""
    timeline = []
    if case.get("created_at"):
        timeline.append({
            "event": "Case filed",
            "date": case["created_at"],
            "detail": f"Complaint filed against {case.get('platform', 'Unknown')}"
        })
    if case.get("filing_channel"):
        timeline.append({
            "event": "Grievance submitted",
            "date": case.get("created_at"),
            "detail": f"Filed via {case['filing_channel']}"
        })
    if case.get("resolved_at"):
        timeline.append({
            "event": "Case resolved",
            "date": case["resolved_at"],
            "detail": case.get("resolution_type", "Resolved")
        })
    return timeline


def _next_action(case: dict) -> str:
    """Determine next action based on case status."""
    status = case.get("case_status", "open")
    if status == "open":
        return "Awaiting platform response (7 days)"
    if status == "escalated":
        return "Escalated to Labour Department — awaiting response (30 days)"
    if status == "resolved":
        return "Case resolved — no further action needed"
    return "Under review"


def _expected_response_date(case: dict) -> str:
    """Calculate expected response date."""
    try:
        created = datetime.fromisoformat(case["created_at"])
        status = case.get("case_status", "open")
        if status == "open":
            from datetime import timedelta
            expected = created + timedelta(days=7)
        elif status == "escalated":
            from datetime import timedelta
            expected = created + timedelta(days=30)
        else:
            return "N/A"
        return expected.strftime("%Y-%m-%d")
    except Exception:
        return "N/A"


@router.get("/dashboard/{case_id}")
async def get_dashboard(case_id: str):
    """
    Returns case status and timeline for a given case_id.
    Used by Person 4's frontend dashboard.
    """
    # Find the case across all sessions
    # We search by case_id directly using get_case
    from app.db.database import get_case
    case = get_case(case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Get session for worker phone
    session_id = case.get("session_id")
    session = None
    if session_id:
        # Find session by id — use a direct DB lookup
        import sqlite3
        from pathlib import Path
        db_path = Path(__file__).parent.parent / "db" / "gigguard.db"
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        conn.close()
        if row:
            session = dict(row)

    worker_phone = session["phone_number"] if session else "Unknown"

    return {
        "case_id": case_id,
        "worker_phone": _mask_phone(worker_phone),
        "platform": case.get("platform", "Unknown"),
        "status": case.get("case_status", "open"),
        "filed_at": case.get("created_at", ""),
        "reference_id": case.get("reference_id", "N/A"),
        "next_action": _next_action(case),
        "expected_response_date": _expected_response_date(case),
        "days_pending": _days_pending(case.get("created_at", "")),
        "timeline": _build_timeline(case)
    }