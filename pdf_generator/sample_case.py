"""
pdf_generator/sample_case.py

Sample case data for testing the grievance PDF generator.
Uses the Ramesh Kumar demo case (Swiggy deactivation, Bengaluru).

This dict mirrors the full pipeline output:
  Agent 1 (Parser) → Agent 2 (Researcher) → Agent 3 (Drafter)
"""

from agents.drafter_node import MANDATORY_DISCLAIMER


SAMPLE_CASE: dict = {
    "case_id": "GG-2026-001",
    "generated_at": "2026-06-07T14:30:00Z",

    "worker": {
        "name": "Ramesh Kumar",
        "phone": "+919876544821",
        "platform": "Swiggy",
        "city": "Bengaluru",
        "worker_id": "SWG-BLR-228194",
    },

    "parsed_data": {
        "event_type": "Account Deactivation",
        "event_date": "2026-06-07",
        "reason_given": "Customer rating fell below minimum threshold",
        "amount_withheld": 1840.0,
        "notice_provided": False,
        "notice_period_days": 0,
        "earnings_blocked": True,
    },

    "legal_analysis": {
        "case_strength": "STRONG",
        "confidence": 0.87,
        "violations": [
            {
                "law": "Code on Social Security, 2020",
                "section": "Section 114",
                "description": (
                    "Platform workers are entitled to social security benefits "
                    "and cannot be arbitrarily removed from the platform without "
                    "due process."
                ),
            },
            {
                "law": "Industrial Disputes Act, 1947",
                "section": "Section 25F",
                "description": (
                    "No workman employed for more than one year shall be "
                    "retrenched until one month's notice in writing has been "
                    "given and compensation paid."
                ),
            },
            {
                "law": "Payment of Wages Act, 1936",
                "section": "Section 5",
                "description": (
                    "Wages must be paid within the prescribed period. "
                    "Withholding earned wages without lawful authority is "
                    "a violation."
                ),
            },
            {
                "law": "Karnataka Shops and Commercial Establishments Act, 1961",
                "section": "Section 26",
                "description": (
                    "No employee shall be dismissed without reasonable cause "
                    "and without a proper inquiry being conducted."
                ),
            },
        ],
    },

    "drafter_output": {
        "english_letter": (
            "GRIEVANCE NOTICE\n\n"
            "FROM:\n"
            "Ramesh Kumar\n"
            "GigGuard Legal Advocacy Platform\n\n"
            "TO:\n"
            "The Grievance Officer\n"
            "Swiggy\n\n"
            "DATE: 7 June 2026\n\n"
            "SUBJECT: Wrongful Account Deactivation Without Notice "
            "and Withholding of Earned Wages\n\n"
            "FACTS:\n"
            "1. The complainant, Ramesh Kumar (Partner ID: SWG-BLR-228194), "
            "has been working as a delivery partner with Swiggy in Bengaluru.\n"
            "2. On 7 June 2026, the complainant's account was deactivated "
            "without any prior notice or warning.\n"
            "3. The reason cited was 'Customer rating fell below minimum "
            "threshold,' however no specific incidents were communicated "
            "to the complainant.\n"
            "4. An amount of ₹1,840 in earned wages has been withheld "
            "and remains unpaid.\n"
            "5. No opportunity for appeal or review was provided to the "
            "complainant before or after the deactivation.\n\n"
            "LEGAL BASIS:\n"
            "As per Code on Social Security, 2020, Section 114: Platform "
            "workers are entitled to social security benefits and cannot "
            "be arbitrarily removed from the platform without due process.\n\n"
            "As per Industrial Disputes Act, 1947, Section 25F: No workman "
            "employed for more than one year shall be retrenched until one "
            "month's notice in writing has been given and compensation paid.\n\n"
            "As per Payment of Wages Act, 1936, Section 5: Wages must be "
            "paid within the prescribed period. Withholding earned wages "
            "without lawful authority is a violation.\n\n"
            "As per Karnataka Shops and Commercial Establishments Act, 1961, "
            "Section 26: No employee shall be dismissed without reasonable "
            "cause and without a proper inquiry being conducted.\n\n"
            "RELIEF SOUGHT:\n"
            "1. Immediate reinstatement of the complainant's Swiggy delivery "
            "partner account.\n"
            "2. Release of all withheld earnings amounting to ₹1,840.\n"
            "3. Written explanation of the specific grounds for deactivation.\n"
            "4. Response within 15 days of receipt of this notice.\n\n"
            "ESCALATION WARNING:\n"
            "Failure to respond within 15 days will compel the complainant "
            "to escalate this matter to the appropriate labour authorities "
            "and consumer forums.\n\n"
            "Yours faithfully,\n"
            "The Complainant\n"
            "Via GigGuard Legal Advocacy Platform\n\n"
            "DISCLAIMER:\n"
            + MANDATORY_DISCLAIMER
        ),

        "hindi_letter": "[Hindi translation will be generated by Agent 3 at runtime]",

        "demands": [
            "Immediate reinstatement of the complainant's Swiggy delivery partner account.",
            "Release of all withheld earnings amounting to ₹1,840.",
            "Written explanation of the specific grounds for deactivation.",
            "Response within 15 days of receipt of this notice.",
        ],

        "escalation_warning": (
            "Failure to respond within 15 days will compel the complainant "
            "to escalate this matter to the appropriate labour authorities "
            "and consumer forums."
        ),

        "disclaimer": MANDATORY_DISCLAIMER,
    },
}
