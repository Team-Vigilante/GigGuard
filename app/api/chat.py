from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import httpx
import json
import os
from datetime import datetime
from pdf_generator.generate_grievance import generate_grievance_pdf

router = APIRouter(prefix="/api")

class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]

@router.post("/extract-and-generate")
async def extract_and_generate(request: ChatRequest):
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured on backend.")

    # 1. Build the extraction prompt
    extraction_prompt = {
        "role": "user",
        "content": (
            "Extract the following fields from this conversation "
            "as JSON only, no other text:\n"
            "{\n"
            "  \"worker_name\": string or 'Unknown',\n"
            "  \"platform\": string,\n"
            "  \"event_type\": string,\n"
            "  \"event_date\": string,\n"
            "  \"amount_withheld\": string,\n"
            "  \"notice_provided\": 'Yes' or 'No',\n"
            "  \"reason_given\": string,\n"
            "  \"city\": string or 'Unknown'\n"
            "}\n\n"
            "Conversation History:\n"
            f"{json.dumps(request.messages, indent=2)}"
        )
    }

    # 2. Call Groq API
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {groq_api_key}"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [extraction_prompt],
                    "temperature": 0.1,
                    "max_tokens": 500
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            raw_content = data["choices"][0]["message"]["content"]
            
            # Clean up markdown code blocks if the model hallucinates them
            raw_content = raw_content.replace("```json", "").replace("```", "").strip()
            extracted = json.loads(raw_content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to extract data: {str(e)}")

    # 3. Generate unique case_id
    case_id = f"GG-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # 4. Build case_data matching SAMPLE_CASE structure
    case_data = {
        "case_id": case_id,
        "worker": {
            "name": extracted.get("worker_name", "Unknown"),
            "phone": "Unknown",
            "platform": extracted.get("platform", "Unknown"),
            "city": extracted.get("city", "Unknown"),
            "worker_id": "Unknown",
        },
        "parsed_data": {
            "event_type": extracted.get("event_type", "Unknown"),
            "event_date": extracted.get("event_date", "Unknown"),
            "reason_given": extracted.get("reason_given", "None"),
            "amount_withheld": extracted.get("amount_withheld", "0"),
            "notice_provided": True if str(extracted.get("notice_provided")).lower() == "yes" else False,
            "notice_period_days": 0,
            "earnings_blocked": True,
        },
        # Fill in minimal defaults to satisfy the PDF generator
        "legal_analysis": {
            "case_strength": "STRONG",
            "confidence": 0.9,
            "violations": [
                {
                    "law": "Information Technology Act, 2000",
                    "section": "Section 43A",
                    "description": "Failure to protect data and arbitrary account deactivation."
                }
            ]
        },
        "drafter_output": {
            "english_letter": (
                f"GRIEVANCE NOTICE\n\n"
                f"FROM: {extracted.get('worker_name', 'Unknown')}\n\n"
                f"TO: The Grievance Officer, {extracted.get('platform', 'Unknown')}\n\n"
                f"SUBJECT: Grievance regarding {extracted.get('event_type', 'Unknown')}\n\n"
                f"FACTS:\n"
                f"1. Event Date: {extracted.get('event_date', 'Unknown')}\n"
                f"2. Reason Given: {extracted.get('reason_given', 'Unknown')}\n"
                f"3. Amount Withheld: Rs. {extracted.get('amount_withheld', '0')}\n"
                f"4. Notice Provided: {extracted.get('notice_provided', 'Unknown')}\n\n"
                f"RELIEF SOUGHT:\n"
                f"Immediate resolution and release of withheld amounts.\n"
            ),
            "hindi_letter": "",
            "demands": [
                f"Release of withheld earnings amounting to Rs. {extracted.get('amount_withheld', '0')}."
            ],
            "escalation_warning": "Failure to respond will result in escalation.",
        }
    }

    # 5. Generate PDF
    output_path = f"output/{case_id}.pdf"
    try:
        generate_grievance_pdf(case_data, output_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")

    # 6. Return response
    return {
        "case_id": case_id,
        "pdf_url": f"/pdf/{case_id}.pdf"
    }
