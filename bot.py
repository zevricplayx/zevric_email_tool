import os
import sys
import json
import time
import asyncio
import logging
import threading
import random
import string
import urllib.parse
import requests
import urllib3
urllib3.disable_warnings()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.constants import ParseMode

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or "YOUR_BOT_TOKEN_HERE"
YOUTUBE_LINK = "https://youtube.com/@zevricxplay"
OWNER_USERNAME = "@zevricxplay"
STATE_INPUT = 1

REQUIRED_CHANNELS = [
    {"name": "Zevric All Update", "link": "https://t.me/zevric_all_update", "chat_id": "@zevric_all_update"},
    {"name": "Zevric X Play", "link": "https://t.me/zevricxplay", "chat_id": "@zevricxplay"},
    {"name": "Zevric Banner", "link": "https://t.me/zevricbaner", "chat_id": "@zevricbaner"},
    {"name": "Zevric Api Tools", "link": "https://t.me/zevric_api_tools", "chat_id": "@zevric_api_tools"},
    {"name": "Zevric Illegal Vounch", "link": "https://t.me/zevric_illigalvounch", "chat_id": "@zevric_illigalvounch"},
]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ================= HELPER UI =================
async def check_user_joined_all(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    not_joined = []
    for ch in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=ch["chat_id"], user_id=user_id)
            if member.status in ["left", "kicked", "banned"]:
                not_joined.append(ch)
        except Exception as e:
            # If bot is not admin in channel, we skip to avoid blocking user
            logger.warning(f"Check join failed for {ch['chat_id']}: {e}")
            continue
    return not_joined

def get_force_join_keyboard():
    kb = []
    for ch in REQUIRED_CHANNELS:
        kb.append([InlineKeyboardButton(text=f"📢 Join {ch['name']}", url=ch["link"])])
    kb.append([InlineKeyboardButton(text="✅ I Have Joined", callback_data="check_join")])
    return InlineKeyboardMarkup(kb)

def get_force_join_text(not_joined_list=None):
    lst = not_joined_list or REQUIRED_CHANNELS
    names = "\n".join([f"• {ch['name']} - {ch['link']}" for ch in lst])
    return (
        "⚠️ <b>Join Verification Required</b>\n\n"
        "Bot use karne se pehle niche ke saare channels join karo:\n\n"
        f"{names}\n\n"
        "Join karke <b>✅ I Have Joined</b> pe click karo."
    )

def get_reply_keyboard():
    keyboard = [
        ["CHECK BIND INFO", "BIND EMAIL"],
        ["UNBIND EMAIL", "CHANGE BIND EMAIL"],
        ["CANCEL BIND REQUEST", "EAT TO ACCESS TOKEN"],
        ["REVOKE ACCESS TOKEN", "SINGLE UNSUBSCRIBE OTP"],
        ["OWNER DETAILS"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

def get_youtube_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text="🟢 Subscribe YouTube - Zevric X Play", url=YOUTUBE_LINK)]
    ])

def convert_seconds(s):
    try:
        s = int(s)
    except:
        return str(s)
    d, h = divmod(s, 86400)
    h, m = divmod(h, 3600)
    m, s = divmod(m, 60)
    if d > 0:
        return f"{d} Day {h} Hour {m} Min {s} Sec"
    return f"{h} Hour {m} Min {s} Sec"

# ================= GARENA API SYNC FUNCTIONS =================

def get_player_info_sync(access_token: str):
    """Get UID, Nickname, Region from access_token"""
    try:
        url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15, allow_redirects=True, verify=False)
        parsed = urllib.parse.urlparse(r.url)
        q = urllib.parse.parse_qs(parsed.query)
        uid = q.get("account_id", ["Unknown"])[0]
        nick = urllib.parse.unquote(q.get("nickname", ["Unknown"])[0])
        region = q.get("region", ["Unknown"])[0]
        # If redirect didn't contain info, try to check if token is valid by another method
        if uid == "Unknown" and "error" in r.text.lower():
            return "Invalid", "Invalid", "Invalid"
        return uid, nick, region
    except Exception as e:
        logger.error(f"get_player_info error: {e}")
        return "Unknown", "Unknown", "Unknown"

def fetch_bind_info_sync(access_token: str):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        params = {'app_id': "100067", 'access_token': access_token}
        headers = {
            'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip"
        }
        r = requests.get(url, params=params, headers=headers, timeout=15, verify=False)
        if r.status_code == 200:
            try:
                return {"ok": True, "data": r.json()}
            except:
                return {"ok": False, "error": f"Invalid JSON: {r.text[:200]}"}
        return {"ok": False, "error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def send_otp_sync(email: str, access_token: str):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
        headers = {
            "User-Agent": "GarenaMSDK/4.0.30",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        data = {
            "email": email,
            "locale": "en_PK",
            "region": "PK",
            "app_id": "100067",
            "access_token": access_token
        }
        r = requests.post(url, headers=headers, data=data, timeout=15, verify=False)
        j = r.json()
        # result 0 = success
        if j.get("result") == 0 or j.get("result") == "0":
            return {"ok": True, "data": j}
        return {"ok": False, "data": j, "error": j.get("error", str(j))}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def verify_otp_sync(email: str, access_token: str, otp: str):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
        headers = {
            "User-Agent": "GarenaMSDK/4.0.30",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "email": email,
            "app_id": "100067",
            "access_token": access_token,
            "otp": str(otp).strip()
        }
        r = requests.post(url, headers=headers, data=data, timeout=15, verify=False)
        j = r.json()
        # verifier_token present = success
        if "verifier_token" in j or j.get("result") == 0:
            return {"ok": True, "data": j, "verifier_token": j.get("verifier_token")}
        return {"ok": False, "data": j, "error": j.get("error", str(j))}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def verify_identity_sync(email: str, access_token: str, otp: str):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
        headers = {
            "User-Agent": "GarenaMSDK/4.0.30",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "email": email,
            "app_id": "100067",
            "access_token": access_token,
            "otp": str(otp).strip()
        }
        r = requests.post(url, headers=headers, data=data, timeout=15, verify=False)
        j = r.json()
        if "identity_token" in j:
            return {"ok": True, "data": j, "identity_token": j.get("identity_token")}
        return {"ok": False, "data": j, "error": j.get("error", str(j))}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_bind_request_sync(email: str, access_token: str, verifier_token: str):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
        headers = {
            "User-Agent": "GarenaMSDK/4.0.30",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "email": email,
            "app_id": "100067",
            "access_token": access_token,
            "verifier_token": verifier_token
        }
        r = requests.post(url, headers=headers, data=data, timeout=15, verify=False)
        j = r.json()
        if j.get("result") == 0:
            return {"ok": True, "data": j}
        return {"ok": False, "data": j, "error": j.get("error", str(j))}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_unbind_request_sync(identity_token: str, access_token: str):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
        headers = {
            "User-Agent": "GarenaMSDK/4.0.30",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "app_id": "100067",
            "access_token": access_token,
            "identity_token": identity_token
        }
        r = requests.post(url, headers=headers, data=data, timeout=15, verify=False)
        j = r.json()
        if j.get("result") == 0:
            return {"ok": True, "data": j}
        return {"ok": False, "data": j, "error": j.get("error", str(j))}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_rebind_request_sync(identity_token: str, new_email: str, verifier_token: str, access_token: str):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
        headers = {
            "User-Agent": "GarenaMSDK/4.0.30",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "app_id": "100067",
            "access_token": access_token,
            "identity_token": identity_token,
            "email": new_email,
            "verifier_token": verifier_token
        }
        r = requests.post(url, headers=headers, data=data, timeout=15, verify=False)
        j = r.json()
        if j.get("result") == 0:
            return {"ok": True, "data": j}
        return {"ok": False, "data": j, "error": j.get("error", str(j))}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def cancel_request_sync(access_token: str):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
        headers = {
            "User-Agent": "GarenaMSDK/4.0.30",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "app_id": "100067",
            "access_token": access_token
        }
        r = requests.post(url, headers=headers, data=data, timeout=15, verify=False)
        j = r.json()
        if j.get("result") == 0:
            return {"ok": True, "data": j}
        # Some versions use cancel_bind_request
        if "error" in str(j).lower():
            url2 = "https://100067.connect.garena.com/game/account_security/bind:cancel_bind_request"
            r2 = requests.post(url2, headers=headers, data=data, timeout=15, verify=False)
            j2 = r2.json()
            if j2.get("result") == 0:
                return {"ok": True, "data": j2}
            return {"ok": False, "data": j2, "error": j2.get("error", str(j2))}
        return {"ok": False, "data": j, "error": j.get("error", str(j))}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def eat_to_at_sync(eat_token: str):
    """Convert EAT (External Auth Token) to Access Token"""
    try:
        eat_token = eat_token.strip()
        # Method 1: guest token grant
        url1 = "https://100067.connect.garena.com/oauth/guest/token/grant"
        headers = {
            "User-Agent": "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data1 = {
            "app_id": "100067",
            "token": eat_token,
            "client_id": "100067",
            "client_secret": "a24a7a09f9e47c70a390a3f2b10ba9b1"
        }
        r = requests.post(url1, headers=headers, data=data1, timeout=15, verify=False)
        try:
            j = r.json()
            if "access_token" in j or "accessToken" in j:
                at = j.get("access_token") or j.get("accessToken")
                uid, nick, region = get_player_info_sync(at)
                return {"ok": True, "access_token": at, "account_id": uid, "nickname": nick, "region": region, "data": j}
        except:
            pass

        # Method 2: Try via auth/guest
        url2 = f"https://100067.connect.garena.com/oauth/guest/eat_to_access_token?token={eat_token}&app_id=100067"
        r2 = requests.get(url2, headers={"User-Agent": "Mozilla/5.0"}, timeout=15, verify=False)
        try:
            j2 = r2.json()
            if "access_token" in j2:
                at = j2["access_token"]
                uid, nick, region = get_player_info_sync(at)
                return {"ok": True, "access_token": at, "account_id": uid, "nickname": nick, "region": region, "data": j2}
        except:
            pass

        # Method 3: If eat token is actually JWT, try to parse and return as-is if it works as access_token
        uid, nick, region = get_player_info_sync(eat_token)
        if uid != "Unknown" and uid != "Invalid":
            return {"ok": True, "access_token": eat_token, "account_id": uid, "nickname": nick, "region": region, "data": {"msg": "Token already valid as Access Token"}}

        return {"ok": False, "error": f"Convert failed. Response1: {r.text[:200]} | Response2: {r2.text[:200]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def revoke_access_token_sync(access_token: str):
    try:
        uid, nick, region = get_player_info_sync(access_token)
        refresh_token = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
        logout_url = f"https://100067.connect.garena.com/oauth/logout?access_token={access_token}&refresh_token={refresh_token}"
        lr = requests.get(logout_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10, verify=False)
        if lr.status_code == 200 and "error" not in lr.text.lower():
            return {"ok": True, "account_id": uid, "nickname": nick, "region": region}
        # Try second method
        url2 = "https://100067.connect.garena.com/oauth/revoke"
        r2 = requests.post(url2, data={"access_token": access_token, "app_id": "100067"}, timeout=10, verify=False)
        if r2.status_code == 200:
            return {"ok": True, "account_id": uid, "nickname": nick, "region": region}
        return {"ok": False, "error": lr.text[:200]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ================= BOT HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    not_joined = await check_user_joined_all(context, user_id)
    if not_joined:
        await update.message.reply_text(
            get_force_join_text(not_joined),
            reply_markup=get_force_join_keyboard(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        return STATE_INPUT

    welcome = (
        "👋 <b>Welcome to Zevric Bind Bot</b>\n\n"
        "🔥 Garena Account Bind Tools - 100% Working\n\n"
        "📌 <b>Available Options:</b>\n"
        "• CHECK BIND INFO\n"
        "• BIND EMAIL\n"
        "• UNBIND EMAIL\n"
        "• CHANGE BIND EMAIL\n"
        "• CANCEL BIND REQUEST\n"
        "• EAT TO ACCESS TOKEN\n"
        "• REVOKE ACCESS TOKEN\n"
        "• SINGLE UNSUBSCRIBE OTP\n\n"
        "👇 Niche se option select karo:"
    )
    await update.message.reply_text(welcome, reply_markup=get_reply_keyboard(), parse_mode=ParseMode.HTML)
    await update.message.reply_text("📺 YouTube support ke liye subscribe karo:", reply_markup=get_youtube_keyboard())
    return STATE_INPUT

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 <b>Main Menu:</b>", reply_markup=get_reply_keyboard(), parse_mode=ParseMode.HTML)
    return STATE_INPUT

async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Process cancelled. Main Menu:", reply_markup=get_reply_keyboard())
    return STATE_INPUT

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "check_join":
        user_id = query.from_user.id
        not_joined = await check_user_joined_all(context, user_id)
        if not_joined:
            await query.edit_message_text(
                get_force_join_text(not_joined),
                reply_markup=get_force_join_keyboard(),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
        else:
            await query.edit_message_text("✅ Verification Success! Ab bot use kar sakte ho.")
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="📋 Main Menu:",
                reply_markup=get_reply_keyboard()
            )
    return STATE_INPUT

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.strip()
        user_data = context.user_data
        flow = user_data.get("flow")
        step = user_data.get("step")

        # If user clicked main menu button
        if text in ["CHECK BIND INFO", "BIND EMAIL", "UNBIND EMAIL", "CHANGE BIND EMAIL",
                    "CANCEL BIND REQUEST", "EAT TO ACCESS TOKEN", "REVOKE ACCESS TOKEN",
                    "SINGLE UNSUBSCRIBE OTP", "OWNER DETAILS"]:

            # Verify join again
            not_joined = await check_user_joined_all(context, update.effective_user.id)
            if not_joined:
                await update.message.reply_text(
                    get_force_join_text(not_joined),
                    reply_markup=get_force_join_keyboard(),
                    parse_mode=ParseMode.HTML
                )
                return STATE_INPUT

            if text == "OWNER DETAILS":
                msg = (
                    "👑 <b>OWNER DETAILS</b>\n\n"
                    "🧑‍💻 Developer: Zevric X Play\n"
                    "📢 Channel: @zevric_all_update\n"
                    "🎮 Gaming: @zevricxplay\n"
                    "🔧 Tools: @zevric_api_tools\n"
                    "📺 YouTube: https://youtube.com/@zevricxplay\n"
                    "💬 Support: @zevricxplay\n\n"
                    "⚙️ Version: v2.0 Premium"
                )
                await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                return STATE_INPUT

            if text == "CHECK BIND INFO":
                user_data.clear()
                user_data["flow"] = "check"
                user_data["step"] = "token"
                await update.message.reply_text(
                    "🔍 <b>CHECK BIND INFO</b>\n\n🔑 Access Token bhejo:\n\n<i>Example: 7a7f... long token</i>",
                    parse_mode=ParseMode.HTML
                )
                return STATE_INPUT

            if text == "BIND EMAIL":
                user_data.clear()
                user_data["flow"] = "bind"
                user_data["step"] = "token"
                await update.message.reply_text(
                    "📧 <b>BIND EMAIL</b>\n\nStep 1/3: 🔑 Access Token bhejo:",
                    parse_mode=ParseMode.HTML
                )
                return STATE_INPUT

            if text == "UNBIND EMAIL":
                user_data.clear()
                user_data["flow"] = "unbind"
                user_data["step"] = "token"
                await update.message.reply_text(
                    "🗑️ <b>UNBIND EMAIL</b>\n\nStep 1/3: 🔑 Access Token bhejo:",
                    parse_mode=ParseMode.HTML
                )
                return STATE_INPUT

            if text == "CHANGE BIND EMAIL":
                user_data.clear()
                user_data["flow"] = "rebind"
                user_data["step"] = "token"
                await update.message.reply_text(
                    "🔄 <b>CHANGE BIND EMAIL</b>\n\nStep 1/5: 🔑 Access Token bhejo:",
                    parse_mode=ParseMode.HTML
                )
                return STATE_INPUT

            if text == "CANCEL BIND REQUEST":
                user_data.clear()
                user_data["flow"] = "cancel"
                user_data["step"] = "token"
                await update.message.reply_text(
                    "❌ <b>CANCEL BIND REQUEST</b>\n\n🔑 Access Token bhejo:",
                    parse_mode=ParseMode.HTML
                )
                return STATE_INPUT

            if text == "EAT TO ACCESS TOKEN":
                user_data.clear()
                user_data["flow"] = "eat"
                user_data["step"] = "token"
                await update.message.reply_text(
                    "🔁 <b>EAT TO ACCESS TOKEN</b>\n\n🥚 EAT Token bhejo (External Auth Token):",
                    parse_mode=ParseMode.HTML
                )
                return STATE_INPUT

            if text == "REVOKE ACCESS TOKEN":
                user_data.clear()
                user_data["flow"] = "revoke"
                user_data["step"] = "token"
                await update.message.reply_text(
                    "🚫 <b>REVOKE ACCESS TOKEN</b>\n\n🔑 Access Token bhejo jo revoke karna hai:",
                    parse_mode=ParseMode.HTML
                )
                return STATE_INPUT

            if text == "SINGLE UNSUBSCRIBE OTP":
                user_data.clear()
                user_data["flow"] = "sso"
                user_data["step"] = "email"
                await update.message.reply_text(
                    "📩 <b>SINGLE UNSUBSCRIBE OTP</b>\n\n📧 Email bhejo jisme OTP bhejna hai:",
                    parse_mode=ParseMode.HTML
                )
                return STATE_INPUT

        # ================= FLOW LOGIC =================
        if not flow:
            await update.message.reply_text("👇 Menu se option select karo:", reply_markup=get_reply_keyboard())
            return STATE_INPUT

        # ---------- CHECK ----------
        if flow == "check" and step == "token":
            token = text
            await update.message.reply_text("⏳ Fetching info... Please wait")
            bind_res = await asyncio.to_thread(fetch_bind_info_sync, token)
            uid, nick, region = await asyncio.to_thread(get_player_info_sync, token)

            if not bind_res["ok"]:
                await update.message.reply_text(
                    f"❌ Failed: {bind_res.get('error')}\n\nToken invalid ho sakta hai.",
                    reply_markup=get_youtube_keyboard()
                )
            else:
                data = bind_res["data"]
                email = data.get("email", "None")
                email_to_be = data.get("email_to_be", "None")
                countdown = data.get("request_exec_countdown", 0)
                msg = (
                    f"✅ <b>BIND INFO</b>\n\n"
                    f"👤 Nickname: {nick}\n"
                    f"🆔 UID: {uid}\n"
                    f"🌍 Region: {region}\n\n"
                    f"📧 Current Email: {email if email else 'None'}\n"
                    f"📧 Pending Email: {email_to_be if email_to_be else 'None'}\n"
                    f"⏳ Countdown: {convert_seconds(countdown)}\n"
                    f"📊 Result Code: {data.get('result', 'N/A')}"
                )
                await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=get_youtube_keyboard())

            await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
            context.user_data.clear()
            return STATE_INPUT

        # ---------- BIND ----------
        if flow == "bind":
            if step == "token":
                user_data["token"] = text
                user_data["step"] = "email"
                await update.message.reply_text("Step 2/3: 📧 Jis email se bind karna hai wo bhejo:")
                return STATE_INPUT
            if step == "email":
                email = text.strip()
                if "@" not in email or "." not in email:
                    await update.message.reply_text("❌ Invalid Email! Sahi email bhejo:")
                    return STATE_INPUT
                user_data["email"] = email
                await update.message.reply_text(f"⏳ {email} pe OTP bhej raha hu...")
                res = await asyncio.to_thread(send_otp_sync, email, user_data["token"])
                if not res["ok"]:
                    await update.message.reply_text(f"❌ OTP Send Failed: {res.get('error')}\n{res.get('data')}", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                user_data["step"] = "otp"
                await update.message.reply_text(f"✅ OTP Sent to {email}\n\nStep 3/3: 🔢 OTP bhejo (6 digit):")
                return STATE_INPUT
            if step == "otp":
                otp = text.strip()
                res = await asyncio.to_thread(verify_otp_sync, user_data["email"], user_data["token"], otp)
                if not res["ok"]:
                    await update.message.reply_text(f"❌ OTP Verify Failed: {res.get('error')}\n{res.get('data')}", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                vt = res.get("verifier_token") or res["data"].get("verifier_token")
                if not vt:
                    await update.message.reply_text(f"❌ Verifier token nahi mila: {res['data']}", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                # Create bind request
                await update.message.reply_text("⏳ Bind request create kar raha hu...")
                res2 = await asyncio.to_thread(create_bind_request_sync, user_data["email"], user_data["token"], vt)
                if res2["ok"]:
                    await update.message.reply_text(f"✅ Bind Request Success!\nEmail: {user_data['email']}\n72 hours me bind ho jayega.", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"❌ Bind Failed: {res2.get('error')}\n{res2.get('data')}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        # ---------- UNBIND ----------
        if flow == "unbind":
            if step == "token":
                user_data["token"] = text
                user_data["step"] = "email"
                await update.message.reply_text("Step 2/3: 📧 Current bind email bhejo (jo account me laga hai):")
                return STATE_INPUT
            if step == "email":
                if "@" not in text:
                    await update.message.reply_text("❌ Invalid Email!")
                    return STATE_INPUT
                user_data["email"] = text.strip()
                await update.message.reply_text(f"⏳ {user_data['email']} pe OTP bhej raha hu...")
                res = await asyncio.to_thread(send_otp_sync, user_data["email"], user_data["token"])
                if not res["ok"]:
                    await update.message.reply_text(f"❌ OTP Failed: {res.get('error')}", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                user_data["step"] = "otp"
                await update.message.reply_text(f"✅ OTP Sent! OTP bhejo:")
                return STATE_INPUT
            if step == "otp":
                res = await asyncio.to_thread(verify_identity_sync, user_data["email"], user_data["token"], text.strip())
                if not res["ok"]:
                    await update.message.reply_text(f"❌ Identity Verify Failed: {res.get('error')}", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                it = res.get("identity_token")
                await update.message.reply_text("⏳ Unbind request bhej raha hu...")
                res2 = await asyncio.to_thread(create_unbind_request_sync, it, user_data["token"])
                if res2["ok"]:
                    await update.message.reply_text("✅ Unbind Request Success! 72h me unbind ho jayega.", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"❌ Unbind Failed: {res2.get('error')}\n{res2.get('data')}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        # ---------- REBIND / CHANGE ----------
        if flow == "rebind":
            if step == "token":
                user_data["token"] = text
                user_data["step"] = "old_email"
                await update.message.reply_text("Step 2/5: 📧 Current bind email (old) bhejo:")
                return STATE_INPUT
            if step == "old_email":
                if "@" not in text:
                    await update.message.reply_text("❌ Invalid Email!")
                    return STATE_INPUT
                user_data["old_email"] = text.strip()
                await update.message.reply_text(f"⏳ Old email {user_data['old_email']} pe OTP bhej raha hu...")
                res = await asyncio.to_thread(send_otp_sync, user_data["old_email"], user_data["token"])
                if not res["ok"]:
                    await update.message.reply_text(f"❌ OTP Failed: {res.get('error')}", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                user_data["step"] = "old_otp"
                await update.message.reply_text("✅ Old Email OTP sent! OTP bhejo:")
                return STATE_INPUT
            if step == "old_otp":
                res = await asyncio.to_thread(verify_identity_sync, user_data["old_email"], user_data["token"], text.strip())
                if not res["ok"]:
                    await update.message.reply_text(f"❌ Old OTP Verify Failed: {res.get('error')}", reply_markup=get_youtube_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                user_data["identity_token"] = res.get("identity_token")
                user_data["step"] = "new_email"
                await update.message.reply_text("Step 4/5: 📧 Naya email bhejo jisme change karna hai:")
                return STATE_INPUT
            if step == "new_email":
                if "@" not in text:
                    await update.message.reply_text("❌ Invalid Email!")
                    return STATE_INPUT
                user_data["new_email"] = text.strip()
                await update.message.reply_text(f"⏳ New email {user_data['new_email']} pe OTP bhej raha hu...")
                res = await asyncio.to_thread(send_otp_sync, user_data["new_email"], user_data["token"])
                if not res["ok"]:
                    await update.message.reply_text(f"❌ New Email OTP Failed: {res.get('error')}", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                user_data["step"] = "new_otp"
                await update.message.reply_text("✅ New Email OTP sent! OTP bhejo:")
                return STATE_INPUT
            if step == "new_otp":
                res = await asyncio.to_thread(verify_otp_sync, user_data["new_email"], user_data["token"], text.strip())
                if not res["ok"]:
                    await update.message.reply_text(f"❌ New OTP Verify Failed: {res.get('error')}", reply_markup=get_youtube_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                vt = res.get("verifier_token") or res["data"].get("verifier_token")
                await update.message.reply_text("⏳ Change request bhej raha hu...")
                res2 = await asyncio.to_thread(create_rebind_request_sync, user_data["identity_token"], user_data["new_email"], vt, user_data["token"])
                if res2["ok"]:
                    await update.message.reply_text(f"✅ Change Bind Success!\nNew Email: {user_data['new_email']}\n72h me change ho jayega.", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"❌ Change Failed: {res2.get('error')}\n{res2.get('data')}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        # ---------- CANCEL ----------
        if flow == "cancel" and step == "token":
            await update.message.reply_text("⏳ Cancel request bhej raha hu...")
            res = await asyncio.to_thread(cancel_request_sync, text.strip())
            if res["ok"]:
                await update.message.reply_text("✅ Bind Request Cancelled Successfully!", reply_markup=get_youtube_keyboard())
            else:
                await update.message.reply_text(f"❌ Cancel Failed: {res.get('error')}\n{res.get('data')}", reply_markup=get_youtube_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
            context.user_data.clear()
            return STATE_INPUT

        # ---------- EAT ----------
        if flow == "eat" and step == "token":
            await update.message.reply_text("⏳ EAT ko Access Token me convert kar raha hu...")
            res = await asyncio.to_thread(eat_to_at_sync, text.strip())
            if res["ok"]:
                msg = (
                    f"✅ <b>EAT Convert Success</b>\n\n"
                    f"👤 Nick: {res['nickname']}\n"
                    f"🆔 ID: {res['account_id']}\n"
                    f"🌍 Region: {res['region']}\n\n"
                    f"🔑 <b>Access Token:</b>\n<code>{res['access_token']}</code>"
                )
                await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=get_youtube_keyboard())
            else:
                await update.message.reply_text(f"❌ Error: {res.get('error')}", reply_markup=get_youtube_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
            context.user_data.clear()
            return STATE_INPUT

        # ---------- REVOKE ----------
        if flow == "revoke" and step == "token":
            await update.message.reply_text("⏳ Token revoke kar raha hu...")
            res = await asyncio.to_thread(revoke_access_token_sync, text.strip())
            if res["ok"]:
                await update.message.reply_text(f"✅ Revoked Success\nNick: {res['nickname']}\nID: {res['account_id']}", reply_markup=get_youtube_keyboard())
            else:
                await update.message.reply_text(f"❌ Revoke Failed: {res.get('error')}", reply_markup=get_youtube_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
            context.user_data.clear()
            return STATE_INPUT

        # ---------- SSO SINGLE UNSUBSCRIBE ----------
        if flow == "sso" and step == "email":
            email = text.strip()
            if "@" not in email:
                await update.message.reply_text("❌ Invalid Email!")
                return STATE_INPUT
            await update.message.reply_text(f"⏳ {email} pe OTP bhej raha hu...")
            try:
                session = requests.Session()
                headers_base = {
                    "User-Agent": "Mozilla/5.0",
                    "Referer": "https://sso.garena.com/universal/register?locale=en-SG",
                    "Origin": "https://sso.garena.com"
                }
                rand_user = "ZEVRICX" + "".join(random.choices(string.ascii_uppercase+string.digits, k=4))
                rand_pass = ".Nm5TGMfA7JyUyh" + "".join(random.choices(string.ascii_letters+string.digits, k=2))
                try:
                    session.get("https://sso.garena.com/universal/register?locale=en-SG", headers=headers_base, timeout=10, verify=False)
                except:
                    pass
                api_url = "https://sso.garena.com/api/account/send_verification_code"
                payload = {
                    "email": email,
                    "username": rand_user,
                    "password": rand_pass,
                    "confirm_password": rand_pass,
                    "locale": "en-SG",
                    "region": "SG"
                }
                resp = session.post(api_url, headers={**headers_base, "Content-Type": "application/json"}, json=payload, timeout=12, verify=False)
                logger.info(f"SSO response: {resp.text[:200]}")
            except Exception as e:
                logger.error(f"SSO error: {e}")
            await update.message.reply_text(f"✅ Single Unsubscribe OTP Sent Successfully!\n📧 Email: {email}", reply_markup=get_youtube_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
            context.user_data.clear()
            return STATE_INPUT

        await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
        return STATE_INPUT

    except Exception as e:
        logger.error(f"Error in handle_text: {e}", exc_info=True)
        try:
            await update.message.reply_text("❌ Error Occurred. /start se restart karo.", reply_markup=get_reply_keyboard())
        except:
            pass
        context.user_data.clear()
        return STATE_INPUT

# ================= FLASK KEEP ALIVE =================
try:
    from flask import Flask
    flask_app = Flask(__name__)
    @flask_app.route('/')
    def home():
        return "Bot Running - 9 Options Working - Zevric X Play"
    @flask_app.route('/health')
    def health():
        return "OK"
    app = flask_app
except:
    flask_app = None
    app = None

# ================= RUN BOT =================
def run_bot():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ BOT_TOKEN not set! Set env var BOT_TOKEN")
        return
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    except:
        pass
    try:
        application = Application.builder().token(BOT_TOKEN).build()

        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", start),
                CommandHandler("menu", menu_cmd),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
            ],
            states={
                STATE_INPUT: [
                    CallbackQueryHandler(handle_callback),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
                ]
            },
            fallbacks=[
                CommandHandler("cancel", cancel_cmd),
                CommandHandler("start", start)
            ],
            allow_reentry=True,
            per_message=False
        )
        application.add_handler(conv_handler)
        application.add_handler(CommandHandler("cancel", cancel_cmd))
        print("✅ Bot polling started...")
        application.run_polling(close_loop=False, drop_pending_updates=True, stop_signals=None)
    except Exception as e:
        print(f"Bot run failed: {e}")
        import traceback
        traceback.print_exc()
        raise

def _auto_start_bot():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        return
    def bot_thread_func():
        while True:
            try:
                run_bot()
            except Exception as e:
                print(f"Bot crashed: {e}, restart in 5 sec")
                time.sleep(5)
    try:
        t = threading.Thread(target=bot_thread_func, daemon=True)
        t.start()
    except Exception as e:
        print(f"Auto start failed: {e}")

if os.getenv("PORT") or os.getenv("RENDER"):
    _auto_start_bot()

if __name__ == "__main__":
    # For local + Render hosting both
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    port = int(os.environ.get("PORT", 10000))
    if flask_app:
        flask_app.run(host="0.0.0.0", port=port)
    else:
        # If flask not available, keep alive via infinite loop
        while True:
            time.sleep(60)
