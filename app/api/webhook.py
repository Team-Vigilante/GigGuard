from fastapi import APIRouter, Form
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
import logging
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/webhook/whatsapp", response_class=PlainTextResponse)
async def receive_whatsapp(
    From: str = Form(...),
    Body: str = Form(...),
    MediaUrl0: Optional[str] = Form(None),
    MediaContentType0: Optional[str] = Form(None),
    NumMedia: Optional[str] = Form("0")
):
    logger.info(f"Incoming message from {From}")
    logger.info(f"Message body: {Body}")
    logger.info(f"Media URL: {MediaUrl0}")
    logger.info(f"Media type: {MediaContentType0}")

    print("=" * 50)
    print(f"FROM: {From}")
    print(f"BODY: {Body}")
    print(f"MEDIA URL: {MediaUrl0}")
    print(f"MEDIA TYPE: {MediaContentType0}")
    print("=" * 50)

    response = MessagingResponse()

    if MediaUrl0 and MediaContentType0 and MediaContentType0.startswith("image"):
        response.message("Screenshot mil gayi. Processing kar raha hoon... thoda wait karo.")
    else:
        response.message("Namaste! Aapka message mila. Main aapki madad karunga.")

    return PlainTextResponse(str(response), media_type="application/xml")
