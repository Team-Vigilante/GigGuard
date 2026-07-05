import httpx
import base64
import json
import re
from groq import Groq
from google import genai
from google.genai import types
from app.config import GROQ_API_KEY, GEMINI_API_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
from app.agents.state import GigGuardState

# Initialize clients
groq_client = Groq(api_key=GROQ_API_KEY)
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

EXTRACTION_PROMPT = """You are a structured data extraction agent for GigGuard, a legal
advocacy system for gig workers in India.

Your ONLY job is to extract structured information from a worker's
complaint message or screenshot description and return it as a
strict JSON object.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LANGUAGE HANDLING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input may be in Hindi, Kannada, Tamil, English, or any mix of
these languages. You must understand all of them.
Extract the MEANING, not the words. Always output field values
in English regardless of input language.
Detect and record the primary language of the input.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXTRACTION RULES — READ CAREFULLY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

platform:
  Extract the name of the gig platform (e.g. Swiggy, Zomato,
  Ola, Uber, Urban Company, Dunzo, Blinkit, Zepto).
  If not mentioned → null

event_type:
  Classify the complaint into ONE of these exact values:
    "ACCOUNT_DEACTIVATION"
    "PAYMENT_WITHHELD"
    "UNFAIR_DEDUCTION"
    "FORCED_CANCELLATION"
    "RATING_MANIPULATION"
    "OTHER"
  If unclear → "OTHER"

date:
  Extract any date or time reference for when the event occurred.
  Normalize to ISO format YYYY-MM-DD if possible.
  If only approximate (e.g. "last week", "3 days ago") → record
  as descriptive string, e.g. "approximately 3 days before
  complaint"
  If not mentioned → null

reason:
  Extract the reason given by the platform for the action taken.
  Use the worker's own words, translated to English.
  If no reason was given by the platform → "NO_REASON_PROVIDED"
  If not mentioned at all → null

worker_id:
  Extract any worker ID, driver ID, delivery partner ID, or
  account ID mentioned.
  If not mentioned → null

earnings_withheld:
  Extract any specific amount of money mentioned as withheld,
  deducted, or unpaid. Record as a number in INR.
  If mentioned but amount unclear → "AMOUNT_UNCLEAR"
  If not mentioned → null

notice_provided:
  Did the platform give the worker any prior warning or notice
  before taking action?
  true → worker explicitly says they received a warning
  false → worker explicitly says they received NO warning
  null → not mentioned or unclear

appeal_offered:
  Was the worker given any option to appeal or contest the
  decision?
  true → appeal option was mentioned or offered
  false → worker explicitly says no appeal was offered
  null → not mentioned or unclear

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONFIDENCE SCORING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
For each field, assign a confidence score from 0.0 to 1.0:
  1.0 → explicitly stated, no ambiguity
  0.7 → strongly implied but not directly stated
  0.4 → inferred from context, could be wrong
  0.0 → not present, value is null

overall_confidence:
  The average of all non-null field confidence scores.
  If fewer than 3 fields could be extracted → set
  overall_confidence to 0.2 regardless of individual scores.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INCOMPLETE OR BLURRY INPUT HANDLING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If the input describes a blurry, partial, or unreadable screenshot:
  - Extract only what is clearly legible
  - Set unreadable fields to null
  - Set confidence scores accordingly — never inflate them
  - Set input_quality to "DEGRADED"

If the input is not a complaint at all (irrelevant message):
  - Set event_type to null
  - Set overall_confidence to 0.0
  - Set input_quality to "NOT_A_COMPLAINT"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT — STRICT JSON ONLY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You must return ONLY a valid JSON object.
No explanations. No prose. No markdown. No code blocks.
If you add anything outside the JSON object, you have failed
your task.

Return exactly this structure:

{
  "platform": string | null,
  "event_type": string | null,
  "date": string | null,
  "reason": string | null,
  "worker_id": string | null,
  "earnings_withheld": number | string | null,
  "notice_provided": boolean | null,
  "appeal_offered": boolean | null,
  "language_detected": string,
  "input_quality": "CLEAR" | "DEGRADED" | "NOT_A_COMPLAINT",
  "confidence": {
    "platform": float,
    "event_type": float,
    "date": float,
    "reason": float,
    "worker_id": float,
    "earnings_withheld": float,
    "notice_provided": float,
    "appeal_offered": float,
    "overall": float
  }
}

Respond ONLY with the JSON object. Nothing else."""


def download_image(media_url: str) -> tuple[str, str]:
    with httpx.Client() as http_client:
        response = http_client.get(
            media_url,
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            follow_redirects=True,
            timeout=30.0
        )
        response.raise_for_status()
        media_type = response.headers.get("content-type", "image/jpeg").split(";")[0]
        image_data = base64.standard_b64encode(response.content).decode("utf-8")
        return image_data, media_type


def extract_with_vision(image_data: str, media_type: str) -> dict:
    image_bytes = base64.b64decode(image_data)
    response = gemini_client.models.generate_content(
        model="gemini-1.5-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=media_type),
            EXTRACTION_PROMPT
        ]
    )
    raw = response.text.strip()
    raw = re.sub(r"```json|```", "", raw).strip()
    return json.loads(raw)


def extract_from_text(message: str) -> dict:
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": f"{EXTRACTION_PROMPT}\n\nWorker's message:\n{message}"
            }
        ],
        temperature=0.1
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"```json|```", "", raw).strip()
    return json.loads(raw)


def parser_node(state: GigGuardState) -> GigGuardState:
    print(f"[parser_node] phone={state['phone']} | has_media={state['media_url'] is not None}")
    try:
        if state["media_url"]:
            print(f"[parser_node] downloading image from {state['media_url']}")
            image_data, media_type = download_image(state["media_url"])
            parsed = extract_with_vision(image_data, media_type)
        else:
            print(f"[parser_node] no image, using text extraction")
            parsed = extract_from_text(state["message"])

        print(f"[parser_node] extracted: {parsed}")

        confidence = parsed.get("confidence", 0)
        # Handle new nested confidence format
        if isinstance(confidence, dict):
            confidence = confidence.get("overall", 0)
        if confidence < 0.75:
            return {
                **state,
                "parsed_data": parsed,
                "conversation_state": "AWAITING_SCREENSHOT",
                "error": "low_confidence"
            }

        return {
            **state,
            "parsed_data": parsed,
            "conversation_state": "AWAITING_CONFIRMATION",
            "error": None
        }

    except json.JSONDecodeError as e:
        print(f"[parser_node] JSON parse error: {e}")
        return {
            **state,
            "error": "parse_failed",
            "conversation_state": "AWAITING_SCREENSHOT"
        }
    except Exception as e:
        print(f"[parser_node] error: {e}")
        return {
            **state,
            "error": str(e),
            "conversation_state": "AWAITING_SCREENSHOT"
        }