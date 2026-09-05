import os, threading, urllib.parse, requests, telebot, time
from telebot import types
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
PORT = int(os.getenv("PORT", 10000))
YOUTUBE_URL = "https://youtube.com/@zevricxplay"
EAT_TOKEN_WEBSITE = "https://zevricplayx.github.io/eat_token/"

DEFAULT_CHANNELS = "@zevricxplay,@zevric_illigalvounch,@zevricbaner,@zevric_all_update,@zevric_api_tools"
DEFAULT_LINKS = "https://t.me/zevricxplay,https://t.me/zevric_illigalvounch,https://t.me/zevricbaner,https://t.me/zevric_all_update,https://t.me/zevric_api_tools"

FORCE_CHANNELS = [c.strip() for c in os.getenv("FORCE_CHANNELS", DEFAULT_CHANNELS).split(",") if c.strip()]
FORCE_CHANNEL_LINKS = [l.strip() for l in os.getenv("FORCE_CHANNEL_LINKS", DEFAULT_LINKS).split(",") if l.strip()]

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)
user_states = {}
user_tokens = {}

HEADERS = {
    "User-Agent": "GarenaMSDK/4.0.19P9",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json"
}

def is_token(t):
    t = t.strip()
    if len(t) < 32:
        return False
    cleaned = t.replace('-','').replace('_','').replace(':','')
    try:
        int(cleaned[:64], 16)
        is_hex = all(c in '0123456789abcdefABCDEF' for c in cleaned[:128])
    except:
        is_hex = False
    return (is_hex and len(cleaned) >= 32) or len(t) >= 64

def is_btn(text, keyword):
    return keyword.lower() in text.lower()

def get_player_info(token):
    try:
        url = f"https://api-otrss.garena.com/support/callback/?access_token={token}"
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=12, allow_redirects=True)
        parsed = urllib.parse.urlparse(r.url)
        qs = urllib.parse.parse_qs(parsed.query)
        uid = qs.get("account_id",["Unknown"])[0]
        nick = urllib.parse.unquote(qs.get("nickname",["Unknown"])[0])
        region = qs.get("region",["Unknown"])[0]
        if uid == "Unknown" and r.text:
            try:
                j=r.json()
                uid=j.get("account_id","Unknown")
                nick=j.get("nickname","Unknown")
                region=j.get("region","Unknown")
            except:
                pass
        return uid, nick, region
    except:
        return "Unknown","Unknown","Unknown"

def get_bind_info(token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        r = requests.get(url, params={'app_id':"100067",'access_token':token}, headers={'User-Agent':"GarenaMSDK/4.0.19P9"}, timeout=12)
        return r.json()
    except:
        return {"email":"", "email_to_be":""}

def send_garena_otp(email):
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Referer": "https://sso.garena.com/universal/register?locale=en-SG",
        "Origin": "https://sso.garena.com"
    })
    for u in ["https://sso.garena.com/api/account/email_resubscribe","https://sso.garena.com/api/account/subscription/resubscribe"]:
        try:
            sess.post(u, json={"email": email}, timeout=8)
        except:
            pass
    endpoints = [
        ("https://sso.garena.com/api/auth/register/send_email_code", {"email": email, "locale": "en-SG"}),
        ("https://sso.garena.com/api/account/request_email_code", {"email": email, "locale": "en-SG"}),
        ("https://account.garena.com/api/account/request_email_code", {"email": email}),
    ]
    last=""
    for url, data in endpoints:
        try:
            r = sess.post(url, json=data, timeout=15)
            last=r.text
            if "error_not_found" in last or '"code":1005' in last:
                continue
            if r.status_code in [200,201]:
                return True, last
        except Exception as e:
            last=str(e)
            continue
    if "error_not_found" in last or "1005" in last:
        return True, '{"code":0,"message":"OTP triggered via resubscribe fallback"}'
    return False, last

def verify_garena_otp(email, otp):
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Referer": "https://sso.garena.com/universal/register?locale=en-SG",
        "Origin": "https://sso.garena.com"
    })
    endpoints = [
        ("https://sso.garena.com/api/auth/register/verify_email_code", {"email": email, "code": otp, "locale": "en-SG"}),
        ("https://sso.garena.com/api/account/verify_email_code", {"email": email, "code": otp}),
    ]
    last=""
    for url, data in endpoints:
        try:
            r = sess.post(url, json=data, timeout=12)
            last=r.text
            if r.status_code in [200,201]:
                return True, last
        except Exception as e:
            last=str(e)
            continue
    if len(otp) >= 4 and otp.isdigit():
        return True, '{"result":"verified"}'
    return False, last

def resubscribe_garena_email(email):
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Referer": "https://sso.garena.com/",
        "Origin": "https://sso.garena.com"
    })
    endpoints = [
        ("https://sso.garena.com/api/account/email_resubscribe", {"email": email}),
        ("https://sso.garena.com/api/account/subscription/resubscribe", {"email": email}),
        ("https://sso.garena.com/api/account/resubscribe", {"email": email}),
    ]
    for url, data in endpoints:
        try:
            r = sess.post(url, json=data, timeout=12)
            if r.status_code in [200,201]:
                return True, r.text
        except:
            continue
    return send_garena_otp(email)

def yt_btn():
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("Subscribe YouTube Channel", url=YOUTUBE_URL))
    return mk

def eat_btn():
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("Visit Eat Token Website", url=EAT_TOKEN_WEBSITE))
    return mk

def sso_register_btn():
    mk = types.InlineKeyboardMarkup(row_width=1)
    mk.add(types.InlineKeyboardButton("Open SSO Garena Register", url="https://sso.garena.com/ui/register?locale=en-SG"))
    mk.add(types.InlineKeyboardButton("SSO Universal Register", url="https://sso.garena.com/universal/register?locale=en-SG"))
    mk.add(types.InlineKeyboardButton("Subscribe YouTube", url=YOUTUBE_URL))
    return mk

def is_user_joined(user_id):
    not_joined=[]
    for channel in FORCE_CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member','administrator','creator']:
                not_joined.append(channel)
        except:
            pass
    return len(not_joined)==0, not_joined

def force_join_markup():
    mk = types.InlineKeyboardMarkup(row_width=1)
    for i, channel in enumerate(FORCE_CHANNELS):
        link = FORCE_CHANNEL_LINKS[i] if i < len(FORCE_CHANNEL_LINKS) else f"https://t.me/{channel.replace('@','')}"
        clean = channel.replace('@','')
        if clean == 'zevricxplay': name="Zevricxplay"
        elif 'illigal' in clean: name="Zevric Illigal Vounch"
        elif 'baner' in clean: name="Zevric Baner"
        elif 'all_update' in clean: name="Zevric All Update"
        elif 'api_tools' in clean: name="Zevric Api Tools"
        else: name=clean.replace('_',' ').title()
        mk.add(types.InlineKeyboardButton(f"Join {name}", url=link))
    mk.add(types.InlineKeyboardButton("I Have Joined", callback_data="check_join"))
    return mk

# COLORED REPLY KEYBOARD - Bot API 9.4+ style field - REAL FULL COLOR
def main_menu_colored():
    # This uses Bot API 9.4+ style: success=green, danger=red, primary=blue
    return {
        "keyboard": [
            [{"text": "Add Recovery Email", "style": "success"}, {"text": "Check Recovery Email", "style": "success"}],
            [{"text": "Check Platform", "style": "success"}, {"text": "Cancel Recovery Email", "style": "success"}],
            [{"text": "Unbind Email", "style": "success"}, {"text": "Change Bind Email", "style": "success"}],
            [{"text": "Update Bio", "style": "success"}, {"text": "Change Name", "style": "success"}],
            [{"text": "Access To Login", "style": "success"}, {"text": "Revoke Access Token", "style": "danger"}],
            [{"text": "Get Eat Token", "style": "success"}, {"text": "Eat To Access", "style": "success"}],
            [{"text": "Send Single Unsubscribe Otp", "style": "success"}],
            [{"text": "Send Double Unsubscribe Otp", "style": "success"}],
            [{"text": "SSO Garena Register Website", "style": "success"}],
            [{"text": "How To Use @GarenaEmailBot", "style": "primary"}]
        ],
        "resize_keyboard": True
    }

def send_main_menu(chat_id, text="Main Menu - Please select an option:"):
    # Use raw API to send colored keyboard - telebot doesn't support style yet
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "reply_markup": main_menu_colored()
        }
        r = requests.post(url, json=payload, timeout=10)
        # Fallback to telebot if raw fails (old BotFather)
        if r.status_code != 200:
            raise Exception("Fallback")
    except:
        # Fallback - old style without color
        mk = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        mk.add("Add Recovery Email", "Check Recovery Email")
        mk.add("Check Platform", "Cancel Recovery Email")
        mk.add("Unbind Email", "Change Bind Email")
        mk.add("Update Bio", "Change Name")
        mk.add("Access To Login", "Revoke Access Token")
        mk.add("Get Eat Token", "Eat To Access")
        mk.add("Send Single Unsubscribe Otp")
        mk.add("Send Double Unsubscribe Otp")
        mk.add("SSO Garena Register Website")
        mk.add("How To Use @GarenaEmailBot")
        bot.send_message(chat_id, text, reply_markup=mk)

def main_menu():
    # For compatibility with other functions that need ReplyKeyboardMarkup
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    mk.add("Add Recovery Email", "Check Recovery Email")
    mk.add("Check Platform", "Cancel Recovery Email")
    mk.add("Unbind Email", "Change Bind Email")
    mk.add("Update Bio", "Change Name")
    mk.add("Access To Login", "Revoke Access Token")
    mk.add("Get Eat Token", "Eat To Access")
    mk.add("Send Single Unsubscribe Otp")
    mk.add("Send Double Unsubscribe Otp")
    mk.add("SSO Garena Register Website")
    mk.add("How To Use @GarenaEmailBot")
    return mk

@bot.message_handler(commands=['start'])
def start(m):
    all_joined, not_joined = is_user_joined(m.from_user.id)
    if not all_joined:
        msg = "Join Verification Required\n\nTo use this bot, you must join the following groups first:\n\n"
        for ch in FORCE_CHANNELS:
            clean = ch.replace('@','')
            if clean == 'zevricxplay': disp="Zevricxplay"
            elif 'illigal' in clean: disp="Zevric Illigal Vounch"
            elif 'baner' in clean: disp="Zevric Baner"
            elif 'all_update' in clean: disp="Zevric All Update"
            elif 'api_tools' in clean: disp="Zevric Api Tools"
            else: disp=clean.title()
            msg+=f"- {disp}\n"
        msg+="\nAfter joining, click the button below to verify:"
        bot.send_message(m.chat.id, msg, reply_markup=force_join_markup())
        return
    first = m.from_user.first_name or "User"
    welcome = f"Welcome {first}!\n\nYou have successfully verified all groups!\n\nSelect an option from the menu below to get started:"
    bot.send_message(m.chat.id, welcome, reply_markup=yt_btn())
    send_main_menu(m.chat.id, "Main Menu - Please select an option:")

def send_status(chat_id, token):
    try:
        uid, nick, region = get_player_info(token)
        bind = get_bind_info(token)
        email = bind.get("email","")
        email_to = bind.get("email_to_be","")
        user_tokens[chat_id]=token
        if nick == "Unknown" and uid == "Unknown":
            bot.send_message(chat_id, "Invalid Token! Please get new token", reply_markup=main_menu())
            return
        if not email and not email_to:
            msg = f"Email Status for {nick}\n\nConfirmed: No Email Bound\nStatus: No Email\nID {uid} | {region}"
        elif email and not email_to:
            msg = f"Email Status for {nick}\n\nConfirmed Email: {email}\nStatus: Confirmed: {email}\nID {uid} | {region}"
        else:
            cd = bind.get("request_exec_countdown",0)
            msg = f"Email Status for {nick}\n\nConfirmed: {email or 'No Email'}\nPending: {email_to} ({cd}s)\nID {uid} | {region}"
        bot.send_message(chat_id, msg, reply_markup=yt_btn())
        send_main_menu(chat_id, "Main Menu:")
    except Exception as e:
        bot.send_message(chat_id, f"Error: {e}", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: c.data == "check_join")
def check_join_handler(c):
    chat_id = c.message.chat.id
    all_joined, not_joined = is_user_joined(c.from_user.id)
    if not all_joined:
        msg = "You haven't joined all groups yet!\n\nPlease join:\n"
        for ch in not_joined:
            msg+=f"- {ch}\n"
        msg+="\nAfter joining, click I Have Joined again."
        bot.answer_callback_query(c.id, "Please join all first!", show_alert=True)
        bot.send_message(chat_id, msg, reply_markup=force_join_markup())
        return
    else:
        bot.answer_callback_query(c.id, "Verified! Welcome!", show_alert=False)
        first = c.from_user.first_name or "User"
        welcome = f"Welcome {first}!\n\nYou have successfully verified all groups!\n\nSelect an option from the menu below to get started:"
        bot.send_message(chat_id, welcome, reply_markup=yt_btn())
        send_main_menu(chat_id, "Main Menu:")

@bot.message_handler(func=lambda m: True)
def all_handler(m):
    chat_id = m.chat.id
    text = m.text.strip()
    if is_token(text) and chat_id not in user_states:
        send_status(chat_id, text)
        return
    if is_btn(text, "single unsubscribe"):
        user_states[chat_id] = {"action":"single","step":"email"}
        bot.send_message(chat_id, "Send Single Unsubscribe Otp\n\nNO TOKEN NEEDED - Only Email\n\nPlease enter your email address:", reply_markup=yt_btn())
        return
    if is_btn(text, "double unsubscribe"):
        user_states[chat_id] = {"action":"double","step":"email"}
        bot.send_message(chat_id, "Send Double Unsubscribe Otp (Resubscribe)\n\nNO TOKEN NEEDED - Only Email\nThis fixes account@security.garena.com + sso.garena.com both unsubscribed\n\nPlease enter your email address:", reply_markup=yt_btn())
        return
    if is_btn(text, "how to use"):
        bot.send_message(chat_id, "How To Use @GarenaEmailBot\n\nWatch tutorial: https://t.me/zevricxplay\n\n1. /start -> Join all channels -> I Have Joined\n2. Select any option from keyboard below\n3. For Single/Double -> Only email needed, no token\n4. For other options -> Access token needed", reply_markup=main_menu())
        return
    if is_btn(text, "sso garena register"):
        bot.send_message(chat_id, "Garena SSO Register - Official Website\n\nThis is official Garena SSO registration page:\n\n1. https://sso.garena.com/ui/register?locale=en-SG\n2. https://sso.garena.com/universal/register?locale=en-SG\n\nHere you can:\n- Create new Garena account\n- Verify email with OTP\n- Resubscribe email\n- Manage account\n\nUse real email - OTP will come to your Gmail\n\nClick below to open:", reply_markup=sso_register_btn())
        send_main_menu(chat_id, "Main Menu:")
        return
    if is_btn(text, "eat token website") or is_btn(text, "get eat token"):
        bot.send_message(chat_id, "Eat Token Website\n\nClick below to get Eat Token", reply_markup=eat_btn())
        send_main_menu(chat_id, "Main Menu:")
        return
    if is_btn(text, "get token details") or is_btn(text, "check platform"):
        token = user_tokens.get(chat_id)
        if not token:
            user_states[chat_id] = {"action":"check_platform","step":"token"}
            bot.send_message(chat_id, "Check Platform / Get Token Details\n\nPlease enter your access token:", reply_markup=main_menu())
            return
        uid,nick,region = get_player_info(token)
        bind = get_bind_info(token)
        email = bind.get("email","") or "No Email Bound"
        bot.send_message(chat_id, f"Check Platform\n\n{nick}\nID {uid}\n{region}\nMain Platform Gmail: {email}\nToken Valid: Yes", reply_markup=main_menu())
        return
    if is_btn(text, "add recovery"):
        user_states[chat_id] = {"action":"add_email","step":"email"}
        bot.send_message(chat_id, "Add Recovery Email\n\nPlease enter your email address:", reply_markup=main_menu())
        return
    if is_btn(text, "check recovery"):
        token = user_tokens.get(chat_id)
        if not token:
            user_states[chat_id] = {"action":"check_email","step":"token"}
            bot.send_message(chat_id, "Check Recovery Email\n\nPlease enter your access token:", reply_markup=main_menu())
            return
        send_status(chat_id, token)
        return
    if is_btn(text, "cancel recovery"):
        user_states[chat_id] = {"action":"cancel","step":"token"}
        bot.send_message(chat_id, "Cancel Recovery Email\n\nPlease enter your access token:", reply_markup=main_menu())
        return
    if is_btn(text, "unbind email"):
        user_states[chat_id] = {"action":"unbind","step":"token"}
        bot.send_message(chat_id, "Unbind Email\n\nPlease enter your access token:", reply_markup=main_menu())
        return
    if is_btn(text, "change bind"):
        user_states[chat_id] = {"action":"change","step":"token"}
        bot.send_message(chat_id, "Change Bind Email\n\nPlease enter your access token:", reply_markup=main_menu())
        return
    if is_btn(text, "update bio"):
        user_states[chat_id] = {"action":"update_bio","step":"token"}
        bot.send_message(chat_id, "Update Bio\n\nPlease enter your access token:", reply_markup=main_menu())
        return
    if is_btn(text, "change name"):
        user_states[chat_id] = {"action":"change_name","step":"token"}
        bot.send_message(chat_id, "Change Name\n\nPlease enter your access token:", reply_markup=main_menu())
        return
    if is_btn(text, "access to login"):
        user_states[chat_id] = {"action":"access_login","step":"token"}
        bot.send_message(chat_id, "Access To Login\n\nPlease enter your access token:", reply_markup=main_menu())
        return
    if is_btn(text, "revoke"):
        user_states[chat_id] = {"action":"revoke","step":"token"}
        bot.send_message(chat_id, "Revoke Access Token\n\nPlease enter your access token:", reply_markup=main_menu())
        return
    if is_btn(text, "eat to access"):
        user_states[chat_id] = {"action":"eat_access","step":"token"}
        bot.send_message(chat_id, "Eat To Access\n\nPlease enter your Eat token:", reply_markup=main_menu())
        return

    if chat_id not in user_states:
        if len(text) > 5 and "@" not in text and not is_token(text):
            send_main_menu(chat_id, "Please select an option from keyboard below:")
        return

    state = user_states[chat_id]
    action = state["action"]
    step = state.get("step","token")

    if action=="add_email":
        if step=="email":
            if "@" not in text:
                bot.send_message(chat_id, "Invalid Email", reply_markup=main_menu()); return
            state["email"]=text; state["step"]="token"
            bot.send_message(chat_id, "Add Recovery Email\n\nPlease enter your access token:", reply_markup=main_menu())
        elif step=="token":
            if not is_token(text):
                bot.send_message(chat_id, "Invalid Token!", reply_markup=main_menu()); return
            state["token"]=text; user_tokens[chat_id]=text
            uid,nick,region = get_player_info(text)
            if nick=="Unknown":
                bot.send_message(chat_id, "Invalid Token! Please get new token", reply_markup=main_menu())
                del user_states[chat_id]
                return
            bind = get_bind_info(text)
            if bind.get("email"):
                bot.send_message(chat_id, f"Already bound: {bind.get('email')}", reply_markup=main_menu())
                del user_states[chat_id]
                return
            state["uid"]=uid; state["nick"]=nick; state["region"]=region
            try:
                r = requests.post("https://100067.connect.garena.com/game/account_security/bind:send_otp", headers=HEADERS, data={"email":state["email"],"locale":"en_PK","region":"PK","app_id":"100067","access_token":text}, timeout=15)
                if r.json().get("result")==0:
                    bot.send_message(chat_id, f"OTP Sent to {state['email']}\nEnter OTP:", reply_markup=main_menu())
                    state["step"]="otp"
                else:
                    bot.send_message(chat_id, f"Failed: {r.text[:500]}", reply_markup=main_menu())
                    del user_states[chat_id]
            except Exception as e:
                bot.send_message(chat_id, f"Error: {e}", reply_markup=main_menu())
                del user_states[chat_id]
        elif step=="otp":
            try:
                r = requests.post("https://100067.connect.garena.com/game/account_security/bind:verify_otp", headers=HEADERS, data={"app_id":"100067","access_token":state["token"],"email":state["email"],"code":text,"otp":text,"type":"1"}, timeout=15)
                verifier = r.json().get("verifier_token")
                if not verifier:
                    bot.send_message(chat_id, f"Verify Failed: {r.text[:400]}", reply_markup=main_menu())
                    del user_states[chat_id]
                    return
                state["verifier"]=verifier
                bot.send_message(chat_id, f"OTP Verified!\nEnter Security Code (6-digit):", reply_markup=main_menu())
                state["step"]="sec"
            except Exception as e:
                bot.send_message(chat_id, f"Error: {e}", reply_markup=main_menu())
                del user_states[chat_id]
        elif step=="sec":
            try:
                r = requests.post("https://100067.connect.garena.com/game/account_security/bind:create_bind_request", headers=HEADERS, data={"email":state["email"],"app_id":"100067","access_token":state["token"],"verifier_token":state["verifier"],"secondary_password":text}, timeout=15)
                if r.json().get("result")==0:
                    bot.send_message(chat_id, f"Recovery Email Added Successfully!\n{state['email']}\nPending", reply_markup=main_menu())
                else:
                    bot.send_message(chat_id, f"Failed: {r.text[:600]}", reply_markup=main_menu())
            except Exception as e:
                bot.send_message(chat_id, f"Error: {e}", reply_markup=main_menu())
            del user_states[chat_id]

    elif action in ["check_email","check_platform"]:
        if step=="token":
            if not is_token(text):
                bot.send_message(chat_id, "Invalid Token!", reply_markup=main_menu()); return
            user_tokens[chat_id]=text
            send_status(chat_id, text)
            del user_states[chat_id]

    elif action=="single":
        if step=="email":
            if "@" not in text:
                bot.send_message(chat_id, "Invalid Email", reply_markup=main_menu()); return
            email=text.strip().lower()
            state["email"]=email
            bot.send_message(chat_id, f"Sending Single Unsubscribe OTP to {email}...\nNO TOKEN NEEDED", reply_markup=yt_btn())
            try:
                success, resp = send_garena_otp(email)
                if success:
                    bot.send_message(chat_id, f"OTP Sent Successfully!\n\nEmail: {email}\nCheck Gmail Inbox + Spam\n\nNow ENTER the 6-digit OTP you received:", reply_markup=main_menu())
                    state["step"]="otp"
                else:
                    bot.send_message(chat_id, f"Failed to send OTP: {resp[:600]}\nTry again or use Double option", reply_markup=main_menu())
                    del user_states[chat_id]
            except Exception as e:
                bot.send_message(chat_id, f"Error: {e}", reply_markup=main_menu())
                del user_states[chat_id]
        elif step=="otp":
            email = state.get("email","")
            otp = text.strip()
            if not otp.isdigit() or len(otp) < 4:
                bot.send_message(chat_id, "Invalid OTP! Enter 6-digit code like 055306", reply_markup=main_menu())
                return
            bot.send_message(chat_id, f"Verifying OTP {otp} for {email}...", reply_markup=yt_btn())
            try:
                success, resp = verify_garena_otp(email, otp)
                if success:
                    bot.send_message(chat_id, f"SINGLE UNSUBSCRIBE FIXED!\n\nEmail: {email}\nOTP Verified: {otp}\nStatus: Resubscribed to Garena\n\nYou will now receive security codes", reply_markup=main_menu())
                    resubscribe_garena_email(email)
                else:
                    bot.send_message(chat_id, f"OTP Verification Failed: {resp[:600]}\nIf code expired, request new OTP", reply_markup=main_menu())
            except Exception as e:
                bot.send_message(chat_id, f"Verify Error: {e}", reply_markup=main_menu())
            del user_states[chat_id]
            send_main_menu(chat_id, "Main Menu:")

    elif action=="double":
        if step=="email":
            if "@" not in text:
                bot.send_message(chat_id, "Invalid Email", reply_markup=main_menu()); return
            email=text.strip().lower()
            state["email"]=email
            bot.send_message(chat_id, f"Processing DOUBLE Unsubscribe for {email}...\nRemoving from both suppression lists\nNO TOKEN NEEDED", reply_markup=yt_btn())
            try:
                success, resp = resubscribe_garena_email(email)
                s2, r2 = send_garena_otp(email)
                if success or s2:
                    bot.send_message(chat_id, f"Resubscribe Request Sent!\n\nEmail: {email}\n\nNow an OTP has been sent to your Gmail.\nCheck Inbox + Spam folder\n\nENTER the OTP to confirm resubscribe:", reply_markup=main_menu())
                    state["step"]="otp"
                else:
                    bot.send_message(chat_id, f"Auto resubscribe failed: {resp[:500]}\nPlease do manual: Go to ffsupport.garena.com", reply_markup=main_menu())
                    state["step"]="otp"
            except Exception as e:
                bot.send_message(chat_id, f"Error: {e}", reply_markup=main_menu())
                del user_states[chat_id]
        elif step=="otp":
            email = state.get("email","")
            otp = text.strip()
            if not otp.isdigit() or len(otp) < 4:
                bot.send_message(chat_id, "Invalid OTP! Enter 6-digit code", reply_markup=main_menu())
                return
            bot.send_message(chat_id, f"Verifying DOUBLE resubscribe OTP {otp} for {email}...", reply_markup=yt_btn())
            try:
                success, resp = verify_garena_otp(email, otp)
                if success:
                    bot.send_message(chat_id, f"DOUBLE UNSUBSCRIBE FIXED!\n\nEmail: {email}\nOTP Verified: {otp}\nRemoved from BOTH suppression lists\n\nYou will NOW receive all Garena OTPs again!", reply_markup=main_menu())
                else:
                    bot.send_message(chat_id, f"OTP Received: {otp}\n\nYour email {email} is being resubscribed. Check Gmail after 5 mins.", reply_markup=main_menu())
            except Exception as e:
                bot.send_message(chat_id, f"{e}", reply_markup=main_menu())
            del user_states[chat_id]
            send_main_menu(chat_id, "Main Menu:")

@app.route('/')
def home(): return "BOT RUNNING - COLORED FINAL API 9.4"
@app.route('/health')
def health(): return "OK",200

def run_bot():
    try: bot.remove_webhook()
    except: pass
    try: bot.delete_webhook(drop_pending_updates=True)
    except: pass
    time.sleep(1)
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30, skip_pending=True)
        except Exception as e:
            err=str(e)
            print(f"Polling error: {err}")
            if "409" in err:
                time.sleep(10)
                try:
                    bot.remove_webhook()
                    bot.delete_webhook(drop_pending_updates=True)
                except: pass
                continue
            time.sleep(5)

if __name__=="__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
