"""
GigGuard — Agent 4: Navigator
"""
import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict
from app.agents.state import GigGuardState

PLATFORM_CHANNELS = {
    "swiggy": {"code": "SWG", "tier1_email": "grievances@swiggy.in", "tier1_name": "Swiggy Grievance Officer"},
    "zomato": {"code": "ZMT", "tier1_email": "partner-support@zomato.com", "tier1_name": "Zomato Partner Grievance Officer"},
    "ola": {"code": "OLA", "tier1_email": "drivergrievance@olacabs.com", "tier1_name": "Ola Driver Grievance Officer"},
    "uber": {"code": "UBR", "tier1_email": "india-partner-support@uber.com", "tier1_name": "Uber Partner Grievance Officer"},
    "blinkit": {"code": "BLK", "tier1_email": "partner-grievance@blinkit.com", "tier1_name": "Blinkit Partner Grievance Officer"},
    "default": {"code": "GIG", "tier1_email": "grievance@platform.in", "tier1_name": "Platform Grievance Officer"},
}

def _generate_reference_id(platform_code: str) -> str:
    year = datetime.now().year
    random_digits = "".join(random.choices(string.digits, k=6))
    return f"{platform_code}-{year}-{random_digits}"

def _format_date(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")

def _get_platform_channel(platform: str) -> dict:
    key = platform.lower().strip() if platform else "default"
    return PLATFORM_CHANNELS.get(key, PLATFORM_CHANNELS["default"])

def _build_escalation_schedule(filed_at: datetime) -> dict:
    return {
        "tier2_date": _format_date(filed_at + timedelta(days=7)),
        "tier3_date": _format_date(filed_at + timedelta(days=30)),
        "tier4_date": _format_date(filed_at + timedelta(days=60)),
    }

def _build_worker_confirmation_message(channel_name, channel_email, reference_id, expected_response_date, case_strength):
    if case_strength in ("STRONG", "MODERATE"):
        strength_note = "Your case has strong legal grounds. I will automatically escalate if there is no response."
    elif case_strength == "WEAK":
        strength_note = "Your case has some grounds but the legal basis is limited. I have filed it honestly on your behalf."
    else:
        strength_note = "I have documented your case and filed a formal complaint even though the specific legal basis is limited."
    return (
        f"✅ FILED!\n\n"
        f"Channel: {channel_name}\n"
        f"Email: {channel_email}\n\n"
        f"📋 Reference ID: {reference_id}\n"
        f"⏰ Filed at: {datetime.now().strftime('%B %d, %Y, %I:%M %p')}\n"
        f"📅 Expected Response: {expected_response_date}\n\n"
        f"{strength_note}\n\n"
        f"I will check for a response and follow up automatically. You will receive updates here on WhatsApp."
    )

def navigator_node(state: GigGuardState) -> Dict[str, Any]:
    """
    Agent 4: Navigator Node
    Selects filing channel based on case_strength.
    Generates mock reference ID and escalation schedule.
    Person 1: plug this into app/agents/graph.py
    """
    parsed_data = state.get("parsed_data") or {}
    legal_analysis = state.get("legal_analysis") or {}
    platform = parsed_data.get("platform", "default")
    case_strength = legal_analysis.get("case_strength", "INSUFFICIENT_BASIS")
    platform_info = _get_platform_channel(platform)
    platform_code = platform_info["code"]
    channel_email = platform_info["tier1_email"]
    channel_name = platform_info["tier1_name"]

    if case_strength == "INSUFFICIENT_BASIS":
        return {"filing_result": {
            "channel": "Document Only — No Formal Filing",
            "channel_email": None,
            "reference_id": None,
            "filed_at": datetime.now().isoformat(),
            "expected_response_date": None,
            "escalation_schedule": None,
            "worker_confirmation_message": (
                "I have documented your case fully. However, because I could not find a specific law that was violated, "
                "I have not filed a formal complaint. Your documentation is saved and you can request it at any time."
            ),
        }}

    reference_id = _generate_reference_id(platform_code)
    filed_at = datetime.now()
    expected_response_date = _format_date(filed_at + timedelta(days=7))

    if case_strength == "WEAK":
        escalation_schedule = {"tier2_date": None, "tier3_date": None, "tier4_date": None}
    else:
        escalation_schedule = _build_escalation_schedule(filed_at)

    return {"filing_result": {
        "channel": channel_name,
        "channel_email": channel_email,
        "reference_id": reference_id,
        "filed_at": filed_at.isoformat(),
        "expected_response_date": expected_response_date,
        "escalation_schedule": escalation_schedule,
        "worker_confirmation_message": _build_worker_confirmation_message(
            channel_name, channel_email, reference_id, expected_response_date, case_strength
        ),
    }}
