
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

PAYMENT_KB = {
    "inline_keyboard": [
        [{"text": "Cash", "callback_data": "pm_cash"}],
        [{"text": "Cash App", "callback_data": "pm_cashapp"}],
        [{"text": "PayPal", "callback_data": "pm_paypal"}],
        [{"text": "Apple Pay", "callback_data": "pm_applepay"}],
        [{"text": "XRP", "callback_data": "pm_xrp"}],
    ]
}

MENU_KB = {
    "inline_keyboard": [
        [{"text": "Cannabis", "callback_data": "menu_cannabis"}],
        [{"text": "Hookah", "callback_data": "menu_hookah"}],
        [{"text": "Liquor", "callback_data": "menu_liquor"}],
    ]
}

MORE_KB = {
    "inline_keyboard": [
        [{"text": "Yes", "callback_data": "more_yes"}],
        [{"text": "No", "callback_data": "more_no"}],
    ]
}

CANNABIS_STRAINS = {
    "pm": "Permanent Marker",
    "ls": "Lemon Smack",
    "km": "Kush Mints",
    "ie": "Island Express",
}

CANNABIS_WEIGHTS = {
    "60": ("1/8th", 60),
    "110": ("7G", 110),
    "200": ("14G", 200),
    "400": ("Oz", 400),
}

HOOKAH_HEADS = {
    "oh": ("Orange Head", 40),
    "gh": ("Grapefruit Head", 50),
}

HOOKAH_FLAVORS = {
    "lm": "Lemon Mint",
    "da": "Double Apple",
    "g": "Grape",
    "gm": "Grape Mint",
}

LIQUOR_OPTIONS = {
    "hen": ("Hennessy", 75),
    "cas": ("Casamigos", 75),
    "req": ("Request something else", 0),
}

def start_order(chat_id):
    sessions[chat_id] = {
        "order": [],
        "total": 0,
    }
    send_message(chat_id, "Select a payment method:", PAYMENT_KB)

def send_menu(chat_id):
    send_message(chat_id, "Choose from the menu:", MENU_KB)

def ask_need_anything(chat_id):
    send_message(chat_id, "Need anything else?", MORE_KB)

def finalize_order(chat_id):
    data = sessions.get(chat_id, {})
    total = data.get("total", 0) + 10
    lines = [*data.get("order", []), "Delivery Fee $10"]
    payment = data.get("payment", "N/A")
    phone = data.get("phone", "N/A")
    text = (
        f"Order Summary:\n" + "\n".join(lines) +
        f"\nTotal: ${total}\nPayment Method: {payment}\nPlease turn on notifications."
    )
    send_message(chat_id, text)
    admin_text = (
        f"User {chat_id}\nPayment: {payment}\nPhone: {phone}\n" + "\n".join(lines) +
        f"\nTotal: ${total}"
    )
    if ADMIN_CHAT_ID:
        send_message(ADMIN_CHAT_ID, admin_text)
        if data.get("id_file"):
            send_photo(ADMIN_CHAT_ID, data["id_file"])
    sessions.pop(chat_id, None)

def handle_photo(chat_id, message):
    user = sessions.get(chat_id)
    if not user or "payment" not in user or user.get("id_file"):
        return
    file_id = message["photo"][-1]["file_id"]
    user["id_file"] = file_id
    send_message(chat_id, "Thanks! Now share your location with /location.")
    if ADMIN_CHAT_ID:
        forward_message(ADMIN_CHAT_ID, chat_id, message["message_id"])

def handle_location(chat_id, message):
    user = sessions.get(chat_id)
    if not user or "payment" not in user or "id_file" not in user:
        return
    user["location"] = message["location"]
    send_menu(chat_id)

def handle_text(chat_id, text):
    user = sessions.setdefault(chat_id, {})
    if text == "/start":
        start_order(chat_id)
        return
    if text == "/id":
        if "payment" not in user:
            send_message(chat_id, "Select a payment method first.")
        elif "id_file" in user:
            send_message(chat_id, "ID already received.")
        else:
            send_message(chat_id, "Please send a photo of your ID.")
        return
    if text == "/location":
        if "payment" not in user:
            send_message(chat_id, "Select a payment method first.")
        elif "id_file" not in user:
            send_message(chat_id, "Upload your ID first using /id.")
        else:
            send_message(chat_id, "Share your live location from Telegram.")
        return
    if user.get("waiting_for_phone"):
        user["phone"] = text
        user.pop("waiting_for_phone")
        ask_need_anything(chat_id)
        return

def handle_callback(callback):
    data = callback["data"]
    chat_id = callback["message"]["chat"]["id"]
    user = sessions.setdefault(chat_id, {"order": [], "total": 0})

    if data.startswith("pm_"):
        method = data[3:]
        user["payment"] = {
            "cash": "Cash",
            "cashapp": "Cash App",
            "paypal": "PayPal",
            "applepay": "Apple Pay",
            "xrp": "XRP",
        }.get(method, method)
        send_message(chat_id, "Upload your ID with /id and send your location with /location.")

    elif data == "menu_cannabis":
        kb = {"inline_keyboard": [[{"text": v, "callback_data": f"c_strain_{k}"}] for k, v in CANNABIS_STRAINS.items()]}
        send_message(chat_id, "Choose a strain:", kb)

    elif data.startswith("c_strain_"):
        code = data.split("_")[-1]
        user["cannabis_strain"] = CANNABIS_STRAINS.get(code)
        kb = {"inline_keyboard": [[{"text": f"{v[0]} ${v[1]}", "callback_data": f"c_weight_{k}"}] for k, v in CANNABIS_WEIGHTS.items()]}
        send_message(chat_id, "Choose amount:", kb)

    elif data.startswith("c_weight_"):
        key = data.split("_")[-1]
        label, price = CANNABIS_WEIGHTS[key]
        strain = user.pop("cannabis_strain", "")
        user["order"].append(f"Cannabis {strain} {label} ${price}")
        user["total"] += price
        ask_need_anything(chat_id)

    elif data == "menu_hookah":
        kb = {"inline_keyboard": [[{"text": f"{v[0]} ${v[1]}", "callback_data": f"h_head_{k}"}] for k, v in HOOKAH_HEADS.items()]}
        send_message(chat_id, "Choose hookah head:", kb)

    elif data.startswith("h_head_"):
        code = data.split("_")[-1]
        user["hookah_head"] = code
        kb = {"inline_keyboard": [[{"text": v, "callback_data": f"h_flavor_{k}"}] for k, v in HOOKAH_FLAVORS.items()]}
        send_message(chat_id, "Choose flavor:", kb)

    elif data.startswith("h_flavor_"):
        code = data.split("_")[-1]
        head_code = user.pop("hookah_head", "oh")
        head_name, price = HOOKAH_HEADS[head_code]
        flavor = HOOKAH_FLAVORS[code]
        user["order"].append(f"Hookah {head_name} {flavor} ${price}")
        user["total"] += price
        ask_need_anything(chat_id)

    elif data == "menu_liquor":
        kb = {"inline_keyboard": [[{"text": f"{v[0]} ${v[1]}", "callback_data": f"l_{k}"}] for k, v in LIQUOR_OPTIONS.items()]}
        send_message(chat_id, "Choose liquor option:", kb)

    elif data.startswith("l_"):
        code = data.split("_")[-1]
        name, price = LIQUOR_OPTIONS[code]
        if code == "req":
            user["waiting_for_phone"] = True
            send_message(chat_id, "Please send your phone number to confirm your request.")
            return
        user["order"].append(f"Liquor {name} ${price}")
        user["total"] += price
        ask_need_anything(chat_id)

    elif data == "more_yes":
        send_menu(chat_id)

    elif data == "more_no":
        finalize_order(chat_id)

def handle_update(update):
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        if "photo" in msg:
            handle_photo(chat_id, msg)
        elif "location" in msg:
            handle_location(chat_id, msg)
        elif "text" in msg:
            handle_text(chat_id, msg["text"].strip())
    elif "callback_query" in update:
        handle_callback(update["callback_query"])

@app.route("/", methods=["GET"])
def index():
    return "Bot is running"

@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(force=True)
    handle_update(update)
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
