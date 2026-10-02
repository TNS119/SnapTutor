import os
import streamlit as stl
from google import genai
from google.genai import types

import smtplib
from email.mime.text import MIMEText



from prompts import SYSTEM_PROMPT,WELCOME_MESSAGE_TEMPLATE,SUMMARY_REQUEST_PROMPT,SUBJECT_REQUEST_PROMPT

from Through_whatsapp.sender import send_to_user
from Through_gmail.sender import send_email
from Through_telegram.sender import send_telegram


GEMINI_API_KEY = stl.secrets["GEMINI_API_KEY"]


@stl.cache_resource
def get_gemini_client():
    return genai.Client(api_key= GEMINI_API_KEY)


gemini_client = get_gemini_client()
MODEL_NAME = "gemini-3.5-flash"

def render_message(message):
    with stl.chat_message(message["role"]):
        if message["type"] == "text":
            stl.write(message["content"])
        elif message["type"] == "image":
            stl.image(message["content"])
            

def add_message(role,type,content):
    stl.session_state.messages.append({"role":role,"type":type,"content":content})
    render_message(stl.session_state.messages[-1])


def ask_gemini(parts):
    try:
        return stl.session_state.chat.send_message(parts).text
    except Exception as error:
        return f"Sorry, something went wrong: {error}"

        

if (
    "onboarded" not in stl.session_state
    or "delivery_channel" not in stl.session_state
    or "delivery_recipient" not in stl.session_state
):
    stl.title("SnapTutor 🎓")
    stl.caption("Snap & Learn, With Clarity.")

    if stl.session_state.get("onboarding_step", 1) == 1:
        with stl.form("onboarding_channel_form"):
            name = stl.text_input("Your name")
            delivery_channel = stl.selectbox(
                "Choose how to receive your study summary",
                ("WhatsApp", "Telegram", "Gmail"),
                key="onboarding_delivery_channel",
            )
            continue_onboarding = stl.form_submit_button("Continue")

        if continue_onboarding:
            if not name.strip():
                stl.warning("Enter your name to continue.")
            else:
                stl.session_state.name = name.strip()
                stl.session_state.delivery_channel = delivery_channel
                stl.session_state.onboarding_step = 2
                stl.rerun()
    else:
        delivery_channel = stl.session_state.delivery_channel
        with stl.form("onboarding_recipient_form"):
            if delivery_channel == "WhatsApp":
                recipient = stl.text_input(
                    "WhatsApp number (with country code)",
                    placeholder="+91XXXXXXXXXX",
                )
            elif delivery_channel == "Telegram":
                recipient = stl.text_input(
                    "Telegram chat ID",
                    help="Start a chat with your Telegram bot, then enter your chat ID here",
                )
            else:
                recipient = stl.text_input("Gmail address", type="email")
            finish_onboarding = stl.form_submit_button("Start tutoring")

        if stl.button("Change delivery method"):
            stl.session_state.onboarding_step = 1
            stl.rerun()

        if finish_onboarding:
            if not recipient.strip():
                stl.warning("Enter the selected delivery address to continue.")
            else:
                stl.session_state.delivery_recipient = recipient.strip()
                stl.session_state.chat = gemini_client.chats.create(
                    model=MODEL_NAME,
                    config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
                )
                stl.session_state.messages = []
                stl.session_state.onboarded = True
                stl.session_state.onboarding_step = 3
                stl.rerun()
    stl.stop()

head_col, action_col = stl.columns([5, 2], vertical_alignment="center")

with head_col:
    stl.title("SnapTutor ")

with action_col:
    send_disable = len(stl.session_state.messages) <= 1
    if stl.button("Send summary", disabled=send_disable, use_container_width=True):
        delivery_channel = stl.session_state.delivery_channel
        recipient = stl.session_state.delivery_recipient
        try:
            with stl.spinner("Preparing and sending your study summary..."):
                summary = ask_gemini([SUMMARY_REQUEST_PROMPT])

                if delivery_channel == "WhatsApp":
                    success, info = send_to_user(
                        stl.session_state.name,
                        summary,
                        recipient,
                    )
                elif delivery_channel == "Telegram":
                    send_telegram(recipient, summary)
                    success, info = True, "Telegram message sent."
                else:
                    subject = "Your Snap Tutor study summary"
                    if SUBJECT_REQUEST_PROMPT.strip():
                        generated_subject = ask_gemini([SUBJECT_REQUEST_PROMPT]).strip()
                        if generated_subject and not generated_subject.startswith(
                            "Sorry, something went wrong:"
                        ):
                            subject = generated_subject.replace("\r", " ").replace("\n", " ")
                    subject = f"{stl.session_state.name} - {subject}"
                    send_email(
                        stl.session_state.name,
                        subject,
                        summary,
                        recipient,
                    )
                    success, info = True, "Email sent."

            if success:
                stl.success(f"Summary sent via {delivery_channel}.")
            else:
                stl.error(f"Could not send summary: {info}")
        except Exception as error:
            stl.error(f"Could not send summary via {delivery_channel}: {error}")

    
stl.caption(
    f"Hello, {stl.session_state.name}. Your summaries are sent via "
    f"{stl.session_state.delivery_channel}."
)
        
if not stl.session_state.messages:
    add_message("asistant","text", WELCOME_MESSAGE_TEMPLATE.format(name=stl.session_state.name))
else:
    for message in stl.session_state.messages:
        render_message(message)

user_input = stl.chat_input(
    "Ask a question, or attach a snap of your doubt....",
    accept_file=True,
    file_type=["jpg","jpeg","png"],
)

if user_input:
    photo = user_input.files[0] if user_input.files else None
    text = user_input.text
    parts = []
    
    if photo is not None:
        photo_bytes = photo.getvalue()
        add_message("user","image",photo_bytes)
        parts.append(types.Part.from_bytes(data= photo_bytes, mime_type= photo.type))
    if text:
        add_message("user","text",text)
        parts.append(text)
    elif photo is not None:
        parts.append("What is this about? and solve/clarify it accordingly.")
    
    with stl.spinner("crunching the nummbers......"):
        answer = ask_gemini(parts)
    add_message("assistant", "text", answer)
        
        