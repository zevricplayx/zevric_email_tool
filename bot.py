"""
Spidey Bind Tool - Telegram Bot Version
Developer: @spideyabd AND @INDRAJIT_1M
Converted from CLI to Telegram Bot API

Requirements:
pip install pyTelegramBotAPI requests pycryptodome protobuf

Files needed in same folder:
- MajoRLogin_pb2.py (DaNgEr_MajoRLogin_pb2.py rename if needed)
- MajorLoginRes_pb2.py
- telegram_bot.py (this file)

Setup:
1. BotFather se token lo
2. BOT_TOKEN me token daalo
3. python telegram_bot.py run karo
"""

import requests
import os
import sys
import json
import time
import urllib.parse
import base64
import hashlib
import urllib3
from datetime import datetime
import telebot
from telebot import types

# Protobuf imports
try:
    import MajoRLogin_pb2 as mLpB
    import MajorLoginRes_pb2 as mLrPb
except ImportError:
    try:
        import DaNgEr_MajoRLogin_pb2 as mLpB
        import MajorLoginRes_pb2 as mLrPb
    except ImportError:
        print("[!] Error: Protobuf files not found!")
        print("Make sure MajoRLogin_pb2.py and MajorLoginRes_pb2.py are in same folder")
        # Don't exit for bot, just warn
        mLpB = None
        mLrPb = None

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================== CONFIG ==================
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # <-- Yaha apna token daalo
# BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# User states for conversation flow
user_states = {}
user_data = {}

# ================== HELPER FUNCTIONS ==================

def convert_seconds(s):
    d, h = divmod(s, 86400)
    h, m = divmod(h, 3600)
    m, s = divmod(m, 60)
    return f"{d} Day {h} Hour {m} Min {s} Sec"

def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("🔍 CHECK BIND INFO", callback_data="check_bind")
    btn2 = types.InlineKeyboardButton("📧 BIND EMAIL", callback_data="bind_email")
    btn3 = types.InlineKeyboardButton("❌ UNBIND EMAIL", callback_data="unbind_email")
    btn4 = types.InlineKeyboardButton("🔄 CHANGE EMAIL", callback_data="change_email")
    btn5 = types.InlineKeyboardButton("🚫 CANCEL REQUEST", callback_data="cancel_bind")
    btn6 = types.InlineKeyboardButton("🔑 EAT TO TOKEN", callback_data="eat_token")
    btn7 = types.InlineKeyboardButton("♻️ REVOKE TOKEN", callback_data="revoke_token")
    btn8 = types.InlineKeyboardButton("📜 LOGIN HISTORY", callback_data="login_history")
    btn9 = types.InlineKeyboardButton("🔗 BOUND ACCOUNTS", callback_data="bound_accounts")
    btn10 = types.InlineKeyboardButton("👤 OWNER DETAILS", callback_data="owner_details")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5, btn6)
    markup.add(btn7, btn8)
    markup.add(btn9, btn10)
    return markup

def format_bind_response(data, uid="Unknown", nickname="Unknown", region="Unknown"):
    email = data.get("email", "")
    email_to_be = data.get("email_to_be", "")
    countdown = data.get("request_exec_countdown", 0)
    countdown_human = convert_seconds(countdown)
    
    text = f"<b>≡ Player Information</b>\n"
    text += f"● UID: <code>{uid}</code>\n"
    text += f"● Nickname: {nickname}\n"
    text += f"● Region: {region}\n\n"
    text += f"<b>≡ Bind Information</b>\n"
    text += f"● Current Email: {email if email else 'None'}\n"
    text += f"● Pending Email: {email_to_be if email_to_be else 'None'}\n"
    if email_to_be:
        text += f"● Countdown: {countdown_human}\n"
    text += f"\n● Result Code: {data.get('result', -1)}"
    return text

def fetch_player_info(access_token):
    try:
        player_url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        p_res = requests.get(player_url, headers=headers, timeout=15, allow_redirects=True)
        parsed_url = urllib.parse.urlparse(p_res.url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        uid = query_params.get("account_id", ["Unknown"])[0]
        nickname = query_params.get("nickname", ["Unknown"])[0]
        region = query_params.get("region", ["Unknown"])[0]
        return uid, nickname, region
    except Exception as e:
        return "Unknown", "Unknown", "Unknown"

# ================== CORE API FUNCTIONS (from your app.py) ==================

def api_check_bind_info(access_token):
    uid, nickname, region = fetch_player_info(access_token)
    
    url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
    payload = {'app_id': "100067", 'access_token': access_token}
    headers = {
        'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip"
    }
    response = requests.get(url, params=payload, headers=headers, timeout=15)
    if response.status_code == 200:
        data = response.json()
        return format_bind_response(data, uid, nickname, region)
    else:
        return f"❌ Failed to fetch bind info. HTTP {response.status_code}\n{response.text}"

def api_bind_email(access_token, email):
    # This logic is taken from your original bind_email function
    url = "https://100067.connect.garena.com/game/account_security/bind:bind_email"
    payload = {'app_id': "100067", 'access_token': access_token, 'email': email}
    headers = {
        'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip"
    }
    response = requests.get(url, params=payload, headers=headers, timeout=15)
    try:
        data = response.json()
        if data.get("result") == 0:
            return f"✅ Bind Email SUCCESS\nEmail: {email}\nResponse: {data}"
        else:
            return f"❌ Bind Email FAILED\nCode: {data.get('result')} | {data.get('error', 'Unknown')}\nFull: {data}"
    except:
        return f"📩 Response: {response.text}"

def api_unbind_email(access_token):
    url = "https://100067.connect.garena.com/game/account_security/bind:unbind_email"
    payload = {'app_id': "100067", 'access_token': access_token}
    headers = {
        'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip"
    }
    response = requests.get(url, params=payload, headers=headers, timeout=15)
    try:
        data = response.json()
        if data.get("result") == 0:
            return f"✅ Unbind Email SUCCESS\n{data}"
        else:
            return f"❌ Unbind FAILED: {data}"
    except:
        return f"Response: {response.text}"

def api_change_bind_email(access_token, new_email):
    url = "https://100067.connect.garena.com/game/account_security/bind:change_bind_email"
    payload = {'app_id': "100067", 'access_token': access_token, 'email': new_email}
    headers = {
        'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip"
    }
    response = requests.get(url, params=payload, headers=headers, timeout=15)
    try:
        data = response.json()
        if data.get("result") == 0:
            return f"✅ Change Email Request SUCCESS\nNew Email: {new_email}\n{data}"
        else:
            return f"❌ Change Email FAILED: {data}"
    except:
        return f"Response: {response.text}"

def api_cancel_bind(access_token):
    url = "https://100067.connect.garena.com/game/account_security/bind:cancel_bind_request"
    payload = {'app_id': "100067", 'access_token': access_token}
    headers = {
        'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip"
    }
    response = requests.get(url, params=payload, headers=headers, timeout=15)
    try:
        data = response.json()
        if data.get("result") == 0:
            return f"✅ Cancel Request SUCCESS\n{data}"
        else:
            return f"❌ Cancel FAILED: {data}"
    except:
        return f"Response: {response.text}"

def api_check_bound_accounts(access_token):
    url = "https://100067.connect.garena.com/bind/app/platform/info/get"
    params = {"access_token": access_token}
    headers = {
        "User-Agent": "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    }
    response = requests.get(url, params=params, headers=headers, timeout=10)
    if response.status_code != 200:
        return f"❌ Failed to fetch (HTTP {response.status_code})"

    d = response.json()
    bounded_accounts = d.get("bounded_accounts", [])
    available_platforms = d.get("available_platforms", [])

    PLATFORM_MAP = {
        1: "Garena", 3: "Facebook", 4: "Guest", 5: "VK",
        6: "Huawei", 7: "Apple", 8: "Google", 10: "GameCenter / Line",
        11: "X (Twitter)", 13: "Apple ID", 28: "Line", 35: "TikTok"
    }

    text = "<b>≡ PLATFORM BINDS</b>\n\n<b>⊛ BOUND ACCOUNTS:</b>\n"
    if not bounded_accounts:
        text += "● No third-party platforms are currently bound.\n"
    else:
        for p_id in bounded_accounts:
            p_name = PLATFORM_MAP.get(p_id, f"Unknown ({p_id})")
            text += f"● {p_name}\n"
    
    text += "\n<b>⊛ AVAILABLE PLATFORMS:</b>\n"
    if not available_platforms:
        text += "● None\n"
    else:
        for p_id in available_platforms:
            p_name = PLATFORM_MAP.get(p_id, f"Unknown ({p_id})")
            text += f"● {p_name}\n"
    return text

# Note: EAT to token, Revoke, History, Owner details functions depend on your protobuf logic
# Placeholder wrappers - you can copy exact logic from original app.py into these

def api_eat_to_token(eat_token):
    # Original function: eat_to_access_token()
    # It usually uses protobuf to exchange
    if mLpB is None:
        return "❌ Protobuf files missing. Cannot process EAT token."
    try:
        # --- COPY YOUR ORIGINAL eat_to_access_token LOGIC HERE ---
        # Example structure:
        # You need to implement the protobuf encoding as in original
        # For now, placeholder for API call
        return "⚙️ EAT TO TOKEN logic needs to be ported.\nPaste your original function body here if this placeholder fails."
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ================== BOT HANDLERS ==================

@bot.message_handler(commands=['start', 'menu', 'help'])
def handle_start(message):
    welcome_text = f"""
<b>🕷️ Spidey Bind Tool - Telegram Bot</b>

● Developer: @spideyabd & @INDRAJIT_1M
● Status: SAFE & SECURE

Neeche se koi option select karo 👇
Access Token chahiye hoga har action ke liye.

<b>Commands:</b>
/start - Main menu
/bindinfo - Check Bind Info
/bindemail - Bind Email
/unbindemail - Unbind Email
/changeemail - Change Email
/cancelbind - Cancel Request
/platforms - Check Bound Accounts
/history - Login History

<i>Note: EAT token aur protobuf wale features ke liye original files same folder me rakho</i>
"""
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_menu())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    data = call.data
    
    if data == "check_bind":
        msg = bot.send_message(chat_id, "🔑 <b>Access Token bhejo:</b>\n\nExample: <code>eyJhbGc...</code>", reply_markup=types.ForceReply())
        user_states[chat_id] = "awaiting_token_for_bind"
        bot.register_next_step_handler(msg, process_token_bind)
    
    elif data == "bind_email":
        msg = bot.send_message(chat_id, "🔑 <b>Pehle Access Token bhejo:</b>", reply_markup=types.ForceReply())
        user_states[chat_id] = "awaiting_token_for_bind_email"
        bot.register_next_step_handler(msg, process_token_for_bind_email)

    elif data == "unbind_email":
        msg = bot.send_message(chat_id, "🔑 <b>Access Token bhejo unbind ke liye:</b>", reply_markup=types.ForceReply())
        user_states[chat_id] = "awaiting_token_for_unbind"
        bot.register_next_step_handler(msg, process_token_unbind)

    elif data == "change_email":
        msg = bot.send_message(chat_id, "🔑 <b>Access Token bhejo change ke liye:</b>", reply_markup=types.ForceReply())
        user_states[chat_id] = "awaiting_token_for_change"
        bot.register_next_step_handler(msg, process_token_for_change)

    elif data == "cancel_bind":
        msg = bot.send_message(chat_id, "🔑 <b>Access Token bhejo cancel ke liye:</b>", reply_markup=types.ForceReply())
        user_states[chat_id] = "awaiting_token_for_cancel"
        bot.register_next_step_handler(msg, process_token_cancel)

    elif data == "eat_token":
        msg = bot.send_message(chat_id, "🔑 <b>EAT Token bhejo (ey... se start hota hai):</b>", reply_markup=types.ForceReply())
        user_states[chat_id] = "awaiting_eat"
        bot.register_next_step_handler(msg, process_eat_token)

    elif data == "bound_accounts":
        msg = bot.send_message(chat_id, "🔑 <b>Access Token bhejo platform check ke liye:</b>", reply_markup=types.ForceReply())
        user_states[chat_id] = "awaiting_token_for_platforms"
        bot.register_next_step_handler(msg, process_token_platforms)

    elif data == "login_history":
        msg = bot.send_message(chat_id, "🔑 <b>Access Token bhejo login history ke liye:</b>", reply_markup=types.ForceReply())
        user_states[chat_id] = "awaiting_token_for_history"
        bot.register_next_step_handler(msg, process_token_history)

    elif data == "owner_details":
        bot.send_message(chat_id, "👤 <b>Owner Details feature</b>\nOriginal app.py se owner_details() ka logic yaha add karna hoga.\nFile me dekh ke copy kar do.", reply_markup=get_main_menu())

    elif data == "revoke_token":
        msg = bot.send_message(chat_id, "🔑 <b>Access Token bhejo revoke ke liye:</b>", reply_markup=types.ForceReply())
        user_states[chat_id] = "awaiting_token_for_revoke"
        bot.register_next_step_handler(msg, process_token_revoke)

    bot.answer_callback_query(call.id)

# --- Processors ---

def process_token_bind(message):
    token = message.text.strip()
    chat_id = message.chat.id
    bot.send_message(chat_id, "⏳ Fetching bind info...")
    try:
        result = api_check_bind_info(token)
        bot.send_message(chat_id, result, reply_markup=get_main_menu())
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {str(e)}", reply_markup=get_main_menu())
    user_states.pop(chat_id, None)

def process_token_for_bind_email(message):
    token = message.text.strip()
    chat_id = message.chat.id
    user_data[chat_id] = {"token": token}
    msg = bot.send_message(chat_id, "📧 <b>Ab Email bhejo jo bind karna hai:</b>\nExample: yourmail@gmail.com", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_email_for_bind)

def process_email_for_bind(message):
    email = message.text.strip()
    chat_id = message.chat.id
    token = user_data.get(chat_id, {}).get("token")
    if not token:
        bot.send_message(chat_id, "❌ Token missing. /start se dobara try karo.", reply_markup=get_main_menu())
        return
    bot.send_message(chat_id, f"⏳ Binding {email}...")
    try:
        result = api_bind_email(token, email)
        bot.send_message(chat_id, result, reply_markup=get_main_menu())
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {str(e)}", reply_markup=get_main_menu())
    user_data.pop(chat_id, None)
    user_states.pop(chat_id, None)

def process_token_unbind(message):
    token = message.text.strip()
    chat_id = message.chat.id
    bot.send_message(chat_id, "⏳ Unbinding...")
    try:
        result = api_unbind_email(token)
        bot.send_message(chat_id, result, reply_markup=get_main_menu())
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {str(e)}", reply_markup=get_main_menu())

def process_token_for_change(message):
    token = message.text.strip()
    chat_id = message.chat.id
    user_data[chat_id] = {"token": token}
    msg = bot.send_message(chat_id, "📧 <b>New Email bhejo:</b>", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_email_for_change)

def process_email_for_change(message):
    email = message.text.strip()
    chat_id = message.chat.id
    token = user_data.get(chat_id, {}).get("token")
    bot.send_message(chat_id, f"⏳ Changing to {email}...")
    try:
        result = api_change_bind_email(token, email)
        bot.send_message(chat_id, result, reply_markup=get_main_menu())
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {str(e)}", reply_markup=get_main_menu())

def process_token_cancel(message):
    token = message.text.strip()
    chat_id = message.chat.id
    bot.send_message(chat_id, "⏳ Cancelling request...")
    try:
        result = api_cancel_bind(token)
        bot.send_message(chat_id, result, reply_markup=get_main_menu())
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {str(e)}", reply_markup=get_main_menu())

def process_eat_token(message):
    eat = message.text.strip()
    chat_id = message.chat.id
    bot.send_message(chat_id, "⏳ Converting EAT to Access Token...")
    result = api_eat_to_token(eat)
    bot.send_message(chat_id, result, reply_markup=get_main_menu())

def process_token_platforms(message):
    token = message.text.strip()
    chat_id = message.chat.id
    bot.send_message(chat_id, "⏳ Checking platforms...")
    try:
        result = api_check_bound_accounts(token)
        bot.send_message(chat_id, result, reply_markup=get_main_menu())
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {str(e)}", reply_markup=get_main_menu())

def process_token_history(message):
    token = message.text.strip()
    chat_id = message.chat.id
    bot.send_message(chat_id, "⏳ Fetching login history...\n(Ye feature protobuf decryption use karta hai, original logic add karna padega)", reply_markup=get_main_menu())

def process_token_revoke(message):
    token = message.text.strip()
    chat_id = message.chat.id
    bot.send_message(chat_id, "⏳ Revoking token...")
    # Add your revoke_access_token logic here from original file
    bot.send_message(chat_id, "♻️ Revoke logic - original file se port karna baki hai. api URL: /revoke", reply_markup=get_main_menu())

# Direct commands
@bot.message_handler(commands=['bindinfo'])
def cmd_bindinfo(message):
    handle_callback(types.CallbackQuery(id="1", from_user=message.from_user, message=message, data="check_bind", chat_instance=""))

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    # If user sends token directly without menu
    if len(message.text) > 100:  # likely token
        bot.send_message(message.chat.id, "🔑 Token detected! Kya karna hai?", reply_markup=get_main_menu())
    else:
        bot.send_message(message.chat.id, "👋 /start bhejo menu ke liye", reply_markup=get_main_menu())

# ================== RUN ==================
if __name__ == "__main__":
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("[!] BOT_TOKEN set nahi hai! File me BOT_TOKEN variable me apna token daalo")
    else:
        print("Bot started... Spidey Bind Tool")
        print("Press Ctrl+C to stop")
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
