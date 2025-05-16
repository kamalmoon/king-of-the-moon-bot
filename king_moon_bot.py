
import os
from flask import Flask, request
import requests

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")  # Optional
TELEGRAM_API = f'https://api.telegram.org/bot{BOT_TOKEN}'

def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    requests.post(url, json=payload)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if 'message' in data:
        message = data['message']
        chat_id = message['chat']['id']
        text = message.get('text', '').lower()
        has_photo = 'photo' in message
        has_location = 'location' in message

        if '/start' in text:
            send_message(chat_id, "🌙 *Welcome to KING OF THE MOON PR*\n\nWe deliver drinks, food, hookah & more — straight to your Airbnb, hotel, or beach chair.\n\nTap /location to send your pin\nTap /id to upload your ID\nOnce verified, you’ll get the menu.")
        elif '/location' in text:
            send_message(chat_id, "📍 *Please send your live location.*\n\nTap the 📎 next to your message box → Location → Share Live Location → Choose *1 hour*.\nIf you're on the beach, drop your pin within *6 feet* of where you're sitting.")
        elif '/id' in text:
            send_message(chat_id, "🪪 *Please upload a photo of your ID to confirm you're 18+.*\n\nYou can cover any info except your *name and age.*")
        elif '/menu' in text:
            send_message(chat_id, "🔒 *Menu is locked until you're verified.*\n\nPlease send /location and /id first.")
        elif '/textahuman' in text:
            send_message(chat_id, "📱 *Texting a human may take longer.*\n\nSend a photo of your *ID and address* to 414-265-6510 and a runner will get back to you ASAP.")
        elif has_photo:
            send_message(chat_id, "✅ *Thanks! We received your ID.*\n⏳ *Verification takes 5–10 minutes.*\nWe'll message you when you're approved.")
            if ADMIN_CHAT_ID:
                requests.post(f"{TELEGRAM_API}/forwardMessage", json={
                    "chat_id": ADMIN_CHAT_ID,
                    "from_chat_id": chat_id,
                    "message_id": message['message_id']
                })
        elif has_location:
            send_message(chat_id, "📍 *Location received.*\n⏳ *We’ll match you with a runner in 5–10 min.*\n🧷 If you need help: tap the 📎 → Location → Share Live Location → 1 hour.")
            if ADMIN_CHAT_ID:
                requests.post(f"{TELEGRAM_API}/forwardMessage", json={
                    "chat_id": ADMIN_CHAT_ID,
                    "from_chat_id": chat_id,
                    "message_id": message['message_id']
                })
        else:
            send_message(chat_id, "🤖 *I'm still learning.*\nTry one of these: /start | /location | /id | /menu | /textahuman")
    return 'ok'

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
