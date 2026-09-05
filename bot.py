
import os, threading, urllib.parse, requests, telebot
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
    payloads = [
        ("https://sso.garena.com/api/auth/register/send_email_code", {"email": email, "locale": "en-SG"}),
        ("https://sso.garena.com/api/account/request_email_code", {"email": email, "locale": "en-SG"}),
    ]
    last=""
    for url, data in payloads:
        try:
            r = sess.post(url, json=data, timeout=15)
            last=r.text
            if r.status_code in [200,201]:
                return True, last
        except Exception as e:
            last=str(e)
            continue
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

def main_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add(types.KeyboardButton("Add Recovery Email"), types.KeyboardButton("Check Recovery Email"))
    m.add(types.KeyboardButton("Check Platform"), types.KeyboardButton("Cancel Recovery Email"))
    m.add(types.KeyboardButton("Unbind Email"), types.KeyboardButton("Change Bind Email"))
    m.add(types.KeyboardButton("Update Bio"), types.KeyboardButton("Change Name"))
    m.add(types.KeyboardButton("Access To Login"), types.KeyboardButton("Revoke Access Token"))
    m.add(types.KeyboardButton("Get Eat Token"), types.KeyboardButton("Eat To Access"))
    m.add(types.KeyboardButton("Send Single Unsubscribe Otp"), types.KeyboardButton("Send Double Unsubscribe Otp"))
    return m

@bot.message_handler(commands=['start'])
def start(m):
    all_joined, not_joined = is_user_joined(m.from_user.id)
    if not all_joined:
        msg = "Join Verification Required\n\nTo use this bot, you must join the following groups first:\n\n"
        for ch in FORCE_CHANNELS:
            clean = ch.replace('@','')
            if clean == 'zevricxplay': name="Zevricxplay"
            elif 'illigal' in clean: name="Zevric Illigal Vounch"
            elif 'baner' in clean: name="Zevric Baner"
            elif 'all_update' in clean: name="Zevric All Update"
            elif 'api_tools' in clean: name="Zevric Api Tools"
            else: name=clean.title()
            msg+=f"- {name}\n"
        msg+="\nAfter joining, click the button below to verify:"
        bot.send_message(m.chat.id, msg, reply_markup=force_join_markup())
        return
    first = m.from_user.first_name or "User"
    welcome = f"Welcome {first}!\n\nYou have successfully verified all groups!\n\nSelect an option from the menu below to get started:"
    bot.send_message(m.chat.id, welcome, reply_markup=yt_btn())
    bot.send_message(m.chat.id, "Main Menu - Please select an option:", reply_markup=main_menu())

def send_status(chat_id, token):
    try:
        uid, nick, region = get_player_info(token)
        bind = get_bind_info(token)
        email = bind.get("email","")
        email_to = bind.get("email_to_be","")
        user_tokens[chat_id]=token
        if nick == "Unknown" and uid == "Unknown":
            bot.send_message(chat_id, "❌ Invalid Token! Please get new token", reply_markup=yt_btn())
            return
        if not email and not email_to:
            msg = f"Email Status for {nick}\n\n📧 Confirmed: No Email Bound\n⏳ Status: No Email\n🆔 {uid} | 🌍 {region}"
        elif email and not email_to:
            msg = f"Email Status for {nick}\n\n✅ Confirmed Email: {email}\n📊 Status: Confirmed: {email}\n🆔 {uid} | 🌍 {region}"
        else:
            cd = bind.get("request_exec_countdown",0)
            msg = f"Email Status for {nick}\n\n📧 Confirmed: {email or 'No Email'}\n⏳ Pending: {email_to} ({cd}s)\n🆔 {uid} | 🌍 {region}"
        bot.send_message(chat_id, msg, reply_markup=yt_btn())
        bot.send_message(chat_id, "Main Menu - Please select an option:", reply_markup=main_menu())
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {e}", reply_markup=yt_btn())

@bot.message_handler(func=lambda m: is_btn(m.text, "Add Recovery Email"))
def add_btn(m):
    user_states[m.chat.id] = {"action":"add_email","step":"email"}
    bot.send_message(m.chat.id, "Add Recovery Email\n\n📧 Please enter your email address: 👇", reply_markup=yt_btn())

@bot.message_handler(func=lambda m: is_btn(m.text, "Check Recovery Email"))
def check_btn(m):
    token = user_tokens.get(m.chat.id)
    if not token:
        user_states[m.chat.id] = {"action":"check_email","step":"token"}
        bot.send_message(m.chat.id, "Check Recovery Email\n\n🔑 Please enter your access token: 👇", reply_markup=yt_btn())
        return
    send_status(m.chat.id, token)

@bot.message_handler(func=lambda m: is_btn(m.text, "Check Platform"))
def plat_btn(m):
    token = user_tokens.get(m.chat.id)
    if not token:
        user_states[m.chat.id] = {"action":"check_platform","step":"token"}
        bot.send_message(m.chat.id, "Check Platform\n\n🔑 Please enter your access token: 👇", reply_markup=yt_btn())
        return
    uid,nick,region = get_player_info(token)
    bind = get_bind_info(token)
    email = bind.get("email","") or "No Email Bound"
    bot.send_message(m.chat.id, f"Check Platform\n\n👤 {nick}\n🆔 {uid}\n🌍 {region}\n📧 Main Platform Gmail: {email}\n✅ Token Valid: Yes", reply_markup=yt_btn())
    bot.send_message(m.chat.id, "Main Menu - Please select an option:", reply_markup=main_menu())

@bot.message_handler(func=lambda m: is_btn(m.text, "Cancel Recovery Email"))
def cancel_btn(m):
    user_states[m.chat.id] = {"action":"cancel","step":"token"}
    bot.send_message(m.chat.id, "Cancel Recovery Email\n\n🔑 Please enter your access token: 👇", reply_markup=yt_btn())

@bot.message_handler(func=lambda m: is_btn(m.text, "Unbind Email"))
def unbind_btn(m):
    user_states[m.chat.id] = {"action":"unbind","step":"token"}
    bot.send_message(m.chat.id, "Unbind Email\n\n🔑 Please enter your access token: 👇", reply_markup=yt_btn())

@bot.message_handler(func=lambda m: is_btn(m.text, "Change Bind Email"))
def change_btn(m):
    user_states[m.chat.id] = {"action":"change","step":"token"}
    bot.send_message(m.chat.id, "Change Bind Email\n\n🔑 Please enter your access token: 👇", reply_markup=yt_btn())

@bot.message_handler(func=lambda m: is_btn(m.text, "Update Bio"))
def bio_btn(m):
    user_states[m.chat.id] = {"action":"update_bio","step":"token"}
    bot.send_message(m.chat.id, "Update Bio\n\n🔑 Please enter your access token: 👇", reply_markup=yt_btn())

@bot.message_handler(func=lambda m: is_btn(m.text, "Change Name"))
def name_btn(m):
    user_states[m.chat.id] = {"action":"change_name","step":"token"}
    bot.send_message(m.chat.id, "Change Name\n\n🔑 Please enter your access token: 👇", reply_markup=yt_btn())

@bot.message_handler(func=lambda m: is_btn(m.text, "Access To Login"))
def access_btn(m):
    token = user_tokens.get(m.chat.id)
    if not token:
        user_states[m.chat.id] = {"action":"access_login","step":"token"}
        bot.send_message(m.chat.id, "Access To Login\n\n🔑 Please enter your access token: 👇", reply_markup=yt_btn())
        return
    uid,nick,region = get_player_info(token)
    bot.send_message(m.chat.id, f"Access To Login\n\n👤 {nick}\n🆔 {uid}\n🌍 {region}\n✅ Access Granted", reply_markup=yt_btn())
    bot.send_message(m.chat.id, "Main Menu:", reply_markup=main_menu())

@bot.message_handler(func=lambda m: is_btn(m.text, "Revoke Access Token"))
def revoke_btn(m):
    user_states[m.chat.id] = {"action":"revoke","step":"token"}
    bot.send_message(m.chat.id, "Revoke Access Token\n\n🔑 Please enter your access token: 👇", reply_markup=yt_btn())

@bot.message_handler(func=lambda m: is_btn(m.text, "Get Eat Token"))
def geteat_btn(m):
    bot.send_message(m.chat.id, "Get Eat Token\n\n🌐 Click below to get Eat Token", reply_markup=eat_btn())
    bot.send_message(m.chat.id, "Main Menu:", reply_markup=main_menu())

@bot.message_handler(func=lambda m: is_btn(m.text, "Eat To Access"))
def eataccess_btn(m):
    user_states[m.chat.id] = {"action":"eat_access","step":"token"}
    bot.send_message(m.chat.id, "Eat To Access\n\n🔑 Please enter your Eat token: 👇", reply_markup=yt_btn())

@bot.message_handler(func=lambda m: is_btn(m.text, "Send Single Unsubscribe"))
def single_btn(m):
    user_states[m.chat.id] = {"action":"single","step":"email"}
    bot.send_message(m.chat.id, "Send Single Unsubscribe Otp\n\nPlease enter your email address:", reply_markup=yt_btn())

@bot.message_handler(func=lambda m: is_btn(m.text, "Send Double Unsubscribe"))
def double_btn(m):
    user_states[m.chat.id] = {"action":"double","step":"email"}
    bot.send_message(m.chat.id, "Send Double Unsubscribe Otp (Resubscribe)\n\nPlease enter your email address to resubscribe:", reply_markup=yt_btn())

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    chat_id = c.message.chat.id
    if c.data == "check_join":
        all_joined, not_joined = is_user_joined(c.from_user.id)
        if not all_joined:
            msg = "❌ You haven't joined all groups yet!\n\nPlease join:\n"
            for ch in not_joined:
                msg+=f"- {ch}\n"
            msg+="\nAfter joining, click I Have Joined again."
            bot.answer_callback_query(c.id, "Please join all first!", show_alert=True)
            bot.send_message(chat_id, msg, reply_markup=force_join_markup())
            return
        else:
            bot.answer_callback_query(c.id, "✅ Verified! Welcome!", show_alert=False)
            first = c.from_user.first_name or "User"
            welcome = f"Welcome {first}!\n\nYou have successfully verified all groups!\n\nSelect an option from the menu below to get started:"
            bot.send_message(chat_id, welcome, reply_markup=yt_btn())
            bot.send_message(chat_id, "Main Menu - Please select an option:", reply_markup=main_menu())
            return

@bot.message_handler(func=lambda m: True)
def all_handler(m):
    chat_id = m.chat.id
    text = m.text.strip()
    if is_token(text) and chat_id not in user_states:
        send_status(chat_id, text)
        return
    if chat_id not in user_states:
        return
    state = user_states[chat_id]
    action = state["action"]
    step = state.get("step","token")

    if action=="add_email":
        if step=="email":
            if "@" not in text:
                bot.send_message(chat_id, "❌ Invalid Email", reply_markup=yt_btn()); return
            state["email"]=text; state["step"]="token"
            bot.send_message(chat_id, "Add Recovery Email\n\n🔑 Please enter your access token: 👇", reply_markup=yt_btn())
        elif step=="token":
            if not is_token(text):
                bot.send_message(chat_id, "❌ Invalid Token!", reply_markup=yt_btn()); return
            state["token"]=text; user_tokens[chat_id]=text
            uid,nick,region = get_player_info(text)
            if nick=="Unknown":
                bot.send_message(chat_id, "❌ Invalid Token! Please get new token", reply_markup=yt_btn())
                del user_states[chat_id]
                bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())
                return
            bind = get_bind_info(text)
            if bind.get("email"):
                bot.send_message(chat_id, f"❌ Already bound: {bind.get('email')}", reply_markup=yt_btn())
                del user_states[chat_id]
                bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())
                return
            state["uid"]=uid; state["nick"]=nick; state["region"]=region
            try:
                r = requests.post("https://100067.connect.garena.com/game/account_security/bind:send_otp", headers=HEADERS, data={"email":state["email"],"locale":"en_PK","region":"PK","app_id":"100067","access_token":text}, timeout=15)
                if r.json().get("result")==0:
                    bot.send_message(chat_id, f"✅ OTP Sent to {state['email']}\n🔑 Enter OTP:", reply_markup=yt_btn())
                    state["step"]="otp"
                else:
                    bot.send_message(chat_id, f"❌ {r.text[:500]}", reply_markup=yt_btn())
                    del user_states[chat_id]
                    bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
                del user_states[chat_id]
        elif step=="otp":
            try:
                r = requests.post("https://100067.connect.garena.com/game/account_security/bind:verify_otp", headers=HEADERS, data={"app_id":"100067","access_token":state["token"],"email":state["email"],"code":text,"otp":text,"type":"1"}, timeout=15)
                verifier = r.json().get("verifier_token")
                if not verifier:
                    bot.send_message(chat_id, f"❌ Verify Failed: {r.text[:400]}", reply_markup=yt_btn())
                    del user_states[chat_id]
                    bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())
                    return
                state["verifier"]=verifier
                bot.send_message(chat_id, f"✅ OTP Verified!\n🔑 Enter Security Code (6-digit):", reply_markup=yt_btn())
                state["step"]="sec"
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
                del user_states[chat_id]
        elif step=="sec":
            try:
                r = requests.post("https://100067.connect.garena.com/game/account_security/bind:create_bind_request", headers=HEADERS, data={"email":state["email"],"app_id":"100067","access_token":state["token"],"verifier_token":state["verifier"],"secondary_password":text}, timeout=15)
                if r.json().get("result")==0:
                    bot.send_message(chat_id, f"🎉 Recovery Email Added Successfully!\n📧 {state['email']}\n⏳ Pending", reply_markup=yt_btn())
                else:
                    bot.send_message(chat_id, f"❌ {r.text[:600]}", reply_markup=yt_btn())
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
            del user_states[chat_id]
            bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())

    elif action=="check_email":
        if step=="token":
            if not is_token(text):
                bot.send_message(chat_id, "❌ Invalid Token!", reply_markup=yt_btn()); return
            user_tokens[chat_id]=text
            send_status(chat_id, text)
            del user_states[chat_id]

    elif action=="check_platform":
        if step=="token":
            if not is_token(text):
                bot.send_message(chat_id, "❌ Invalid Token!", reply_markup=yt_btn()); return
            user_tokens[chat_id]=text
            uid,nick,region = get_player_info(text)
            bind = get_bind_info(text)
            email = bind.get("email","") or "No Email Bound"
            bot.send_message(chat_id, f"Check Platform\n\n👤 {nick}\n🆔 {uid}\n🌍 {region}\n📧 Main Platform Gmail: {email}\n✅ Token Valid: Yes", reply_markup=yt_btn())
            del user_states[chat_id]
            bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())

    elif action=="cancel":
        if step=="token":
            if not is_token(text):
                bot.send_message(chat_id, "❌ Invalid Token!", reply_markup=yt_btn()); return
            try:
                r = requests.post("https://100067.connect.garena.com/game/account_security/bind:cancel_request", headers=HEADERS, data={"app_id":"100067","access_token":text}, timeout=12)
                if r.json().get("result")==0:
                    bot.send_message(chat_id, f"✅ Cancel SUCCESS\n👤 {get_player_info(text)[1]}", reply_markup=yt_btn())
                else:
                    bot.send_message(chat_id, f"❌ No Pending Request: {r.text[:400]}", reply_markup=yt_btn())
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
            del user_states[chat_id]
            bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())

    elif action=="update_bio":
        if step=="token":
            if not is_token(text):
                bot.send_message(chat_id, "❌ Invalid Token!", reply_markup=yt_btn()); return
            state["token"]=text; user_tokens[chat_id]=text
            uid,nick,region = get_player_info(text)
            if nick=="Unknown":
                bot.send_message(chat_id, "❌ Invalid Token!", reply_markup=yt_btn())
                del user_states[chat_id]
                return
            state["uid"]=uid; state["nick"]=nick
            bot.send_message(chat_id, f"Update Bio\n\n👤 {nick} | 🆔 {uid}\n✅ Token Valid\n\n✍️ Now enter your new Bio:", reply_markup=yt_btn())
            state["step"]="bio"
        elif step=="bio":
            try:
                bio_text=text
                r = requests.post("https://100067.connect.garena.com/game/profile/update", headers=HEADERS, data={"app_id":"100067","access_token":state["token"],"bio":bio_text}, timeout=12)
                if r.status_code==200 and '"result":0' in r.text:
                    bot.send_message(chat_id, f"✅ Bio Updated Successfully!\n👤 {state['nick']}\n📝 New Bio: {bio_text}", reply_markup=yt_btn())
                else:
                    bot.send_message(chat_id, f"✅ Bio Update Request Sent!\n📝 {bio_text}", reply_markup=yt_btn())
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
            del user_states[chat_id]
            bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())

    elif action=="change_name":
        if step=="token":
            if not is_token(text):
                bot.send_message(chat_id, "❌ Invalid Token!", reply_markup=yt_btn()); return
            state["token"]=text; user_tokens[chat_id]=text
            uid,nick,region = get_player_info(text)
            state["uid"]=uid; state["nick"]=nick
            bot.send_message(chat_id, f"Change Name\n\n👤 Current: {nick} | 🆔 {uid}\n✍️ Enter new nickname:", reply_markup=yt_btn())
            state["step"]="name"
        elif step=="name":
            try:
                r = requests.post("https://100067.connect.garena.com/game/profile/update", headers=HEADERS, data={"app_id":"100067","access_token":state["token"],"nickname":text}, timeout=12)
                if '"result":0' in r.text:
                    bot.send_message(chat_id, f"✅ Name Changed Successfully!\n👤 {state['nick']} → {text}", reply_markup=yt_btn())
                else:
                    bot.send_message(chat_id, f"❌ Failed: {r.text[:500]}", reply_markup=yt_btn())
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
            del user_states[chat_id]
            bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())

    elif action=="unbind":
        if step=="token":
            if not is_token(text):
                bot.send_message(chat_id, "❌ Invalid Token!", reply_markup=yt_btn()); return
            state["token"]=text; user_tokens[chat_id]=text
            bind = get_bind_info(text)
            if not bind.get("email"):
                bot.send_message(chat_id, "❌ No Email Bound to Unbind", reply_markup=yt_btn())
                del user_states[chat_id]
                bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())
                return
            state["email"]=bind.get("email")
            uid,nick,region = get_player_info(text)
            bot.send_message(chat_id, f"Unbind Email\n\n📧 Bound: {state['email']}\n👤 {nick}\n🔑 Enter Security Code (6-digit) OR type 'otp':", reply_markup=yt_btn())
            state["step"]="sec_or_otp"
        elif step=="sec_or_otp":
            if text.lower()=="otp":
                try:
                    r = requests.post("https://100067.connect.garena.com/game/account_security/bind:send_otp", headers=HEADERS, data={"email":state["email"],"locale":"en_PK","region":"PK","app_id":"100067","access_token":state["token"]}, timeout=12)
                    if r.json().get("result")==0:
                        bot.send_message(chat_id, f"✅ OTP Sent to {state['email']}\nEnter OTP:", reply_markup=yt_btn())
                        state["step"]="otp"
                    else:
                        bot.send_message(chat_id, f"❌ {r.text[:400]}", reply_markup=yt_btn())
                except Exception as e:
                    bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
            else:
                try:
                    r = requests.post("https://100067.connect.garena.com/game/account_security/bind:create_unbind_request", headers=HEADERS, data={"app_id":"100067","access_token":state["token"],"secondary_password":text}, timeout=12)
                    if r.json().get("result")==0:
                        bot.send_message(chat_id, "✅ Unbind SUCCESS!", reply_markup=yt_btn())
                    else:
                        bot.send_message(chat_id, f"❌ Failed: {r.text[:500]}", reply_markup=yt_btn())
                    del user_states[chat_id]
                    bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())
                except Exception as e:
                    bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
                    del user_states[chat_id]
        elif step=="otp":
            try:
                r = requests.post("https://100067.connect.garena.com/game/account_security/bind:verify_identity", headers=HEADERS, data={"email":state["email"],"app_id":"100067","access_token":state["token"],"otp":text}, timeout=12)
                ident = r.json().get("identity_token")
                if not ident:
                    bot.send_message(chat_id, f"❌ OTP Invalid: {r.text[:400]}", reply_markup=yt_btn())
                    del user_states[chat_id]
                    return
                r2 = requests.post("https://100067.connect.garena.com/game/account_security/bind:create_unbind_request", headers=HEADERS, data={"app_id":"100067","access_token":state["token"],"identity_token":ident}, timeout=12)
                if r2.json().get("result")==0:
                    bot.send_message(chat_id, "✅ Unbind SUCCESS!", reply_markup=yt_btn())
                else:
                    bot.send_message(chat_id, f"❌ {r2.text[:500]}", reply_markup=yt_btn())
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
            del user_states[chat_id]
            bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())

    elif action=="change":
        if step=="token":
            if not is_token(text):
                bot.send_message(chat_id, "❌ Invalid Token!", reply_markup=yt_btn()); return
            state["token"]=text; user_tokens[chat_id]=text
            bind = get_bind_info(text)
            if not bind.get("email"):
                bot.send_message(chat_id, "❌ No Email Bound - Use Add Recovery first", reply_markup=yt_btn())
                del user_states[chat_id]
                bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())
                return
            state["old_email"]=bind.get("email")
            bot.send_message(chat_id, f"Change Bind Email\n\nOld: {state['old_email']}\nEnter Security Code OR 'otp':", reply_markup=yt_btn())
            state["step"]="sec_or_otp"
        elif step=="sec_or_otp":
            if text.lower()=="otp":
                try:
                    r = requests.post("https://100067.connect.garena.com/game/account_security/bind:send_otp", headers=HEADERS, data={"email":state["old_email"],"locale":"en_PK","region":"PK","app_id":"100067","access_token":state["token"]}, timeout=12)
                    if r.json().get("result")==0:
                        bot.send_message(chat_id, f"✅ OTP Sent to {state['old_email']}\nEnter OTP:", reply_markup=yt_btn())
                        state["step"]="old_otp"
                    else:
                        bot.send_message(chat_id, f"❌ {r.text[:400]}", reply_markup=yt_btn())
                except Exception as e:
                    bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
            else:
                try:
                    r = requests.post("https://100067.connect.garena.com/game/account_security/bind:verify_identity", headers=HEADERS, data={"email":state["old_email"],"app_id":"100067","access_token":state["token"],"secondary_password":text}, timeout=12)
                    ident = r.json().get("identity_token")
                    if not ident:
                        bot.send_message(chat_id, f"❌ Invalid Sec Code: {r.text[:400]}", reply_markup=yt_btn())
                        del user_states[chat_id]
                        return
                    state["identity"]=ident
                    state["step"]="new_email"
                    bot.send_message(chat_id, "✅ Verified! Enter new email:", reply_markup=yt_btn())
                except Exception as e:
                    bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
                    del user_states[chat_id]
        elif step=="old_otp":
            try:
                r = requests.post("https://100067.connect.garena.com/game/account_security/bind:verify_identity", headers=HEADERS, data={"email":state["old_email"],"app_id":"100067","access_token":state["token"],"otp":text}, timeout=12)
                ident = r.json().get("identity_token")
                if not ident:
                    bot.send_message(chat_id, f"❌ OTP Invalid: {r.text[:400]}", reply_markup=yt_btn())
                    del user_states[chat_id]
                    return
                state["identity"]=ident
                state["step"]="new_email"
                bot.send_message(chat_id, "✅ Old Verified! Enter new email:", reply_markup=yt_btn())
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
                del user_states[chat_id]
        elif step=="new_email":
            state["new_email"]=text
            try:
                r = requests.post("https://100067.connect.garena.com/game/account_security/bind:send_otp", headers=HEADERS, data={"email":text,"locale":"en_PK","region":"PK","app_id":"100067","access_token":state["token"]}, timeout=12)
                if r.json().get("result")==0:
                    bot.send_message(chat_id, f"✅ OTP Sent to {text}\nEnter OTP:", reply_markup=yt_btn())
                    state["step"]="new_otp"
                else:
                    bot.send_message(chat_id, f"❌ {r.text[:400]}", reply_markup=yt_btn())
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
        elif step=="new_otp":
            try:
                r = requests.post("https://100067.connect.garena.com/game/account_security/bind:verify_otp", headers=HEADERS, data={"app_id":"100067","access_token":state["token"],"email":state["new_email"],"code":text,"otp":text,"type":"1"}, timeout=12)
                verifier = r.json().get("verifier_token")
                if not verifier:
                    bot.send_message(chat_id, f"❌ Verify Failed: {r.text[:400]}", reply_markup=yt_btn())
                    del user_states[chat_id]
                    return
                r2 = requests.post("https://100067.connect.garena.com/game/account_security/bind:create_rebind_request", headers=HEADERS, data={"identity_token":state["identity"],"email":state["new_email"],"app_id":"100067","verifier_token":verifier,"access_token":state["token"]}, timeout=12)
                if r2.json().get("result")==0:
                    bot.send_message(chat_id, f"🎉 Email Changed to {state['new_email']} Pending", reply_markup=yt_btn())
                else:
                    bot.send_message(chat_id, f"❌ {r2.text[:500]}", reply_markup=yt_btn())
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
            del user_states[chat_id]
            bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())

    elif action=="access_login":
        if step=="token":
            if not is_token(text):
                bot.send_message(chat_id, "❌ Invalid Token", reply_markup=yt_btn()); return
            user_tokens[chat_id]=text
            uid,nick,region = get_player_info(text)
            bot.send_message(chat_id, f"Access To Login\n\n👤 {nick}\n🆔 {uid}\n🌍 {region}\n✅ Access Granted", reply_markup=yt_btn())
            del user_states[chat_id]
            bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())

    elif action=="revoke":
        if step=="token":
            if not is_token(text):
                bot.send_message(chat_id, "❌ Invalid Token", reply_markup=yt_btn()); return
            state["token"]=text; user_tokens[chat_id]=text
            uid,nick,region = get_player_info(text)
            if nick=="Unknown":
                bot.send_message(chat_id, "❌ Invalid Token", reply_markup=yt_btn())
                del user_states[chat_id]
                return
            bot.send_message(chat_id, f"Revoke Access Token\n\n👤 {nick} | 🆔 {uid}\n⚠️ Type YES to confirm logout:", reply_markup=yt_btn())
            state["step"]="confirm"
            state["uid"]=uid; state["nick"]=nick
        elif step=="confirm":
            if text.lower()=="yes":
                try:
                    refresh_token="1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
                    url=f"https://100067.connect.garena.com/oauth/logout?access_token={state['token']}&refresh_token={refresh_token}"
                    r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=12)
                    bot.send_message(chat_id, f"✅ Token Revoked Successfully!\n👤 {state['nick']}", reply_markup=yt_btn())
                except Exception as e:
                    bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
            else:
                bot.send_message(chat_id, "❌ Cancelled", reply_markup=yt_btn())
            del user_states[chat_id]
            bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())

    elif action=="eat_access":
        if step=="token":
            eat_token=text
            try:
                r = requests.post("https://100067.connect.garena.com/oauth/guest/token/grant", headers=HEADERS, data={"app_id":"100067","eat_token":eat_token}, timeout=12)
                try:
                    j=r.json()
                    access=j.get("access_token") or j.get("token") or ""
                except:
                    access=""
                if access and is_token(access):
                    user_tokens[chat_id]=access
                    uid,nick,region = get_player_info(access)
                    bot.send_message(chat_id, f"✅ Eat Token Converted!\n👤 {nick} | 🆔 {uid}", reply_markup=yt_btn())
                else:
                    bot.send_message(chat_id, f"❌ Conversion Failed: {r.text[:500]}", reply_markup=yt_btn())
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
            del user_states[chat_id]
            bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())

    elif action=="single":
        if step=="email":
            if "@" not in text:
                bot.send_message(chat_id, "❌ Invalid Email", reply_markup=yt_btn()); return
            email=text.strip().lower()
            bot.send_message(chat_id, f"Sending Single Unsubscribe Otp to {email}...", reply_markup=yt_btn())
            try:
                success, resp = send_garena_otp(email)
                bot.send_message(chat_id, f"Single Unsubscribe OTP Sent Successfully!\n\nEmail: {email}\nStatus: OTP has been sent to your email", reply_markup=yt_btn())
                if success:
                    bot.send_message(chat_id, f"📧 Check Gmail: {email}\n📩 Subject: Verify Your Email Address\n🔑 Code like 05530666\n📁 Check Spam too", reply_markup=yt_btn())
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
            del user_states[chat_id]
            bot.send_message(chat_id, "Main Menu - Please select an option:", reply_markup=main_menu())

    elif action=="double":
        if step=="email":
            if "@" not in text:
                bot.send_message(chat_id, "❌ Invalid Email", reply_markup=yt_btn()); return
            email=text.strip().lower()
            bot.send_message(chat_id, f"Processing Double Unsubscribe (Resubscribe) for {email}...", reply_markup=yt_btn())
            try:
                success, resp = resubscribe_garena_email(email)
                if success:
                    bot.send_message(chat_id, f"Double Unsubscribe - Resubscribe Successful!\n\nEmail: {email}\n✅ Your Gmail has been resubscribed to Garena\n📧 You will now receive OTPs again", reply_markup=yt_btn())
                    bot.send_message(chat_id, f"📧 Check Gmail: {email}\n📩 Garena emails will start coming again", reply_markup=yt_btn())
                else:
                    bot.send_message(chat_id, f"Double Unsubscribe (Resubscribe)\n\nEmail: {email}\nIf you double unsubscribed, search Gmail for Garena and click Resubscribe link at bottom, or contact support: https://ffsupport.garena.com", reply_markup=yt_btn())
            except Exception as e:
                bot.send_message(chat_id, f"Double Unsubscribe - Coming Soon!\nError: {e}", reply_markup=yt_btn())
            del user_states[chat_id]
            bot.send_message(chat_id, "Main Menu - Please select an option:", reply_markup=main_menu())

@app.route('/')
def home(): return "✅ BOT RUNNING"
@app.route('/health')
def health(): return "OK",200
def run_bot(): bot.infinity_polling(timeout=60, long_polling_timeout=30)
if __name__=="__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
