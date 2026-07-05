"""
GigGuard — WhatsApp Message Router
Routes each incoming message based on conversation state.
Connects webhook → DB → LangGraph → Twilio response.
"""

from app.db.database import (
    get_session,
    create_session,
    update_session,
    create_case,
    update_case,
    get_cases_by_session
)
from app.agents.graph import gigguard_graph


async def handle_message(
    phone: str,
    message: str,
    media_url: str | None,
    media_type: str | None
) -> str:
    """
    Main router. Called by webhook for every incoming message.
    Returns the text response to send back to the worker.
    """

    # ── Step 1: Get or create session ─────────────────────────────
    session = get_session(phone)
    if not session:
        session = create_session(phone)
        print(f"[router] new session created for {phone}")

    state = session.get("state", "intake")
    print(f"[router] phone={phone} | state={state}")

    # ── Step 2: Route based on conversation state ──────────────────

    # First message — welcome and ask for screenshot
    if state == "intake":
        update_session(phone, {"state": "awaiting_screenshot"})
        return (
            "Namaste! Main GigGuard hoon — aapka legal advocate. 🛡️\n\n"
            "Kya aapka gig platform account band hua hai ya koi paisa roka gaya hai?\n\n"
            "Kripya apne deactivation ka screenshot bhejein, "
            "ya apni samasya Hindi ya English mein type karein."
        )

    # Waiting for screenshot or text description
    if state == "awaiting_screenshot":
        if not message and not media_url:
            return "Kripya screenshot ya message bhejein taaki main aapki madad kar sakoon."

        # Run parser node
        graph_state = {
            "phone": phone,
            "message": message or "",
            "media_url": media_url,
            "conversation_state": state,
            "parsed_data": None,
            "legal_analysis": None,
            "grievance_letter": None,
            "filing_result": None,
            "confirmation_pending": False,
            "case_id": None,
            "error": None
        }

        result = gigguard_graph.invoke(graph_state)
        parsed = result.get("parsed_data")
        error = result.get("error")

        # Low confidence or parse failure — ask to resend
        if error in ("low_confidence", "parse_failed") or not parsed:
            return (
                "Mujhe screenshot clearly samajh nahi aaya. 😕\n\n"
                "Kripya:\n"
                "1️⃣ Ek aur clear screenshot bhejein\n"
                "2️⃣ Ya yeh details type karein:\n"
                "   - Platform ka naam (Swiggy, Zomato, Ola...)\n"
                "   - Kya hua (account band, paisa roka...)\n"
                "   - Kitna paisa roka gaya"
            )

        # Good parse — create case and ask for confirmation
        platform = parsed.get("platform", "Unknown")
        event = parsed.get("event_type", "Unknown")
        earnings = parsed.get("earnings_withheld")
        notice = parsed.get("notice_provided")

        # Create case in DB
        case = create_case(
            session_id=session["id"],
            case_data={
                "platform": platform,
                "event_type": event,
                "date_occurred": parsed.get("date"),
                "amount_affected": earnings,
                "case_status": "open"
            }
        )

        # Save case_id and move state
        update_session(phone, {
            "state": "awaiting_confirmation",
            "conversation_history": session.get("conversation_history", []) + [
                {"role": "system", "case_id": case["id"]}
            ]
        })

        # Build confirmation message
        earnings_line = f"💰 Roka gaya paisa: ₹{earnings}" if earnings else ""
        notice_line = "⚠️ Koi notice nahi diya gaya" if notice is False else ""

        return (
            f"Yeh main samajh gaya:\n\n"
            f"🏢 Platform: {platform}\n"
            f"❌ Kya hua: {event}\n"
            f"{earnings_line}\n"
            f"{notice_line}\n\n"
            f"Kya yeh sahi hai?\n"
            f"✅ *Haan* bhejein aage badhne ke liye\n"
            f"❌ *Nahi* bhejein dobara batane ke liye"
        ).strip()

    # Worker confirmed — run full pipeline
    if state == "awaiting_confirmation":
        msg_lower = message.lower().strip()

        if msg_lower in ("nahi", "no", "nhi", "galat", "wrong"):
            update_session(phone, {"state": "awaiting_screenshot"})
            return (
                "Theek hai, dobara batayein. 📝\n\n"
                "Kripya apni samasya detail mein likhein ya naya screenshot bhejein."
            )

        if msg_lower not in ("haan", "yes", "ha", "han", "sahi", "correct", "ok", "okay"):
            return "Kripya *Haan* ya *Nahi* mein jawab dein."

        # Get case_id from conversation history
        history = session.get("conversation_history", [])
        case_id = None
        for entry in reversed(history):
            if isinstance(entry, dict) and "case_id" in entry:
                case_id = entry["case_id"]
                break

        if not case_id:
            return "Kuch galat hua. Kripya dobara shuru karein — apna screenshot bhejein."

        # Get case data to rebuild graph state
        cases = get_cases_by_session(session["id"])
        case = next((c for c in cases if c["id"] == case_id), None)

        if not case:
            return "Case nahi mila. Kripya dobara shuru karein."

        update_session(phone, {"state": "in_progress"})

        return (
            "Shukriya! Main abhi aapki complaint bana raha hoon. ⚙️\n\n"
            "1️⃣ Legal research kar raha hoon\n"
            "2️⃣ Formal complaint likh raha hoon\n"
            "3️⃣ Sahi channel identify kar raha hoon\n\n"
            "2-3 minute dijiye... 🕐"
        )

    # Fallback for any other state
    return (
        "Main aapki madad ke liye yahan hoon. 🛡️\n"
        "Kripya apni samasya batayein ya screenshot bhejein."
    )