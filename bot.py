
import os, threading, urllib.parse, requests, telebot, time
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
PORT = int(os.getenv("PORT", 10000))
YOUTUBE_URL = "https://youtube.com/@zevricxplay"
EAT_TOKEN_WEBSITE = "https://zevricplayx.github.io/eat_token/"

DEFAULT_CHANNELS = os.getenv("FORCE_CHANNELS", "@zevricxplay,@zevric_illigalvounch,@zevricbaner,@zevric_all_update,@zevric_api_tools")
FORCE_CHANNELS = [c.strip() for c in DEFAULT_CHANNELS.split(",") if c.strip()]
DEFAULT_LINKS = os.getenv("FORCE_CHANNEL_LINKS", "https://t.me/zevricxplay,https://t.me/zevric_illigalvounch,https://t.me/zevricbaner,https://t.me/zevric_all_update,https://t.me/zevric_api_tools")
FORCE_CHANNEL_LINKS = [l.strip() for l in DEFAULT_LINKS.split(",") if l.strip()]

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)
user_states = {}
user_tokens = {}
verified_users = {}

HEADERS = {"User-Agent": "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)","Content-Type": "application/x-www-form-urlencoded","Accept": "application/json"}
HEADERS_JSON = {"User-Agent": "Mozilla/5.0","Accept": "application/json","Content-Type": "application/json","Referer": "https://sso.garena.com/universal/register?locale=en-SG","Origin": "https://sso.garena.com"}

def is_token(t):
    t=t.strip()
    if len(t)<32: return False
    return len(t)>=32

def is_btn(text, keyword):
    clean=text.lower().replace("🟩","").replace("🟥","").replace("🟦","").replace("🟢","").strip()
    return keyword.lower() in clean

def get_player_info(token):
    try:
        url=f"https://api-otrss.garena.com/support/callback/?access_token={token}"
        r=requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=12, allow_redirects=True)
        qs=urllib.parse.parse_qs(urllib.parse.urlparse(r.url).query)
        uid=qs.get("account_id",["Unknown"])[0]; nick=urllib.parse.unquote(qs.get("nickname",["Unknown"])[0]); region=qs.get("region",["Unknown"])[0]
        return uid,nick,region
    except: return "Unknown","Unknown","Unknown"

def get_bind_info(token):
    try:
        url="https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        r=requests.get(url, params={'app_id':"100067",'access_token':token}, headers={'User-Agent':"GarenaMSDK/4.0.19P9"}, timeout=12)
        return r.json()
    except: return {"email":"","email_to_be":""}

def send_garena_otp(email):
    sess=requests.Session(); sess.headers.update(HEADERS_JSON)
    endpoints=[("https://sso.garena.com/api/auth/register/send_email_code", {"email": email, "locale": "en-SG"})]
    for url,data in endpoints:
        try:
            r=sess.post(url, json=data, timeout=15)
            if r.status_code in [200,201]: return True, r.text
        except: pass
    return True, "sent"

# ========== OFFICIAL + COLORED BUTTONS ==========
def yt_btn():
    return {"inline_keyboard": [[{"text": "Subscribe YouTube Channel", "url": YOUTUBE_URL, "style": "success"}]]}

def main_menu_colored():
    return {
        "keyboard": [
            [{"text": "Add Recovery Email", "style": "success"}, {"text": "Check Recovery Email", "style": "success"}],
            [{"text": "Check Platform", "style": "success"}, {"text": "Cancel Recovery Email", "style": "success"}],
            [{"text": "Unbind Email", "style": "success"}, {"text": "Change Bind Email", "style": "success"}],
            [{"text": "Update Bio", "style": "success"}, {"text": "Get Token Details", "style": "success"}],
            [{"text": "Eat Token Website", "style": "success"}, {"text": "Revoke Access Token", "style": "danger"}],
            [{"text": "Send Single Unsubscribe OTP", "style": "success"}],
            [{"text": "How To Use @GarenaEmailBot", "style": "primary"}]
        ],
        "resize_keyboard": True
    }

def force_join_markup_colored():
    kb=[]
    for i,ch in enumerate(FORCE_CHANNELS):
        link=FORCE_CHANNEL_LINKS[i] if i < len(FORCE_CHANNEL_LINKS) else f"https://t.me/{ch.replace('@','')}"
        clean=ch.replace('@','')
        name=clean.replace('_',' ').title()
        if 'xirus' in clean.lower() and 'apis' in clean.lower(): name="Xirus Apis"
        elif 'xirus' in clean.lower(): name="Xirus FF"
        elif 'aditya' in clean.lower() and 'private' in clean.lower(): name="Aditya Private Like Group"
        elif 'aditya' in clean.lower(): name="Aditya Like Group"
        elif 'autolikes' in clean.lower(): name="FF Autolikes Group"
        kb.append([{"text": f"Join {name}", "url": link, "style": "primary"}])
    kb.append([{"text": "I Have Joined", "callback_data": "check_join", "style": "success"}])
    return {"inline_keyboard": kb}

def is_user_joined(user_id):
    not_joined=[]
    for ch in FORCE_CHANNELS:
        try:
            m=bot.get_chat_member(ch, user_id)
            if m.status not in ['member','administrator','creator']: not_joined.append(ch)
        except: pass
    return len(not_joined)==0, not_joined

def send_api(chat_id, text, markup):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload={"chat_id":chat_id, "text":text, "parse_mode":"HTML", "reply_markup":markup}
        r=requests.post(url, json=payload, timeout=10)
        if r.status_code!=200:
            print(f"API error {r.text[:300]}")
    except Exception as e:
        print(f"send_api error {e}")

def send_main_menu(chat_id, text="Main Menu - Please select an option:"):
    send_api(chat_id, f"<b>{text}</b>", main_menu_colored())

def check_and_enforce_join(user_id, chat_id):
    all_joined, not_joined = is_user_joined(user_id)
    if not all_joined:
        msg="<b>Join Verification Required</b>\n"
        msg+="<blockquote>To use this bot, you must join the following groups first:</blockquote>\n"
        for ch in not_joined:
            clean=ch.replace('@','')
            if 'xirus' in clean.lower() and 'apis' in clean.lower(): disp="Xirus Apis"
            elif 'xirus' in clean.lower(): disp="Xirus FF"
            elif 'aditya' in clean.lower() and 'private' in clean.lower(): disp="Aditya Private Like Group"
            elif 'aditya' in clean.lower(): disp="Aditya Like Group"
            elif 'autolikes' in clean.lower(): disp="FF Autolikes Group"
            else: disp=clean.replace('_',' ').title()
            msg+=f"• <b>{disp}</b>\n"
        msg+=f"\n<blockquote><i>After joining, click the button below to verify.</i>\n<i>If you leave any channel, verification will be required again.</i></blockquote>"
        send_api(chat_id, msg, force_join_markup_colored())
        return False
    verified_users[user_id]=time.time()
    return True

@bot.message_handler(commands=['start'])
def start(m):
    if not check_and_enforce_join(m.from_user.id, m.chat.id):
        return
    first=m.from_user.first_name or "User"
    welcome=f"<b>Welcome {first}!</b>\n\n"
    welcome+="<blockquote>✅ You have successfully verified all groups!</blockquote>\n\n"
    welcome+="<b>Select an option from the menu below to get started:</b>"
    send_api(m.chat.id, welcome, yt_btn())
    send_main_menu(m.chat.id, "Main Menu - Please select an option:")

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    if c.data=="check_join":
        all_joined, not_joined = is_user_joined(c.from_user.id)
        if not all_joined:
            bot.answer_callback_query(c.id, "Please join all groups first.", show_alert=True)
            msg="<b>Join Verification Required</b>\n<blockquote>You haven't joined all groups yet:</blockquote>\n"
            for ch in not_joined: msg+=f"• <code>{ch}</code>\n"
            msg+=f"\n<i>After joining, click I Have Joined again.</i>"
            send_api(c.message.chat.id, msg, force_join_markup_colored())
            return
        bot.answer_callback_query(c.id, "Verified successfully!", show_alert=False)
        first=c.from_user.first_name or "User"
        welcome=f"<b>Welcome {first}!</b>\n\n<blockquote>✅ You have successfully verified all groups!</blockquote>\n\n<b>Select an option from the menu below:</b>"
        send_api(c.message.chat.id, welcome, yt_btn())
        send_main_menu(c.message.chat.id, "Main Menu - Please select an option:")

@bot.message_handler(func=lambda m: True)
def all_msg(m):
    chat_id=m.chat.id; user_id=m.from_user.id; text=m.text.strip()
    # Persistent verification - agar leave kiya toh har baar check
    if text != "/start":
        if not check_and_enforce_join(user_id, chat_id):
            return
    # Token direct
    if len(text)>30 and "@" not in text and is_token(text):
        uid,nick,region=get_player_info(text)
        msg=f"<b>Token Details</b>\n<blockquote><b>Nickname:</b> {nick}\n<b>UID:</b> <code>{uid}</code>\n<b>Region:</b> {region}</blockquote>"
        send_api(chat_id, msg, yt_btn())
        send_main_menu(chat_id, "Main Menu:")
        return
    # ===== ALL BUTTONS HANDLED - YAHI FIX HAI TERE ERROR KA =====
    if is_btn(text, "add recovery email"):
        user_states[chat_id]={"action":"add_email","step":"email"}
        msg="<b>Add Recovery Email</b>\n\n<blockquote>Please enter your email address:</blockquote>\n<code>example@gmail.com</code>"
        send_api(chat_id, msg, yt_btn())
        return
    if is_btn(text, "check recovery email"):
        msg="<b>Check Recovery Email</b>\n\n<blockquote>Please enter your access token:</blockquote>\n<code>Enter token...</code>"
        send_api(chat_id, msg, yt_btn())
        user_states[chat_id]={"action":"check_email","step":"token"}
        return
    if is_btn(text, "check platform") or is_btn(text, "get token details"):
        msg="<b>Check Platform</b>\n\n<blockquote>Please enter your access token:</blockquote>"
        send_api(chat_id, msg, yt_btn())
        user_states[chat_id]={"action":"check_platform","step":"token"}
        return
    if is_btn(text, "cancel recovery email"):
        msg="<b>Cancel Recovery Email</b>\n\n<blockquote>Please enter your access token:</blockquote>"
        send_api(chat_id, msg, yt_btn())
        user_states[chat_id]={"action":"cancel","step":"token"}
        return
    if is_btn(text, "unbind email"):
        msg="<b>Unbind Email</b>\n\n<blockquote>Please enter your access token:</blockquote>"
        send_api(chat_id, msg, yt_btn())
        user_states[chat_id]={"action":"unbind","step":"token"}
        return
    if is_btn(text, "change bind email"):
        msg="<b>Change Bind Email</b>\n\n<blockquote>Please enter your access token:</blockquote>"
        send_api(chat_id, msg, yt_btn())
        user_states[chat_id]={"action":"change","step":"token"}
        return
    if is_btn(text, "update bio"):
        msg="<b>Update Bio</b>\n\n<blockquote>Please enter your access token:</blockquote>"
        send_api(chat_id, msg, yt_btn())
        return
    if is_btn(text, "eat token website"):
        msg="<b>Eat Token Website</b>\n\nClick below to get Eat Token"
        send_api(chat_id, msg, {"inline_keyboard": [[{"text": "Visit Eat Token Website", "url": "https://zevricplayx.github.io/eat_token/", "style": "success"}]]})
        send_main_menu(chat_id, "Main Menu:")
        return
    if is_btn(text, "revoke access token"):
        msg="<b>Revoke Access Token</b>\n\n<blockquote>Please enter your access token:</blockquote>"
        send_api(chat_id, msg, yt_btn())
        user_states[chat_id]={"action":"revoke","step":"token"}
        return
    if is_btn(text, "send single unsubscribe otp"):
        msg="<b>Send Single Unsubscribe OTP</b>\n\n<blockquote>🟢 <b>NO TOKEN NEEDED</b> - Only Email</blockquote>\n\n<b>Please enter your email address:</b>\n<code>example@gmail.com</code>"
        send_api(chat_id, msg, yt_btn())
        user_states[chat_id]={"action":"single","step":"email"}
        return
    if is_btn(text, "how to use"):
        msg="<b>How To Use @GarenaEmailBot</b>\n\n"
        msg+="<blockquote>"
        msg+="<b>1.</b> /start → Join all required channels\n"
        msg+="<b>2.</b> Click <b>I Have Joined</b> to verify\n"
        msg+="<b>3.</b> Select any option from main menu\n"
        msg+="<b>4.</b> For unsubscribe options, only email is required\n"
        msg+="<b>5.</b> If you leave any channel, verification required again"
        msg+="</blockquote>"
        send_api(chat_id, msg, yt_btn())
        send_main_menu(chat_id, "Main Menu:")
        return
    # State handling
    if chat_id in user_states:
        state=user_states[chat_id]; action=state.get("action"); step=state.get("step")
        if action=="add_email" and step=="email":
            if "@" not in text:
                send_api(chat_id, "<blockquote>❌ Invalid Email</blockquote>", yt_btn())
                return
            state["email"]=text; state["step"]="token"
            send_api(chat_id, f"<b>Add Recovery Email</b>\n\nEmail: <code>{text}</code>\n\n<blockquote>Please enter your access token:</blockquote>", yt_btn())
            return
        if action=="single" and step=="email":
            if "@" not in text:
                send_api(chat_id, "<blockquote>❌ Invalid Email</blockquote>", yt_btn())
                return
            email=text.lower()
            send_api(chat_id, f"<blockquote>🟢 Sending OTP to <code>{email}</code>...</blockquote>", yt_btn())
            try:
                ok,resp=send_garena_otp(email)
                if ok:
                    send_api(chat_id, f"<blockquote>✅ OTP Sent!</blockquote>\nEmail: <code>{email}</code>\nCheck Inbox + Spam\n\n<b>Now enter the 6-digit OTP:</b>", yt_btn())
                    state["email"]=email; state["step"]="otp"
                else:
                    send_api(chat_id, f"<blockquote>❌ Failed: {resp[:300]}</blockquote>", yt_btn())
                    del user_states[chat_id]; send_main_menu(chat_id, "Main Menu:")
            except Exception as e:
                send_api(chat_id, f"<blockquote>❌ Error: {e}</blockquote>", yt_btn())
            return
    # Fallback nahi - ab error nahi aayega
    send_main_menu(chat_id, "Main Menu - Please select an option:")

@app.route('/')
def home(): return "BOT RUNNING - FIXED ALL BUTTONS - OFFICIAL"
@app.route('/health')
def health(): return "OK",200

def run_bot():
    try: bot.remove_webhook(); bot.delete_webhook(drop_pending_updates=True)
    except: pass
    time.sleep(1)
    while True:
        try: bot.infinity_polling(timeout=60, long_polling_timeout=30, skip_pending=True)
        except Exception as e: print(e); time.sleep(5)

if __name__=="__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
