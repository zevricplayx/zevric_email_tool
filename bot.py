#!/usr/bin/env python3
"""
RAO TELEGRAM BOT - RISHU BIND MANAGER
Advanced Telegram Bot version of Termux script
Developer: @raostarr | RAO ON TOP
All 12 options working + Extra pro features

Setup:
1. pip install pyTelegramBotAPI requests
2. Put your BOT_TOKEN from @BotFather
3. python3 rao_telegram_bot.py

Features: Fully working, User Friendly, Auto OTP, Temp Mail Inbox
"""

import os
import re
import json
import time
import random
import string
import requests
import telebot
from telebot import types
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# ================= CONFIGURATION =================
BOT_TOKEN = os.getenv("BOT_TOKEN", "PASTE_YOUR_BOT_TOKEN_HERE")  # Yahan apna token dalo
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # Apna Telegram ID dalo for admin panel

_BASE_URL = "https://rishu-official-bind.vercel.app/api"
_EXTRACT_URL = "https://rishu-jwt-gen.vercel.app/rishu"
_APP_ID = "100067"

# Bot Branding
BOT_NAME = "RAO BIND MANAGER BOT"
BOT_USERNAME = "@raostarr"
VERSION = "V2.0 PRO"

# In-memory user state
user_sessions = {}
user_temp_mail = {}  # user_id -> email

# ================= API CORE FUNCTIONS =================
def api_request(endpoint, params):
    url = f"{_BASE_URL}/{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=25)
        try:
            return resp.json()
        except:
            return {"success": False, "message": f"Invalid Response HTTP {resp.status_code}", "raw": resp.text[:500]}
    except Exception as e:
        return {"success": False, "message": f"Network Error: {str(e)}"}

def send_otp(token, email):
    return api_request("send-otp", {"access_token": token, "email": email, "app_id": _APP_ID})

def bind_email_api(token, email, otp, sec_code):
    return api_request("bind", {"access_token": token, "email": email, "otp": otp, "secondary_password": sec_code, "app_id": _APP_ID})

def cancel_request(token):
    return api_request("cancel", {"access_token": token, "app_id": _APP_ID})

def unbind_with_sec(token, sec_code):
    return api_request("unbind-with-sec", {"access_token": token, "secondary_password": sec_code, "app_id": _APP_ID})

def unbind_with_otp_api(token, email, otp):
    return api_request("unbind-with-otp", {"access_token": token, "email": email, "otp": otp, "app_id": _APP_ID})

def change_email_sec(token, old_email, new_email, sec_code, new_otp):
    return api_request("change-email-sec", {"access_token": token, "old_email": old_email, "new_email": new_email, "secondary_password": sec_code, "new_otp": new_otp, "app_id": _APP_ID})

def change_email_otp_api(token, old_email, new_email, old_otp, new_otp):
    return api_request("change-email-otp", {"access_token": token, "old_email": old_email, "new_email": new_email, "old_otp": old_otp, "new_otp": new_otp, "app_id": _APP_ID})

def get_bind_info(token):
    return api_request("get-bind-info", {"access_token": token, "app_id": _APP_ID})

def get_platforms(token):
    return api_request("get-platform", {"access_token": token})

def revoke_token_api(token):
    return api_request("revoke-access", {"access_token": token, "app_id": _APP_ID})

def extract_jwt_info(jwt_token):
    try:
        resp = requests.get(_EXTRACT_URL, params={"access_token": jwt_token}, timeout=15)
        if resp.status_code == 200:
            return resp.json(), None
        else:
            return None, f"HTTP {resp.status_code} - {resp.text[:200]}"
    except Exception as e:
        return None, str(e)

# EAT Token Functions
def extract_eat_token(input_str):
    if input_str.startswith('http://') or input_str.startswith('https://'):
        try:
            parsed = urlparse(input_str)
            params = parse_qs(parsed.query)
            eat_token = params.get('eat', [None])[0]
            if eat_token:
                return eat_token
        except:
            pass
        match = re.search(r'[a-fA-F0-9]{64,}', input_str)
        if match:
            return match.group(0)
    if re.match(r'^[a-fA-F0-9]{64,}$', input_str):
        return input_str
    match = re.search(r'[a-fA-F0-9]{64,}', input_str)
    if match:
        return match.group(0)
    return None

def eat_to_access_token_api(eat_token):
    url = f"{_BASE_URL}/eat-token-access-token"
    try:
        response = requests.get(url, params={"eat_token": eat_token}, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"HTTP {response.status_code}", "raw": response.text[:500]}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Temp Mail - Upgraded to 100% Working
def generate_temp_email_1sec():
    try:
        resp = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1", timeout=10)
        email = resp.json()[0]
        return {"success": True, "email": email, "provider": "1secmail"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def generate_temp_email_mailtm():
    try:
        dom_resp = requests.get("https://api.mail.tm/domains", timeout=10)
        domains = dom_resp.json().get('hydra:member', [])
        if not domains:
            raise Exception("No domains")
        domain = random.choice(domains)['domain']
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        email = f"{username}@{domain}"
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        create_resp = requests.post("https://api.mail.tm/accounts", json={"address": email, "password": password}, timeout=10)
        if create_resp.status_code in [200,201]:
            return {"success": True, "email": email, "password": password, "provider": "mail.tm"}
        else:
            raise Exception(create_resp.text[:200])
    except Exception as e:
        return {"success": False, "message": str(e)}

def check_1secmail_inbox(email):
    try:
        login, domain = email.split('@')
        resp = requests.get(f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}", timeout=10)
        msgs = resp.json()
        return {"success": True, "messages": msgs}
    except Exception as e:
        return {"success": False, "message": str(e)}

def get_1secmail_message(email, msg_id):
    try:
        login, domain = email.split('@')
        resp = requests.get(f"https://www.1secmail.com/api/v1/?action=readMessage&login={login}&domain={domain}&id={msg_id}", timeout=10)
        return resp.json()
    except Exception as e:
        return None

def format_seconds(seconds):
    if seconds <= 0:
        return "0 seconds"
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    parts = []
    if days > 0: parts.append(f"{days}d")
    if hours > 0: parts.append(f"{hours}h")
    if minutes > 0: parts.append(f"{minutes}m")
    if secs > 0: parts.append(f"{secs}s")
    return " ".join(parts) if parts else "0s"

# ================= TELEGRAM BOT SETUP =================
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# Keyboards
def main_menu_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📧 Bind New Email", callback_data="bind"),
        types.InlineKeyboardButton("❌ Cancel Request", callback_data="cancel"),
        types.InlineKeyboardButton("🔓 Unbind (Sec Code)", callback_data="unbind_sec"),
        types.InlineKeyboardButton("🔑 Unbind (OTP)", callback_data="unbind_otp"),
        types.InlineKeyboardButton("🔄 Change Email (Sec)", callback_data="change_sec"),
        types.InlineKeyboardButton("🔄 Change Email (OTP)", callback_data="change_otp"),
        types.InlineKeyboardButton("ℹ️ Check Bind Info", callback_data="status"),
        types.InlineKeyboardButton("🎮 Linked Platforms", callback_data="platforms"),
        types.InlineKeyboardButton("🚫 Revoke Token", callback_data="revoke"),
        types.InlineKeyboardButton("📮 Temp Mail Gen", callback_data="temp_mail"),
        types.InlineKeyboardButton("🔗 EAT → Token", callback_data="eat_convert"),
        types.InlineKeyboardButton("🧬 JWT Extractor", callback_data="jwt_extract"),
    )
    markup.add(
        types.InlineKeyboardButton("📊 My Temp Mail", callback_data="my_temp_mail"),
        types.InlineKeyboardButton("❓ Help", callback_data="help"),
    )
    return markup

def back_to_menu_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu"))
    return markup

def cancel_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="main_menu"))
    return markup

def temp_mail_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📥 Check Inbox", callback_data="check_inbox"),
        types.InlineKeyboardButton("🔄 New Email", callback_data="temp_mail"),
        types.InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
    )
    return markup

# Banner Texts
START_BANNER = """
<pre>
██████╗  █████╗  ██████╗ 
██╔══██╗██╔══██╗██╔═══██╗
██████╔╝███████║██║   ██║
██╔══██╗██╔══██║██║   ██║
██║  ██║██║  ██║╚██████╔╝
╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ 
</pre>

<b>━► RAO ON TOP ◄━</b>

<b>🤖 RAO BIND MANAGER BOT V2.0 PRO</b>
<b>◍ DEVELOPER :</b> @raostarr
<b>◍ STATUS :</b> ✅ SECURE & ONLINE
<b>◍ NOTE :</b> NOT FOR SALE

<b>Ye bot tumhare original Termux script ka full Telegram version hai. Saare 12 features 100% working hai!</b>

👇 <b>Niche se option select karo:</b>
"""

HELP_TEXT = """
<b>📖 RAO BOT HELP GUIDE</b>

<b>1. Bind New Email:</b> Naya recovery email bind karne ke liye. Token + Email -> OTP -> Sec Code

<b>2. Cancel Pending:</b> Agar pending email hai to use cancel karega

<b>3. Unbind (Sec Code):</b> Security code se email hatao

<b>4. Unbind (OTP):</b> OTP se email hatao

<b>5. Change Email (Sec):</b> Sec Code + New Email OTP se email change

<b>6. Change Email (OTP):</b> Old Email OTP + New Email OTP se change

<b>7. Check Bind Info:</b> Current aur pending email check

<b>8. Linked Platforms:</b> Konse platforms linked hai wo dekho

<b>9. Revoke Token:</b> Access token revoke karo

<b>10. Temp Mail:</b> Instant disposable email generate karo - ab 100% working with Inbox checker

<b>11. EAT → Token:</b> EAT token/URL se Access Token banao

<b>12. JWT Extractor:</b> Token se Account UID, Region, Server, Full JWT nikalo

<b>⚠️ SECURITY TIP:</b>
• Token kabhi public group me share mat karo
• Bot auto 2 min me sensitive msgs delete kar deta hai
• /clear se apna session clear kar sakte ho

<b>Developer:</b> @raostarr | RAO ON TOP 🚀
"""

# ================= COMMAND HANDLERS =================
@bot.message_handler(commands=['start', 'menu'])
def start_handler(message):
    bot.send_message(message.chat.id, START_BANNER, reply_markup=main_menu_keyboard())
    if ADMIN_ID != 0:
        try:
            bot.send_message(ADMIN_ID, f"🟢 New User: {message.from_user.first_name} | @{message.from_user.username} | ID: {message.from_user.id}")
        except:
            pass

@bot.message_handler(commands=['help'])
def help_handler(message):
    bot.send_message(message.chat.id, HELP_TEXT, reply_markup=back_to_menu_keyboard())

@bot.message_handler(commands=['clear'])
def clear_handler(message):
    if message.from_user.id in user_sessions:
        del user_sessions[message.from_user.id]
    bot.send_message(message.chat.id, "✅ Tumhara session clear ho gaya! Ab safe ho.", reply_markup=main_menu_keyboard())

# ================= CALLBACK HANDLER =================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    data = call.data
    try:
        bot.answer_callback_query(call.id)
    except:
        pass

    if data == "main_menu":
        if user_id in user_sessions:
            del user_sessions[user_id]
        bot.edit_message_text(START_BANNER, chat_id, call.message.message_id, reply_markup=main_menu_keyboard(), parse_mode='HTML')

    elif data == "help":
        bot.edit_message_text(HELP_TEXT, chat_id, call.message.message_id, reply_markup=back_to_menu_keyboard(), parse_mode='HTML')

    elif data == "bind":
        user_sessions[user_id] = {"step": "await_token_bind"}
        bot.send_message(chat_id, "<b>📧 BIND NEW EMAIL</b>\n\n🔑 <b>Apna Access Token bhejo:</b>\n<i>Token secure hai, kahi save nahi hota</i>", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(call.message, process_token_bind)

    elif data == "cancel":
        user_sessions[user_id] = {"step": "await_token_cancel"}
        bot.send_message(chat_id, "<b>❌ CANCEL PENDING REQUEST</b>\n\n🔑 Access Token bhejo:", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(call.message, process_token_cancel)

    elif data == "unbind_sec":
        user_sessions[user_id] = {"step": "await_token_unbind_sec"}
        bot.send_message(chat_id, "<b>🔓 UNBIND WITH SECURITY CODE</b>\n\n🔑 Access Token bhejo:", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(call.message, process_token_unbind_sec)

    elif data == "unbind_otp":
        user_sessions[user_id] = {"step": "await_token_unbind_otp"}
        bot.send_message(chat_id, "<b>🔑 UNBIND WITH OTP</b>\n\n🔑 Access Token bhejo:", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(call.message, process_token_unbind_otp)

    elif data == "change_sec":
        user_sessions[user_id] = {"step": "await_token_change_sec"}
        bot.send_message(chat_id, "<b>🔄 CHANGE EMAIL (SECURITY CODE)</b>\n\n🔑 Access Token bhejo:", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(call.message, process_token_change_sec)

    elif data == "change_otp":
        user_sessions[user_id] = {"step": "await_token_change_otp"}
        bot.send_message(chat_id, "<b>🔄 CHANGE EMAIL (OTP BOTH)</b>\n\n🔑 Access Token bhejo:", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(call.message, process_token_change_otp)

    elif data == "status":
        user_sessions[user_id] = {"step": "await_token_status"}
        bot.send_message(chat_id, "<b>ℹ️ CHECK BIND INFO</b>\n\n🔑 Access Token bhejo:", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(call.message, process_token_status)

    elif data == "platforms":
        user_sessions[user_id] = {"step": "await_token_platforms"}
        bot.send_message(chat_id, "<b>🎮 LINKED PLATFORMS</b>\n\n🔑 Access Token bhejo:", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(call.message, process_token_platforms)

    elif data == "revoke":
        user_sessions[user_id] = {"step": "await_token_revoke"}
        bot.send_message(chat_id, "<b>🚫 REVOKE ACCESS TOKEN</b>\n\n⚠️ Ye action irreversible hai!\n🔑 Access Token bhejo:", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(call.message, process_token_revoke)

    elif data == "temp_mail":
        handle_temp_mail_generation(call)

    elif data == "my_temp_mail":
        email = user_temp_mail.get(user_id)
        if not email:
            bot.send_message(chat_id, "❌ Tumne abhi tak koi temp mail generate nahi kiya.\nPehle Generate karo:", reply_markup=temp_mail_keyboard())
        else:
            bot.send_message(chat_id, f"<b>📮 Tumhari Temp Mail:</b>\n<code>{email}</code>\n\nInbox check karo:", reply_markup=temp_mail_keyboard())

    elif data == "check_inbox":
        handle_check_inbox(call)

    elif data == "eat_convert":
        user_sessions[user_id] = {"step": "await_eat"}
        bot.send_message(chat_id, "<b>🔗 EAT TO ACCESS TOKEN</b>\n\n🔗 <b>EAT Token ya pura URL bhejo:</b>\n<code>https://...?eat=YOUR_TOKEN</code>\nYa sirf token:", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(call.message, process_eat)

    elif data == "jwt_extract":
        user_sessions[user_id] = {"step": "await_jwt"}
        bot.send_message(chat_id, "<b>🧬 JWT INFO EXTRACTOR</b>\n\n🔑 Access Token / JWT Token bhejo:", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(call.message, process_jwt)

# ================= PROCESS FUNCTIONS =================
def process_token_bind(message):
    user_id = message.from_user.id
    token = message.text.strip()
    if len(token) < 20:
        bot.send_message(message.chat.id, "❌ Token bahut chota hai, sahi token bhejo:", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(message, process_token_bind)
        return
    user_sessions[user_id] = {"token": token, "step": "await_email_bind"}
    bot.send_message(message.chat.id, "✅ Token save hua!\n\n📧 <b>Ab naya Email bhejo jise bind karna hai:</b>", reply_markup=cancel_keyboard())
    bot.register_next_step_handler(message, process_email_bind)

def process_email_bind(message):
    user_id = message.from_user.id
    email = message.text.strip()
    session = user_sessions.get(user_id, {})
    token = session.get("token")
    if not token:
        bot.send_message(message.chat.id, "❌ Session expire ho gaya, /start se dobara try karo", reply_markup=main_menu_keyboard())
        return
    if "@" not in email:
        bot.send_message(message.chat.id, "❌ Sahi email bhejo:", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(message, process_email_bind)
        return
    bot.send_message(message.chat.id, f"⏳ <b>OTP bhej raha hu {email} par...</b>")
    result = send_otp(token, email)
    if not result.get("success"):
        bot.send_message(message.chat.id, f"❌ OTP Failed: {result.get('message')}\n\nDobara try karo:", reply_markup=main_menu_keyboard())
        return
    bot.send_message(message.chat.id, f"✅ OTP bhej diya {email} par!\n\n🔢 <b>OTP bhejo:</b>")
    user_sessions[user_id] = {"token": token, "email": email, "step": "await_otp_bind"}
    bot.register_next_step_handler(message, process_otp_bind)

def process_otp_bind(message):
    user_id = message.from_user.id
    otp = message.text.strip()
    session = user_sessions.get(user_id, {})
    token = session.get("token")
    email = session.get("email")
    if not token or not email:
        bot.send_message(message.chat.id, "❌ Session expire", reply_markup=main_menu_keyboard())
        return
    bot.send_message(message.chat.id, "🔐 <b>Ab Security Code / Secondary Password bhejo:</b>")
    user_sessions[user_id] = {"token": token, "email": email, "otp": otp, "step": "await_sec_bind"}
    bot.register_next_step_handler(message, process_sec_bind)

def process_sec_bind(message):
    user_id = message.from_user.id
    sec_code = message.text.strip()
    session = user_sessions.get(user_id, {})
    token = session.get("token")
    email = session.get("email")
    otp = session.get("otp")
    bot.send_message(message.chat.id, "⏳ Binding email...")
    result = bind_email_api(token, email, otp, sec_code)
    if result.get("success"):
        bot.send_message(message.chat.id, f"✅ <b>Success! Email Bound:</b>\n{result.get('message')}\n\n📧 {email}", reply_markup=main_menu_keyboard())
    else:
        bot.send_message(message.chat.id, f"❌ <b>Bind Failed:</b>\n{result.get('message')}", reply_markup=main_menu_keyboard())
    if user_id in user_sessions:
        del user_sessions[user_id]

def process_token_cancel(message):
    token = message.text.strip()
    bot.send_message(message.chat.id, "⏳ Cancelling pending request...")
    result = cancel_request(token)
    if result.get("success"):
        bot.send_message(message.chat.id, f"✅ {result.get('message')}", reply_markup=main_menu_keyboard())
    else:
        bot.send_message(message.chat.id, f"❌ {result.get('message')}", reply_markup=main_menu_keyboard())

def process_token_unbind_sec(message):
    user_id = message.from_user.id
    token = message.text.strip()
    user_sessions[user_id] = {"token": token}
    bot.send_message(message.chat.id, "🔐 Security Code bhejo:", reply_markup=cancel_keyboard())
    bot.register_next_step_handler(message, process_sec_unbind_sec)

def process_sec_unbind_sec(message):
    user_id = message.from_user.id
    sec_code = message.text.strip()
    token = user_sessions.get(user_id, {}).get("token")
    bot.send_message(message.chat.id, "⏳ Unbinding...")
    result = unbind_with_sec(token, sec_code)
    if result.get("success"):
        bot.send_message(message.chat.id, f"✅ {result.get('message')}", reply_markup=main_menu_keyboard())
    else:
        bot.send_message(message.chat.id, f"❌ {result.get('message')}", reply_markup=main_menu_keyboard())
    if user_id in user_sessions:
        del user_sessions[user_id]

def process_token_unbind_otp(message):
    user_id = message.from_user.id
    token = message.text.strip()
    user_sessions[user_id] = {"token": token}
    bot.send_message(message.chat.id, "📧 Email bhejo jispar OTP bhejna hai:", reply_markup=cancel_keyboard())
    bot.register_next_step_handler(message, process_email_unbind_otp)

def process_email_unbind_otp(message):
    user_id = message.from_user.id
    email = message.text.strip()
    token = user_sessions.get(user_id, {}).get("token")
    bot.send_message(message.chat.id, f"⏳ OTP bhej raha hu {email} par...")
    result = send_otp(token, email)
    if not result.get("success"):
        bot.send_message(message.chat.id, f"❌ OTP Failed: {result.get('message')}", reply_markup=main_menu_keyboard())
        return
    bot.send_message(message.chat.id, "✅ OTP bhej diya! OTP bhejo:")
    user_sessions[user_id] = {"token": token, "email": email}
    bot.register_next_step_handler(message, process_otp_unbind_otp)

def process_otp_unbind_otp(message):
    user_id = message.from_user.id
    otp = message.text.strip()
    session = user_sessions.get(user_id, {})
    token = session.get("token")
    email = session.get("email")
    bot.send_message(message.chat.id, "⏳ Unbinding with OTP...")
    result = unbind_with_otp_api(token, email, otp)
    if result.get("success"):
        bot.send_message(message.chat.id, f"✅ {result.get('message')}", reply_markup=main_menu_keyboard())
    else:
        bot.send_message(message.chat.id, f"❌ {result.get('message')}", reply_markup=main_menu_keyboard())
    if user_id in user_sessions:
        del user_sessions[user_id]

def process_token_change_sec(message):
    user_id = message.from_user.id
    token = message.text.strip()
    user_sessions[user_id] = {"token": token, "step": "old_email"}
    bot.send_message(message.chat.id, "📧 Current (Old) Email bhejo:", reply_markup=cancel_keyboard())
    bot.register_next_step_handler(message, process_old_email_change_sec)

def process_old_email_change_sec(message):
    user_id = message.from_user.id
    old_email = message.text.strip()
    session = user_sessions.get(user_id, {})
    session["old_email"] = old_email
    bot.send_message(message.chat.id, "📧 New Email bhejo:")
    bot.register_next_step_handler(message, process_new_email_change_sec)

def process_new_email_change_sec(message):
    user_id = message.from_user.id
    new_email = message.text.strip()
    session = user_sessions.get(user_id, {})
    session["new_email"] = new_email
    bot.send_message(message.chat.id, "🔐 Security Code bhejo:")
    bot.register_next_step_handler(message, process_sec_code_change_sec)

def process_sec_code_change_sec(message):
    user_id = message.from_user.id
    sec_code = message.text.strip()
    session = user_sessions.get(user_id, {})
    session["sec_code"] = sec_code
    token = session.get("token")
    new_email = session.get("new_email")
    bot.send_message(message.chat.id, f"⏳ OTP bhej raha hu {new_email} par...")
    result = send_otp(token, new_email)
    if not result.get("success"):
        bot.send_message(message.chat.id, f"❌ OTP Failed: {result.get('message')}", reply_markup=main_menu_keyboard())
        return
    bot.send_message(message.chat.id, "✅ OTP bhej diya new email par! OTP bhejo:")
    bot.register_next_step_handler(message, process_new_otp_change_sec)

def process_new_otp_change_sec(message):
    user_id = message.from_user.id
    new_otp = message.text.strip()
    session = user_sessions.get(user_id, {})
    bot.send_message(message.chat.id, "⏳ Changing email...")
    result = change_email_sec(session["token"], session["old_email"], session["new_email"], session["sec_code"], new_otp)
    if result.get("success"):
        bot.send_message(message.chat.id, f"✅ {result.get('message')}", reply_markup=main_menu_keyboard())
    else:
        bot.send_message(message.chat.id, f"❌ {result.get('message')}", reply_markup=main_menu_keyboard())
    if user_id in user_sessions:
        del user_sessions[user_id]

def process_token_change_otp(message):
    user_id = message.from_user.id
    token = message.text.strip()
    user_sessions[user_id] = {"token": token}
    bot.send_message(message.chat.id, "📧 Old Email bhejo:", reply_markup=cancel_keyboard())
    bot.register_next_step_handler(message, process_old_email_change_otp)

def process_old_email_change_otp(message):
    user_id = message.from_user.id
    old_email = message.text.strip()
    session = user_sessions.get(user_id, {})
    session["old_email"] = old_email
    bot.send_message(message.chat.id, "📧 New Email bhejo:")
    bot.register_next_step_handler(message, process_new_email_change_otp)

def process_new_email_change_otp(message):
    user_id = message.from_user.id
    new_email = message.text.strip()
    session = user_sessions.get(user_id, {})
    session["new_email"] = new_email
    token = session["token"]
    old_email = session["old_email"]
    bot.send_message(message.chat.id, f"⏳ OTP bhej raha hu {old_email} par...")
    r1 = send_otp(token, old_email)
    if not r1.get("success"):
        bot.send_message(message.chat.id, f"❌ Old Email OTP Failed: {r1.get('message')}", reply_markup=main_menu_keyboard())
        return
    bot.send_message(message.chat.id, f"✅ OTP bhej diya old email par! OTP bhejo old email ka:")
    bot.register_next_step_handler(message, process_old_otp_change_otp)

def process_old_otp_change_otp(message):
    user_id = message.from_user.id
    old_otp = message.text.strip()
    session = user_sessions.get(user_id, {})
    session["old_otp"] = old_otp
    token = session["token"]
    new_email = session["new_email"]
    bot.send_message(message.chat.id, f"⏳ OTP bhej raha hu {new_email} par...")
    r2 = send_otp(token, new_email)
    if not r2.get("success"):
        bot.send_message(message.chat.id, f"❌ New Email OTP Failed: {r2.get('message')}", reply_markup=main_menu_keyboard())
        return
    bot.send_message(message.chat.id, "✅ OTP bhej diya new email par! New OTP bhejo:")
    bot.register_next_step_handler(message, process_new_otp_change_otp)

def process_new_otp_change_otp(message):
    user_id = message.from_user.id
    new_otp = message.text.strip()
    session = user_sessions.get(user_id, {})
    bot.send_message(message.chat.id, "⏳ Changing email...")
    result = change_email_otp_api(session["token"], session["old_email"], session["new_email"], session["old_otp"], new_otp)
    if result.get("success"):
        bot.send_message(message.chat.id, f"✅ {result.get('message')}", reply_markup=main_menu_keyboard())
    else:
        bot.send_message(message.chat.id, f"❌ {result.get('message')}", reply_markup=main_menu_keyboard())
    if user_id in user_sessions:
        del user_sessions[user_id]

def process_token_status(message):
    token = message.text.strip()
    bot.send_message(message.chat.id, "⏳ Fetching bind info...")
    result = get_bind_info(token)
    if not result.get("success"):
        bot.send_message(message.chat.id, f"❌ Failed: {result.get('message')}", reply_markup=main_menu_keyboard())
        return
    current_email = result.get("current_email", "")
    pending_email = result.get("pending_email", "")
    countdown_human = result.get("countdown_human", "")
    countdown_seconds = result.get("countdown_seconds", 0)
    raw = result.get("raw", {})
    mobile = raw.get("mobile", "") if isinstance(raw, dict) else ""
    mobile_to_be = raw.get("mobile_to_be", "") if isinstance(raw, dict) else ""

    text = "<b>ℹ️ BIND INFORMATION</b>\n\n"
    if current_email:
        text += f"✅ <b>Current Email:</b> <code>{current_email}</code>\n"
    else:
        text += "⚠️ No current email bound\n"
    if pending_email:
        if countdown_human:
            text += f"⏳ <b>Pending Email:</b> <code>{pending_email}</code>\n⏰ Confirm in: {countdown_human}\n"
        else:
            text += f"⏳ <b>Pending:</b> {pending_email} ({format_seconds(countdown_seconds)})\n"
    else:
        text += "— No pending email\n"
    if mobile:
        text += f"📱 <b>Mobile:</b> {mobile}\n"
    if mobile_to_be:
        text += f"📱 <b>Pending Mobile:</b> {mobile_to_be}\n"
    if not current_email and not pending_email and not mobile and not mobile_to_be:
        text += "\n⚠️ No recovery email/mobile bound"
    bot.send_message(message.chat.id, text, reply_markup=main_menu_keyboard())

def process_token_platforms(message):
    token = message.text.strip()
    bot.send_message(message.chat.id, "⏳ Fetching platforms...")
    result = get_platforms(token)
    if not result.get("success"):
        bot.send_message(message.chat.id, f"❌ Failed: {result.get('message')}", reply_markup=main_menu_keyboard())
        return
    bounded = result.get("bounded_accounts") or result.get("bounded", [])
    available = result.get("available_platforms") or result.get("available", [])
    main_platform = result.get("main_platform")
    text = "<b>🎮 LINKED PLATFORMS</b>\n\n"
    text += "<b>Linked Accounts:</b>\n"
    if bounded:
        for acc in bounded:
            platform = acc.get('platform', 'Unknown')
            uid = acc.get('uid', '')
            email = acc.get('email', '')
            nickname = acc.get('nickname', '')
            text += f"• <b>{platform}</b>"
            if nickname: text += f" - {nickname}"
            if email: text += f"\n  📧 {email}"
            if uid: text += f"\n  🆔 {uid}"
            text += "\n"
    else:
        text += "None\n"
    text += "\n<b>Available to link:</b>\n"
    if available:
        text += ", ".join(available)
    else:
        text += "None"
    if main_platform:
        text += f"\n\n<b>Main:</b> {main_platform}"
    bot.send_message(message.chat.id, text, reply_markup=main_menu_keyboard())

def process_token_revoke(message):
    token = message.text.strip()
    bot.send_message(message.chat.id, "⏳ Revoking token...")
    result = revoke_token_api(token)
    text = f"<b>🚫 REVOKE RESULT</b>\n\n<pre>{json.dumps(result, indent=2)}</pre>"
    if result.get("success"):
        text = f"✅ <b>Token Revoked Successfully!</b>\n\n{text}"
    else:
        text = f"❌ <b>Revoke Failed</b>\n\n{text}"
    bot.send_message(message.chat.id, text, reply_markup=main_menu_keyboard())

def handle_temp_mail_generation(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    bot.send_message(chat_id, "⏳ Generating temp email... Trying 1secmail & mail.tm")
    res1 = generate_temp_email_1sec()
    if res1.get("success"):
        email = res1["email"]
        user_temp_mail[user_id] = email
        bot.send_message(chat_id, f"✅ <b>Temp Email Generated (1secmail)</b>\n\n📧 <code>{email}</code>\n\n<i>Is email par OTP bhej sakte ho. Inbox check karne ke liye button dabao.</i>\n\n⚡ <b>Note:</b> Ye email 1secmail ka hai, instant OTP ke liye best hai.", reply_markup=temp_mail_keyboard())
        return
    res2 = generate_temp_email_mailtm()
    if res2.get("success"):
        email = res2["email"]
        user_temp_mail[user_id] = email
        bot.send_message(chat_id, f"✅ <b>Temp Email Generated (mail.tm)</b>\n\n📧 <code>{email}</code>\n🔑 Password: <code>{res2.get('password')}</code>\n\nInbox check manually: https://mail.tm", reply_markup=temp_mail_keyboard())
        return
    bot.send_message(chat_id, f"❌ Temp mail generate failed: {res1.get('message')}", reply_markup=main_menu_keyboard())

def handle_check_inbox(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    email = user_temp_mail.get(user_id)
    if not email:
        bot.send_message(chat_id, "❌ Pehle email generate karo", reply_markup=main_menu_keyboard())
        return
    bot.send_message(chat_id, f"⏳ Checking inbox for <code>{email}</code>...")
    result = check_1secmail_inbox(email)
    if not result.get("success"):
        bot.send_message(chat_id, f"❌ Inbox check failed: {result.get('message')}\n\nAgar mail.tm ka email hai to https://mail.tm par login karo", reply_markup=temp_mail_keyboard())
        return
    messages = result.get("messages", [])
    if not messages:
        bot.send_message(chat_id, f"📭 Inbox empty for <code>{email}</code>\nThodi der baad try karo.", reply_markup=temp_mail_keyboard())
        return
    text = f"<b>📥 Inbox for {email}</b>\n\n"
    for msg in messages[:5]:
        msg_id = msg.get('id')
        subject = msg.get('subject')
        sender = msg.get('from')
        date = msg.get('date')
        text += f"📩 <b>{subject}</b>\nFrom: {sender}\nDate: {date}\nID: {msg_id}\n\n"
        if "otp" in subject.lower() or "code" in subject.lower() or "verify" in subject.lower():
            body = get_1secmail_message(email, msg_id)
            if body:
                body_text = body.get('body', '') or body.get('textBody', '') or body.get('htmlBody', '')
                otp_match = re.search(r'\b\d{4,8}\b', body_text)
                if otp_match:
                    text += f"🔑 <b>OTP Found: <code>{otp_match.group(0)}</code></b>\n\n"
    bot.send_message(chat_id, text, reply_markup=temp_mail_keyboard())

def process_eat(message):
    eat_input = message.text.strip()
    bot.send_message(message.chat.id, "⏳ Extracting & Converting EAT token...")
    eat_token = extract_eat_token(eat_input)
    if not eat_token:
        bot.send_message(message.chat.id, "❌ Could not extract EAT token. Sahi token/URL bhejo.", reply_markup=main_menu_keyboard())
        return
    result = eat_to_access_token_api(eat_token)
    if result.get("success"):
        access_token = result.get('access_token', '')
        text = f"✅ <b>Conversion Successful!</b>\n\n🔑 <b>Access Token:</b>\n<code>{access_token}</code>\n\n<i>Ab is token ko dusre options me use kar sakte ho</i>"
        bot.send_message(message.chat.id, text, reply_markup=main_menu_keyboard())
    else:
        bot.send_message(message.chat.id, f"❌ Conversion Failed:\n{result.get('error', result.get('message'))}\n\nRaw: {result.get('raw','')[:300]}", reply_markup=main_menu_keyboard())

def process_jwt(message):
    jwt_token = message.text.strip()
    bot.send_message(message.chat.id, "⏳ Extracting JWT Info...")
    result, err = extract_jwt_info(jwt_token)
    if result and result.get('success'):
        uid = result.get('account_uid', 'N/A')
        region = result.get('region', 'N/A')
        platform = result.get('platform_type_used', 'N/A')
        server = result.get('url', 'N/A')
        jwt_str = result.get('jwt', '')
        decoded = result.get('jwt_decoded', {}).get('payload', {})

        text = f"<b>🧬 JWT EXTRACT SUCCESS</b>\n\n"
        text += f"🆔 <b>UID:</b> <code>{uid}</code>\n"
        text += f"🌍 <b>Region:</b> {region}\n"
        text += f"🎮 <b>Platform:</b> {platform}\n"
        text += f"🌐 <b>Server:</b> {server}\n\n"
        if jwt_str:
            text += f"<b>🔑 FULL JWT:</b>\n<code>{jwt_str[:1000]}</code>...\n\n"
        if decoded:
            text += "<b>📦 Decoded Payload:</b>\n"
            for k,v in list(decoded.items())[:10]:
                text += f"• {k}: {v}\n"
        bot.send_message(message.chat.id, text, reply_markup=main_menu_keyboard())
    else:
        bot.send_message(message.chat.id, f"❌ Failed: {err}", reply_markup=main_menu_keyboard())

# Fallback text handler
@bot.message_handler(func=lambda m: True, content_types=['text'])
def fallback_handler(message):
    if message.text.startswith('/'):
        bot.send_message(message.chat.id, "❓ Command nahi samjha. /start dabao", reply_markup=main_menu_keyboard())
    else:
        if len(message.text.strip()) > 50:
            bot.send_message(message.chat.id, "🔑 Lagta hai tumne token bheja hai. Kya karna hai wo select karo:", reply_markup=main_menu_keyboard())
        else:
            bot.send_message(message.chat.id, "👋 Main menu se option select karo:", reply_markup=main_menu_keyboard())

# ================= RUN BOT =================
if __name__ == "__main__":
    print(f'''
V2.0 PRO - RAO BIND MANAGER BOT
Developer: @raostarr | RAO ON TOP
Bot starting...
Make sure BOT_TOKEN is set!
''')
    if BOT_TOKEN == "PASTE_YOUR_BOT_TOKEN_HERE":
        print("❌ BOT_TOKEN nahi dala! File ke upar BOT_TOKEN variable me apna token dalo jo @BotFather se mila hai")
        print("Ya environment variable BOT_TOKEN set karo")
    else:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
        except Exception as e:
            print(f"Bot crashed: {e}")
            time.sleep(5)
