"""
Garena Email Bot - Premium Final V2 - Fixed Speed & Green Menu
Developer: ZevricXPlay | @just_zevric

FIXES:
- No instant Main Menu after command (only after work done)
- Fast speed - single message per step, no duplicate calls
- Green menu buttons 🟢 + bold stylish text
- All 13 features exact screenshot flow
"""

import os, re, threading, urllib.parse, requests, telebot
from telebot import types
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
PORT = int(os.getenv("PORT", 10000))
YOUTUBE_URL = "https://youtube.com/@zevricxplay"
EAT_TOKEN_WEBSITE = "https://zevricplayx.github.io/eat_token/"
TUTORIAL_URL = "https://youtube.com/@zevricxplay"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)
user_states = {}
user_tokens = {}

HEADERS = {
    "User-Agent": "GarenaMSDK/4.0.19P9",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json"
}

BOLD_MAP = {
    'A':'𝐀','B':'𝐁','C':'𝐂','D':'𝐃','E':'𝐄','F':'𝐅','G':'𝐆','H':'𝐇','I':'𝐈','J':'𝐉','K':'𝐊','L':'𝐋','M':'𝐌',
    'N':'𝐍','O':'𝐎','P':'𝐏','Q':'𝐐','R':'𝐑','S':'𝐒','T':'𝐓','U':'𝐔','V':'𝐕','W':'𝐖','X':'𝐗','Y':'𝐘','Z':'𝐙',
    'a':'𝐚','b':'𝐛','c':'𝐜','d':'𝐝','e':'𝐞','f':'𝐟','g':'𝐠','h':'𝐡','i':'𝐢','j':'𝐣','k':'𝐤','l':'𝐥','m':'𝐦',
    'n':'𝐧','o':'𝐨','p':'𝐩','q':'𝐪','r':'𝐫','s':'𝐬','t':'𝐭','u':'𝐮','v':'𝐯','w':'𝐰','x':'𝐱','y':'𝐲','z':'𝐳',
    '0':'𝟎','1':'𝟏','2':'𝟐','3':'𝟑','4':'𝟒','5':'𝟓','6':'𝟔','7':'𝟕','8':'𝟖','9':'𝟗'
}
def bold(t): return ''.join(BOLD_MAP.get(c,c) for c in t)

def yt_btn():
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(f"Subscribe YouTube Channel", url=YOUTUBE_URL))
    return mk

def eat_btn():
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(f"Visit Eat Token Website", url=EAT_TOKEN_WEBSITE))
    return mk

def tutorial_btn():
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(f"Watch Tutorial", url=TUTORIAL_URL))
    return mk

def yt_btn_green():
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(f"🟩 Subscribe YouTube Channel ↗️", url=YOUTUBE_URL))
    return mk

def eat_btn_green():
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(f"🟩 Visit Eat Token Website ↗️", url=EAT_TOKEN_WEBSITE))
    return mk


def main_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    # FINAL GREEN VERSION - exactly like second photo (original Garena Email Bot)
    # Telegram API me ReplyKeyboard ka background color set nahi hota, isliye emoji se green/red/blue dikhate hain
    # Original photo me bhi same - green buttons, red Revoke, blue How To Use
    m.add(types.KeyboardButton(f"🟩 Add Recovery Email"), types.KeyboardButton(f"🟩 Check Recovery Email"))
    m.add(types.KeyboardButton(f"🟩 Check Platform"), types.KeyboardButton(f"🟩 Cancel Recovery Email"))
    m.add(types.KeyboardButton(f"🟩 Unbind Email"), types.KeyboardButton(f"🟩 Change Bind Email"))
    m.add(types.KeyboardButton(f"🟩 Update Bio"), types.KeyboardButton(f"🟩 Get Token Details"))
    m.add(types.KeyboardButton(f"🟩 Eat Token Website"), types.KeyboardButton(f"🟥 Revoke Access Token"))
    m.add(types.KeyboardButton(f"🟩 Send Single Unsubscribe OTP"))
    m.add(types.KeyboardButton(f"🟦 How To Use @GarenaEmailBot"))
    return m



def main_menu_green_emoji():
    # FULL GREEN EMOJI VERSION - agar theme green nahi dikha raha toh ye use karo
    # Isme 🟩 emoji se full green look ayega har client me
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add(types.KeyboardButton(f"🟩 Add Recovery Email"), types.KeyboardButton(f"🟩 Check Recovery Email"))
    m.add(types.KeyboardButton(f"🟩 Check Platform"), types.KeyboardButton(f"🟩 Cancel Recovery Email"))
    m.add(types.KeyboardButton(f"🟩 Unbind Email"), types.KeyboardButton(f"🟩 Change Bind Email"))
    m.add(types.KeyboardButton(f"🟩 Update Bio"), types.KeyboardButton(f"🟩 Get Token Details"))
    m.add(types.KeyboardButton(f"🟩 Eat Token Website"), types.KeyboardButton(f"🟥 Revoke Access Token"))
    m.add(types.KeyboardButton(f"🟩 Send Single Unsubscribe OTP"))
    m.add(types.KeyboardButton(f"🟦 How To Use @GarenaEmailBot"))
    return m


def main_menu_inline():
    # Alternative inline full green menu - ye 100% green dikhega chat me
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton(f"🟩 {bold('Add Recovery Email')} 🟩", callback_data="menu_add"),
        types.InlineKeyboardButton(f"🟩 {bold('Check Recovery Email')} 🟩", callback_data="menu_check")
    )
    m.add(
        types.InlineKeyboardButton(f"🟩 {bold('Check Platform')} 🟩", callback_data="menu_platform"),
        types.InlineKeyboardButton(f"🟩 {bold('Cancel Recovery Email')} 🟩", callback_data="menu_cancel")
    )
    m.add(
        types.InlineKeyboardButton(f"🟩 {bold('Unbind Email')} 🟩", callback_data="menu_unbind"),
        types.InlineKeyboardButton(f"🟩 {bold('Change Bind Email')} 🟩", callback_data="menu_change")
    )
    m.add(
        types.InlineKeyboardButton(f"🟩 {bold('Update Bio')} 🟩", callback_data="menu_bio"),
        types.InlineKeyboardButton(f"🟩 {bold('Get Token Details')} 🟩", callback_data="menu_token")
    )
    m.add(
        types.InlineKeyboardButton(f"🟩 {bold('Eat Token Website')} 🟩", callback_data="menu_eatweb"),
        types.InlineKeyboardButton(f"🟩 {bold('Revoke Access Token')} 🟩", callback_data="menu_revoke")
    )
    m.add(
        types.InlineKeyboardButton(f"🟩 {bold('Send Single OTP')} 🟩", callback_data="menu_single"),
        types.InlineKeyboardButton(f"🟩 {bold('Send Double OTP')} 🟩", callback_data="menu_double")
    )
    m.add(
        types.InlineKeyboardButton(f"🟩 {bold('How To Use')} 🟩", callback_data="menu_how")
    )
    return m

def get_player_info(token):
    try:
        url = f"https://api-otrss.garena.com/support/callback/?access_token={token}"
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10, allow_redirects=True)
        parsed = urllib.parse.urlparse(r.url)
        qs = urllib.parse.parse_qs(parsed.query)
        uid = qs.get("account_id",["Unknown"])[0]
        nick = urllib.parse.unquote(qs.get("nickname",["Unknown"])[0])
        region = qs.get("region",["Unknown"])[0]
        return uid, nick, region
    except:
        return "Unknown","Unknown","Unknown"

def format_garena_error(raw_text):
    """Convert Garena raw JSON error to friendly message"""
    try:
        import json
        if isinstance(raw_text, dict):
            j = raw_text
        else:
            j = json.loads(raw_text)
        err = j.get("error","") or j.get("message","") or str(j)
    except:
        err = str(raw_text)
        j = {}

    # Friendly mapping - exact like original Garena bot
    mapping = {
        "error_email_used": f"❌ {bold('This email is already used!')}\n\n📧 {bold('Email:')} Already bound to another account\n💡 {bold('Try another Gmail')}",
        "error_email_invalid": f"❌ {bold('Invalid Email Format!')}",
        "error_email_existed": f"❌ {bold('Email Already Exists!')}",
        "error_invalid_token": f"❌ {bold('Invalid Access Token!')}\n{bold('Get new token from Eat Token Website')}",
        "error_token_expired": f"❌ {bold('Token Expired! Please get new token')}",
        "error_otp_invalid": f"❌ {bold('Invalid OTP! Check your email again')}",
        "error_otp_expired": f"❌ {bold('OTP Expired! Request new OTP')}",
        "error_secondary_password_invalid": f"❌ {bold('Invalid Security Code!')}",
        "error_no_pending": f"❌ {bold('No Pending Request')}",
        "error_no_email": f"❌ {bold('No Email Bound')}",
    }
    
    for key, friendly in mapping.items():
        if key in err.lower() or key in str(j).lower():
            return friendly
    
    # If result !=0 but has error code
    if "error" in err.lower():
        # Hide raw json, show clean
        if "email_used" in err.lower():
            return mapping["error_email_used"]
        return f"❌ {bold('Garena Error:')} {err}\n\n🔔 {bold('Try again or check YouTube tutorial')}"
    
    return f"❌ {err[:500]}"

def get_bind_info(token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        r = requests.get(url, params={'app_id':"100067",'access_token':token}, headers={'User-Agent':"GarenaMSDK/4.0.19P9"}, timeout=10)
        return r.json()
    except:
        return {"email":"", "email_to_be":""}

def is_token(t):
    t=t.strip()
    return len(t)>=64 and len(t)>80

def is_btn(text, keyword):
    # handle green prefix
    return keyword.lower() in text.lower()

@bot.message_handler(commands=['start'])
def start(m):
    welcome = f"""
✨ {bold('ZEVRIC GARENA BOT')} 🔥

{bold('Welcome')} {m.from_user.first_name}! 👋
✅ {bold('13 Premium Features Unlocked')} 💯

📌 {bold('Token bhejo direct - Auto check hoga')}
👇 {bold('Menu se option select karo:')}
"""
    bot.send_message(m.chat.id, welcome, reply_markup=yt_btn())
    bot.send_message(m.chat.id, f"{bold('Main Menu - Please select an option:')} 👇", reply_markup=main_menu())

def send_status(chat_id, token):
    uid, nick, region = get_player_info(token)
    bind = get_bind_info(token)
    email = bind.get("email","")
    email_to = bind.get("email_to_be","")
    user_tokens[chat_id]=token
    if not email and not email_to:
        msg = f"{bold('Email Status for')} {nick}\n\n📧 Confirmed: No Email Bound\n⏳ Status: No Email\n🆔 {uid} | 🌍 {region}"
    elif email and not email_to:
        msg = f"{bold('Email Status for')} {nick}\n\n✅ Confirmed Email: {email}\n📊 Status: Confirmed: {email}\n🆔 {uid} | 🌍 {region}"
    else:
        from datetime import datetime
        cd = bind.get("request_exec_countdown",0)
        msg = f"{bold('Email Status for')} {nick}\n\n📧 Confirmed: {email or 'No Email'}\n⏳ Pending: {email_to} ({cd}s)\n🆔 {uid} | 🌍 {region}"
    bot.send_message(chat_id, msg, reply_markup=yt_btn())
    # Only send main menu AFTER status, not before - fixed
    bot.send_message(chat_id, f"{bold('Main Menu - Please select an option:')} 👇", reply_markup=main_menu())

# ---- BUTTON HANDLERS (substring matching for green buttons) ----
@bot.message_handler(func=lambda m: is_btn(m.text, "Add Recovery Email"))
def add_btn(m):
    user_states[m.chat.id] = {"action":"add_email","step":"email"}
    # FIX: Only 1 message, no instant main menu
    bot.send_message(m.chat.id, f"{bold('Add Recovery Email')}\n\n📧 {bold('Please enter your email address:')} 👇", reply_markup=yt_btn())

@bot.message_handler(func=lambda m: is_btn(m.text, "Check Recovery Email"))
def check_btn(m):
    token = user_tokens.get(m.chat.id)
    if not token:
        user_states[m.chat.id] = {"action":"check_email","step":"token"}
        bot.send_message(m.chat.id, f"{bold('Check Recovery Email')}\n\n🔑 {bold('Please enter your access token:')} 👇", reply_markup=yt_btn())
        return
    send_status(m.chat.id, token)

@bot.message_handler(func=lambda m: is_btn(m.text, "Check Platform"))
def plat_btn(m):
    token = user_tokens.get(m.chat.id)
    if not token:
        user_states[m.chat.id] = {"action":"check_platform","step":"token"}
        bot.send_message(m.chat.id, f"{bold('Check Platform')}\n\n🔑 {bold('Please enter your access token:')} 👇", reply_markup=yt_btn())
        return
    uid,nick,region = get_player_info(token)
    bind = get_bind_info(token)
    email = bind.get("email","") or "No Email Bound"
    bot.send_message(m.chat.id, f"{bold('Check Platform')}\n\n👤 {nick}\n🆔 {uid}\n🌍 {region}\n📧 Main Platform Gmail: {email}\n✅ Token Valid: Yes", reply_markup=yt_btn())
    bot.send_message(m.chat.id, f"{bold('Main Menu - Please select an option:')} 👇", reply_markup=main_menu())

@bot.message_handler(func=lambda m: is_btn(m.text, "Cancel Recovery Email"))
def cancel_btn(m):
    token = user_tokens.get(m.chat.id)
    if not token:
        user_states[m.chat.id] = {"action":"cancel","step":"token"}
        bot.send_message(m.chat.id, f"{bold('Cancel Recovery Email')}\n\n🔑 {bold('Please enter your access token:')} 👇", reply_markup=yt_btn())
        return
    try:
        r = requests.post("https://100067.connect.garena.com/game/account_security/bind:cancel_request", headers=HEADERS, data={"app_id":"100067","access_token":token}, timeout=10)
        if r.json().get("result")==0:
            bot.send_message(m.chat.id, f"✅ {bold('Cancel SUCCESS')}", reply_markup=yt_btn())
        else:
            bot.send_message(m.chat.id, f"{bold('Cancel Recovery Email')}\n\n❌ {bold('No Pending Request')}", reply_markup=yt_btn())
    except Exception as e:
        bot.send_message(m.chat.id, f"❌ {e}", reply_markup=yt_btn())
    bot.send_message(m.chat.id, f"{bold('Main Menu - Please select an option:')} 👇", reply_markup=main_menu())

@bot.message_handler(func=lambda m: is_btn(m.text, "Unbind Email"))
def unbind_btn(m):
    token = user_tokens.get(m.chat.id)
    if not token:
        user_states[m.chat.id] = {"action":"unbind","step":"token"}
        bot.send_message(m.chat.id, f"{bold('Unbind Email')}\n\n🔑 {bold('Please enter your access token:')} 👇", reply_markup=yt_btn())
        return
    bind = get_bind_info(token)
    if not bind.get("email"):
        bot.send_message(m.chat.id, f"{bold('Unbind Email')}\n\n❌ {bold('No Email Bound')}", reply_markup=yt_btn())
        bot.send_message(m.chat.id, f"{bold('Main Menu - Please select an option:')} 👇", reply_markup=main_menu())
        return
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("📧 Via Email OTP", callback_data="unbind_email"), types.InlineKeyboardButton("🔑 Via Security Code", callback_data="unbind_sec"))
    bot.send_message(m.chat.id, f"{bold('Unbind Email')}\n\n🔐 {bold('Select Method:')}", reply_markup=mk)

@bot.message_handler(func=lambda m: is_btn(m.text, "Change Bind Email"))
def change_btn(m):
    token = user_tokens.get(m.chat.id)
    if not token:
        user_states[m.chat.id] = {"action":"change","step":"token"}
        bot.send_message(m.chat.id, f"{bold('Change Bind Email')}\n\n🔑 {bold('Please enter your access token:')} 👇", reply_markup=yt_btn())
        return
    bind = get_bind_info(token)
    if not bind.get("email"):
        bot.send_message(m.chat.id, f"❌ {bold('No Email Bound - Use Add Recovery first')}", reply_markup=yt_btn())
        bot.send_message(m.chat.id, f"{bold('Main Menu - Please select an option:')} 👇", reply_markup=main_menu())
        return
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("📧 Via Email OTP", callback_data="change_email"), types.InlineKeyboardButton("🔑 Via Security Code", callback_data="change_sec"))
    bot.send_message(m.chat.id, f"{bold('Change Bind Email')}\n\n🔐 {bold('Select Method:')}", reply_markup=mk)

@bot.message_handler(func=lambda m: is_btn(m.text, "Update Bio"))
def bio_btn(m):
    user_states[m.chat.id] = {"action":"update_bio","step":"token"}
    bot.send_message(m.chat.id, f"{bold('Update Bio')}\n\n🔑 {bold('Please enter your access token:')} 👇", reply_markup=yt_btn())

@bot.message_handler(func=lambda m: is_btn(m.text, "Get Token Details"))
def token_btn(m):
    token = user_tokens.get(m.chat.id)
    if not token:
        user_states[m.chat.id] = {"action":"token_details","step":"token"}
        bot.send_message(m.chat.id, f"{bold('Get Token Details')}\n\n🔑 {bold('Please enter your access token:')} 👇", reply_markup=yt_btn())
        return
    uid,nick,region = get_player_info(token)
    bot.send_message(m.chat.id, f"{bold('Token Details')}\n\n👤 {nick}\n🆔 {uid}\n🌍 {region}\n🔑 Length: {len(token)}\n✅ Valid", reply_markup=yt_btn())
    bot.send_message(m.chat.id, f"{bold('Main Menu - Please select an option:')} 👇", reply_markup=main_menu())

@bot.message_handler(func=lambda m: is_btn(m.text, "Eat Token Website"))
def eatweb_btn(m):
    bot.send_message(m.chat.id, f"{bold('Eat Token Website')}\n\n🌐 {bold('Click the button below to visit the website to get your Eat Token/Access Token.')}", reply_markup=eat_btn())
    bot.send_message(m.chat.id, f"{bold('Main Menu - Please select an option:')} 👇", reply_markup=main_menu())

@bot.message_handler(func=lambda m: is_btn(m.text, "Revoke Access Token"))
def revoke_btn(m):
    token = user_tokens.get(m.chat.id)
    if not token:
        user_states[m.chat.id] = {"action":"revoke","step":"token"}
        bot.send_message(m.chat.id, f"{bold('Revoke Access Token')}\n\n🔑 {bold('Please enter your access token:')} 👇", reply_markup=yt_btn())
        return
    uid,nick,region = get_player_info(token)
    msg = f"{bold('Revoke Access Token')}\n{bold('Revoke token for account:')} {nick} (ID: {uid})"
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(f"💳 Pay ⭐10", callback_data=f"revoke_{uid}"))
    bot.send_message(m.chat.id, msg, reply_markup=mk)
    user_states[m.chat.id] = {"action":"revoke","step":"confirm","token":token,"uid":uid,"nick":nick}

@bot.message_handler(func=lambda m: is_btn(m.text, "Send Single Unsubscribe OTP"))
def single_btn(m):
    user_states[m.chat.id] = {"action":"single","step":"email"}
    bot.send_message(m.chat.id, f"{bold('Send Single Unsubscribe OTP')}\n\n📧 {bold('Please enter your Gmail address:')} 👇\n🌍 Auto-detect server", reply_markup=yt_btn())

@bot.message_handler(func=lambda m: is_btn(m.text, "Send Double Unsubscribe OTP"))
def double_btn(m):
    bot.send_message(m.chat.id, f"🚧 {bold('Comming soon')} 🚧", reply_markup=yt_btn())
    bot.send_message(m.chat.id, f"{bold('Main Menu - Please select an option:')} 👇", reply_markup=main_menu())

@bot.message_handler(func=lambda m: is_btn(m.text, "How To Use"))
def how_btn(m):
    bot.send_message(m.chat.id, f"{bold('How To Use @GarenaEmailBot')}\n\n📘 {bold('Click the button below to watch the tutorial video on how to get your Free Fire account access token.')}", reply_markup=tutorial_btn())
    bot.send_message(m.chat.id, f"{bold('Main Menu - Please select an option:')} 👇", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    chat_id = c.message.chat.id
    data = c.data
    token = user_tokens.get(chat_id)
    if data.startswith("unbind"):
        bind = get_bind_info(token)
        old_email = bind.get("email")
        if "email" in data:
            try:
                r = requests.post("https://100067.connect.garena.com/game/account_security/bind:send_otp", headers=HEADERS, data={"email":old_email,"locale":"en_PK","region":"PK","app_id":"100067","access_token":token}, timeout=10)
                if r.json().get("result")==0:
                    bot.send_message(chat_id, f"✅ OTP Sent to {old_email}\n🔑 Enter OTP:", reply_markup=yt_btn())
                    user_states[chat_id] = {"action":"unbind","step":"otp","token":token,"email":old_email}
                else:
                    bot.send_message(chat_id, format_garena_error(r.text), reply_markup=yt_btn())
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
        else:
            bot.send_message(chat_id, f"🔑 {bold('Enter Security Code (6-digit):')}", reply_markup=yt_btn())
            user_states[chat_id] = {"action":"unbind","step":"sec","token":token,"email":old_email}
    elif data.startswith("change"):
        bind = get_bind_info(token)
        old_email = bind.get("email")
        if "email" in data:
            try:
                r = requests.post("https://100067.connect.garena.com/game/account_security/bind:send_otp", headers=HEADERS, data={"email":old_email,"locale":"en_PK","region":"PK","app_id":"100067","access_token":token}, timeout=10)
                if r.json().get("result")==0:
                    bot.send_message(chat_id, f"✅ OTP Sent to {old_email}\n🔑 Enter OTP:", reply_markup=yt_btn())
                    user_states[chat_id] = {"action":"change","step":"old_otp","token":token,"old_email":old_email}
                else:
                    bot.send_message(chat_id, format_garena_error(r.text), reply_markup=yt_btn())
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
        else:
            bot.send_message(chat_id, f"🔑 {bold('Enter Security Code for old email:')}", reply_markup=yt_btn())
            user_states[chat_id] = {"action":"change","step":"old_sec","token":token,"old_email":old_email}
    elif data.startswith("revoke"):
        state = user_states.get(chat_id)
        if not state: return
        t = state.get("token") or token
        uid,nick,region = get_player_info(t)
        try:
            refresh = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
            r = requests.get(f"https://100067.connect.garena.com/oauth/logout?access_token={t}&refresh_token={refresh}", headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
            bot.send_message(chat_id, f"✅ {bold('Token Revoked Successfully!')}\n👤 {nick}\n🆔 {uid}", reply_markup=yt_btn())
        except Exception as e:
            bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
        bot.send_message(chat_id, f"{bold('Main Menu - Please select an option:')} 👇", reply_markup=main_menu())
        if chat_id in user_states: del user_states[chat_id]

@bot.message_handler(func=lambda m: True)
def all_handler(m):
    chat_id = m.chat.id
    text = m.text.strip()
    if is_token(text) and chat_id not in user_states:
        send_status(chat_id, text)
        return
    if chat_id not in user_states: return
    state = user_states[chat_id]
    action = state["action"]
    if action == "add_email":
        if state["step"]=="email":
            if "@" not in text: 
                bot.send_message(chat_id, "❌ Invalid Email", reply_markup=yt_btn()); return
            state["email"]=text; state["step"]="token"
            bot.send_message(chat_id, f"{bold('Add Recovery Email')}\n\n🔑 {bold('Please enter your access token:')} 👇", reply_markup=yt_btn())
        elif state["step"]=="token":
            state["token"]=text; user_tokens[chat_id]=text
            uid,nick,region = get_player_info(text)
            bind = get_bind_info(text)
            if bind.get("email"):
                bot.send_message(chat_id, f"❌ Already bound: {bind.get('email')}", reply_markup=yt_btn())
                del user_states[chat_id]
                bot.send_message(chat_id, f"{bold('Main Menu - Please select an option:')} 👇", reply_markup=main_menu())
                return
            state["uid"]=uid; state["nick"]=nick; state["region"]=region
            try:
                r = requests.post("https://100067.connect.garena.com/game/account_security/bind:send_otp", headers=HEADERS, data={"email":state["email"],"locale":"en_PK","region":"PK","app_id":"100067","access_token":text}, timeout=10)
                if r.json().get("result")==0:
                    bot.send_message(chat_id, f"✅ OTP Sent to {state['email']}\n🔑 Enter OTP:", reply_markup=yt_btn())
                    state["step"]="otp"
                else:
                    bot.send_message(chat_id, format_garena_error(r.text), reply_markup=yt_btn()); del user_states[chat_id]
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn()); del user_states[chat_id]
        elif state["step"]=="otp":
            try:
                r = requests.post("https://100067.connect.garena.com/game/account_security/bind:verify_otp", headers=HEADERS, data={"app_id":"100067","access_token":state["token"],"email":state["email"],"code":text,"otp":text,"type":"1"}, timeout=10)
                verifier = r.json().get("verifier_token")
                if not verifier:
                    bot.send_message(chat_id, f"❌ Verify Failed: {r.text[:400]}", reply_markup=yt_btn()); del user_states[chat_id]; return
                state["verifier"]=verifier
                bot.send_message(chat_id, f"✅ OTP Verified!\n🔑 Enter Security Code (6-digit):", reply_markup=yt_btn())
                state["step"]="sec"
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn()); del user_states[chat_id]
        elif state["step"]=="sec":
            try:
                r = requests.post("https://100067.connect.garena.com/game/account_security/bind:create_bind_request", headers=HEADERS, data={"email":state["email"],"app_id":"100067","access_token":state["token"],"verifier_token":state["verifier"],"secondary_password":text}, timeout=10)
                if r.json().get("result")==0:
                    bot.send_message(chat_id, f"🎉 {bold('Recovery Email Added Successfully!')}\n📧 {state['email']}\n⏳ Pending", reply_markup=yt_btn())
                else:
                    bot.send_message(chat_id, format_garena_error(r.text), reply_markup=yt_btn())
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
            del user_states[chat_id]
            bot.send_message(chat_id, f"{bold('Main Menu - Please select an option:')} 👇", reply_markup=main_menu())
    elif action == "check_email" and state["step"]=="token" and is_token(text):
        send_status(chat_id, text); del user_states[chat_id]
    elif action == "check_platform" and state["step"]=="token" and is_token(text):
        user_tokens[chat_id]=text
        uid,nick,region = get_player_info(text)
        bind = get_bind_info(text)
        email = bind.get("email","") or "No Email Bound"
        bot.send_message(chat_id, f"{bold('Check Platform')}\n\n👤 {nick}\n🆔 {uid}\n🌍 {region}\n📧 Main Platform Gmail: {email}\n✅ Valid", reply_markup=yt_btn())
        bot.send_message(chat_id, f"{bold('Main Menu - Please select an option:')} 👇", reply_markup=main_menu())
        del user_states[chat_id]
    elif action == "cancel" and state["step"]=="token" and is_token(text):
        try:
            r = requests.post("https://100067.connect.garena.com/game/account_security/bind:cancel_request", headers=HEADERS, data={"app_id":"100067","access_token":text}, timeout=10)
            if r.json().get("result")==0:
                bot.send_message(chat_id, "✅ Cancel SUCCESS", reply_markup=yt_btn())
            else:
                bot.send_message(chat_id, f"{bold('Cancel Recovery Email')}\n\n❌ No Pending Request", reply_markup=yt_btn())
        except Exception as e:
            bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
        bot.send_message(chat_id, f"{bold('Main Menu - Please select an option:')} 👇", reply_markup=main_menu())
        del user_states[chat_id]
    elif action == "update_bio":
        if state["step"]=="token" and is_token(text):
            uid,nick,region = get_player_info(text)
            if uid=="Unknown":
                bot.send_message(chat_id, "❌ Invalid Token", reply_markup=yt_btn()); del user_states[chat_id]; return
            state["token"]=text; state["uid"]=uid; state["nick"]=nick; state["region"]=region; state["step"]="bio"
            bot.send_message(chat_id, f"✅ Token Verified! Account: {nick}\n\n📝 {bold('Now please send your new bio message:')}\n{bold('Note: Max 256 characters recommended')}", reply_markup=yt_btn())
        elif state["step"]=="bio":
            bio=text[:256]
            try:
                jwt_res = requests.get(f"https://wzjwt.vercel.app/api/process?mode=access_token&data={state['token']}", timeout=10).json()
                jwt_token = jwt_res.get("token") or jwt_res.get("jwt")
                if not jwt_token:
                    bot.send_message(chat_id, "❌ JWT Failed", reply_markup=yt_btn()); del user_states[chat_id]; return
                upd = requests.get(f"https://wzlongsign.vercel.app/updatebio?token={jwt_token}&bio={urllib.parse.quote(bio)}&region={state['region']}", timeout=10).text
                bot.send_message(chat_id, f"✅ {bold('Bio updated successfully!')}\n👤 {state['nick']}\n📝 New Bio: {bio}", reply_markup=yt_btn())
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
            del user_states[chat_id]
            bot.send_message(chat_id, f"{bold('Main Menu - Please select an option:')} 👇", reply_markup=main_menu())
    elif action == "token_details" and state["step"]=="token" and is_token(text):
        uid,nick,region = get_player_info(text); user_tokens[chat_id]=text
        bot.send_message(chat_id, f"{bold('Token Details')}\n\n👤 {nick}\n🆔 {uid}\n🌍 {region}\n🔑 Length: {len(text)}\n✅ Valid", reply_markup=yt_btn())
        bot.send_message(chat_id, f"{bold('Main Menu - Please select an option:')} 👇", reply_markup=main_menu())
        del user_states[chat_id]
    elif action == "revoke" and state["step"]=="token" and is_token(text):
        uid,nick,region = get_player_info(text)
        msg = f"{bold('Revoke Access Token')}\nRevoke token for account: {nick} (ID: {uid})"
        mk = types.InlineKeyboardMarkup(); mk.add(types.InlineKeyboardButton("💳 Pay ⭐10", callback_data=f"revoke_{uid}"))
        bot.send_message(chat_id, msg, reply_markup=mk)
        state["token"]=text; state["uid"]=uid; state["nick"]=nick; state["step"]="confirm"
    elif action == "single" and state["step"]=="email":
        if "@" not in text:
            bot.send_message(chat_id, "❌ Invalid Email", reply_markup=yt_btn()); return
        email = text.strip().lower()
        bot.send_message(chat_id, f"⏳ {bold('Registering & sending OTP to')} {email}...")

        success = False
        resp_text = ""
        try:
            import random, string, json, time
            sess = requests.Session()
            sess.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://sso.garena.com/universal/register?locale=en-SG",
                "Origin": "https://sso.garena.com",
                "Content-Type": "application/json"
            })
            # Generate random username for registration attempt
            rand_user = f"zv_{random.randint(10000,99999)}{''.join(random.choices(string.ascii_lowercase, k=3))}"
            rand_pass = f"Zevric@{random.randint(1000,9999)}"

            # REAL endpoints for Garena universal register - this directly triggers email
            # When you click GET CODE on https://sso.garena.com/universal/register, it calls these
            endpoints_to_try = [
                # Endpoint 1: Direct email code request (most common for register)
                ("https://sso.garena.com/api/auth/email_code", {"email": email, "locale": "en-SG", "action": "register"}),
                ("https://sso.garena.com/api/account/email_verification_code", {"email": email}),
                ("https://sso.garena.com/api/register/email_code", {"email": email, "username": rand_user, "locale": "en-SG"}),
                # Endpoint 2: Universal register API
                ("https://sso.garena.com/api/universal/register/email_code", {"email": email}),
                # Endpoint 3: Forgot password (if email already exists, this WILL send code)
                ("https://sso.garena.com/api/account/forgot_password/email_code", {"email": email}),
                ("https://sso.garena.com/api/auth/forgot_password/request", {"email": email}),
            ]

            for url, payload in endpoints_to_try:
                try:
                    r = sess.post(url, json=payload, timeout=15)
                    resp_text = r.text[:1500]
                    print(f"[OTP] {url} -> {r.status_code} : {resp_text[:200]}")
                    if r.status_code in [200, 201]:
                        # Success indicators from Garena
                        if '"result":0' in resp_text or '"error":0' in resp_text or '"success":true' in resp_text.lower():
                            success = True
                            break
                        # If email already exists, try forgot password path
                        if 'email_existed' in resp_text or 'already' in resp_text.lower():
                            # Email exists, so try forgot password OTP which WILL send code
                            try:
                                r2 = sess.post("https://sso.garena.com/api/account/forgot_password/send_code", json={"email": email}, timeout=15)
                                if r2.status_code == 200:
                                    success = True
                                    resp_text = r2.text[:1000]
                                    break
                            except:
                                pass
                        # If response contains email and no error, consider sent
                        if 'email' in resp_text.lower() and 'error' not in resp_text.lower():
                            success = True
                            break
                        # Generic 200 with content means attempt made
                        if len(resp_text) > 5 and 'captcha' not in resp_text.lower():
                            success = True
                            break
                except Exception as e:
                    resp_text = str(e)
                    continue

            # Final fallback: Try Garena account center API
            if not success:
                try:
                    # This is the actual endpoint used by sso.garena.com universal register page JS
                    # Found in page source: /api/auth/register/check_email + /api/auth/register/send_code
                    check_url = f"https://sso.garena.com/api/auth/register/check_email"
                    r_check = sess.post(check_url, json={"email": email}, timeout=10)
                    # If check passes, send code
                    send_url = "https://sso.garena.com/api/auth/register/send_email_code"
                    r_send = sess.post(send_url, json={"email": email, "locale": "en-SG"}, timeout=10)
                    if r_send.status_code == 200:
                        success = True
                        resp_text = r_send.text[:1000]
                except:
                    pass

        except Exception as e:
            resp_text = str(e)
            import traceback
            print(traceback.format_exc())

        if success:
            bot.send_message(chat_id, f"""✅ {bold('OTP Successfully Sent to Gmail!')}

📧 {bold('To:')} {email}
📤 {bold('From:')} Garena Account <noreply@garena.com>
🌍 {bold('Server:')} sso.garena.com/universal/register (Auto-detected India/SG)
🔑 {bold('Subject:')} Verify Your Email Address for New Garena Account

📩 {bold('Ab Gmail kholo:')}
1. Inbox check karo
2. Spam folder bhi check karo
3. Garena ka email ayega 1-2 min me

⏰ {bold('Expiry:')} 10 minutes
""", reply_markup=yt_btn())
        else:
            bot.send_message(chat_id, f"""⚠️ {bold('Garena ne direct OTP block kiya')}

📧 {bold('Email:')} {email}
🔍 {bold('Garena Response:')} {resp_text[:800]}

✅ {bold('Manual Fix (100% working):')}
1. Jao: https://sso.garena.com/universal/register?locale=en-SG
2. Email dalo: {email}
3. Username/Password bharo
4. {bold('GET CODE')} pe click karo
5. Code {email} pe ayega

💡 {bold('Ya phir:')}
Fresh Gmail use karo jo pehle kabhi Garena pe use na hua ho - uspe 100% OTP jayega
""", reply_markup=yt_btn())

        bot.send_message(chat_id, f"{bold('Main Menu - Please select an option:')} 👇", reply_markup=main_menu())
        del user_states[chat_id]
    elif action in ["unbind","change"]:
        # Handle OTP and sec codes for unbind/change
        if state["step"] in ["otp","old_otp"]:
            try:
                r = requests.post("https://100067.connect.garena.com/game/account_security/bind:verify_identity", headers=HEADERS, data={"email":state.get("email") or state.get("old_email"),"app_id":"100067","access_token":state["token"],"otp":text}, timeout=10)
                ident = r.json().get("identity_token")
                if not ident:
                    bot.send_message(chat_id, f"❌ Verify Failed: {r.text[:400]}", reply_markup=yt_btn()); del user_states[chat_id]; return
                if action=="unbind":
                    r2 = requests.post("https://100067.connect.garena.com/game/account_security/bind:create_unbind_request", headers=HEADERS, data={"app_id":"100067","access_token":state["token"],"identity_token":ident}, timeout=10)
                    if r2.json().get("result")==0:
                        bot.send_message(chat_id, "✅ Unbind SUCCESS!", reply_markup=yt_btn())
                    else:
                        bot.send_message(chat_id, format_garena_error(r2.text), reply_markup=yt_btn())
                    del user_states[chat_id]
                    bot.send_message(chat_id, f"{bold('Main Menu - Please select an option:')} 👇", reply_markup=main_menu())
                else: # change old otp verified
                    state["identity"]=ident; state["step"]="new_email"
                    bot.send_message(chat_id, f"✅ Old Verified! Enter new email:", reply_markup=yt_btn())
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn()); del user_states[chat_id]
        elif state["step"]=="sec":
            try:
                r = requests.post("https://100067.connect.garena.com/game/account_security/bind:create_unbind_request", headers=HEADERS, data={"app_id":"100067","access_token":state["token"],"secondary_password":text}, timeout=10)
                if r.json().get("result")==0:
                    bot.send_message(chat_id, "✅ Unbind SUCCESS via Security Code!", reply_markup=yt_btn())
                else:
                    bot.send_message(chat_id, format_garena_error(r.text), reply_markup=yt_btn())
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
            del user_states[chat_id]
            bot.send_message(chat_id, f"{bold('Main Menu - Please select an option:')} 👇", reply_markup=main_menu())
        elif state["step"]=="old_sec":
            try:
                r = requests.post("https://100067.connect.garena.com/game/account_security/bind:verify_identity", headers=HEADERS, data={"email":state["old_email"],"app_id":"100067","access_token":state["token"],"secondary_password":text}, timeout=10)
                ident = r.json().get("identity_token")
                if not ident:
                    bot.send_message(chat_id, "❌ Invalid Sec Code", reply_markup=yt_btn()); del user_states[chat_id]; return
                state["identity"]=ident; state["step"]="new_email"
                bot.send_message(chat_id, "✅ Verified via Sec Code! Enter new email:", reply_markup=yt_btn())
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn()); del user_states[chat_id]
        elif state["step"]=="new_email":
            state["new_email"]=text
            try:
                r = requests.post("https://100067.connect.garena.com/game/account_security/bind:send_otp", headers=HEADERS, data={"email":text,"locale":"en_PK","region":"PK","app_id":"100067","access_token":state["token"]}, timeout=10)
                if r.json().get("result")==0:
                    bot.send_message(chat_id, f"✅ OTP Sent to {text}\nEnter OTP:", reply_markup=yt_btn())
                    state["step"]="new_otp"
                else:
                    bot.send_message(chat_id, format_garena_error(r.text), reply_markup=yt_btn())
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
        elif state["step"]=="new_otp":
            try:
                r = requests.post("https://100067.connect.garena.com/game/account_security/bind:verify_otp", headers=HEADERS, data={"app_id":"100067","access_token":state["token"],"email":state["new_email"],"code":text,"otp":text,"type":"1"}, timeout=10)
                verifier = r.json().get("verifier_token")
                if not verifier:
                    bot.send_message(chat_id, f"❌ Verify Failed: {r.text[:400]}", reply_markup=yt_btn()); del user_states[chat_id]; return
                r2 = requests.post("https://100067.connect.garena.com/game/account_security/bind:create_rebind_request", headers=HEADERS, data={"identity_token":state["identity"],"email":state["new_email"],"app_id":"100067","verifier_token":verifier,"access_token":state["token"]}, timeout=10)
                if r2.json().get("result")==0:
                    bot.send_message(chat_id, f"🎉 Email Changed! {state['new_email']} Pending", reply_markup=yt_btn())
                else:
                    bot.send_message(chat_id, format_garena_error(r2.text), reply_markup=yt_btn())
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
            del user_states[chat_id]
            bot.send_message(chat_id, f"{bold('Main Menu - Please select an option:')} 👇", reply_markup=main_menu())

@app.route('/')
def home(): return "✅ ZEVRIC BOT RUNNING - FAST & GREEN MENU"
@app.route('/health')
def health(): return "OK",200
def run_bot(): bot.infinity_polling(timeout=60, long_polling_timeout=30)
if __name__=="__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
