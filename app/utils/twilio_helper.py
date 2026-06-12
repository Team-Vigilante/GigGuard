from twilio.rest import Client
from app.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
import logging

logger = logging.getLogger(__name__)

def get_twilio_client():
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

async def send_whatsapp_message(to: str, body: str):
    try:
        client = get_twilio_client()
        message = client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            to=to,
            body=body
        )
        logger.info(f"Message sent to {to}: SID {message.sid}")
        return message.sid
    except Exception as e:
        logger.error(f"Failed to send message to {to}: {e}")
        raise
