import asyncio
import streamlit as stl
from telegram import Bot
 
TELEGRAM_BOT_TOKEN = stl.secrets["TELEGRAM_BOT_TOKEN"]
 
 
def send_telegram(chat_id, text):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    asyncio.run(bot.send_message(chat_id=chat_id, text=text))
