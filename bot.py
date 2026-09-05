
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
verified_users = {}

def is_token(t):
    return len(t.strip())>=32

def is_btn(text, keyword):
    clean=text.lower().replace("🟩","").replace("🟥","").replace("🟦","").strip()
    return keyword.lower() in clean

def is_user_joined(user_id):
    not_joined=[]
    for ch in FORCE_CHANNELS:
        try:
            m=bot.get_chat_member(ch, user_id)
            if m.status not in ['member','administrator','creator']: not_joined.append(ch)
        except: pass
    return len(not_joined)==0, not_joined

# ========== OFFICIALLY COLORED - PREMIUM ==========
def yt_btn():
    return {"inline_keyboard": [[{"text": "Subscribe YouTube Channel", "url": YOUTUBE_URL, "style": "success"}]]}

def main_menu_colored():
    # Officially colored - Green / Red / Blue exactly as screenshot
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
        if 'xirus' in clean.lower() and 'apis' in clean.lower(): name="Xirus Apis"
        elif 'xirus' in clean.lower(): name="Xirus FF"
        elif 'aditya' in clean.lower() and 'private' in clean.lower(): name="Aditya Private Like Group"
        elif 'aditya' in clean.lower(): name="Aditya Like Group" if 'like' in clean.lower() else "Aditya Group"
        elif 'autolikes' in clean.lower(): name="FF Autolikes Group"
        else: name=clean.replace('_',' ').title()
        kb.append([{"text": f"Join {name}", "url": link, "style": "primary"}])  # BLUE
    kb.append([{"text": "I Have Joined", "callback_data": "check_join", "style": "success"}])  # GREEN
    return {"inline_keyboard": kb}

def send_api(chat_id, text, markup):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload={"chat_id":chat_id, "text":text, "parse_mode":"HTML", "reply_markup":markup}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(e)

def send_main_menu(chat_id, text="Main Menu - Please select an option:"):
    send_api(chat_id, f"<b>{text}</b>", main_menu_colored())

def check_and_enforce_join(user_id, chat_id):
    all_joined, not_joined = is_user_joined(user_id)
    if not all_joined:
        # OFFICIAL STYLE TEXT
        msg = "<b>Join Verification Required</b>\n"
        msg += "<blockquote>To use this bot, you must join the following groups first:</blockquote>\n"
        for ch in FORCE_CHANNELS:
            clean=ch.replace('@','')
            if 'xirus' in clean.lower() and 'apis' in clean.lower(): disp="Xirus Apis"
            elif 'xirus' in clean.lower(): disp="Xirus FF"
            elif 'aditya' in clean.lower() and 'private' in clean.lower(): disp="Aditya Private Like Group"
            elif 'aditya' in clean.lower(): disp="Aditya Like Group"
            elif 'autolikes' in clean.lower(): disp="FF Autolikes Group"
            else: disp=clean.replace('_',' ').title()
            msg+=f"• <b>{disp}</b>\n"
        msg+=f"\n<blockquote><i>After joining, click the button below to verify.</i>\n"
        msg+=f"<i>If you leave any channel, verification will be required again.</i></blockquote>"
        send_api(chat_id, msg, force_join_markup_colored())
        return False
    verified_users[user_id]=time.time()
    return True

@bot.message_handler(commands=['start'])
def start(m):
    if not check_and_enforce_join(m.from_user.id, m.chat.id):
        return
    first=m.from_user.first_name or "User"
    welcome = f"<b>Welcome {first}!</b>\n\n"
    welcome += f"<blockquote>You have successfully verified all groups!</blockquote>\n\n"
    welcome += f"<b>Select an option from the menu below to get started:</b>"
    send_api(m.chat.id, welcome, yt_btn())
    send_main_menu(m.chat.id, "Main Menu - Please select an option:")

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    if c.data=="check_join":
        all_joined, not_joined = is_user_joined(c.from_user.id)
        if not all_joined:
            bot.answer_callback_query(c.id, "Please join all groups first.", show_alert=True)
            msg = "<b>Join Verification Required</b>\n"
            msg += "<blockquote>You haven't joined all groups yet:</blockquote>\n"
            for ch in not_joined: msg+=f"• <code>{ch}</code>\n"
            msg+=f"\n<i>After joining, click I Have Joined again.</i>"
            send_api(c.message.chat.id, msg, force_join_markup_colored())
            return
        bot.answer_callback_query(c.id, "Verified successfully!", show_alert=False)
        first=c.from_user.first_name or "User"
        welcome=f"<b>Welcome {first}!</b>\n\n<blockquote>You have successfully verified all groups!</blockquote>\n\n<b>Select an option from the menu below to get started:</b>"
        send_api(c.message.chat.id, welcome, yt_btn())
        send_main_menu(c.message.chat.id, "Main Menu - Please select an option:")

@bot.message_handler(func=lambda m: True)
def all_msg(m):
    chat_id=m.chat.id
    if m.text != "/start":
        if not check_and_enforce_join(m.from_user.id, chat_id):
            return
    text=m.text.strip()
    if is_btn(text, "single unsubscribe"):
        msg="<b>Send Single Unsubscribe OTP</b>\n\n"
        msg+="<blockquote><b>NO TOKEN NEEDED</b> - Only Email</blockquote>\n\n"
        msg+="<b>Please enter your email address:</b>\n"
        msg+="<code>example@gmail.com</code>"
        send_api(chat_id, msg, yt_btn())
        return
    if is_btn(text, "how to use"):
        msg="<b>How To Use @GarenaEmailBot</b>\n\n"
        msg+="<blockquote>"
        msg+="<b>1.</b> Start the bot and join all required channels\n"
        msg+="<b>2.</b> Click <b>I Have Joined</b> to verify\n"
        msg+="<b>3.</b> Select an option from the main menu\n"
        msg+="<b>4.</b> For unsubscribe options, only email is required\n"
        msg+="<b>5.</b> If you leave any channel, you will need to verify again"
        msg+="</blockquote>"
        send_api(chat_id, msg, yt_btn())
        send_main_menu(chat_id, "Main Menu:")
        return
    send_main_menu(chat_id, "Please select an option from the menu first.")
    send_api(chat_id, "<b>Main Menu - Please select an option:</b>", yt_btn())

@app.route('/')
def home(): return "BOT RUNNING - OFFICIAL STYLE - COLORED"
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
    import threading
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
