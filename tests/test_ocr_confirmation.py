"""
Quick manual test of ocr_confirmation.py using realistic Agent 1 outputs.
Run with: python3 test_ocr_confirmation.py
"""

import sys
sys.path.insert(0, ".")

from app.services.ocr_confirmation import (
    build_confirmation_response,
    handle_confirmation_reply,
    build_timeout_message,
    SessionContext,
)


def section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


# -----------------------------------------------------------------
# CASE 1: Demo case (Ramesh Kumar) — clear, high confidence
# -----------------------------------------------------------------
ramesh_data = {
    "platform": "Swiggy",
    "event_type": "account_deactivation",
    "date": "2026-06-07",
    "reason": "Customer rating fell below minimum threshold",
    "worker_id": "SWG-BLR-228194",
    "earnings_withheld": 1840,
    "notice_provided": False,
    "appeal_offered": False,
    "language_detected": "en",
    "input_quality": "CLEAR",
    "confidence": {
        "platform": 0.98,
        "event_type": 0.95,
        "date": 0.97,
        "reason": 0.9,
        "worker_id": 0.92,
        "earnings_withheld": 0.96,
        "notice_provided": 0.85,
        "appeal_offered": 0.85,
        "overall": 0.93,
    },
}

section("CASE 1: Ramesh Kumar — CLEAR, high confidence")
resp = build_confirmation_response(ramesh_data)
print("ACTION:", resp["action"])
print("STATE: ", resp["state"])
print("-" * 60)
print(resp["message"])

# Worker replies YES
session = SessionContext(case_id="case_ramesh_001", state="AWAITING_CONFIRMATION")
section("Worker replies: YES")
result = handle_confirmation_reply("YES", ramesh_data, session)
print("STATE:", result["state"], "| advance_to_agent2:", result["advance_to_agent2"])
print(result["message"])


# -----------------------------------------------------------------
# CASE 2: Worker says NO, corrects the amount, then confirms
# -----------------------------------------------------------------
section("CASE 2: Worker replies NO, corrects 'Amount withheld', then YES")
session2 = SessionContext(case_id="case_ramesh_002", state="AWAITING_CONFIRMATION")

step1 = handle_confirmation_reply("NO", ramesh_data, session2)
print(">> Bot:", step1["message"])
print("State now:", session2.state)

step2 = handle_confirmation_reply("4", ramesh_data, session2)  # 4 = Amount withheld
print("\n>> Bot:", step2["message"])
print("State now:", session2.state, "| awaiting_field:", session2.awaiting_field)

step3 = handle_confirmation_reply("2200", ramesh_data, session2)
print("\n>> Bot:")
print(step3["message"])
print("\nUpdated earnings_withheld:", step3["updated_data"]["earnings_withheld"])

step4 = handle_confirmation_reply("yes", step3["updated_data"], session2)
print("\n>> Bot:", step4["message"])
print("advance_to_agent2:", step4["advance_to_agent2"])


# -----------------------------------------------------------------
# CASE 3: Low confidence / degraded screenshot -> ask resend
# -----------------------------------------------------------------
section("CASE 3: DEGRADED input, low overall confidence")
blurry_data = {
    "platform": "Zomato",
    "event_type": None,
    "date": None,
    "reason": None,
    "worker_id": None,
    "earnings_withheld": None,
    "notice_provided": None,
    "appeal_offered": None,
    "language_detected": "hi",
    "input_quality": "DEGRADED",
    "confidence": {
        "platform": 0.4,
        "event_type": 0.1,
        "date": 0.1,
        "reason": 0.1,
        "worker_id": 0.1,
        "earnings_withheld": 0.1,
        "notice_provided": 0.1,
        "appeal_offered": 0.1,
        "overall": 0.2,
    },
}
resp3 = build_confirmation_response(blurry_data)
print("ACTION:", resp3["action"], "| STATE:", resp3["state"])
print(resp3["message"])


# -----------------------------------------------------------------
# CASE 4: Not a complaint at all
# -----------------------------------------------------------------
section("CASE 4: NOT_A_COMPLAINT")
random_data = {
    "platform": None,
    "event_type": None,
    "date": None,
    "reason": None,
    "worker_id": None,
    "earnings_withheld": None,
    "notice_provided": None,
    "appeal_offered": None,
    "language_detected": "en",
    "input_quality": "NOT_A_COMPLAINT",
    "confidence": {
        "platform": 0.0, "event_type": 0.0, "date": 0.0, "reason": 0.0,
        "worker_id": 0.0, "earnings_withheld": 0.0, "notice_provided": 0.0,
        "appeal_offered": 0.0, "overall": 0.0,
    },
}
resp4 = build_confirmation_response(random_data)
print("ACTION:", resp4["action"], "| STATE:", resp4["state"])
print(resp4["message"])


# -----------------------------------------------------------------
# CASE 5: Borderline field confidence -> ⚠️ marker shown
# -----------------------------------------------------------------
section("CASE 5: Mostly clear, but 'notice_provided' has low confidence")
mixed_data = dict(ramesh_data)
mixed_data["confidence"] = dict(ramesh_data["confidence"])
mixed_data["confidence"]["notice_provided"] = 0.35
resp5 = build_confirmation_response(mixed_data)
print(resp5["message"])


# -----------------------------------------------------------------
# CASE 6: Timeout flow
# -----------------------------------------------------------------
section("CASE 6: Timeout — first reminder, then pause")
t1 = build_timeout_message(reminder_already_sent=False)
print("First timeout ->", t1["send_message"], "| new_state:", t1["new_state"])
print(t1["message"])

t2 = build_timeout_message(reminder_already_sent=True)
print("\nSecond timeout ->", t2["send_message"], "| new_state:", t2["new_state"])
print(t2["message"])
