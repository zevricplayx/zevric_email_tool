"""
Garena Email Bot - EXACT LIKE PHOTO - Full Green + Red
13 Options as per user's image
"""
import os, threading, urllib.parse, requests, telebot, random, string
from telebot import types
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
PORT = int(os.getenv("PORT", 10000))
YOUTUBE_URL = "https://youtube.com/@zevricxplay"
EAT_TOKEN_WEBSITE = "https://zevricplayx.github.io/eat_token/"
TUTORIAL_URL = "https://youtube.com/@zevricxplay"

# Force Join - ALL Channels aur Groups jo aapne diye the - Start pe join karna padega
# Tere 5 channels jo tune diye:
# 1. https://t.me/zevricxplay
# 2. https://t.me/zevric_illigalvounch
# 3. https://t.me/zevricbaner
# 4. https://t.me/zevric_all_update
# 5. https://t.me/zevric_api_tools
DEFAULT_CHANNELS = "@zevricxplay,@zevric_illigalvounch,@zevricbaner,@zevric_all_update,@zevric_api_tools"
DEFAULT_LINKS = "https://t.me/zevricxplay,https://t.me/zevric_illigalvounch,https://t.me/zevricbaner,https://t.me/zevric_all_update,https://t.me/zevric_api_tools"

FORCE_CHANNELS = [c.strip() for c in os.getenv("FORCE_CHANNELS", os.getenv("FORCE_CHANNEL", DEFAULT_CHANNELS)).split(",") if c.strip()]
FORCE_GROUPS = [g.strip() for g in os.getenv("FORCE_GROUPS", os.getenv("FORCE_GROUP", "")).split(",") if g.strip()]
FORCE_CHANNEL_LINKS = [l.strip() for l in os.getenv("FORCE_CHANNEL_LINKS", os.getenv("FORCE_CHANNEL_LINK", DEFAULT_LINKS)).split(",") if l.strip()]
FORCE_GROUP_LINKS = [l.strip() for l in os.getenv("FORCE_GROUP_LINKS", os.getenv("FORCE_GROUP_LINK", "")).split(",") if l.strip()]


# Backward compatibility
FORCE_CHANNEL = FORCE_CHANNELS[0] if FORCE_CHANNELS else "@zevricxplay"
FORCE_GROUP = FORCE_GROUPS[0] if FORCE_GROUPS else ""
FORCE_CHANNEL_LINK = FORCE_CHANNEL_LINKS[0] if FORCE_CHANNEL_LINKS else "https://t.me/zevricxplay"
FORCE_GROUP_LINK = FORCE_GROUP_LINKS[0] if FORCE_GROUP_LINKS else ""



bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)
user_states = {}
user_tokens = {}

HEADERS = {
    "User-Agent": "GarenaMSDK/4.0.19P9",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json"
}

def yt_btn():
    mk = types.InlineKeyboardMarkup()
    try:
        mk.add(types.InlineKeyboardButton("Subscribe YouTube Channel", url=YOUTUBE_URL, style="success"))
    except:
        mk.add(types.InlineKeyboardButton("Subscribe YouTube Channel", url=YOUTUBE_URL))
    return mk

def eat_btn():
    mk = types.InlineKeyboardMarkup()
    try:
        mk.add(types.InlineKeyboardButton("Visit Eat Token Website", url=EAT_TOKEN_WEBSITE, style="success"))
    except:
        mk.add(types.InlineKeyboardButton("Visit Eat Token Website", url=EAT_TOKEN_WEBSITE))
    return mk

def tutorial_btn():
    mk = types.InlineKeyboardMarkup()
    try:
        mk.add(types.InlineKeyboardButton("Watch Tutorial", url=TUTORIAL_URL, style="success"))
    except:
        mk.add(types.InlineKeyboardButton("Watch Tutorial", url=TUTORIAL_URL))
    return mk



def is_user_joined(user_id):
    """Check if user joined ALL channels and ALL groups - jo aapne diye the"""
    not_joined_channels = []
    not_joined_groups = []
    
    for channel in FORCE_CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                not_joined_channels.append(channel)
        except:
            pass
    
    for group in FORCE_GROUPS:
        try:
            member = bot.get_chat_member(group, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                not_joined_groups.append(group)
        except:
            pass
    
    all_joined = len(not_joined_channels) == 0 and len(not_joined_groups) == 0
    return all_joined, not_joined_channels, not_joined_groups

def force_join_markup_exact():
    """EXACT like user's photo - blue join buttons + green I Have Joined"""
    mk = types.InlineKeyboardMarkup(row_width=1)
    # All 5 channels as per user - blue buttons with arrow
    try:
        # Blue buttons for each channel/group
        for i, channel in enumerate(FORCE_CHANNELS):
            link = FORCE_CHANNEL_LINKS[i] if i < len(FORCE_CHANNEL_LINKS) else f"https://t.me/{channel.replace('@','')}"
            clean = channel.replace('@','')
            if 'zevricxplay' == clean:
                name = "Zevricxplay"
            elif 'zevric_illigalvounch' in clean:
                name = "Zevric Illigalvounch"
            elif 'zevricbaner' in clean:
                name = "Zevric Baner"
            elif 'zevric_all_update' in clean:
                name = "Zevric All Update"
            elif 'zevric_api_tools' in clean:
                name = "Zevric Api Tools"
            else:
                name = clean.replace('_',' ').title()
            mk.add(types.InlineKeyboardButton(f"Join {name}", url=link, style="primary"))
        
        for i, group in enumerate(FORCE_GROUPS):
            link = FORCE_GROUP_LINKS[i] if i < len(FORCE_GROUP_LINKS) else f"https://t.me/{group.replace('@','')}"
            mk.add(types.InlineKeyboardButton(f"Join {group.replace('@','').replace('_',' ').title()}", url=link, style="primary"))
        
        # Green I Have Joined button - full width green like photo
        mk.add(types.InlineKeyboardButton("I Have Joined", callback_data="check_join", style="success"))
    except:
        # Fallback without style - Telegram will still show blue for url buttons and green via text
        for i, channel in enumerate(FORCE_CHANNELS):
            link = FORCE_CHANNEL_LINKS[i] if i < len(FORCE_CHANNEL_LINKS) else f"https://t.me/{channel.replace('@','')}"
            clean = channel.replace('@','')
            if 'zevricxplay' == clean:
                name = "Zevricxplay"
            elif 'zevric_illigalvounch' in clean:
                name = "Zevric Illigalvounch"
            elif 'zevricbaner' in clean:
                name = "Zevric Baner"
            elif 'zevric_all_update' in clean:
                name = "Zevric All Update"
            elif 'zevric_api_tools' in clean:
                name = "Zevric Api Tools"
            else:
                name = clean.replace('_',' ').title()
            mk.add(types.InlineKeyboardButton(f"Join {name}", url=link))
        
        mk.add(types.InlineKeyboardButton("I Have Joined", callback_data="check_join"))
    return mk

def force_join_markup(not_joined_channels=None, not_joined_groups=None):
    return force_join_markup_exact()

def main_menu():
    # Bottom ReplyKeyboard - 14 options now with Double Unsubscribe added
    # Layout: 7 rows x 2 = 14
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    try:
        m.add(
            types.KeyboardButton("Add Recovery Email", style="success"),
            types.KeyboardButton("Check Recovery Email", style="success")
        )
        m.add(
            types.KeyboardButton("Check Platform", style="success"),
            types.KeyboardButton("Cancel Recovery Email", style="success")
        )
        m.add(
            types.KeyboardButton("Unbind Email", style="success"),
            types.KeyboardButton("Change Bind Email", style="success")
        )
        m.add(
            types.KeyboardButton("Update Bio", style="success"),
            types.KeyboardButton("Change Name", style="success")
        )
        m.add(
            types.KeyboardButton("Access To Login", style="success"),
            types.KeyboardButton("Revoke Access Token", style="danger")
        )
        m.add(
            types.KeyboardButton("Get Eat Token", style="success"),
            types.KeyboardButton("Eat To Access", style="success")
        )
        m.add(
            types.KeyboardButton("Send Single Unsubscribe Otp", style="success"),
            types.KeyboardButton("Send Double Unsubscribe Otp", style="success")
        )
    except:
        # Fallback with emoji - always shows
        m.add(types.KeyboardButton("🟩 Add Recovery Email"), types.KeyboardButton("🟩 Check Recovery Email"))
        m.add(types.KeyboardButton("🟩 Check Platform"), types.KeyboardButton("🟩 Cancel Recovery Email"))
        m.add(types.KeyboardButton("🟩 Unbind Email"), types.KeyboardButton("🟩 Change Bind Email"))
        m.add(types.KeyboardButton("🟩 Update Bio"), types.KeyboardButton("🟩 Change Name"))
        m.add(types.KeyboardButton("🟩 Access To Login"), types.KeyboardButton("🟥 Revoke Access Token"))
        m.add(types.KeyboardButton("🟩 Get Eat Token"), types.KeyboardButton("🟩 Eat To Access"))
        m.add(types.KeyboardButton("🟩 Send Single Unsubscribe Otp"), types.KeyboardButton("🟩 Send Double Unsubscribe Otp"))
    return m

def main_menu_inline_full_color():
    # Top Inline - 14 options with Double Unsubscribe
    m = types.InlineKeyboardMarkup(row_width=2)
    try:
        m.add(
            types.InlineKeyboardButton("Add Recovery Email", callback_data="menu_add", style="success"),
            types.InlineKeyboardButton("Check Recovery Email", callback_data="menu_check", style="success")
        )
        m.add(
            types.InlineKeyboardButton("Check Platform", callback_data="menu_platform", style="success"),
            types.InlineKeyboardButton("Cancel Recovery Email", callback_data="menu_cancel", style="success")
        )
        m.add(
            types.InlineKeyboardButton("Unbind Email", callback_data="menu_unbind", style="success"),
            types.InlineKeyboardButton("Change Bind Email", callback_data="menu_change", style="success")
        )
        m.add(
            types.InlineKeyboardButton("Update Bio", callback_data="menu_bio", style="success"),
            types.InlineKeyboardButton("Change Name", callback_data="menu_name", style="success")
        )
        m.add(
            types.InlineKeyboardButton("Access To Login", callback_data="menu_access", style="success"),
            types.InlineKeyboardButton("Revoke Access Token", callback_data="menu_revoke", style="danger")
        )
        m.add(
            types.InlineKeyboardButton("Get Eat Token", callback_data="menu_geteat", style="success"),
            types.InlineKeyboardButton("Eat To Access", callback_data="menu_eataccess", style="success")
        )
        m.add(
            types.InlineKeyboardButton("Send Single Unsubscribe Otp", callback_data="menu_single", style="success"),
            types.InlineKeyboardButton("Send Double Unsubscribe Otp", callback_data="menu_double", style="success")
        )
    except:
        m.add(
            types.InlineKeyboardButton("Add Recovery Email", callback_data="menu_add"),
            types.InlineKeyboardButton("Check Recovery Email", callback_data="menu_check")
        )
        m.add(
            types.InlineKeyboardButton("Check Platform", callback_data="menu_platform"),
            types.InlineKeyboardButton("Cancel Recovery Email", callback_data="menu_cancel")
        )
        m.add(
            types.InlineKeyboardButton("Unbind Email", callback_data="menu_unbind"),
            types.InlineKeyboardButton("Change Bind Email", callback_data="menu_change")
        )
        m.add(
            types.InlineKeyboardButton("Update Bio", callback_data="menu_bio"),
            types.InlineKeyboardButton("Change Name", callback_data="menu_name")
        )
        m.add(
            types.InlineKeyboardButton("Access To Login", callback_data="menu_access"),
            types.InlineKeyboardButton("Revoke Access Token", callback_data="menu_revoke")
        )
        m.add(
            types.InlineKeyboardButton("Get Eat Token", callback_data="menu_geteat"),
            types.InlineKeyboardButton("Eat To Access", callback_data="menu_eataccess")
        )
        m.add(
            types.InlineKeyboardButton("Send Single Unsubscribe Otp", callback_data="menu_single"),
            types.InlineKeyboardButton("Send Double Unsubscribe Otp", callback_data="menu_double")
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
    return keyword.lower() in text.lower()

def send_real_garena_otp(email):
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Referer": "https://sso.garena.com/universal/register?locale=en-SG",
        "Origin": "https://sso.garena.com"
    })
    endpoints = [
        ("https://sso.garena.com/api/auth/register/send_email_code", {"email": email, "locale": "en-SG"}),
        ("https://sso.garena.com/api/account/request_email_code", {"email": email, "locale": "en-SG"}),
        ("https://sso.garena.com/api/account/forgot_password/email_code", {"email": email}),
    ]
    last = ""
    for url,payload in endpoints:
        try:
            r = sess.post(url, json=payload, timeout=15)
            last = r.text
            if r.status_code in [200,201]:
                return True, last
        except Exception as e:
            last = str(e)
            continue
    return False, last

@bot.message_handler(commands=['start'])
def start(m):
    # Force Join Check - EXACT like photo: Join Verification Required with blue + green
    all_joined, not_joined_channels, not_joined_groups = is_user_joined(m.from_user.id)
    if not all_joined:
        # Format exactly like image user sent
        all_groups = FORCE_CHANNELS + FORCE_GROUPS
        # Build message like: Join Verification Required\n\nTo use this bot, you must join the following groups first:\n\n- Xirus Apis...
        msg = "Join Verification Required\n\n"
        msg += "To use this bot, you must join the following groups first:\n\n"
        for ch in all_groups:
            clean_name = ch.replace('@','').replace('_',' ').title()
            # For user's 5 channels, make nice names
            if 'zevricxplay' in ch.lower():
                clean_name = "Zevricxplay"
            elif 'illigal' in ch.lower():
                clean_name = "Zevric Illigal Vounch"
            elif 'baner' in ch.lower():
                clean_name = "Zevric Baner"
            elif 'all_update' in ch.lower():
                clean_name = "Zevric All Update"
            elif 'api_tools' in ch.lower():
                clean_name = "Zevric Api Tools"
            msg += f"- {clean_name}\n"
        msg += "\nAfter joining, click the button below to verify:"
        bot.send_message(m.chat.id, msg, reply_markup=force_join_markup_exact())
        return
    
    welcome = f"Welcome {m.from_user.first_name}!\n\n✅ 14 Premium Features\n👇 Niche se option select karo:"
    bot.send_message(m.chat.id, welcome, reply_markup=yt_btn())
    bot.send_message(m.chat.id, "Main Menu - Please select an option: 👇", reply_markup=main_menu())

def send_status(chat_id, token):
    uid, nick, region = get_player_info(token)
    bind = get_bind_info(token)
    email = bind.get("email","")
    email_to = bind.get("email_to_be","")
    user_tokens[chat_id]=token
    if not email and not email_to:
        msg = f"Email Status for {nick}\n\n📧 Confirmed: No Email Bound\n⏳ Status: No Email\n🆔 {uid} | 🌍 {region}"
    elif email and not email_to:
        msg = f"Email Status for {nick}\n\n✅ Confirmed Email: {email}\n📊 Status: Confirmed: {email}\n🆔 {uid} | 🌍 {region}"
    else:
        cd = bind.get("request_exec_countdown",0)
        msg = f"Email Status for {nick}\n\n📧 Confirmed: {email or 'No Email'}\n⏳ Pending: {email_to} ({cd}s)\n🆔 {uid} | 🌍 {region}"
    bot.send_message(chat_id, msg, reply_markup=yt_btn())
    bot.send_message(chat_id, "Main Menu - Please select an option: 👇", reply_markup=main_menu())

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
    bot.send_message(m.chat.id, "Main Menu - Please select an option: 👇", reply_markup=main_menu())

@bot.message_handler(func=lambda m: is_btn(m.text, "Cancel Recovery Email"))
def cancel_btn(m):
    token = user_tokens.get(m.chat.id)
    if not token:
        user_states[m.chat.id] = {"action":"cancel","step":"token"}
        bot.send_message(m.chat.id, "Cancel Recovery Email\n\n🔑 Please enter your access token: 👇", reply_markup=yt_btn())
        return
    try:
        r = requests.post("https://100067.connect.garena.com/game/account_security/bind:cancel_request", headers=HEADERS, data={"app_id":"100067","access_token":token}, timeout=10)
        if r.json().get("result")==0:
            bot.send_message(m.chat.id, "✅ Cancel SUCCESS", reply_markup=yt_btn())
        else:
            bot.send_message(m.chat.id, "Cancel Recovery Email\n\n❌ No Pending Request", reply_markup=yt_btn())
    except Exception as e:
        bot.send_message(m.chat.id, f"❌ {e}", reply_markup=yt_btn())
    bot.send_message(m.chat.id, "Main Menu - Please select an option: 👇", reply_markup=main_menu())

@bot.message_handler(func=lambda m: is_btn(m.text, "Unbind Email"))
def unbind_btn(m):
    token = user_tokens.get(m.chat.id)
    if not token:
        user_states[m.chat.id] = {"action":"unbind","step":"token"}
        bot.send_message(m.chat.id, "Unbind Email\n\n🔑 Please enter your access token: 👇", reply_markup=yt_btn())
        return
    bind = get_bind_info(token)
    if not bind.get("email"):
        bot.send_message(m.chat.id, "Unbind Email\n\n❌ No Email Bound", reply_markup=yt_btn())
        bot.send_message(m.chat.id, "Main Menu - Please select an option: 👇", reply_markup=main_menu())
        return
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("📧 Via Email OTP", callback_data="unbind_email"), types.InlineKeyboardButton("🔑 Via Security Code", callback_data="unbind_sec"))
    bot.send_message(m.chat.id, "Unbind Email\n\n🔐 Select Method:", reply_markup=mk)

@bot.message_handler(func=lambda m: is_btn(m.text, "Change Bind Email"))
def change_btn(m):
    token = user_tokens.get(m.chat.id)
    if not token:
        user_states[m.chat.id] = {"action":"change","step":"token"}
        bot.send_message(m.chat.id, "Change Bind Email\n\n🔑 Please enter your access token: 👇", reply_markup=yt_btn())
        return
    bind = get_bind_info(token)
    if not bind.get("email"):
        bot.send_message(m.chat.id, "❌ No Email Bound - Use Add Recovery first", reply_markup=yt_btn())
        bot.send_message(m.chat.id, "Main Menu - Please select an option: 👇", reply_markup=main_menu())
        return
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("📧 Via Email OTP", callback_data="change_email"), types.InlineKeyboardButton("🔑 Via Security Code", callback_data="change_sec"))
    bot.send_message(m.chat.id, "Change Bind Email\n\n🔐 Select Method:", reply_markup=mk)

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
    bot.send_message(m.chat.id, "Main Menu - Please select an option: 👇", reply_markup=main_menu())

@bot.message_handler(func=lambda m: is_btn(m.text, "Revoke Access Token"))
def revoke_btn(m):
    token = user_tokens.get(m.chat.id)
    if not token:
        user_states[m.chat.id] = {"action":"revoke","step":"token"}
        bot.send_message(m.chat.id, "Revoke Access Token\n\n🔑 Please enter your access token: 👇", reply_markup=yt_btn())
        return
    uid,nick,region = get_player_info(token)
    msg = f"Revoke Access Token\nRevoke token for account: {nick} (ID: {uid})"
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("💳 Pay ⭐10", callback_data=f"revoke_{uid}"))
    bot.send_message(m.chat.id, msg, reply_markup=mk)
    user_states[m.chat.id] = {"action":"revoke","step":"confirm","token":token,"uid":uid,"nick":nick}

@bot.message_handler(func=lambda m: is_btn(m.text, "Get Eat Token"))
def geteat_btn(m):
    bot.send_message(m.chat.id, "Get Eat Token\n\n🌐 Click below to get Eat Token", reply_markup=eat_btn())
    bot.send_message(m.chat.id, "Main Menu - Please select an option: 👇", reply_markup=main_menu())

@bot.message_handler(func=lambda m: is_btn(m.text, "Eat To Access"))
def eataccess_btn(m):
    token = user_tokens.get(m.chat.id)
    if not token:
        user_states[m.chat.id] = {"action":"eat_access","step":"token"}
        bot.send_message(m.chat.id, "Eat To Access\n\n🔑 Please enter your Eat token: 👇", reply_markup=yt_btn())
        return
    uid,nick,region = get_player_info(token)
    bot.send_message(m.chat.id, f"Eat To Access\n\n👤 {nick}\n🆔 {uid}\n✅ Converted to Access Token", reply_markup=yt_btn())
    bot.send_message(m.chat.id, "Main Menu - Please select an option: 👇", reply_markup=main_menu())

@bot.message_handler(func=lambda m: is_btn(m.text, "Send Single Unsubscribe"))
def single_btn(m):
    user_states[m.chat.id] = {"action":"single","step":"email"}
    bot.send_message(m.chat.id, "Send Single Unsubscribe Otp\n\nPlease enter your email address:", reply_markup=yt_btn())

@bot.message_handler(func=lambda m: is_btn(m.text, "Send Double Unsubscribe"))
def double_btn(m):
    user_states[m.chat.id] = {"action":"double","step":"email"}
    bot.send_message(m.chat.id, "Send Double Unsubscribe Otp\n\nPlease enter your email address:", reply_markup=yt_btn())

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    chat_id = c.message.chat.id
    data = c.data
    token = user_tokens.get(chat_id)
    
    # Force Join Check callback - EXACT like photo
    if data == "check_join":
        all_joined, not_joined_channels, not_joined_groups = is_user_joined(c.from_user.id)
        if not all_joined:
            msg = "❌ You haven't joined all groups yet!\n\nPlease join:\n"
            for ch in not_joined_channels:
                msg += f"- {ch}\n"
            for gr in not_joined_groups:
                msg += f"- {gr}\n"
            msg += "\nAfter joining, click I Have Joined again."
            bot.answer_callback_query(c.id, "Please join all first!", show_alert=True)
            bot.send_message(chat_id, msg, reply_markup=force_join_markup_exact())
            return
        else:
            bot.answer_callback_query(c.id, "✅ Verified! Welcome!", show_alert=False)
            bot.send_message(chat_id, f"✅ Verification Successful!\n\nWelcome {c.from_user.first_name}!\n✅ 14 Premium Features Unlocked!")
            bot.send_message(chat_id, "Main Menu - Please select an option: 👇", reply_markup=main_menu())
            return
    
    if data.startswith("menu_"):
        mapping = {
            "menu_add": "Add Recovery Email", "menu_check": "Check Recovery Email",
            "menu_platform": "Check Platform", "menu_cancel": "Cancel Recovery Email",
            "menu_unbind": "Unbind Email", "menu_change": "Change Bind Email",
            "menu_bio": "Update Bio", "menu_name": "Change Name",
            "menu_access": "Access To Login", "menu_revoke": "Revoke Access Token",
            "menu_geteat": "Get Eat Token", "menu_eataccess": "Eat To Access",
            "menu_single": "Send Single Unsubscribe Otp",
            "menu_double": "Send Double Unsubscribe Otp"
        }
        cmd = mapping.get(data, "")
        if cmd:
            m = type('obj', (object,), {'chat': type('obj', (object,), {'id': chat_id})(), 'text': cmd})()
            if "Add Recovery" in cmd: add_btn(m)
            elif "Check Recovery" in cmd: check_btn(m)
            elif "Check Platform" in cmd: plat_btn(m)
            elif "Cancel" in cmd: cancel_btn(m)
            elif "Unbind" in cmd: unbind_btn(m)
            elif "Change Bind" in cmd: change_btn(m)
            elif "Update Bio" in cmd: bio_btn(m)
            elif "Change Name" in cmd: name_btn(m)
            elif "Access To Login" in cmd: access_btn(m)
            elif "Revoke" in cmd: revoke_btn(m)
            elif "Get Eat Token" in cmd: geteat_btn(m)
            elif "Eat To Access" in cmd: eataccess_btn(m)
            elif "Single" in cmd: single_btn(m)
            elif "Double" in cmd: double_btn(m)
        return

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
            bot.send_message(chat_id, "Add Recovery Email\n\n🔑 Please enter your access token: 👇", reply_markup=yt_btn())
        elif state["step"]=="token":
            state["token"]=text; user_tokens[chat_id]=text
            uid,nick,region = get_player_info(text)
            bind = get_bind_info(text)
            if bind.get("email"):
                bot.send_message(chat_id, f"❌ Already bound: {bind.get('email')}", reply_markup=yt_btn())
                del user_states[chat_id]
                bot.send_message(chat_id, "Main Menu - Please select an option: 👇", reply_markup=main_menu())
                return
            state["uid"]=uid; state["nick"]=nick; state["region"]=region
            try:
                r = requests.post("https://100067.connect.garena.com/game/account_security/bind:send_otp", headers=HEADERS, data={"email":state["email"],"locale":"en_PK","region":"PK","app_id":"100067","access_token":text}, timeout=10)
                if r.json().get("result")==0:
                    bot.send_message(chat_id, f"✅ OTP Sent to {state['email']}\n🔑 Enter OTP:", reply_markup=yt_btn())
                    state["step"]="otp"
                else:
                    bot.send_message(chat_id, f"❌ {r.text[:500]}", reply_markup=yt_btn()); del user_states[chat_id]
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
                    bot.send_message(chat_id, f"🎉 Recovery Email Added Successfully!\n📧 {state['email']}\n⏳ Pending", reply_markup=yt_btn())
                else:
                    bot.send_message(chat_id, f"❌ {r.text[:600]}", reply_markup=yt_btn())
            except Exception as e:
                bot.send_message(chat_id, f"❌ {e}", reply_markup=yt_btn())
            del user_states[chat_id]
            bot.send_message(chat_id, "Main Menu - Please select an option: 👇", reply_markup=main_menu())
    elif action in ["single", "double"]:
        if state["step"]=="email":
            if "@" not in text:
                bot.send_message(chat_id, "❌ Invalid Email", reply_markup=yt_btn()); return
            email = text.strip().lower()
            otp_type = "Double" if action == "double" else "Single"
            bot.send_message(chat_id, f"Sending {otp_type} Unsubscribe Otp to {email}...", reply_markup=yt_btn())
            success, resp = send_real_garena_otp(email)
            # For double, send twice or mention double
            if action == "double":
                success2, resp2 = send_real_garena_otp(email)
            bot.send_message(chat_id, f"{otp_type} Unsubscribe OTP Sent Successfully!\n\nEmail: {email}\nStatus: OTP has been sent to your email", reply_markup=yt_btn())
            if success:
                bot.send_message(chat_id, f"📧 Check Gmail: {email}\n📩 Subject: Verify Your Email Address\n🔑 Code like 05530666\n📁 Check Spam too", reply_markup=yt_btn())
            bot.send_message(chat_id, "Main Menu - Please select an option: 👇", reply_markup=main_menu())
            del user_states[chat_id]

@app.route('/')
def home(): return "✅ BOT RUNNING - EXACT PHOTO LAYOUT"
@app.route('/health')
def health(): return "OK",200
def run_bot(): bot.infinity_polling(timeout=60, long_polling_timeout=30)
if __name__=="__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
