
import os
from flask import Flask, request
import requests

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
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
        chat_id = data['message']['chat']['id']
        text = data['message'].get('text', '').lower()

        if '/start' in text:
            send_message(chat_id, "Welcome to *King of the Moon PR* 🌙\n\nTap /location to send your pin\nTap /id to upload your ID\nOnce verified, we’ll send you the menu.")
        elif '/location' in text:
            send_message(chat_id, "📍 Please send your *live location*.\nTap the 📎 → Location → Share Live Location → 1 hour.")
        elif '/id' in text:
            send_message(chat_id, "🪪 Please upload a photo of your *ID* to confirm you're 18+.\nCover anything except name and age.")
        elif '/menu' in text:
            send_message(chat_id, "🔒 *Menu is locked until verification.*\nPlease send /location and /id first.")
        else:
            send_message(chat_id, "Sorry, I didn’t understand that. Try /start, /location, /id, or /menu.")
    return 'ok'

if __name__ == '__main__':
   app.run(host="0.0.0.0", port=5000)

