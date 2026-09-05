"""
RENDER DEPLOY READY - ZEVRIC BIND EMAIL BOT
Deploy type: Web Service (Flask + Bot polling in background thread)

Render pe isko Web Service ke tarah deploy karna.

ENV VAR:
BOT_TOKEN = your telegram bot token from BotFather

Start Command: python render_bot.py
"""

import os
import threading
import requests
import urllib.parse
import re
import telebot
from telebot import types
from flask import Flask

# ================= CONFIG =================
# Render pe Environment Variable se lega, local pe fallback
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
PORT = int(os.getenv("PORT", 10000))

if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    print("WARNING: BOT_TOKEN set nahi hai! Render pe Environment Variable add karo.")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)

# Store user data
user_states = {}
user_tokens = {}

HEADERS = {
    "User-Agent": "GarenaMSDK/4.0.30",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json"
}

def is_garena_token(text):
    t = text.strip()
    if len(t) < 80:
        return False
    if len(t) > 150:
        return True
    if re.fullmatch(r'[a-fA-F0-9]+', t) and len(t) > 100:
        return True
    return False

def get_player_info(access_token):
    try:
        url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        parsed = urllib.parse.urlparse(res.url)
        params = urllib.parse.parse_qs(parsed.query)
        uid = params.get("account_id", ["Unknown"])[0]
        nickname = urllib.parse.unquote(params.get("nickname", ["Unknown"])[0])
        region = params.get("region", ["Unknown"])[0]
        return uid, nickname, region
    except:
        return "Unknown", "Unknown", "Unknown"

def get_bind_info_api(access_token):
    url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
    payload = {'app_id': "100067", 'access_token': access_token}
    headers = {'User-Agent': "GarenaMSDK/4.0.19P9"}
    try:
        r = requests.get(url, params=payload, headers=headers, timeout=15)
        return r.json()
    except Exception as e:
        return {"email": "", "email_to_be": "", "request_exec_countdown": 0, "error": str(e)}

def convert_seconds(s):
    try:
        s = int(s)
        d, h = divmod(s, 86400)
        h, m = divmod(h, 3600)
        m, s = divmod(m, 60)
        return f"{d}D {h}H {m}M {s}S"
    except:
        return str(s)

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("Add Recovery Email"),
        types.KeyboardButton("Check Recovery Email"),
        types.KeyboardButton("Check Platform"),
        types.KeyboardButton("Cancel Recovery Email"),
        types.KeyboardButton("Unbind Email"),
        types.KeyboardButton("Change Bind Email"),
        types.KeyboardButton("Update Bio"),
        types.KeyboardButton("Get Token Details"),
        types.KeyboardButton("Eat Token Website"),
        types.KeyboardButton("Revoke Access Token"),
    )
    markup.add(types.KeyboardButton("Send Single Unsubscribe OTP"))
    markup.add(types.KeyboardButton("How To Use @GarenaEmailBot"))
    markup.add(types.KeyboardButton("🎫 Eat-Token"))
    return markup

def send_status(chat_id, access_token):
    uid, nick, region = get_player_info(access_token)
    bind = get_bind_info_api(access_token)
    email = bind.get("email", "")
    email_to_be = bind.get("email_to_be", "")
    countdown = bind.get("request_exec_countdown", 0)
    confirmed = email if email else "No Email Bound"
    if email and not email_to_be:
        status = f"Confirmed: {email}"
    elif email_to_be:
        status = f"Pending: {email_to_be} ({convert_seconds(countdown)})"
    else:
        status = "No Email"
    user_tokens[chat_id] = access_token
    msg1 = f"<b>Email Status for {nick}</b>\n\n<b>Confirmed Email:</b> {confirmed}\n<b>Status:</b> {status}\n\n<b>UID:</b> <code>{uid}</code> | <b>Region:</b> {region}"
    bot.send_message(chat_id, msg1)
    inline = types.InlineKeyboardMarkup()
    inline.add(types.InlineKeyboardButton("Subscribe YouTube Channel ↗", url="https://youtube.com/@zevricxplay"))
    bot.send_message(chat_id, "Main Menu - Please select an option:", reply_markup=main_menu())
    bot.send_message(chat_id, "Updates ke liye:", reply_markup=inline)

# ================= BOT COMMANDS =================
@bot.message_handler(commands=['start', 'help'])
def cmd_start(message):
    txt = """
<b>🔥 ZEVRIC BIND BOT - RENDER LIVE</b>

<b>Direct:</b> Token direct bhejo - auto check hoga
<b>Commands:</b>
/check <code>TOKEN</code> - Bind info
/cancel <code>TOKEN</code> - Cancel pending
/revoke <code>TOKEN</code> - Logout
/eat <code>EAT_TOKEN</code> - EAT to Access
/bind - Add Email
/unbind - Unbind
/change - Change Email
/bio - Update Bio
/platform - Platform info

Neeche buttons se bhi use kar sakte ho 👇
    """
    bot.send_message(message.chat.id, txt, reply_markup=main_menu())

@bot.message_handler(commands=['check'])
def cmd_check(message):
    parts = message.text.split(maxsplit=1)
    token = parts[1].strip() if len(parts) > 1 else user_tokens.get(message.chat.id)
    if not token:
        bot.reply_to(message, "Usage: /check YOUR_TOKEN")
        return
    send_status(message.chat.id, token)

@bot.message_handler(commands=['cancel'])
def cmd_cancel(message):
    parts = message.text.split(maxsplit=1)
    token = parts[1].strip() if len(parts) > 1 else user_tokens.get(message.chat.id)
    if not token:
        bot.reply_to(message, "Usage: /cancel YOUR_TOKEN")
        return
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
        data = {"app_id": "100067", "access_token": token}
        r = requests.post(url, headers=HEADERS, data=data, timeout=15)
        if r.json().get("result") == 0:
            bot.reply_to(message, "✅ Cancel SUCCESS")
        else:
            bot.reply_to(message, f"❌ Failed: {r.text[:800]}")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['revoke'])
def cmd_revoke(message):
    parts = message.text.split(maxsplit=1)
    token = parts[1].strip() if len(parts) > 1 else user_tokens.get(message.chat.id)
    if not token:
        bot.reply_to(message, "Usage: /revoke YOUR_TOKEN")
        return
    try:
        refresh = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
        url = f"https://100067.connect.garena.com/oauth/logout?access_token={token}&refresh_token={refresh}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if r.status_code == 200 and "error" not in r.text:
            bot.reply_to(message, "✅ Token Revoked Successfully")
        else:
            bot.reply_to(message, f"❌ Failed: {r.text[:500]}")
    except Exception as e:
        bot.reply_to(message, f"❌ {e}")

@bot.message_handler(commands=['eat'])
def cmd_eat(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /eat EAT_TOKEN")
        return
    user_input = parts[1].strip()
    eat_token = None
    if "http" in user_input or "eat=" in user_input:
        parsed = urllib.parse.urlparse(user_input)
        qs = urllib.parse.parse_qs(parsed.query)
        if 'eat' in qs:
            eat_token = qs['eat'][0]
    else:
        eat_token = user_input
    try:
        api_url = f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
        r = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=15)
        parsed_final = urllib.parse.urlparse(r.url)
        final_params = urllib.parse.parse_qs(parsed_final.query)
        if 'access_token' in final_params:
            access_token = final_params['access_token'][0]
            account_id = final_params.get('account_id', ['Unknown'])[0]
            nickname = urllib.parse.unquote(final_params.get('nickname', ['Unknown'])[0])
            region = final_params.get('region', ['Unknown'])[0]
            bot.reply_to(message, f"<b>✅ EAT Converted</b>\n├ {nickname}\n├ {account_id}\n└ <code>{access_token}</code>")
            user_tokens[message.chat.id] = access_token
        else:
            bot.reply_to(message, "❌ EAT invalid / expired")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['bind'])
def cmd_bind(message):
    bot.reply_to(message, "📩 Access Token bhejo:")
    user_states[message.chat.id] = {"action": "bind", "step": "token"}

@bot.message_handler(commands=['unbind'])
def cmd_unbind(message):
    token = user_tokens.get(message.chat.id)
    if not token:
        bot.reply_to(message, "Pehle token bhejo")
        return
    try:
        bind = get_bind_info_api(token)
        email = bind.get("email")
        if not email:
            bot.reply_to(message, "❌ Koi email bound nahi hai!")
            return
        url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
        data = {"email": email, "locale": "en_PK", "region": "PK", "app_id": "100067", "access_token": token}
        r = requests.post(url, headers=HEADERS, data=data, timeout=15)
        if r.json().get("result") == 0:
            bot.send_message(message.chat.id, f"✅ OTP bheja {email} pe. OTP bhejo:")
            user_states[message.chat.id] = {"action": "unbind", "step": "otp", "token": token, "email": email}
        else:
            bot.reply_to(message, f"❌ OTP Fail: {r.text[:500]}")
    except Exception as e:
        bot.reply_to(message, f"❌ {e}")

@bot.message_handler(commands=['change'])
def cmd_change(message):
    token = user_tokens.get(message.chat.id)
    if not token:
        bot.reply_to(message, "Pehle token bhejo")
        return
    try:
        bind = get_bind_info_api(token)
        old_email = bind.get("email")
        if not old_email:
            bot.reply_to(message, "❌ Pehle se email nahi hai. /bind use karo")
            return
        url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
        data = {"email": old_email, "locale": "en_PK", "region": "PK", "app_id": "100067", "access_token": token}
        r = requests.post(url, headers=HEADERS, data=data, timeout=15)
        if r.json().get("result") == 0:
            bot.send_message(message.chat.id, f"✅ OTP bheja {old_email} pe. OTP bhejo:")
            user_states[message.chat.id] = {"action": "change", "step": "old_otp", "token": token, "old_email": old_email}
        else:
            bot.reply_to(message, f"❌ Fail: {r.text[:500]}")
    except Exception as e:
        bot.reply_to(message, f"❌ {e}")

@bot.message_handler(commands=['bio'])
def cmd_bio(message):
    token = user_tokens.get(message.chat.id)
    if not token:
        bot.reply_to(message, "Pehle token bhejo fir /bio")
        return
    bot.reply_to(message, "Naya Bio bhejo:")
    user_states[message.chat.id] = {"action": "update_bio", "step": "bio", "token": token}

# Buttons
@bot.message_handler(func=lambda m: m.text == "Check Recovery Email")
def btn_check(m): cmd_check(m)
@bot.message_handler(func=lambda m: m.text == "Add Recovery Email")
def btn_add(m): cmd_bind(m)
@bot.message_handler(func=lambda m: m.text == "Cancel Recovery Email")
def btn_cancel(m): cmd_cancel(m)
@bot.message_handler(func=lambda m: m.text == "Revoke Access Token")
def btn_revoke(m): cmd_revoke(m)
@bot.message_handler(func=lambda m: m.text == "Unbind Email")
def btn_unbind(m): cmd_unbind(m)
@bot.message_handler(func=lambda m: m.text == "Change Bind Email")
def btn_change(m): cmd_change(m)
@bot.message_handler(func=lambda m: m.text == "Update Bio")
def btn_bio(m): cmd_bio(m)

# Main text handler for flows + auto token detection
@bot.message_handler(func=lambda m: True)
def all_text(message):
    chat_id = message.chat.id
    text = message.text.strip()
    if is_garena_token(text) and chat_id not in user_states:
        send_status(chat_id, text)
        return
    if chat_id not in user_states:
        return
    state = user_states[chat_id]
    action = state.get("action")
    if action == "bind":
        if state["step"] == "token":
            state["token"] = text
            user_tokens[chat_id] = text
            uid, nick, region = get_player_info(text)
            bot.send_message(chat_id, f"✅ {nick} ({uid}) | {region}\nAb email bhejo:")
            state["step"] = "email"
        elif state["step"] == "email":
            state["email"] = text
            try:
                url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
                data = {"email": text, "locale": "en_PK", "region": "PK", "app_id": "100067", "access_token": state["token"]}
                r = requests.post(url, headers=HEADERS, data=data, timeout=15)
                if r.json().get("result") == 0:
                    bot.send_message(chat_id, f"✅ OTP bheja {text} pe. OTP bhejo:")
                    state["step"] = "otp"
                else:
                    bot.send_message(chat_id, f"❌ OTP Fail: {r.text[:600]}")
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}")
        elif state["step"] == "otp":
            state["otp"] = text
            try:
                url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
                data = {"app_id": "100067", "access_token": state["token"], "email": state["email"], "code": text, "otp": text, "type": "1"}
                r = requests.post(url, headers=HEADERS, data=data, timeout=15)
                verifier = r.json().get("verifier_token")
                if verifier:
                    state["verifier_token"] = verifier
                    bot.send_message(chat_id, "✅ OTP Verified! Ab 6-digit code bhejo (ex: 123456):")
                    state["step"] = "sec_code"
                else:
                    bot.send_message(chat_id, f"❌ Verify Fail: {r.text[:600]}")
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}")
        elif state["step"] == "sec_code":
            try:
                url = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
                data = {"email": state["email"], "app_id": "100067", "access_token": state["token"], "verifier_token": state["verifier_token"], "secondary_password": text}
                r = requests.post(url, headers=HEADERS, data=data, timeout=15)
                if r.json().get("result") == 0:
                    bot.send_message(chat_id, f"✅ BIND SUCCESS! {state['email']} pending.")
                else:
                    bot.send_message(chat_id, f"❌ Bind Fail: {r.text[:800]}")
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}")
            del user_states[chat_id]
    elif action == "unbind" and state["step"] == "otp":
        try:
            url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
            data = {"email": state["email"], "app_id": "100067", "access_token": state["token"], "otp": text}
            r = requests.post(url, headers=HEADERS, data=data, timeout=15)
            identity = r.json().get("identity_token")
            if not identity:
                bot.send_message(chat_id, f"❌ Fail: {r.text[:600]}")
                del user_states[chat_id]
                return
            url2 = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
            data2 = {"app_id": "100067", "access_token": state["token"], "identity_token": identity}
            r2 = requests.post(url2, headers=HEADERS, data=data2, timeout=15)
            if r2.json().get("result") == 0:
                bot.send_message(chat_id, "✅ Unbind Request SUCCESS!")
            else:
                bot.send_message(chat_id, f"❌ Fail: {r2.text[:800]}")
        except Exception as e:
            bot.send_message(chat_id, f"❌ {e}")
        del user_states[chat_id]
    elif action == "change":
        if state["step"] == "old_otp":
            try:
                url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
                data = {"email": state["old_email"], "app_id": "100067", "access_token": state["token"], "otp": text}
                r = requests.post(url, headers=HEADERS, data=data, timeout=15)
                identity = r.json().get("identity_token")
                if not identity:
                    bot.send_message(chat_id, f"❌ Fail: {r.text[:600]}")
                    del user_states[chat_id]
                    return
                state["identity_token"] = identity
                bot.send_message(chat_id, "✅ Old Verified! Naya email bhejo:")
                state["step"] = "new_email"
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}")
                del user_states[chat_id]
        elif state["step"] == "new_email":
            state["new_email"] = text
            try:
                url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
                data = {"email": text, "locale": "en_PK", "region": "PK", "app_id": "100067", "access_token": state["token"]}
                r = requests.post(url, headers=HEADERS, data=data, timeout=15)
                if r.json().get("result") == 0:
                    bot.send_message(chat_id, f"✅ OTP bheja {text} pe. OTP bhejo:")
                    state["step"] = "new_otp"
                else:
                    bot.send_message(chat_id, f"❌ Fail: {r.text[:600]}")
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}")
        elif state["step"] == "new_otp":
            try:
                url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
                data = {"email": state["new_email"], "app_id": "100067", "access_token": state["token"], "otp": text}
                r = requests.post(url, headers=HEADERS, data=data, timeout=15)
                verifier = r.json().get("verifier_token")
                if not verifier:
                    bot.send_message(chat_id, f"❌ Verify Fail: {r.text[:600]}")
                    del user_states[chat_id]
                    return
                url2 = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
                data2 = {"identity_token": state["identity_token"], "email": state["new_email"], "app_id": "100067", "verifier_token": verifier, "access_token": state["token"]}
                r2 = requests.post(url2, headers=HEADERS, data=data2, timeout=15)
                if r2.json().get("result") == 0:
                    bot.send_message(chat_id, f"✅ Change SUCCESS! {state['new_email']} pending.")
                else:
                    bot.send_message(chat_id, f"❌ Fail: {r2.text[:800]}")
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}")
            del user_states[chat_id]

# ================= FLASK APP FOR RENDER =================
@app.route('/')
def home():
    return "✅ ZEVRIC BOT IS RUNNING - Telegram Bot is Live!"

@app.route('/health')
def health():
    return "OK", 200

def run_bot():
    print("🤖 Starting Telegram Bot Polling...")
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"Bot polling error: {e}")
        # Restart after 5 sec
        import time
        time.sleep(5)
        run_bot()

if __name__ == "__main__":
    # Start bot in background thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Start Flask for Render health check
    print(f"🌐 Starting Flask on port {PORT}")
    app.run(host='0.0.0.0', port=PORT)
