
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import sys, json, time, urllib.parse, base64, hashlib, urllib3, requests, threading
from datetime import datetime
from flask import Flask
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import MajoRLogin_pb2 as mLpB
    import MajorLoginRes_pb2 as mLrPb
    PROTOBUF_AVAILABLE = True
except:
    PROTOBUF_AVAILABLE = False
    mLpB = None
    mLrPb = None

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.constants import ParseMode

try:
    from telegram.constants import KeyboardButtonStyle
    HAS_STYLE = True
except ImportError:
    HAS_STYLE = False
    class KeyboardButtonStyle:
        SUCCESS = "success"
        DANGER = "danger"
        PRIMARY = "primary"

BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN_HERE"

# ===== FORCE JOIN CONFIG - USER KE ACTUAL LINKS =====
FORCE_JOIN_CHATS = [
    {"name": "Zevric X Play", "username": "@zevricxplay", "invite_link": "https://t.me/zevricxplay"},
    {"name": "Zevric Illegal Vouch", "username": "@zevric_illigalvounch", "invite_link": "https://t.me/zevric_illigalvounch"},
    {"name": "Zevric Banner", "username": "@zevricbaner", "invite_link": "https://t.me/zevricbaner"},
    {"name": "Zevric All Update", "username": "@zevric_all_update", "invite_link": "https://t.me/zevric_all_update"},
    {"name": "Zevric API Tools", "username": "@zevric_api_tools", "invite_link": "https://t.me/zevric_api_tools"},
]
YOUTUBE_LINK = "https://youtube.com/@zevricxplay"

AeSkEy = b'Yg&tc%DEuh6%Zc^8'
AeSiV  = b'6oyZDr22E3ychjM%'
PLATFORM_MAP_FULL = {1: "Garena", 3: "Facebook", 4: "Guest", 5: "VK", 6: "Huawei", 7: "Apple", 8: "Google", 10: "GameCenter / Line", 11: "X (Twitter)", 13: "Apple ID", 28: "Line", 35: "TikTok"}
STATE_INPUT = 1

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    def enc(d: bytes) -> bytes: 
        return AES.new(AeSkEy, AES.MODE_CBC, AeSiV).encrypt(pad(d, 16))
    def dec(d: bytes) -> bytes: 
        return unpad(AES.new(AeSkEy, AES.MODE_CBC, AeSiV).decrypt(d), 16)
except:
    def enc(d): return d
    def dec(d): return d

def convert_seconds(s):
    try: s = int(s)
    except: return str(s)
    d, h = divmod(s, 86400)
    h, m = divmod(h, 3600)
    m, s = divmod(m, 60)
    return f"{d} Day {h} Hour {m} Min {s} Sec"

def fetch_player_info_sync(access_token):
    try:
        url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15, allow_redirects=True)
        parsed = urllib.parse.urlparse(r.url); qs = urllib.parse.parse_qs(parsed.query)
        return {"uid": qs.get("account_id", ["Unknown"])[0], "nickname": urllib.parse.unquote(qs.get("nickname", ["Unknown"])[0]), "region": qs.get("region", ["Unknown"])[0], "ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def fetch_bind_info_sync(access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        payload = {'app_id': "100067", 'access_token': access_token}
        r = requests.get(url, params=payload, headers={'User-Agent': "GarenaMSDK/4.0.19P9"}, timeout=15)
        if r.status_code == 200: return {"ok": True, "data": r.json()}
        else: return {"ok": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def send_otp_sync(email, access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "locale": "en_PK", "region": "PK", "app_id": "100067", "access_token": access_token}
        r = requests.post(url, headers=headers, data=data, timeout=20, verify=False)
        try: j = r.json()
        except: j = {"raw": r.text[:500]}
        if "captcha" in r.text.lower(): return {"ok": False, "captcha": True, "data": j}
        return {"ok": j.get("result") == 0, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def verify_otp_sync(email, access_token, otp):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "otp": otp, "app_id": "100067", "access_token": access_token}
        r = requests.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result")==0 and "verifier_token" in j, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def verify_identity_otp_sync(email, access_token, otp):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity_otp"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "otp": otp, "app_id": "100067", "access_token": access_token}
        r = requests.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result")==0 and "identity_token" in j, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def verify_identity_sec_sync(email, access_token, sec_code):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity_sec_code"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "sec_code": sec_code, "app_id": "100067", "access_token": access_token}
        r = requests.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result")==0 and "identity_token" in j, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_bind_request_sync(email, verifier_token, access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "verifier_token": verifier_token, "app_id": "100067", "access_token": access_token}
        r = requests.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result")==0, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_unbind_request_sync(identity_token, access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"identity_token": identity_token, "app_id": "100067", "access_token": access_token}
        r = requests.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result")==0, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_rebind_request_sync(identity_token, new_email, verifier_token, access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"identity_token": identity_token, "new_email": new_email, "verifier_token": verifier_token, "app_id": "100067", "access_token": access_token}
        r = requests.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result")==0, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def cancel_bind_request_sync(access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"app_id": "100067", "access_token": access_token}
        r = requests.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result")==0, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def eat_to_token_sync(eat):
    try:
        if "access_token=" in eat:
            parsed = urllib.parse.urlparse(eat); qs = urllib.parse.parse_qs(parsed.query)
            eat = qs.get("access_token", [eat])[0]
        url = f"https://100067.connect.garena.com/oauth/token/grant?grant_type=refresh_token&refresh_token={eat}&client_id=100067&client_secret=8ba7d83f1f3a0d1d5a0a5b7a1b5e7a0e5"
        r = requests.get(url, headers={"User-Agent": "GarenaMSDK/4.0.19P9"}, timeout=15)
        j = r.json()
        if "access_token" in j: return {"ok": True, "token": j["access_token"], "data": j}
        else: return {"ok": False, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def revoke_token_sync(access_token):
    try:
        url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10, allow_redirects=True)
        parsed = urllib.parse.urlparse(r.url); qs = urllib.parse.parse_qs(parsed.query)
        nickname = urllib.parse.unquote(qs.get('nickname',['Unknown'])[0]); account_id = qs.get('account_id',['Unknown'])[0]
        refresh_token = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
        logout_url = f"https://100067.connect.garena.com/oauth/logout?access_token={access_token}&refresh_token={refresh_token}"
        logout_res = requests.get(logout_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if logout_res.status_code==200 and "error" not in logout_res.text: return {"ok": True, "nickname": nickname, "account_id": account_id}
        else: return {"ok": False, "error": f"Revoke failed"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def fetch_platform_binds_sync(access_token):
    try:
        url = "https://100067.connect.garena.com/bind/app/platform/info/get"
        params = {"access_token": access_token}
        r = requests.get(url, params=params, headers={"User-Agent": "GarenaMSDK/4.0.19P9"}, timeout=10)
        if r.status_code!=200: return {"ok": False, "error": f"HTTP {r.status_code}"}
        d = r.json()
        return {"ok": True, "bounded": d.get("bounded_accounts",[]), "available": d.get("available_platforms",[])}
    except Exception as e:
        return {"ok": False, "error": str(e)}

async def check_user_joined_all(context, user_id):
    for chat in FORCE_JOIN_CHATS:
        try:
            member = await context.bot.get_chat_member(chat_id=chat["username"], user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception as e:
            print(f"Join check error for {chat['username']}: {e}")
            continue
    return True

def get_join_verification_keyboard():
    buttons = []
    for chat in FORCE_JOIN_CHATS:
        if HAS_STYLE:
            buttons.append([InlineKeyboardButton(text=f"Join {chat['name']}", url=chat["invite_link"], style=KeyboardButtonStyle.PRIMARY)])
        else:
            buttons.append([InlineKeyboardButton(text=f"Join {chat['name']}", url=chat["invite_link"])])
    if HAS_STYLE:
        buttons.append([InlineKeyboardButton(text="I Have Joined", callback_data="verify_joined", style=KeyboardButtonStyle.SUCCESS)])
    else:
        buttons.append([InlineKeyboardButton(text="I Have Joined", callback_data="verify_joined")])
    return InlineKeyboardMarkup(buttons)

def get_reply_keyboard():
    if HAS_STYLE:
        keyboard = [
            [KeyboardButton(text="1 CHECK BIND INFO", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="2 BIND EMAIL", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="3 UNBIND EMAIL", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="4 CHANGE BIND EMAIL", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="5 CANCEL BIND REQUEST", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="6 EAT TO ACCESS TOKEN", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="7 REVOKE ACCESS TOKEN", style=KeyboardButtonStyle.DANGER), KeyboardButton(text="8 GET LOGIN HISTORY", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="9 CHECK BOUND ACCOUNTS", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="10 OWNER DETAILS", style=KeyboardButtonStyle.PRIMARY)],
        ]
    else:
        keyboard = [
            ["1 CHECK BIND INFO", "2 BIND EMAIL"],
            ["3 UNBIND EMAIL", "4 CHANGE BIND EMAIL"],
            ["5 CANCEL BIND REQUEST", "6 EAT TO ACCESS TOKEN"],
            ["7 REVOKE ACCESS TOKEN", "8 GET LOGIN HISTORY"],
            ["9 CHECK BOUND ACCOUNTS", "10 OWNER DETAILS"],
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

def get_unbind_method_keyboard():
    if HAS_STYLE:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(text="Via Email OTP", callback_data="unbind_otp", style=KeyboardButtonStyle.SUCCESS), InlineKeyboardButton(text="Via Security Code", callback_data="unbind_sec", style=KeyboardButtonStyle.SUCCESS)],
            [InlineKeyboardButton(text="Back to Menu", callback_data="back_menu", style=KeyboardButtonStyle.DANGER)]
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(text="Via Email OTP", callback_data="unbind_otp"), InlineKeyboardButton(text="Via Security Code", callback_data="unbind_sec")],
            [InlineKeyboardButton(text="Back to Menu", callback_data="back_menu")]
        ])

def get_change_method_keyboard():
    if HAS_STYLE:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(text="Via Email OTP", callback_data="change_otp", style=KeyboardButtonStyle.SUCCESS), InlineKeyboardButton(text="Via Security Code", callback_data="change_sec", style=KeyboardButtonStyle.SUCCESS)],
            [InlineKeyboardButton(text="Back to Menu", callback_data="back_menu", style=KeyboardButtonStyle.DANGER)]
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(text="Via Email OTP", callback_data="change_otp"), InlineKeyboardButton(text="Via Security Code", callback_data="change_sec")],
            [InlineKeyboardButton(text="Back to Menu", callback_data="back_menu")]
        ])

def get_youtube_keyboard():
    if HAS_STYLE:
        return InlineKeyboardMarkup([[InlineKeyboardButton(text="Subscribe YouTube Channel", url=YOUTUBE_LINK, style=KeyboardButtonStyle.SUCCESS)]])
    else:
        return InlineKeyboardMarkup([[InlineKeyboardButton(text="Subscribe YouTube Channel", url=YOUTUBE_LINK)]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user_id = update.effective_user.id
    is_joined = await check_user_joined_all(context, user_id)
    if not is_joined:
        join_text = "Join Verification Required\n\nTo use this bot, you must join the following groups first:\n\n"
        for chat in FORCE_JOIN_CHATS:
            join_text += f"- {chat['name']}\n"
        join_text += "\nAfter joining, click the button below to verify:"
        await update.message.reply_text(join_text, reply_markup=get_join_verification_keyboard())
        return STATE_INPUT
    else:
        first_name = update.effective_user.first_name or "S"
        welcome = f"Welcome {first_name}!\n\nYou have successfully verified all groups!\n\nSelect an option from the menu below to get started:"
        await update.message.reply_text(welcome, reply_markup=get_youtube_keyboard())
        await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
        return STATE_INPUT

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_joined = await check_user_joined_all(context, user_id)
    if not is_joined:
        join_text = "Join Verification Required\n\nTo use this bot, you must join the following groups first:\n\n"
        for chat in FORCE_JOIN_CHATS:
            join_text += f"- {chat['name']}\n"
        join_text += "\nAfter joining, click the button below to verify:"
        await update.message.reply_text(join_text, reply_markup=get_join_verification_keyboard())
        return STATE_INPUT
    await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
    return STATE_INPUT

async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Cancelled.", reply_markup=get_reply_keyboard())
    return STATE_INPUT

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); data = query.data
    if data == "verify_joined":
        user_id = update.effective_user.id
        is_joined = await check_user_joined_all(context, user_id)
        if not is_joined:
            await query.answer("You haven't joined all groups! Please join all and try again.", show_alert=True)
            join_text = "Join Verification Required\n\nTo use this bot, you must join the following groups first:\n\n"
            for chat in FORCE_JOIN_CHATS:
                join_text += f"- {chat['name']}\n"
            join_text += "\nAfter joining, click the button below to verify:"
            await query.message.reply_text(join_text, reply_markup=get_join_verification_keyboard())
            return STATE_INPUT
        else:
            first_name = update.effective_user.first_name or "S"
            welcome = f"Welcome {first_name}!\n\nYou have successfully verified all groups!\n\nSelect an option from the menu below to get started:"
            await query.message.reply_text(welcome, reply_markup=get_youtube_keyboard())
            await query.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
            return STATE_INPUT
    if data == "back_menu":
        context.user_data.clear()
        await query.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
        return STATE_INPUT
    if data in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]:
        mapping = {"1": "1 CHECK BIND INFO", "2": "2 BIND EMAIL", "3": "3 UNBIND EMAIL", "4": "4 CHANGE BIND EMAIL", "5": "5 CANCEL BIND REQUEST", "6": "6 EAT TO ACCESS TOKEN", "7": "7 REVOKE ACCESS TOKEN", "8": "8 GET LOGIN HISTORY", "9": "9 CHECK BOUND ACCOUNTS", "10": "10 OWNER DETAILS"}
        clean_text = mapping[data]
        if clean_text == "1 CHECK BIND INFO":
            context.user_data.clear(); context.user_data['flow'] = 'bind_info'; context.user_data['step'] = 'token'
            await query.message.reply_text("CHECK BIND INFO\n\nEnter Access Token:")
            return STATE_INPUT
        if clean_text == "2 BIND EMAIL":
            context.user_data.clear(); context.user_data['flow'] = 'bind_email'; context.user_data['step'] = 'token'
            await query.message.reply_text("BIND EMAIL\n\nEnter Access Token:")
            return STATE_INPUT
        if clean_text == "3 UNBIND EMAIL":
            context.user_data.clear(); context.user_data['flow'] = 'unbind'
            await query.message.reply_text("Change Bind Email - Select Method:", reply_markup=get_unbind_method_keyboard())
            return STATE_INPUT
        if clean_text == "4 CHANGE BIND EMAIL":
            context.user_data.clear(); context.user_data['flow'] = 'change'
            await query.message.reply_text("Change Bind Email - Select Method:", reply_markup=get_change_method_keyboard())
            return STATE_INPUT
        if clean_text == "5 CANCEL BIND REQUEST":
            context.user_data.clear(); context.user_data['flow'] = 'cancel_req'; context.user_data['step'] = 'token'
            await query.message.reply_text("CANCEL BIND REQUEST\n\nEnter Access Token:")
            return STATE_INPUT
        if clean_text == "6 EAT TO ACCESS TOKEN":
            context.user_data.clear(); context.user_data['flow'] = 'eat_token'; context.user_data['step'] = 'token'
            await query.message.reply_text("EAT TO ACCESS TOKEN\n\nEnter EAT Token:")
            return STATE_INPUT
        if clean_text == "7 REVOKE ACCESS TOKEN":
            context.user_data.clear(); context.user_data['flow'] = 'revoke'; context.user_data['step'] = 'token'
            await query.message.reply_text("REVOKE ACCESS TOKEN\n\nEnter Access Token to revoke:")
            return STATE_INPUT
        if clean_text == "8 GET LOGIN HISTORY":
            context.user_data.clear(); context.user_data['flow'] = 'login_history'; context.user_data['step'] = 'token'
            await query.message.reply_text("GET LOGIN HISTORY\n\nEnter Access Token or JWT Token:")
            return STATE_INPUT
        if clean_text == "9 CHECK BOUND ACCOUNTS":
            context.user_data.clear(); context.user_data['flow'] = 'bound_accounts'; context.user_data['step'] = 'token'
            await query.message.reply_text("CHECK BOUND ACCOUNTS\n\nEnter Access Token:")
            return STATE_INPUT
        if clean_text == "10 OWNER DETAILS":
            owner_text = "ZEVRIC Bind Tool - OWNER DETAILS\n\nOWNER : ZEVRIC\nTELEGRAM : @just_zevric\nSTATUS : SAFE & SECURE\n\nPowered by ZEVRIC"
            await query.message.reply_text(owner_text, reply_markup=get_reply_keyboard())
            return STATE_INPUT
    if data.startswith("unbind_"):
        method = data.split("_")[1]; context.user_data['method'] = method; context.user_data['flow'] = 'unbind'; context.user_data['step'] = 'token'
        await query.message.reply_text(f"Change via Via Email OTP\n\nPlease enter your access token:" if method=='otp' else "Change via Via Security Code\n\nPlease enter your access token:")
        return STATE_INPUT
    if data.startswith("change_"):
        method = data.split("_")[1]; context.user_data['method'] = method; context.user_data['flow'] = 'change'; context.user_data['step'] = 'token'
        await query.message.reply_text(f"Change via Via Email OTP\n\nPlease enter your access token:" if method=='otp' else "Change via Via Security Code\n\nPlease enter your access token:")
        return STATE_INPUT
    return STATE_INPUT

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_joined = await check_user_joined_all(context, user_id)
    if not is_joined:
        join_text = "Join Verification Required\n\nTo use this bot, you must join the following groups first:\n\n"
        for chat in FORCE_JOIN_CHATS:
            join_text += f"- {chat['name']}\n"
        join_text += "\nAfter joining, click the button below to verify:"
        await update.message.reply_text(join_text, reply_markup=get_join_verification_keyboard())
        return STATE_INPUT
    text = update.message.text.strip()
    clean_text = text
    flow = context.user_data.get('flow'); step = context.user_data.get('step')
    if clean_text in ["1 CHECK BIND INFO", "CHECK BIND INFO", "1"]:
        context.user_data.clear(); context.user_data['flow'] = 'bind_info'; context.user_data['step'] = 'token'
        await update.message.reply_text("CHECK BIND INFO\n\nEnter Access Token:")
        return STATE_INPUT
    if clean_text in ["2 BIND EMAIL", "BIND EMAIL", "2"]:
        context.user_data.clear(); context.user_data['flow'] = 'bind_email'; context.user_data['step'] = 'token'
        await update.message.reply_text("BIND EMAIL\n\nEnter Access Token:")
        return STATE_INPUT
    if clean_text in ["3 UNBIND EMAIL", "UNBIND EMAIL", "3"]:
        context.user_data.clear(); context.user_data['flow'] = 'unbind'
        await update.message.reply_text("Change Bind Email - Select Method:", reply_markup=get_unbind_method_keyboard())
        return STATE_INPUT
    if clean_text in ["4 CHANGE BIND EMAIL", "CHANGE BIND EMAIL", "4"]:
        context.user_data.clear(); context.user_data['flow'] = 'change'
        await update.message.reply_text("Change Bind Email - Select Method:", reply_markup=get_change_method_keyboard())
        return STATE_INPUT
    if clean_text in ["5 CANCEL BIND REQUEST", "CANCEL BIND REQUEST", "5"]:
        context.user_data.clear(); context.user_data['flow'] = 'cancel_req'; context.user_data['step'] = 'token'
        await update.message.reply_text("CANCEL BIND REQUEST\n\nEnter Access Token:")
        return STATE_INPUT
    if clean_text in ["6 EAT TO ACCESS TOKEN", "EAT TO ACCESS TOKEN", "6"]:
        context.user_data.clear(); context.user_data['flow'] = 'eat_token'; context.user_data['step'] = 'token'
        await update.message.reply_text("EAT TO ACCESS TOKEN\n\nEnter EAT Token:")
        return STATE_INPUT
    if clean_text in ["7 REVOKE ACCESS TOKEN", "REVOKE ACCESS TOKEN", "7"]:
        context.user_data.clear(); context.user_data['flow'] = 'revoke'; context.user_data['step'] = 'token'
        await update.message.reply_text("REVOKE ACCESS TOKEN\n\nEnter Access Token to revoke:")
        return STATE_INPUT
    if clean_text in ["8 GET LOGIN HISTORY", "GET LOGIN HISTORY", "8"]:
        context.user_data.clear(); context.user_data['flow'] = 'login_history'; context.user_data['step'] = 'token'
        await update.message.reply_text("GET LOGIN HISTORY\n\nEnter Access Token or JWT Token:")
        return STATE_INPUT
    if clean_text in ["9 CHECK BOUND ACCOUNTS", "CHECK BOUND ACCOUNTS", "9"]:
        context.user_data.clear(); context.user_data['flow'] = 'bound_accounts'; context.user_data['step'] = 'token'
        await update.message.reply_text("CHECK BOUND ACCOUNTS\n\nEnter Access Token:")
        return STATE_INPUT
    if clean_text in ["10 OWNER DETAILS", "OWNER DETAILS", "10"]:
        owner_text = "ZEVRIC Bind Tool - OWNER DETAILS\n\nOWNER : ZEVRIC\nTELEGRAM : @just_zevric\nSTATUS : SAFE & SECURE\n\nPowered by ZEVRIC"
        await update.message.reply_text(owner_text, reply_markup=get_reply_keyboard())
        return STATE_INPUT
    if not flow:
        await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
        return STATE_INPUT
    if flow == 'bind_info':
        if step == 'token':
            await update.message.reply_text("Checking Platform...")
            player = fetch_player_info_sync(text); bind = fetch_bind_info_sync(text)
            if not bind['ok']:
                await update.message.reply_text(f"Error: {bind['error']}", reply_markup=get_reply_keyboard()); context.user_data.clear(); return STATE_INPUT
            d = bind['data']; email = d.get("email",""); email_to_be = d.get("email_to_be",""); countdown = d.get("request_exec_countdown",0)
            p_text = f"UID: {player['uid']} | {player['nickname']} | {player['region']}\n\n" if player['ok'] else ""
            b_text = f"{p_text}Current: {email or 'None'}\nPending: {email_to_be or 'None'}\nCountdown: {convert_seconds(countdown) if email_to_be else 'N/A'}"
            await update.message.reply_text(b_text, reply_markup=get_reply_keyboard()); context.user_data.clear(); return STATE_INPUT
    if flow == 'bind_email':
        if step == 'token':
            context.user_data['token'] = text; await update.message.reply_text("Checking...")
            bind = fetch_bind_info_sync(text)
            if bind['ok']: d = bind['data']; await update.message.reply_text(f"Current: {d.get('email') or 'None'}\n\nNew Email bhejo:")
            else: await update.message.reply_text("Token doubt me. New Email bhejo:")
            context.user_data['step'] = 'email'; return STATE_INPUT
        if step == 'email':
            context.user_data['email'] = text; await update.message.reply_text(f"OTP bhej raha {text} pe..."); res = send_otp_sync(text, context.user_data['token'])
            if res['ok']: await update.message.reply_text("OTP Sent! OTP bhejo:"); context.user_data['step'] = 'otp'
            else:
                if res.get('captcha'): await update.message.reply_text("Captcha Block! Via Sec Code use karo.", reply_markup=get_reply_keyboard()); context.user_data.clear()
                else: await update.message.reply_text(f"OTP fail: {res.get('data')}")
            return STATE_INPUT
        if step == 'otp':
            await update.message.reply_text("Verifying..."); res = verify_otp_sync(context.user_data['email'], context.user_data['token'], text)
            if res['ok'] and res['data'].get('verifier_token'):
                v_token = res['data']['verifier_token']; await update.message.reply_text("Verified! Bind bana raha...")
                bind_req = create_bind_request_sync(context.user_data['email'], v_token, context.user_data['token'])
                if bind_req['ok']: await update.message.reply_text("BIND SUCCESS", reply_markup=get_reply_keyboard())
                else: await update.message.reply_text(f"Fail: {bind_req['data']}", reply_markup=get_reply_keyboard())
                context.user_data.clear()
            else: await update.message.reply_text(f"Verify fail: {res.get('data')}")
            return STATE_INPUT
    if flow == 'bound_accounts':
        if step == 'token':
            await update.message.reply_text("Checking Platform...")
            res = fetch_platform_binds_sync(text)
            if not res['ok']: await update.message.reply_text(f"{res['error']}", reply_markup=get_reply_keyboard()); context.user_data.clear(); return STATE_INPUT
            bounded = res['bounded']; b_text = "Bound: " + (", ".join([PLATFORM_MAP_FULL.get(pid, str(pid)) for pid in bounded]) if bounded else "None")
            await update.message.reply_text(b_text, reply_markup=get_reply_keyboard()); context.user_data.clear(); return STATE_INPUT
    if flow == 'cancel_req':
        if step == 'token':
            await update.message.reply_text("Cancelling..."); res = cancel_bind_request_sync(text)
            if res['ok']: await update.message.reply_text("CANCEL SUCCESS", reply_markup=get_reply_keyboard())
            else: await update.message.reply_text(f"Fail: {res['data']}", reply_markup=get_reply_keyboard())
            context.user_data.clear(); return STATE_INPUT
    if flow == 'eat_token':
        if step == 'token':
            await update.message.reply_text("Converting..."); res = eat_to_token_sync(text)
            if res['ok']: await update.message.reply_text(f"Token:\n{res['token']}", reply_markup=get_reply_keyboard())
            else: await update.message.reply_text(f"Fail: {res['data']}", reply_markup=get_reply_keyboard())
            context.user_data.clear(); return STATE_INPUT
    if flow == 'revoke':
        if step == 'token':
            await update.message.reply_text("Revoking..."); res = revoke_token_sync(text)
            if res['ok']: await update.message.reply_text("REVOKE SUCCESS", reply_markup=get_reply_keyboard())
            else: await update.message.reply_text(f"Fail: {res['error']}", reply_markup=get_reply_keyboard())
            context.user_data.clear(); return STATE_INPUT
    if flow == 'unbind':
        method = context.user_data.get('method')
        if step == 'token':
            context.user_data['token'] = text; bind = fetch_bind_info_sync(text)
            if not bind['ok'] or not bind['data'].get('email'): await update.message.reply_text("No bound email", reply_markup=get_reply_keyboard()); context.user_data.clear(); return STATE_INPUT
            email = bind['data'].get('email'); context.user_data['email'] = email
            if method == 'otp':
                await update.message.reply_text(f"Current: {email}\nOTP bhej raha..."); res = send_otp_sync(email, text)
                if res['ok']: await update.message.reply_text(f"OTP sent to {email}\nOTP bhejo:"); context.user_data['step'] = 'otp'
                else:
                    if res.get('captcha'): await update.message.reply_text("Captcha! Via Sec Code use karo - 100% working!", reply_markup=get_reply_keyboard()); context.user_data.clear()
                    else: await update.message.reply_text(f"OTP fail", reply_markup=get_reply_keyboard()); context.user_data.clear()
            else: await update.message.reply_text("6-digit Sec Code bhejo:"); context.user_data['step'] = 'sec_code'
            return STATE_INPUT
        if step == 'otp':
            await update.message.reply_text("Verifying..."); res = verify_identity_otp_sync(context.user_data['email'], context.user_data['token'], text)
            if res['ok']:
                id_token = res['data'].get('identity_token'); unr = create_unbind_request_sync(id_token, context.user_data['token'])
                if unr['ok']: await update.message.reply_text("UNBIND SUCCESS", reply_markup=get_reply_keyboard())
                else: await update.message.reply_text(f"Fail", reply_markup=get_reply_keyboard())
                context.user_data.clear()
            else: await update.message.reply_text(f"Verify fail")
            return STATE_INPUT
        if step == 'sec_code':
            await update.message.reply_text("Verifying via Sec Code..."); res = verify_identity_sec_sync(context.user_data['email'], context.user_data['token'], text)
            if res['ok']:
                id_token = res['data'].get('identity_token'); unr = create_unbind_request_sync(id_token, context.user_data['token'])
                if unr['ok']: await update.message.reply_text("UNBIND SUCCESS via Sec Code!", reply_markup=get_reply_keyboard())
                else: await update.message.reply_text(f"Fail", reply_markup=get_reply_keyboard())
                context.user_data.clear()
            else: await update.message.reply_text(f"Verify fail")
            return STATE_INPUT
    if flow == 'change':
        method = context.user_data.get('method')
        if step == 'token':
            context.user_data['token'] = text; bind = fetch_bind_info_sync(text)
            if not bind['ok'] or not bind['data'].get('email'): await update.message.reply_text("No bound email", reply_markup=get_reply_keyboard()); context.user_data.clear(); return STATE_INPUT
            old_email = bind['data'].get('email'); context.user_data['old_email'] = old_email
            if method == 'otp':
                await update.message.reply_text(f"OTP bhej raha {old_email} pe..."); res = send_otp_sync(old_email, text)
                if res['ok']: await update.message.reply_text("OTP sent! Old OTP bhejo:"); context.user_data['step'] = 'old_otp'
                else:
                    if res.get('captcha'): await update.message.reply_text("Captcha! Via Sec Code use karo!", reply_markup=get_reply_keyboard()); context.user_data.clear()
                    else: await update.message.reply_text(f"OTP fail", reply_markup=get_reply_keyboard()); context.user_data.clear()
            else: await update.message.reply_text("Sec Code bhejo (old email ke liye):"); context.user_data['step'] = 'sec_code'
            return STATE_INPUT
        if step == 'sec_code':
            await update.message.reply_text("Verifying..."); res = verify_identity_sec_sync(context.user_data['old_email'], context.user_data['token'], text)
            if res['ok']: context.user_data['identity_token'] = res['data'].get('identity_token'); await update.message.reply_text("Verified! New Email bhejo:"); context.user_data['step'] = 'new_email'
            else: await update.message.reply_text(f"Verify fail")
            return STATE_INPUT
        if step == 'old_otp':
            await update.message.reply_text("Verifying..."); res = verify_identity_otp_sync(context.user_data['old_email'], context.user_data['token'], text)
            if res['ok']: context.user_data['identity_token'] = res['data'].get('identity_token'); await update.message.reply_text("Verified! New Email bhejo:"); context.user_data['step'] = 'new_email'
            else: await update.message.reply_text(f"Verify fail")
            return STATE_INPUT
        if step == 'new_email':
            context.user_data['new_email'] = text; await update.message.reply_text(f"OTP bhej raha {text} pe..."); res = send_otp_sync(text, context.user_data['token'])
            if res['ok']: await update.message.reply_text(f"OTP sent to {text}\nNew OTP bhejo:"); context.user_data['step'] = 'new_otp'
            else: await update.message.reply_text(f"OTP fail", reply_markup=get_reply_keyboard()); context.user_data.clear()
            return STATE_INPUT
        if step == 'new_otp':
            await update.message.reply_text("Verifying..."); res = verify_otp_sync(context.user_data['new_email'], context.user_data['token'], text)
            if res['ok'] and res['data'].get('verifier_token'):
                context.user_data['verifier_token'] = res['data'].get('verifier_token'); await update.message.reply_text("Rebind bana raha...")
                rebind = create_rebind_request_sync(context.user_data['identity_token'], context.user_data['new_email'], context.user_data['verifier_token'], context.user_data['token'])
                if rebind['ok']: await update.message.reply_text("CHANGE SUCCESS", reply_markup=get_reply_keyboard())
                else: await update.message.reply_text(f"Fail", reply_markup=get_reply_keyboard())
                context.user_data.clear()
            else: await update.message.reply_text(f"Verify fail")
            return STATE_INPUT
    await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard()); return STATE_INPUT

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot Running - ZEVRIC OWNER - JOIN VERIFICATION - TRUE GREEN"
@flask_app.route('/health')
def health(): return "OK"
app = flask_app

def run_bot():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("BOT_TOKEN not set!")
        return
    import asyncio
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    except: pass
    application = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("menu", menu_cmd), MessageHandler(filters.Regex("^(1 CHECK BIND INFO|2 BIND EMAIL|3 UNBIND EMAIL|4 CHANGE BIND EMAIL|5 CANCEL BIND REQUEST|6 EAT TO ACCESS TOKEN|7 REVOKE ACCESS TOKEN|8 GET LOGIN HISTORY|9 CHECK BOUND ACCOUNTS|10 OWNER DETAILS)$"), handle_text)],
        states={STATE_INPUT: [CallbackQueryHandler(handle_callback), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)]},
        fallbacks=[CommandHandler("cancel", cancel_cmd), CommandHandler("start", start)], allow_reentry=True, per_message=False
    )
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("cancel", cancel_cmd))
    print("Bot starting with ZEVRIC OWNER...")
    try:
        application.run_polling(close_loop=False)
    except Exception as e:
        print(f"run_polling failed: {e}")
        try:
            loop.run_until_complete(application.initialize())
            loop.run_until_complete(application.start())
            loop.run_until_complete(application.updater.start_polling())
            loop.run_forever()
        except Exception as e2:
            print(f"Fallback failed: {e2}")

def _auto_start_bot():
    if BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
        try:
            t = threading.Thread(target=run_bot, daemon=True)
            t.start()
            print("Bot thread auto-started")
        except Exception as e:
            print(f"Failed: {e}")

if os.getenv("PORT") or os.getenv("RENDER"):
    _auto_start_bot()

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)
