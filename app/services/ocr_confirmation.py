"""
app/services/ocr_confirmation.py

Phase 2 — OCR Confirmation Flow (Person 3 / Demo Infra)

This module takes Agent 1's (Parser) JSON output and:
  1. Decides what to show the worker (resend request / clarification / confirmation card)
  2. Formats the confirmation card as a WhatsApp message
  3. Handles YES / NO / field-correction / timeout branches
  4. Logs every OCR vs worker-correction mismatch for later analysis

INTEGRATION NOTES FOR PERSON 1
--------------------------------
- Call `build_confirmation_response(parsed_data)` right after Agent 1 (Parser)
  returns its JSON. It returns a dict:
      {
          "action": "SEND_CONFIRMATION" | "ASK_RESEND" | "REDIRECT_NOT_COMPLAINT",
          "message": "<text to send to worker on WhatsApp>",
          "state": "<suggested next conversation state>"
      }

- When the worker replies, call `handle_confirmation_reply(reply_text, parsed_data, session)`.
  `session` is a small dict you maintain per-conversation (see SessionContext below).
  It returns a dict describing what to do next (advance state, ask for field,
  re-show confirmation, etc.)

- Timeout handling: call `build_timeout_message(stage)` when your scheduler detects
  no reply for 10 minutes while state == AWAITING_CONFIRMATION (or
  AWAITING_FIELD_CORRECTION). First timeout -> send reminder. Second timeout
  (after reminder) -> pause the session (set state to PAUSED).

- Mismatch logging: `log_mismatch(case_id, field, ocr_value, corrected_value)`
  appends a row to mismatches.jsonl (swap for a DB call later if needed).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Config / thresholds
# ---------------------------------------------------------------------------

LOW_CONFIDENCE_THRESHOLD = 0.6        # per-field: below this -> flag with ⚠️
RESEND_CONFIDENCE_THRESHOLD = 0.5     # overall: below this + DEGRADED -> ask resend

MISMATCH_LOG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "mismatches.jsonl"
)

# Human-readable labels + emoji for each field, in display order
FIELD_LABELS: list[tuple[str, str]] = [
    ("platform", "Platform"),
    ("event_type", "Event"),
    ("date", "Date"),
    ("earnings_withheld", "Amount withheld"),
    ("notice_provided", "Notice provided"),
    ("appeal_offered", "Appeal offered"),
    ("reason", "Reason given"),
    ("worker_id", "Worker / Partner ID"),
]

# Map field name -> the index a worker would type to correct it (1-indexed)
FIELD_INDEX = {name: i + 1 for i, (name, _) in enumerate(FIELD_LABELS)}
INDEX_TO_FIELD = {i + 1: name for i, (name, _) in enumerate(FIELD_LABELS)}


# ---------------------------------------------------------------------------
# Session context (Person 1 will likely store this in their state machine /
# SQLite session row — this dataclass just documents the shape we expect)
# ---------------------------------------------------------------------------

@dataclass
class SessionContext:
    case_id: str
    state: str = "AWAITING_CONFIRMATION"   # or AWAITING_FIELD_CORRECTION, etc.
    awaiting_field: Optional[str] = None   # set when worker said NO and we asked which field
    reminder_sent: bool = False            # whether the 10-min reminder has gone out
    corrections: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Value formatting helpers
# ---------------------------------------------------------------------------

def _format_value(field_name: str, value: Any) -> str:
    """Turn a raw field value into a human-readable string for the card."""
    if value is None:
        return "Not detected"

    if field_name == "earnings_withheld":
        try:
            amount = float(value)
            return f"₹{amount:,.0f}"
        except (ValueError, TypeError):
            return str(value)

    if field_name in ("notice_provided", "appeal_offered"):
        if isinstance(value, bool):
            return "Yes" if value else "No"
        return str(value)

    if field_name == "event_type":
        # e.g. "account_deactivation" -> "Account deactivation"
        return str(value).replace("_", " ").capitalize()

    return str(value)


def _confidence_marker(field_name: str, confidence: dict) -> str:
    """Return a ⚠️ marker if this field's confidence is below threshold."""
    score = confidence.get(field_name)
    if score is None:
        return ""
    if score < LOW_CONFIDENCE_THRESHOLD:
        return " ⚠️ (please double-check)"
    return ""


# ---------------------------------------------------------------------------
# Step 1: Decide what to do with Agent 1's output
# ---------------------------------------------------------------------------

def build_confirmation_response(parsed_data: dict) -> dict:
    """
    Given Agent 1's JSON output, decide the next bot action.

    Returns:
        {
            "action": "SEND_CONFIRMATION" | "ASK_RESEND" | "REDIRECT_NOT_COMPLAINT",
            "message": str,
            "state": str   # suggested conversation state to move into
        }
    """
    input_quality = parsed_data.get("input_quality")
    confidence = parsed_data.get("confidence", {}) or {}
    overall = confidence.get("overall", 0.0) or 0.0

    # Case 1: Not a complaint at all -> friendly redirect, no confirmation flow
    if input_quality == "NOT_A_COMPLAINT":
        message = (
            "Hmm, this doesn't look like a deactivation issue. 🤔\n\n"
            "GigGuard helps with problems like:\n"
            "• Account deactivation / ID block\n"
            "• Payment or earnings withheld\n"
            "• Unfair penalties from your platform\n\n"
            "If this is one of these issues, please send a screenshot of the "
            "notice (or describe what happened) and I'll take it from there. "
            "If not, no action is needed right now."
        )
        return {
            "action": "REDIRECT_NOT_COMPLAINT",
            "message": message,
            "state": "NEW",  # stay / reset to NEW, don't open a case
        }

    # Case 2: Degraded input + low overall confidence -> ask for a clearer resend
    if input_quality == "DEGRADED" and overall < RESEND_CONFIDENCE_THRESHOLD:
        message = (
            "I had trouble reading some details clearly from what you sent. 😕\n\n"
            "Could you please:\n"
            "• Resend a clearer screenshot of the notice (good lighting, "
            "no blur, full message visible), OR\n"
            "• Type out the key details yourself — platform name, what "
            "happened, the date, and any amount withheld.\n\n"
            "This will help me make sure your case is recorded correctly."
        )
        return {
            "action": "ASK_RESEND",
            "message": message,
            "state": "AWAITING_SCREENSHOT",
        }

    # Case 3: Good enough -> build the confirmation card
    message = _build_confirmation_card(parsed_data)
    return {
        "action": "SEND_CONFIRMATION",
        "message": message,
        "state": "AWAITING_CONFIRMATION",
    }


def _build_confirmation_card(parsed_data: dict) -> str:
    """Build the 'I found the following details...' WhatsApp message."""
    confidence = parsed_data.get("confidence", {}) or {}

    lines = ["I found the following details:\n"]
    for field_name, label in FIELD_LABELS:
        value = parsed_data.get(field_name)
        display_value = _format_value(field_name, value)
        marker = _confidence_marker(field_name, confidence)
        lines.append(f"{label}: {display_value}{marker}")

    lines.append("")
    lines.append("Is this correct? Reply *YES* to continue")
    lines.append("or *NO* to correct a detail.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Step 2: Handle the worker's reply to the confirmation card
# ---------------------------------------------------------------------------

def handle_confirmation_reply(
    reply_text: str,
    parsed_data: dict,
    session: SessionContext,
) -> dict:
    """
    Process a worker's reply while state is AWAITING_CONFIRMATION or
    AWAITING_FIELD_CORRECTION.

    Returns a dict describing what the bot should send next and what
    state to move to:
        {
            "message": str,
            "state": str,
            "updated_data": dict | None,   # parsed_data with corrections applied
            "advance_to_agent2": bool      # True once worker confirms YES
        }
    """
    text = reply_text.strip().lower()

    # --- Branch A: we're waiting for a field correction value ---
    if session.state == "AWAITING_FIELD_CORRECTION" and session.awaiting_field:
        field_name = session.awaiting_field
        old_value = parsed_data.get(field_name)
        new_value = _coerce_value(field_name, reply_text.strip())

        # Log the mismatch before overwriting
        log_mismatch(session.case_id, field_name, old_value, new_value)

        # Apply correction
        updated_data = dict(parsed_data)
        updated_data[field_name] = new_value
        session.corrections[field_name] = new_value
        session.awaiting_field = None
        session.state = "AWAITING_CONFIRMATION"

        confirmation_card = _build_confirmation_card(updated_data)
        message = f"Got it, updated. ✅\n\n{confirmation_card}"

        return {
            "message": message,
            "state": "AWAITING_CONFIRMATION",
            "updated_data": updated_data,
            "advance_to_agent2": False,
        }

    # --- Branch B: YES ---
    if text in ("yes", "y", "haan", "ha", "correct", "sahi hai"):
        session.state = "IN_PROGRESS"
        return {
            "message": (
                "Thanks for confirming! ✅\n\n"
                "I'm now reviewing your case against platform policies and "
                "labour laws. This will take a moment..."
            ),
            "state": "IN_PROGRESS",
            "updated_data": parsed_data,
            "advance_to_agent2": True,
        }

    # --- Branch C: NO ---
    if text in ("no", "n", "nahi", "galat", "incorrect"):
        field_list = "\n".join(
            f"{idx}. {label}: {_format_value(name, parsed_data.get(name))}"
            for name, label in FIELD_LABELS
            for idx in [FIELD_INDEX[name]]
        )
        message = (
            "No problem — let's fix it. 🛠️\n\n"
            "Which detail is wrong? Reply with the number:\n\n"
            f"{field_list}"
        )
        session.state = "AWAITING_FIELD_SELECTION"
        return {
            "message": message,
            "state": "AWAITING_FIELD_SELECTION",
            "updated_data": parsed_data,
            "advance_to_agent2": False,
        }

    # --- Branch D: worker is selecting which field to correct (a number) ---
    if session.state == "AWAITING_FIELD_SELECTION":
        try:
            choice = int(text)
            field_name = INDEX_TO_FIELD[choice]
        except (ValueError, KeyError):
            return {
                "message": (
                    "Sorry, I didn't understand that. Please reply with just "
                    "the number of the detail you'd like to correct (e.g. 1)."
                ),
                "state": "AWAITING_FIELD_SELECTION",
                "updated_data": parsed_data,
                "advance_to_agent2": False,
            }

        label = dict(FIELD_LABELS)[field_name]
        session.awaiting_field = field_name
        session.state = "AWAITING_FIELD_CORRECTION"

        prompt = _correction_prompt(field_name, label)
        return {
            "message": prompt,
            "state": "AWAITING_FIELD_CORRECTION",
            "updated_data": parsed_data,
            "advance_to_agent2": False,
        }

    # --- Branch E: unrecognized reply while awaiting YES/NO ---
    return {
        "message": (
            "Sorry, I didn't quite get that. 🙏\n\n"
            "Please reply *YES* if the details above are correct, or "
            "*NO* if something needs to be fixed."
        ),
        "state": session.state,
        "updated_data": parsed_data,
        "advance_to_agent2": False,
    }


def _correction_prompt(field_name: str, label: str) -> str:
    """Tailored prompt for the type of correction being requested."""
    if field_name in ("notice_provided", "appeal_offered"):
        return f"Please reply *Yes* or *No* — was {label.lower()} given to you?"
    if field_name == "date":
        return f"Please send the correct {label.lower()} (e.g. 7 June 2026)."
    if field_name == "earnings_withheld":
        return f"Please send the correct {label.lower()} in ₹ (e.g. 1840)."
    return f"Please send the correct {label.lower()}."


def _coerce_value(field_name: str, raw_text: str) -> Any:
    """Convert worker's free-text correction into the right type."""
    text = raw_text.strip()

    if field_name in ("notice_provided", "appeal_offered"):
        lowered = text.lower()
        if lowered in ("yes", "y", "haan", "ha"):
            return True
        if lowered in ("no", "n", "nahi"):
            return False
        return text  # leave as-is if ambiguous; legal researcher / human can review

    if field_name == "earnings_withheld":
        # Strip currency symbols / commas, try to parse a number
        cleaned = text.replace("₹", "").replace(",", "").strip()
        try:
            return float(cleaned) if "." in cleaned else int(cleaned)
        except ValueError:
            return text

    return text


# ---------------------------------------------------------------------------
# Step 3: Timeout handling
# ---------------------------------------------------------------------------

def build_timeout_message(reminder_already_sent: bool) -> dict:
    """
    Called by Person 1's scheduler when 10 minutes pass with no reply
    while state is AWAITING_CONFIRMATION / AWAITING_FIELD_SELECTION /
    AWAITING_FIELD_CORRECTION.

    Returns:
        {
            "message": str | None,   # None if we should send nothing
            "new_state": str,        # state to set after this
            "send_message": bool
        }
    """
    if not reminder_already_sent:
        return {
            "message": (
                "👋 Just checking in — are you still there?\n\n"
                "Reply *YES* or *NO* to continue with your case, or send "
                "any message and I'll pick up where we left off. "
                "I'll pause this for now if I don't hear back."
            ),
            "new_state": None,  # state unchanged, but reminder_sent -> True
            "send_message": True,
        }

    # Second timeout after reminder -> pause session
    return {
        "message": (
            "I haven't heard back, so I'll pause this case for now. ⏸️\n\n"
            "No worries — just send any message whenever you're ready to "
            "continue, and we'll pick up right where we left off."
        ),
        "new_state": "PAUSED",
        "send_message": True,
    }


# ---------------------------------------------------------------------------
# Step 4: Mismatch logging
# ---------------------------------------------------------------------------

def log_mismatch(case_id: str, field_name: str, ocr_value: Any, corrected_value: Any) -> None:
    """
    Append a record of an OCR-vs-worker-correction mismatch to a JSONL file.
    Swap this for a proper DB insert (Person 4's schema) later if desired —
    signature can stay the same.
    """
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "case_id": case_id,
        "field": field_name,
        "ocr_value": ocr_value,
        "corrected_value": corrected_value,
    }

    os.makedirs(os.path.dirname(MISMATCH_LOG_PATH), exist_ok=True)
    with open(MISMATCH_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
