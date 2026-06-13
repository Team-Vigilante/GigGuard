from fastapi import APIRouter, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from app.router import handle_message

router = APIRouter()


@router.post("/webhook/whatsapp")
async def receive_whatsapp(request: Request):
    form_data = await request.form()

    phone = form_data.get("From", "")
    message = form_data.get("Body", "").strip()
    media_url = form_data.get("MediaUrl0", None)
    media_type = form_data.get("MediaContentType0", None)

    print("=" * 50)
    print(f"FROM: {phone}")
    print(f"BODY: {message}")
    print(f"MEDIA URL: {media_url}")
    print(f"MEDIA TYPE: {media_type}")
    print("=" * 50)

    response_text = await handle_message(
        phone=phone,
        message=message,
        media_url=media_url,
        media_type=media_type
    )

    twiml = MessagingResponse()
    twiml.message(response_text)
    return Response(content=str(twiml), media_type="application/xml")