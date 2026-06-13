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

EXTRACTION_PROMPT = """You are an AI assistant helping gig workers in India fight unfair 
platform decisions. Analyze the provided input and extract case information.

Extract the following fields:
- platform: the platform name (Swiggy, Zomato, Ola, Uber, Blinkit, Zepto, or "Unknown")
- event_type: what happened (deactivation, wage_cut, penalty, rating_drop, or "Unknown")
- date: when it happened (any format found, or null)
- reason: stated reason given by platform (or null if none given)
- worker_id: worker/driver ID if visible (or null)
- earnings_withheld: amount withheld in rupees as a number (or null)
- notice_provided: true if advance notice was given, false if not, null if unclear
- appeal_offered: true if appeal option was offered, false if not, null if unclear
- confidence: your confidence in this extraction as a decimal between 0 and 1

Respond ONLY with a valid JSON object. No explanation, no markdown, no backticks."""


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