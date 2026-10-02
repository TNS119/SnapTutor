import smtplib
import streamlit as stl
from email.mime.text import MIMEText
 
GMAIL_ADDRESS = stl.secrets["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = stl.secrets["GMAIL_APP_PASSWORD"]

def send_email(user_name, subject, body, to_address):
    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = GMAIL_ADDRESS
    message["To"] = to_address

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(message)
