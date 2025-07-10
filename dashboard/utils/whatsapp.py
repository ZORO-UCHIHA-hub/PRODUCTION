# dashboard/utils/whatsapp.py
from twilio.rest import Client
from django.conf import settings

def send_whatsapp_message(to_number, message):
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=settings.TWILIO_WHATSAPP_FROM,  # Example: 'whatsapp:+14155238886'
            to=f'whatsapp:{to_number}'            # Example: 'whatsapp:+919999999999'
        )
    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")