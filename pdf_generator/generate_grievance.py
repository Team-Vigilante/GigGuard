"""
pdf_generator/generate_grievance.py

Generates a professional grievance PDF from the full pipeline output
(Parser → Researcher → Drafter).

Usage:
    python -m pdf_generator.generate_grievance          # from repo root
    python pdf_generator/generate_grievance.py           # from repo root

Requires: reportlab
    pip install reportlab
"""

from __future__ import annotations

import os
import sys
import textwrap
import datetime
from typing import Any

# ---------------------------------------------------------------------------
# Ensure repo root is on sys.path so `agents.*` imports work when run as a
# script (python pdf_generator/generate_grievance.py)
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.drafter_node import MANDATORY_DISCLAIMER  # noqa: E402

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import cm, mm  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# ---------------------------------------------------------------------------
# Style definitions
# ---------------------------------------------------------------------------
PAGE_WIDTH, PAGE_HEIGHT = A4
STYLES = getSampleStyleSheet()

STYLE_TITLE = ParagraphStyle(
    "GGTitle",
    parent=STYLES["Heading1"],
    fontSize=18,
    leading=22,
    alignment=TA_CENTER,
    spaceAfter=4 * mm,
    textColor=colors.HexColor("#1a237e"),
)

STYLE_SUBTITLE = ParagraphStyle(
    "GGSubtitle",
    parent=STYLES["Normal"],
    fontSize=9,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#616161"),
    spaceAfter=6 * mm,
)

STYLE_SECTION = ParagraphStyle(
    "GGSection",
    parent=STYLES["Heading2"],
    fontSize=13,
    leading=16,
    spaceBefore=6 * mm,
    spaceAfter=3 * mm,
    textColor=colors.HexColor("#283593"),
)

STYLE_BODY = ParagraphStyle(
    "GGBody",
    parent=STYLES["Normal"],
    fontSize=10,
    leading=14,
    alignment=TA_JUSTIFY,
    spaceAfter=2 * mm,
)

STYLE_BULLET = ParagraphStyle(
    "GGBullet",
    parent=STYLE_BODY,
    leftIndent=12 * mm,
    bulletIndent=6 * mm,
    spaceAfter=1.5 * mm,
)

STYLE_DISCLAIMER = ParagraphStyle(
    "GGDisclaimer",
    parent=STYLES["Normal"],
    fontSize=8,
    leading=10,
    alignment=TA_JUSTIFY,
    textColor=colors.HexColor("#757575"),
    spaceBefore=8 * mm,
    spaceAfter=2 * mm,
    borderWidth=0.5,
    borderColor=colors.HexColor("#bdbdbd"),
    borderPadding=6,
)

STYLE_FOOTER = ParagraphStyle(
    "GGFooter",
    parent=STYLES["Normal"],
    fontSize=7,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#9e9e9e"),
)

STYLE_LETTER = ParagraphStyle(
    "GGLetter",
    parent=STYLE_BODY,
    fontSize=10,
    leading=14,
    alignment=TA_LEFT,
    leftIndent=4 * mm,
    rightIndent=4 * mm,
    borderWidth=0.5,
    borderColor=colors.HexColor("#e0e0e0"),
    borderPadding=8,
    backColor=colors.HexColor("#fafafa"),
)


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _safe(value: Any, fallback: str = "—") -> str:
    """Return a display-safe string for a value that might be None / bool."""
    if value is None:
        return fallback
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _make_table(data: list[list[str]], col_widths: list[float] | None = None) -> Table:
    """Build a styled two-column key/value table."""
    table = Table(data, colWidths=col_widths, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8eaf6")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1a237e")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEADING", (0, 0), (-1, -1), 13),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bdbdbd")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


# ---------------------------------------------------------------------------
# Core PDF generator
# ---------------------------------------------------------------------------

def generate_grievance_pdf(case_data: dict, output_path: str) -> str:
    """
    Generate a professional grievance PDF from the full pipeline output.

    Args:
        case_data: Dict matching the schema produced by the GigGuard pipeline
                   (see pdf_generator/sample_case.py for structure).
        output_path: File path to write the PDF to.

    Returns:
        The absolute path of the generated PDF.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=f"Grievance Notice — {case_data.get('case_id', 'N/A')}",
        author="GigGuard Legal Advocacy Platform",
    )

    story: list = []
    case_id = case_data.get("case_id", "N/A")
    generated_at = case_data.get("generated_at", datetime.datetime.now(datetime.timezone.utc).isoformat())
    worker = case_data.get("worker", {})
    parsed = case_data.get("parsed_data", {})
    legal = case_data.get("legal_analysis", {})
    drafter = case_data.get("drafter_output", {})

    # ------------------------------------------------------------------
    # 1. GigGuard header + case ID
    # ------------------------------------------------------------------
    story.append(Paragraph("⚖️ GigGuard — Grievance Notice", STYLE_TITLE))
    story.append(Paragraph(f"Case ID: {case_id}", STYLE_SUBTITLE))
    story.append(Spacer(1, 2 * mm))

    # ------------------------------------------------------------------
    # 2. Worker details table
    # ------------------------------------------------------------------
    story.append(Paragraph("Worker Details", STYLE_SECTION))
    worker_rows = [
        ["Name", _safe(worker.get("name"))],
        ["Phone", _safe(worker.get("phone"))],
        ["Platform", _safe(worker.get("platform"))],
        ["City", _safe(worker.get("city"))],
        ["Worker / Partner ID", _safe(worker.get("worker_id"))],
    ]
    story.append(_make_table(worker_rows, col_widths=[5 * cm, 10 * cm]))
    story.append(Spacer(1, 2 * mm))

    # ------------------------------------------------------------------
    # 3. Parsed data / facts table
    # ------------------------------------------------------------------
    story.append(Paragraph("Complaint Facts (Parsed Data)", STYLE_SECTION))
    facts_rows = [
        ["Event Type", _safe(parsed.get("event_type"))],
        ["Event Date", _safe(parsed.get("event_date"))],
        ["Reason Given", _safe(parsed.get("reason_given"))],
        [
            "Amount Withheld",
            f"₹{parsed['amount_withheld']:,}"
            if parsed.get("amount_withheld") is not None
            else "—",
        ],
        ["Notice Provided", _safe(parsed.get("notice_provided"))],
        [
            "Notice Period (days)",
            _safe(parsed.get("notice_period_days")),
        ],
        ["Earnings Blocked", _safe(parsed.get("earnings_blocked"))],
    ]
    story.append(_make_table(facts_rows, col_widths=[5 * cm, 10 * cm]))
    story.append(Spacer(1, 2 * mm))

    # ------------------------------------------------------------------
    # 4. Legal violations list (skip if INSUFFICIENT_BASIS)
    # ------------------------------------------------------------------
    case_strength = legal.get("case_strength", "")
    confidence = legal.get("confidence", 0)
    story.append(Paragraph("Legal Analysis", STYLE_SECTION))
    story.append(
        Paragraph(
            f"Case Strength: <b>{_safe(case_strength)}</b> &nbsp;|&nbsp; "
            f"Confidence: <b>{confidence:.0%}</b>",
            STYLE_BODY,
        )
    )

    if case_strength != "INSUFFICIENT_BASIS":
        violations = legal.get("violations", [])
        if violations:
            story.append(Spacer(1, 2 * mm))
            story.append(Paragraph("Applicable Violations:", STYLE_BODY))
            for v in violations:
                law = v.get("law", "Unknown Law")
                section = v.get("section", "")
                desc = v.get("description", "")
                bullet_text = (
                    f"<b>{law}, {section}</b> — {desc}" if section else f"<b>{law}</b> — {desc}"
                )
                story.append(Paragraph(bullet_text, STYLE_BULLET, bulletText="•"))
    else:
        story.append(
            Paragraph(
                "<i>Case strength is INSUFFICIENT_BASIS — no legal sections are cited. "
                "This notice documents the incident for official record.</i>",
                STYLE_BODY,
            )
        )

    # ------------------------------------------------------------------
    # 5. Demands list
    # ------------------------------------------------------------------
    demands = drafter.get("demands", [])
    if demands:
        story.append(Paragraph("Relief Sought", STYLE_SECTION))
        for i, demand in enumerate(demands, 1):
            story.append(
                Paragraph(f"{i}. {demand}", STYLE_BULLET)
            )

    # ------------------------------------------------------------------
    # 6. Escalation warning
    # ------------------------------------------------------------------
    escalation = drafter.get("escalation_warning", "")
    if escalation:
        story.append(Paragraph("Escalation Warning", STYLE_SECTION))
        story.append(Paragraph(f"<i>{escalation}</i>", STYLE_BODY))

    # ------------------------------------------------------------------
    # 7. English letter (full text)
    # ------------------------------------------------------------------
    story.append(Paragraph("English Grievance Letter", STYLE_SECTION))
    english_letter = drafter.get("english_letter", "")
    # Preserve line breaks in the letter
    for para_text in english_letter.split("\n\n"):
        cleaned = para_text.strip().replace("\n", "<br/>")
        if cleaned:
            story.append(Paragraph(cleaned, STYLE_LETTER))
            story.append(Spacer(1, 1 * mm))

    # ------------------------------------------------------------------
    # 8. Hindi letter placeholder note
    # ------------------------------------------------------------------
    story.append(Paragraph("Hindi Grievance Letter (हिंदी)", STYLE_SECTION))
    hindi_letter = drafter.get("hindi_letter", "")
    if hindi_letter and not hindi_letter.startswith("["):
        for para_text in hindi_letter.split("\n\n"):
            cleaned = para_text.strip().replace("\n", "<br/>")
            if cleaned:
                story.append(Paragraph(cleaned, STYLE_LETTER))
                story.append(Spacer(1, 1 * mm))
    else:
        story.append(
            Paragraph(
                "<i>Hindi translation will be generated by Agent 3 (Drafter) at "
                "runtime. This placeholder will be replaced with a complete, "
                "formal Hindi translation of the English letter above.</i>",
                STYLE_BODY,
            )
        )

    # ------------------------------------------------------------------
    # 9. Evidence attachments note
    # ------------------------------------------------------------------
    story.append(Paragraph("Evidence &amp; Attachments", STYLE_SECTION))
    story.append(
        Paragraph(
            "<i>Supporting evidence (screenshots, platform notifications, "
            "correspondence) should be attached to this notice when submitted "
            "to the platform grievance officer or labour authority. "
            "Originals should be retained by the complainant.</i>",
            STYLE_BODY,
        )
    )

    # ------------------------------------------------------------------
    # 10. MANDATORY DISCLAIMER — hardcoded, never from drafter_output
    # ------------------------------------------------------------------
    story.append(
        Paragraph(
            f"<b>Disclaimer:</b> {MANDATORY_DISCLAIMER}",
            STYLE_DISCLAIMER,
        )
    )

    # ------------------------------------------------------------------
    # 11. Footer with generated_at + case_id
    # ------------------------------------------------------------------
    story.append(Spacer(1, 4 * mm))
    story.append(
        Paragraph(
            f"Generated: {generated_at} &nbsp;|&nbsp; Case ID: {case_id} &nbsp;|&nbsp; "
            f"GigGuard Legal Advocacy Platform",
            STYLE_FOOTER,
        )
    )

    # Build the PDF
    doc.build(story)
    abs_path = os.path.abspath(output_path)
    print(f"✅ PDF generated: {abs_path}")
    return abs_path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from pdf_generator.sample_case import SAMPLE_CASE

    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    output_file = os.path.join(output_dir, "GG-2026-001.pdf")

    generate_grievance_pdf(SAMPLE_CASE, output_file)
