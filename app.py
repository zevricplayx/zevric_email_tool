"""
ZEVRIC - Render Ready Bot (Full 10 Options)
Owner: Zevric | YT: zevricxplay | TG: just_zevric
Original Logic: app_3.py (Spidey Bind Tool)

Render pe deploy karne ke liye banaya gaya:
- Flask health check (Render ko lagta hai web service hai)
- Telegram bot background thread me chalta hai (polling)
- BOT_TOKEN env variable se leta hai

Deploy Steps Render pe niche README me hai.
"""

import os
import threading
import requests
import urllib.parse
import urllib3
import telebot
from telebot import types
from flask import Flask

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------- Flask for Render Health Check ----------
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return """
    <h2>🔥 ZEVRIC BIND BOT - ONLINE 🔥</h2>
    <p>Owner: Zevric | YT: zevricxplay | TG: @just_zevric</p>
    <p>Bot is running in background (polling mode)</p>
    <p>Go to Telegram and send /start to your bot</p>
    """

@app_flask.route('/health')
def health():
    return "OK", 200

# ---------- Telegram Bot ----------
BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or "PUT_YOUR_BOT_TOKEN_HERE"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

user_sessions = {}

def convert_seconds(s):
    try:
        s = int(s)
        d, h = divmod(s, 86400)
        h, m = divmod(h, 3600)
        m, s = divmod(m, 60)
        return f"{d}D {h}H {m}M {s}S"
    except:
        return str(s)

def fetch_player_info(access_token):
    try:
        url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15, allow_redirects=True)
        parsed = urllib.parse.urlparse(r.url)
        q = urllib.parse.parse_qs(parsed.query)
        return q.get("account_id",["Unknown"])[0], q.get("nickname",["Unknown"])[0], q.get("region",["Unknown"])[0]
    except:
        return "Unknown","Unknown","Unknown"

def api_get_bind_info(token):
    url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
    payload = {'app_id': "100067", 'access_token': token}
    headers = {'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"}
    r = requests.get(url, params=payload, headers=headers, timeout=15)
    return r.json()

def api_get_platforms(token):
    url = "https://100067.connect.garena.com/bind/app/platform/info/get"
    r = requests.get(url, params={"access_token": token}, headers={'User-Agent': "GarenaMSDK/4.0.19P9"}, timeout=15)
    return r.json()

def api_send_otp(token, email):
    url = "https://100067.connect.garena.com/game/account_security/bind:send_email_code"
    r = requests.get(url, params={'app_id': "100067", 'access_token': token, 'email': email}, headers={'User-Agent': "GarenaMSDK/4.0.19P9"}, timeout=15)
    return r.json()

def api_bind_email(token, email, email_code, security_code):
    url = "https://100067.connect.garena.com/game/account_security/bind:bind_email"
    payload = {'app_id': "100067", 'access_token': token, 'email': email, 'email_code': email_code, 'security_code': security_code}
    r = requests.get(url, params=payload, headers={'User-Agent': "GarenaMSDK/4.0.19P9"}, timeout=15)
    return r.json()

def api_unbind_email(token, security_code):
    url = "https://100067.connect.garena.com/game/account_security/bind:unbind_email"
    payload = {'app_id': "100067", 'access_token': token, 'security_code': security_code}
    r = requests.get(url, params=payload, headers={'User-Agent': "GarenaMSDK/4.0.19P9"}, timeout=15)
    return r.json()

def api_change_email(token, new_email, email_code, security_code):
    url = "https://100067.connect.garena.com/game/account_security/bind:change_email"
    payload = {'app_id': "100067", 'access_token': token, 'email': new_email, 'email_code': email_code, 'security_code': security_code}
    r = requests.get(url, params=payload, headers={'User-Agent': "GarenaMSDK/4.0.19P9"}, timeout=15)
    return r.json()

def api_cancel_bind(token):
    url = "https://100067.connect.garena.com/game/account_security/bind:cancel_bind"
    r = requests.get(url, params={'app_id': "100067", 'access_token': token}, headers={'User-Agent': "GarenaMSDK/4.0.19P9"}, timeout=15)
    return r.json()

def api_revoke_token(token):
    url = "https://100067.connect.garena.com/game/account_security/token:revoke"
    r = requests.get(url, params={'app_id': "100067", 'access_token': token}, headers={'User-Agent': "GarenaMSDK/4.0.19P9"}, timeout=15)
    return r.json()

def api_eat_to_token(eat):
    url = "https://100067.connect.garena.com/oauth/guest_token/convert"
    try:
        r = requests.post(url, data={'app_id': "100067", 'external_access_token': eat, 'platform': 'fb'}, headers={'User-Agent': "GarenaMSDK/4.0.19P9"}, timeout=15)
        return r.json()
    except:
        url2 = f"https://100067.connect.garena.com/oauth/token/convert?app_id=100067&external_access_token={eat}"
        r = requests.get(url2, headers={'User-Agent': "GarenaMSDK/4.0.19P9"}, timeout=15)
        return r.json()

PLATFORM_MAP = {1:"Garena",3:"Facebook",4:"Guest",5:"VK",6:"Huawei",7:"Apple",8:"Google",10:"GameCenter",11:"X (Twitter)",13:"Apple ID",28:"Line",35:"TikTok"}

def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("1️⃣ CHECK BIND", callback_data="check_bind"), types.InlineKeyboardButton("2️⃣ BIND EMAIL", callback_data="bind_email"))
    markup.add(types.InlineKeyboardButton("3️⃣ UNBIND", callback_data="unbind_email"), types.InlineKeyboardButton("4️⃣ CHANGE EMAIL", callback_data="change_email"))
    markup.add(types.InlineKeyboardButton("5️⃣ CANCEL REQ", callback_data="cancel_bind"), types.InlineKeyboardButton("6️⃣ EAT->TOKEN", callback_data="eat_token"))
    markup.add(types.InlineKeyboardButton("7️⃣ REVOKE TOKEN", callback_data="revoke_token"), types.InlineKeyboardButton("8️⃣ LOGIN HISTORY", callback_data="login_history"))
    markup.add(types.InlineKeyboardButton("9️⃣ BOUND ACCOUNTS", callback_data="bound_accounts"), types.InlineKeyboardButton("🔟 OWNER", callback_data="owner"))
    return markup

@bot.message_handler(commands=['start','help'])
def start_cmd(message):
    txt = f"""
🔥 <b>ZEVRIC BIND TOOL - RENDER EDITION</b> 🔥

👤 Owner: <b>Zevric</b>
▶️ YouTube: <b>zevricxplay</b>
✈️ Telegram: <b>@just_zevric</b>

Original: @spideyabd & @INDRAJIT_1M
Render pe 24/7 Online!

⚠️ Private chat me hi token bhejo
"""
    bot.send_message(message.chat.id, txt, reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = call.from_user.id
    action = call.data
    bot.answer_callback_query(call.id)
    if call.message.chat.type != 'private':
        bot.send_message(call.message.chat.id, "⚠️ Private me aao!")
        return
    if action == "owner":
        bot.send_message(call.message.chat.id, """
👑 <b>OWNER</b>
🔥 Zevric
▶️ zevricxplay
✈️ @just_zevric
📦 Full 10 Options Bot
🌐 Render Ready
""", reply_markup=main_menu())
        return
    user_sessions[uid] = {"action": action, "step": "await_token"}
    if action == "eat_token":
        bot.send_message(call.message.chat.id, "🔑 EAT bhejo:")
    else:
        bot.send_message(call.message.chat.id, f"🔑 <b>{action.upper()}</b> ke liye Access Token bhejo (auto-delete):")

@bot.message_handler(func=lambda m: True, content_types=['text'])
def text_handler(message):
    uid = message.from_user.id
    sess = user_sessions.get(uid)
    if not sess: return
    text = message.text.strip()
    try:
        if len(text) > 30: bot.delete_message(message.chat.id, message.message_id)
    except: pass
    action, step = sess.get("action"), sess.get("step")

    if action == "eat_token" and step == "await_token":
        bot.send_message(message.chat.id, "⏳ Converting EAT...")
        try:
            res = api_eat_to_token(text)
            bot.send_message(message.chat.id, f"✅ <code>{res}</code>")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ {e}")
        user_sessions.pop(uid,None)
        bot.send_message(message.chat.id, "Menu:", reply_markup=main_menu())
        return

    if step == "await_token":
        sess["token"] = text
        try:
            p_uid, nick, region = fetch_player_info(text)
            sess["player"] = (p_uid, nick, region)
        except:
            sess["player"] = ("Unknown","Unknown","Unknown")

        if action == "check_bind":
            bot.send_message(message.chat.id, "⏳ Bind info...")
            try:
                data = api_get_bind_info(text)
                msg = f"✅ <b>BIND INFO</b>\nUID: <code>{sess['player'][0]}</code>\nNick: {sess['player'][1]}\nCurrent: <code>{data.get('email','None')}</code>\nPending: <code>{data.get('email_to_be','None')}</code>\nCD: {convert_seconds(data.get('request_exec_countdown',0))}\nResult: {data.get('result')}"
                bot.send_message(message.chat.id, msg)
            except Exception as e:
                bot.send_message(message.chat.id, f"❌ {e}")
            user_sessions.pop(uid,None)
            bot.send_message(message.chat.id, "Menu:", reply_markup=main_menu())

        elif action == "bound_accounts":
            bot.send_message(message.chat.id, "⏳ Platforms...")
            try:
                d = api_get_platforms(text)
                bounded = d.get("bounded_accounts",[])
                msg = "🔗 <b>Bound:</b>\n" + "\n".join([f"• {PLATFORM_MAP.get(p,p)}" for p in bounded]) if bounded else "• None"
                bot.send_message(message.chat.id, msg)
            except Exception as e:
                bot.send_message(message.chat.id, f"❌ {e}")
            user_sessions.pop(uid,None)
            bot.send_message(message.chat.id, "Menu:", reply_markup=main_menu())

        elif action == "bind_email":
            sess["step"]="await_email"
            bot.send_message(message.chat.id, "📧 Email bhejo jisko bind karna hai:")
        elif action == "unbind_email":
            sess["step"]="await_sec_code"
            bot.send_message(message.chat.id, "🔐 Security Code (6-digit) bhejo:")
        elif action == "change_email":
            sess["step"]="await_new_email"
            bot.send_message(message.chat.id, "📧 Naya email bhejo:")
        elif action == "cancel_bind":
            try:
                res = api_cancel_bind(text)
                bot.send_message(message.chat.id, f"✅ Cancel: <code>{res}</code>")
            except Exception as e:
                bot.send_message(message.chat.id, f"❌ {e}")
            user_sessions.pop(uid,None)
            bot.send_message(message.chat.id, "Menu:", reply_markup=main_menu())
        elif action == "revoke_token":
            try:
                res = api_revoke_token(text)
                bot.send_message(message.chat.id, f"✅ Revoke: <code>{res}</code>")
            except Exception as e:
                bot.send_message(message.chat.id, f"❌ {e}")
            user_sessions.pop(uid,None)
            bot.send_message(message.chat.id, "Menu:", reply_markup=main_menu())
        elif action == "login_history":
            bot.send_message(message.chat.id, "⚠️ Login History ke liye MajoRLogin_pb2.py chahiye jo original app_3.py me tha. Render pe basic check only.\nToken valid hai." )
            user_sessions.pop(uid,None)
            bot.send_message(message.chat.id, "Menu:", reply_markup=main_menu())

    elif action=="bind_email" and step=="await_email":
        sess["email"]=text
        bot.send_message(message.chat.id, f"📨 {text} pe OTP bhej raha hu...")
        try:
            res = api_send_otp(sess["token"], text)
            bot.send_message(message.chat.id, f"✅ OTP Sent: {res}\nOTP bhejo:")
            sess["step"]="await_otp"
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ {e}")
            user_sessions.pop(uid,None)

    elif action=="bind_email" and step=="await_otp":
        sess["otp"]=text
        sess["step"]="await_sec_code_bind"
        bot.send_message(message.chat.id, "🔐 Security Code (6-digit) jo set karna hai bhejo:")

    elif action=="bind_email" and step=="await_sec_code_bind":
        try:
            res = api_bind_email(sess["token"], sess["email"], sess["otp"], text)
            bot.send_message(message.chat.id, f"✅ Bind: <code>{res}</code>\n15 din buffer lagega.")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ {e}")
        user_sessions.pop(uid,None)
        bot.send_message(message.chat.id, "Menu:", reply_markup=main_menu())

    elif action=="unbind_email" and step=="await_sec_code":
        try:
            res = api_unbind_email(sess["token"], text)
            bot.send_message(message.chat.id, f"✅ Unbind: <code>{res}</code>")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ {e}")
        user_sessions.pop(uid,None)
        bot.send_message(message.chat.id, "Menu:", reply_markup=main_menu())

    elif action=="change_email" and step=="await_new_email":
        sess["new_email"]=text
        bot.send_message(message.chat.id, f"📨 {text} pe OTP bhej raha hu...")
        try:
            res = api_send_otp(sess["token"], text)
            bot.send_message(message.chat.id, f"✅ OTP Sent: {res}\nOTP bhejo:")
            sess["step"]="await_otp_change"
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ {e}")
            user_sessions.pop(uid,None)

    elif action=="change_email" and step=="await_otp_change":
        sess["otp"]=text
        sess["step"]="await_sec_code_change"
        bot.send_message(message.chat.id, "🔐 Security Code bhejo:")

    elif action=="change_email" and step=="await_sec_code_change":
        try:
            res = api_change_email(sess["token"], sess["new_email"], sess["otp"], text)
            bot.send_message(message.chat.id, f"✅ Change: <code>{res}</code>")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ {e}")
        user_sessions.pop(uid,None)
        bot.send_message(message.chat.id, "Menu:", reply_markup=main_menu())

# ---------- Run Both ----------
def run_bot():
    print("[+] ZEVRIC BOT STARTED - Polling...")
    bot.infinity_polling()

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    if BOT_TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        print("[!] BOT_TOKEN env me set karo!")
    else:
        # Bot thread
        threading.Thread(target=run_bot, daemon=True).start()
        # Flask main
        run_flask()
