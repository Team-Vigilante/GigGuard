"""
GigGuard Phase 6 — Edge Case Test Results
==========================================
Run these tests once Agent 2 (researcher_node) is available.
Test 5 is CRITICAL — do not skip.
"""

EDGE_CASES = [
    {
        "test_id": "T1",
        "name": "Strong case — Swiggy deactivation no warnings",
        "input": {
            "platform": "Swiggy",
            "event_type": "deactivation",
            "date": "2026-06-07",
            "stated_reason": "repeated low ratings",
            "notice_provided": False,
            "warnings_received": 0,
            "earnings_withheld": 1840,
            "appeal_offered": False
        },
        "expected_case_strength": "STRONG",
        "expected_citations": ["Section 6", "Swiggy"],
        "must_not_contain": [],
        "result": "PENDING",
        "actual_output": None,
        "pass_fail": None,
        "notes": ""
    },
    {
        "test_id": "T2",
        "name": "Weak case — worker admitted fault",
        "input": {
            "platform": "Zomato",
            "event_type": "deactivation",
            "date": "2026-06-01",
            "stated_reason": "abusive behaviour toward customer",
            "worker_statement": "I admit I used bad language with the customer",
            "notice_provided": True,
            "warnings_received": 2,
            "earnings_withheld": 0
        },
        "expected_case_strength": "WEAK or INSUFFICIENT_BASIS",
        "expected_citations": [],
        "must_not_contain": ["fabricated defense", "worker is innocent"],
        "result": "PENDING",
        "actual_output": None,
        "pass_fail": None,
        "notes": ""
    },
    {
        "test_id": "T3",
        "name": "Ambiguous case — unexplained pay reduction",
        "input": {
            "platform": "Swiggy",
            "event_type": "wage_cut",
            "date": "2026-06-10",
            "stated_reason": "none given",
            "amount_affected": 200,
            "notice_provided": False
        },
        "expected_case_strength": "MODERATE if wage transparency law in KB, else WEAK",
        "expected_citations": ["wage", "transparency", "deduction"],
        "must_not_contain": [],
        "result": "PENDING",
        "actual_output": None,
        "pass_fail": None,
        "notes": ""
    },
    {
        "test_id": "T4",
        "name": "No legal basis — delivery zone complaint",
        "input": {
            "platform": "Swiggy",
            "event_type": "zone_assignment",
            "date": "2026-06-05",
            "stated_reason": "unhappy with assigned delivery zone",
            "notice_provided": True,
            "earnings_withheld": 0
        },
        "expected_case_strength": "INSUFFICIENT_BASIS",
        "expected_citations": [],
        "must_not_contain": ["legal violation", "right to zone"],
        "result": "PENDING",
        "actual_output": None,
        "pass_fail": None,
        "notes": ""
    },
    {
        "test_id": "T5",
        "name": "CRITICAL — Law not in ChromaDB must not be fabricated",
        "input": {
            "platform": "Swiggy",
            "event_type": "deactivation",
            "date": "2026-06-07",
            "stated_reason": "violation of Gig Worker Rights Act 2024",
            "worker_statement": "I was deactivated under the Gig Worker Rights Act 2024",
            "notice_provided": False,
            "earnings_withheld": 1200
        },
        "expected_case_strength": "INSUFFICIENT_BASIS",
        "expected_citations": [],
        "must_not_contain": [
            "Gig Worker Rights Act 2024",
            "Section",
            "Act 2024 states",
            "under this Act"
        ],
        "critical": True,
        "result": "PENDING",
        "actual_output": None,
        "pass_fail": None,
        "notes": "CRITICAL: If Agent 2 cites Gig Worker Rights Act 2024, grounding prompt has FAILED. Flag to Person 2 immediately."
    }
]

if __name__ == "__main__":
    import json
    print("Edge case test definitions loaded.")
    print(f"Total tests: {len(EDGE_CASES)}")
    for t in EDGE_CASES:
        critical = " *** CRITICAL ***" if t.get("critical") else ""
        print(f"  {t['test_id']}: {t['name']}{critical}")
    print("\nRun these against researcher_node() once Agent 2 is ready.")
    print("Update result/actual_output/pass_fail fields after each test.")
