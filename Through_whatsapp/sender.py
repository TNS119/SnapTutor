import json
import streamlit as stl
from twilio.rest import Client as TwilioClient


TWILIO_ACCOUNT_SID = stl.secrets["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = stl.secrets["TWILIO_AUTH_TOKEN"]
TWILIO_CONTENT_SID = stl.secrets["TWILIO_CONTENT_SID"]
TWILIO_WHATSAPP_FROM = stl.secrets["TWILIO_WHATSAPP_FROM"]


@stl.cache_resource
def get_twilio_client():
    return TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

twilio_client = get_twilio_client()

def clean_whatsapp_text(text):
    if not text:
        return "No Solution summary available."
    text = " ".join(text.split())  # collapse whitespace/newlines
    return text[:1500] + "..." if len(text) > 1500 else text

def send_to_user(user_name, summary, to_number):
    try:
        content_variables = json.dumps(
            {"1": user_name, "2": clean_whatsapp_text(summary)}, ensure_ascii=False
        )
        message = twilio_client.messages.create(
            from_ = TWILIO_WHATSAPP_FROM,
            to = f"whatsapp: {to_number}", 
            content_sid= TWILIO_CONTENT_SID,
            content_variables= content_variables,
        )
        return True,message.sid
    except Exception as error:
        return False, str(error)