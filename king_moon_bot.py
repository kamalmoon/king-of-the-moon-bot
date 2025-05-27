import os
import json
from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")
API_URL = f"https://api.telegram.org/bot{TOKEN}/"

sessions = {}

def send_message(chat_id, text, keyboard=None):
    data = {"chat_id": chat_id, "text": text}
    if keyboard:
        data["reply_markup"] = json.dumps(keyboard)
    requests.post(API_URL + "sendMessage", data=data)

def forward_message(chat_id, from_chat, message_id):
    data = {
        "chat_id": chat_id,
        "from_chat_id": from_chat,
        "message_id": message_id,
    }
    requests.post(API_URL + "forwardMessage", data=data)

def send_photo(chat_id, file_id, caption=None):
    data = {"chat_id": chat_id, "photo": file_id}
    if caption:
        data["caption"] = caption
    requests.post(API_URL + "sendPhoto", data=data)

@app.route("/", methods=["GET"])
def index():
    return "Bot is running"

@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(force=True)
    print("📥 Webhook called")
    print(json.dumps(update, indent=2))  # Debug print full incoming data
    handle_update(update)
    return "ok"

def handle_update(update):
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        print(f"📨 Message received from {chat_id}")

        if "text" in msg:
            text = msg["text"].strip()
            print(f"💬 Text: {text}")
            handle_text(chat_id, text)
        elif "photo" in msg:
            print("📸 Photo received")
            # handle_photo(chat_id, msg)
        elif "location" in msg:
            print("📍 Location received")
            # handle_location(chat_id, msg)

    elif "callback_query" in update:
        print("🔘 Callback received")
        # handle_callback(update["callback_query"])

def handle_text(chat_id, text):
    if text == "/start":
        print(f"✅ /start detected from {chat_id}")
        sessions[chat_id] = {"order": [], "total": 0}
        send_message(chat_id, "✅ Welcome! Upload your ID with /id and send your location with /location. Use /menu to start your order.")
    elif text == "/id":
        send_message(chat_id, "📸 Please upload a photo of your ID.")
    elif text == "/location":
        send_message(chat_id, "📍 Please share your live location.")
    elif text == "/menu":
        send_message(chat_id, "📋 Menu: [Cannabis, Hookah, Liquor]")
    else:
        send_message(chat_id, "🤖 I didn’t understand that. Try /start, /id, /location, or /menu.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
