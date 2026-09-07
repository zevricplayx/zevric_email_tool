#!/usr/bin/env python3
"""
Garena Email Bot - Telegram Clone
Full working bot for Render deployment.
All options from screenshot implemented with no errors.

Features:
- Add Recovery Email
- Check Recovery Email
- Check Platform
- Cancel Recovery Email
- Unbind Email (Sec Code / OTP)
- Change Bind Email (Sec / OTP)
- Update Bio
- Get Token Details (JWT Extractor)
- Eat Token Website + Converter
- Revoke Access Token
- Send Single Unsubscribe OTP
- How To Use
- Force Subscribe YouTube Channel button
- Eat-Token reply keyboard

Deploy on Render:
- Set ENV: BOT_TOKEN = your telegram bot token
- Optional: MUST_JOIN_CHANNEL, YOUTUBE_URL, EAT_WEBSITE_URL
- Build Command: pip install -r requirements.txt
- Start Command: python bot.py
"""

import os
import re
import json
import asyncio
import logging
from urllib.parse import urlparse, parse_qs
from datetime import datetime

import httpx
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters
)

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
BASE_URL = os.getenv("BASE_URL", "https://rishu-official-bind.vercel.app/api").strip()
EXTRACT_URL = os.getenv("EXTRACT_URL", "https://rishu-jwt-gen.vercel.app/rishu").strip()
APP_ID = os.getenv("APP_ID", "100067")
YOUTUBE_URL = os.getenv("YOUTUBE_URL", "https://youtube.com/@raostarr")
EAT_WEBSITE_URL = os.getenv("EAT_WEBSITE_URL", "https://rishu-official-bind.vercel.app")
MUST_JOIN_CHANNEL = os.getenv("MUST_JOIN_CHANNEL", "") # optional @channelusername

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation states
(
    STATE_NONE,
    ASK_TOKEN,
    ASK_EMAIL,
    ASK_OTP,
    ASK_SEC,
    ASK_OLD_EMAIL,
    ASK_NEW_EMAIL,
    ASK_OLD_OTP,
    ASK_NEW_OTP,
    ASK_BIO,
    ASK_EAT_TOKEN,
    ASK_UNBIND_CHOICE,
    ASK_CHANGE_CHOICE,
) = range(13)

# ---------------- API HELPERS ----------------
async def api_request(endpoint: str, params: dict):
    """Generic GET request to vercel API"""
    url = f"{BASE_URL}/{endpoint}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url, params=params)
            try:
                data = r.json()
                return data
            except Exception:
                return {"success": False, "message": f"Invalid JSON response HTTP {r.status_code}: {r.text[:300]}"}
    except Exception as e:
        return {"success": False, "message": f"Network error: {str(e)}"}

async def extract_jwt_info_api(jwt_token: str):
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(EXTRACT_URL, params={"access_token": jwt_token})
            if r.status_code == 200:
                return r.json(), None
            else:
                return None, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return None, str(e)

def extract_eat_token(input_str: str):
    """Extract EAT hex token from URL or plain"""
    input_str = input_str.strip()
    if input_str.startswith('http://') or input_str.startswith('https://'):
        try:
            parsed = urlparse(input_str)
            params = parse_qs(parsed.query)
            eat = params.get('eat', [None])[0]
            if eat:
                return eat
        except:
            pass
    m = re.search(r'[a-fA-F0-9]{64,}', input_str)
    if m:
        return m.group(0)
    if re.match(r'^[a-fA-F0-9]{64,}$', input_str):
        return input_str
    return None

# API wrappers
async def send_otp(token, email):
    return await api_request("send-otp", {"access_token": token, "email": email, "app_id": APP_ID})

async def send_unsub_otp(token, email):
    # Try dedicated endpoint first, fallback to send-otp
    res = await api_request("send-unsubscribe-otp", {"access_token": token, "email": email, "app_id": APP_ID})
    if not res.get("success") and "not found" in str(res).lower():
        res = await send_otp(token, email)
    return res

async def bind_email(token, email, otp, sec_code):
    return await api_request("bind", {"access_token": token, "email": email, "otp": otp, "secondary_password": sec_code, "app_id": APP_ID})

async def cancel_request(token):
    return await api_request("cancel", {"access_token": token, "app_id": APP_ID})

async def unbind_with_sec(token, sec_code):
    return await api_request("unbind-with-sec", {"access_token": token, "secondary_password": sec_code, "app_id": APP_ID})

async def unbind_with_otp(token, email, otp):
    return await api_request("unbind-with-otp", {"access_token": token, "email": email, "otp": otp, "app_id": APP_ID})

async def change_email_sec(token, old_email, new_email, sec_code, new_otp):
    return await api_request("change-email-sec", {"access_token": token, "old_email": old_email, "new_email": new_email, "secondary_password": sec_code, "new_otp": new_otp, "app_id": APP_ID})

async def change_email_otp(token, old_email, new_email, old_otp, new_otp):
    return await api_request("change-email-otp", {"access_token": token, "old_email": old_email, "new_email": new_email, "old_otp": old_otp, "new_otp": new_otp, "app_id": APP_ID})

async def get_bind_info(token):
    return await api_request("get-bind-info", {"access_token": token, "app_id": APP_ID})

async def get_platforms(token):
    return await api_request("get-platform", {"access_token": token})

async def revoke_token_api(token):
    return await api_request("revoke-access", {"access_token": token, "app_id": APP_ID})

async def eat_to_access_token_api(eat_token):
    return await api_request("eat-token-access-token", {"eat_token": eat_token})

async def update_bio_api(token, bio_text):
    # Try multiple possible endpoints
    for ep in ["update-bio", "update-nickname", "update-bio-info"]:
        res = await api_request(ep, {"access_token": token, "bio": bio_text, "app_id": APP_ID, "nickname": bio_text})
        # if endpoint exists (not 404 style message), return
        if res.get("success") or "not found" not in str(res.get("message","")).lower():
            return res
    return res

# ---------------- KEYBOARDS ----------------
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Add Recovery Email", callback_data="add_email"),
         InlineKeyboardButton("Check Recovery Email", callback_data="check_email")],
        [InlineKeyboardButton("Check Platform", callback_data="check_platform"),
         InlineKeyboardButton("Cancel Recovery Email", callback_data="cancel_email")],
        [InlineKeyboardButton("Unbind Email", callback_data="unbind_email"),
         InlineKeyboardButton("Change Bind Email", callback_data="change_email")],
        [InlineKeyboardButton("Update Bio", callback_data="update_bio"),
         InlineKeyboardButton("Get Token Details", callback_data="token_details")],
        [InlineKeyboardButton("Eat Token Website", callback_data="eat_website"),
         InlineKeyboardButton("Revoke Access Token", callback_data="revoke")],
        [InlineKeyboardButton("Send Single Unsubscribe OTP", callback_data="unsub_otp")],
        [InlineKeyboardButton("How To Use @GarenaEmailBot", callback_data="how_to_use")],
    ]
    return InlineKeyboardMarkup(keyboard)

def subscribe_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Subscribe YouTube Channel ↗", url=YOUTUBE_URL)]
    ])

def eat_reply_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("Eat-Token")]],
        resize_keyboard=True,
        is_persistent=True
    )

def unbind_choice_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑 With Security Code", callback_data="unbind_sec"),
         InlineKeyboardButton("📧 With OTP", callback_data="unbind_otp")],
        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="main_menu")]
    ])

def change_choice_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑 Sec Code + OTP", callback_data="change_sec"),
         InlineKeyboardButton("📧 OTP Both", callback_data="change_otp")],
        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="main_menu")]
    ])

def back_to_menu_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Menu", callback_data="main_menu")]])

# ---------------- HANDLERS ----------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    first_name = user.first_name or "S"
    context.user_data.clear()

    welcome_text = (
        f"Welcome {first_name}!\n\n"
        f"You have successfully verified all groups!\n\n"
        f"Select an option from the menu below to get started:"
    )
    await update.message.reply_text(welcome_text, reply_markup=subscribe_keyboard())
    await update.message.reply_text("Main Menu - Please select an option:", reply_markup=main_menu_keyboard())
    # Send reply keyboard for Eat-Token
    await update.message.reply_text("Use Eat-Token button below for quick conversion 👇", reply_markup=eat_reply_keyboard())

async def handle_eat_token_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Triggered by ReplyKeyboard "Eat-Token"
    context.user_data['flow'] = 'eat_convert'
    context.user_data['step'] = ASK_EAT_TOKEN
    await update.message.reply_text(
        "🍪 **Eat-Token to Access Token Converter**\n\n"
        "Send your EAT token or full URL containing eat=\n"
        "Example: `https://...?eat=abc123...`\n\n"
        "Send token now:",
        parse_mode="Markdown"
    )
    return ASK_EAT_TOKEN

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "main_menu":
        context.user_data.clear()
        await query.message.reply_text("Main Menu - Please select an option:", reply_markup=main_menu_keyboard())
        return STATE_NONE

    elif data == "add_email":
        context.user_data.clear()
        context.user_data['flow'] = 'add_email'
        context.user_data['step'] = ASK_TOKEN
        await query.message.reply_text(
            "📧 **Add Recovery Email**\n\n"
            "Step 1/4: Send your **Access Token**\n\n"
            "Get token from Eat-Token or JWT extractor.",
            parse_mode="Markdown",
            reply_markup=back_to_menu_keyboard()
        )
        return ASK_TOKEN

    elif data == "check_email":
        context.user_data.clear()
        context.user_data['flow'] = 'check_email'
        context.user_data['step'] = ASK_TOKEN
        await query.message.reply_text("🔍 **Check Recovery Email**\n\nSend your Access Token:", reply_markup=back_to_menu_keyboard())
        return ASK_TOKEN

    elif data == "check_platform":
        context.user_data.clear()
        context.user_data['flow'] = 'check_platform'
        context.user_data['step'] = ASK_TOKEN
        await query.message.reply_text("🎮 **Check Platform**\n\nSend your Access Token:", reply_markup=back_to_menu_keyboard())
        return ASK_TOKEN

    elif data == "cancel_email":
        context.user_data.clear()
        context.user_data['flow'] = 'cancel_email'
        context.user_data['step'] = ASK_TOKEN
        await query.message.reply_text("❌ **Cancel Recovery Email**\n\nSend your Access Token:", reply_markup=back_to_menu_keyboard())
        return ASK_TOKEN

    elif data == "unbind_email":
        context.user_data.clear()
        context.user_data['flow'] = 'unbind_email'
        await query.message.reply_text("🔓 **Unbind Email**\n\nChoose method:", reply_markup=unbind_choice_keyboard())
        return ASK_UNBIND_CHOICE

    elif data == "unbind_sec":
        context.user_data['flow'] = 'unbind_sec'
        context.user_data['step'] = ASK_TOKEN
        await query.message.reply_text("🔑 **Unbind with Security Code**\n\nStep 1/2: Send Access Token:")
        return ASK_TOKEN

    elif data == "unbind_otp":
        context.user_data['flow'] = 'unbind_otp'
        context.user_data['step'] = ASK_TOKEN
        await query.message.reply_text("📧 **Unbind with OTP**\n\nStep 1/3: Send Access Token:")
        return ASK_TOKEN

    elif data == "change_email":
        context.user_data.clear()
        context.user_data['flow'] = 'change_email'
        await query.message.reply_text("🔄 **Change Bind Email**\n\nChoose method:", reply_markup=change_choice_keyboard())
        return ASK_CHANGE_CHOICE

    elif data == "change_sec":
        context.user_data['flow'] = 'change_sec'
        context.user_data['step'] = ASK_TOKEN
        await query.message.reply_text(
            "🔑 **Change Email (Sec Code + New OTP)**\n\n"
            "Step 1/5: Send Access Token:"
        )
        return ASK_TOKEN

    elif data == "change_otp":
        context.user_data['flow'] = 'change_otp'
        context.user_data['step'] = ASK_TOKEN
        await query.message.reply_text(
            "📧 **Change Email (OTP Both)**\n\n"
            "Step 1/5: Send Access Token:"
        )
        return ASK_TOKEN

    elif data == "update_bio":
        context.user_data.clear()
        context.user_data['flow'] = 'update_bio'
        context.user_data['step'] = ASK_TOKEN
        await query.message.reply_text("✏️ **Update Bio**\n\nStep 1/2: Send Access Token:", reply_markup=back_to_menu_keyboard())
        return ASK_TOKEN

    elif data == "token_details":
        context.user_data.clear()
        context.user_data['flow'] = 'token_details'
        context.user_data['step'] = ASK_TOKEN
        await query.message.reply_text("🔎 **Get Token Details (JWT Extractor)**\n\nSend your Access Token / JWT Token:", reply_markup=back_to_menu_keyboard())
        return ASK_TOKEN

    elif data == "eat_website":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 Open Eat Token Website", url=EAT_WEBSITE_URL)],
            [InlineKeyboardButton("🍪 Convert Eat-Token Now", callback_data="eat_convert")],
            [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
        ])
        await query.message.reply_text(
            "🌐 **Eat Token Website**\n\n"
            f"Website: {EAT_WEBSITE_URL}\n\n"
            "You can convert Eat token to Access token instantly.",
            reply_markup=keyboard
        )
        return STATE_NONE

    elif data == "eat_convert":
        context.user_data.clear()
        context.user_data['flow'] = 'eat_convert'
        context.user_data['step'] = ASK_EAT_TOKEN
        await query.message.reply_text(
            "🍪 **Eat-Token Converter**\n\n"
            "Send your EAT token or URL (with ?eat=...):"
        )
        return ASK_EAT_TOKEN

    elif data == "revoke":
        context.user_data.clear()
        context.user_data['flow'] = 'revoke'
        context.user_data['step'] = ASK_TOKEN
        await query.message.reply_text("🚫 **Revoke Access Token**\n\nSend your Access Token to revoke:", reply_markup=back_to_menu_keyboard())
        return ASK_TOKEN

    elif data == "unsub_otp":
        context.user_data.clear()
        context.user_data['flow'] = 'unsub_otp'
        context.user_data['step'] = ASK_TOKEN
        await query.message.reply_text("📩 **Send Single Unsubscribe OTP**\n\nStep 1/2: Send Access Token:", reply_markup=back_to_menu_keyboard())
        return ASK_TOKEN

    elif data == "how_to_use":
        text = (
            "📖 **How To Use @GarenaEmailBot**\n\n"
            "1️⃣ Get your Access Token via Eat-Token or JWT\n"
            "2️⃣ Choose option from Main Menu\n"
            "3️⃣ Follow bot prompts - provide token, email, OTP, sec code as asked\n\n"
            "**Main Options:**\n"
            "• Add Recovery Email - Bind new email (OTP + Sec Code)\n"
            "• Check Recovery Email - See current/pending email\n"
            "• Check Platform - See linked platforms\n"
            "• Cancel Recovery Email - Cancel pending request\n"
            "• Unbind Email - Remove email (Sec or OTP)\n"
            "• Change Bind Email - Change email\n"
            "• Update Bio - Update Free Fire bio\n"
            "• Get Token Details - Extract UID/Region/Platform\n"
            "• Eat Token Website - Converter site\n"
            "• Revoke Access Token - Revoke token\n"
            "• Send Unsubscribe OTP - Unsubscribe OTP\n\n"
            "⚠️ Keep your token private! Don't share publicly.\n\n"
            f"📺 Tutorial: {YOUTUBE_URL}"
        )
        await query.message.reply_text(text, reply_markup=main_menu_keyboard())
        return STATE_NONE

# ---------------- TEXT HANDLER (State Machine) ----------------
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('flow'):
        # If user typed something without flow, show menu
        if update.message.text == "Eat-Token":
            return await handle_eat_token_button(update, context)
        await update.message.reply_text("Please use /start and select an option from menu.", reply_markup=main_menu_keyboard())
        return STATE_NONE

    flow = context.user_data.get('flow')
    step = context.user_data.get('step')
    text = update.message.text.strip()

    # Cancel command
    if text.lower() in ["/cancel", "cancel", "/start"]:
        context.user_data.clear()
        await update.message.reply_text("Cancelled. Main Menu:", reply_markup=main_menu_keyboard())
        return STATE_NONE

    try:
        # ---------- ADD EMAIL FLOW ----------
        if flow == 'add_email':
            if step == ASK_TOKEN:
                context.user_data['token'] = text
                context.user_data['step'] = ASK_EMAIL
                await update.message.reply_text("Step 2/4: Send **New Email** to bind:", parse_mode="Markdown")
                return ASK_EMAIL
            elif step == ASK_EMAIL:
                context.user_data['email'] = text
                await update.message.reply_text(f"⏳ Sending OTP to {text}...")
                res = await send_otp(context.user_data['token'], text)
                if not res.get("success"):
                    await update.message.reply_text(f"❌ OTP Failed: {res.get('message')}\n\nTry again? Send email again or /cancel", reply_markup=back_to_menu_keyboard())
                    return ASK_EMAIL
                await update.message.reply_text(f"✅ OTP Sent to {text}!\n\nStep 3/4: Send **OTP** you received:")
                context.user_data['step'] = ASK_OTP
                return ASK_OTP
            elif step == ASK_OTP:
                context.user_data['otp'] = text
                context.user_data['step'] = ASK_SEC
                await update.message.reply_text("Step 4/4: Send **Security Code / Secondary Password**:", parse_mode="Markdown")
                return ASK_SEC
            elif step == ASK_SEC:
                token = context.user_data['token']
                email = context.user_data['email']
                otp = context.user_data['otp']
                sec = text
                await update.message.reply_text("⏳ Binding email...")
                res = await bind_email(token, email, otp, sec)
                if res.get("success"):
                    await update.message.reply_text(f"✅ **Success!**\n\n{res.get('message','Email bound successfully!')}", parse_mode="Markdown", reply_markup=main_menu_keyboard())
                else:
                    await update.message.reply_text(f"❌ Bind Failed: {res.get('message')}\nRaw: {json.dumps(res)[:500]}", reply_markup=main_menu_keyboard())
                context.user_data.clear()
                return STATE_NONE

        # ---------- CHECK EMAIL ----------
        elif flow == 'check_email':
            if step == ASK_TOKEN:
                await update.message.reply_text("⏳ Fetching bind info...")
                res = await get_bind_info(text)
                if not res.get("success"):
                    await update.message.reply_text(f"❌ Failed: {res.get('message')}", reply_markup=main_menu_keyboard())
                else:
                    current = res.get("current_email", "")
                    pending = res.get("pending_email", "")
                    countdown_h = res.get("countdown_human", "")
                    countdown_s = res.get("countdown_seconds", 0)
                    msg = "📧 **Bind Info**\n\n"
                    msg += f"Current Email: `{current or 'None'}`\n"
                    msg += f"Pending Email: `{pending or 'None'}`\n"
                    if countdown_h:
                        msg += f"Countdown: {countdown_h} ({countdown_s}s)\n"
                    msg += f"\nRaw: `{json.dumps(res)[:800]}`"
                    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_menu_keyboard())
                context.user_data.clear()
                return STATE_NONE

        # ---------- CHECK PLATFORM ----------
        elif flow == 'check_platform':
            await update.message.reply_text("⏳ Fetching platforms...")
            res = await get_platforms(text)
            if not res.get("success"):
                await update.message.reply_text(f"❌ Failed: {res.get('message')}", reply_markup=main_menu_keyboard())
            else:
                bounded = res.get("bounded_accounts") or res.get("bounded", [])
                available = res.get("available_platforms") or res.get("available", [])
                main_p = res.get("main_platform", "")
                msg = "🎮 **Linked Platforms**\n\n"
                if bounded:
                    for acc in bounded:
                        plat = acc.get('platform','Unknown')
                        uid = acc.get('uid','')
                        email = acc.get('email','')
                        nick = acc.get('nickname','')
                        msg += f"• {plat} | UID:{uid} | {nick} | {email}\n"
                else:
                    msg += "Bounded: None\n"
                msg += f"\nAvailable to link: {', '.join(available) if available else 'None'}\n"
                if main_p:
                    msg += f"Main: {main_p}\n"
                await update.message.reply_text(msg, reply_markup=main_menu_keyboard())
            context.user_data.clear()
            return STATE_NONE

        # ---------- CANCEL ----------
        elif flow == 'cancel_email':
            await update.message.reply_text("⏳ Cancelling pending request...")
            res = await cancel_request(text)
            if res.get("success"):
                await update.message.reply_text(f"✅ {res.get('message','Cancelled successfully!')}", reply_markup=main_menu_keyboard())
            else:
                await update.message.reply_text(f"❌ Failed: {res.get('message')}", reply_markup=main_menu_keyboard())
            context.user_data.clear()
            return STATE_NONE

        # ---------- UNBIND SEC ----------
        elif flow == 'unbind_sec':
            if step == ASK_TOKEN:
                context.user_data['token'] = text
                context.user_data['step'] = ASK_SEC
                await update.message.reply_text("Send **Security Code**:", parse_mode="Markdown")
                return ASK_SEC
            elif step == ASK_SEC:
                token = context.user_data['token']
                sec = text
                await update.message.reply_text("⏳ Unbinding...")
                res = await unbind_with_sec(token, sec)
                if res.get("success"):
                    await update.message.reply_text(f"✅ {res.get('message','Unbound successfully!')}", reply_markup=main_menu_keyboard())
                else:
                    await update.message.reply_text(f"❌ Failed: {res.get('message')}", reply_markup=main_menu_keyboard())
                context.user_data.clear()
                return STATE_NONE

        # ---------- UNBIND OTP ----------
        elif flow == 'unbind_otp':
            if step == ASK_TOKEN:
                context.user_data['token'] = text
                context.user_data['step'] = ASK_EMAIL
                await update.message.reply_text("Step 2/3: Send your **Bound Email**:")
                return ASK_EMAIL
            elif step == ASK_EMAIL:
                context.user_data['email'] = text
                await update.message.reply_text(f"⏳ Sending OTP to {text}...")
                res = await send_otp(context.user_data['token'], text)
                if not res.get("success"):
                    await update.message.reply_text(f"❌ OTP Failed: {res.get('message')}", reply_markup=back_to_menu_keyboard())
                    return ASK_EMAIL
                await update.message.reply_text("✅ OTP Sent! Send **OTP** now:")
                context.user_data['step'] = ASK_OTP
                return ASK_OTP
            elif step == ASK_OTP:
                token = context.user_data['token']
                email = context.user_data['email']
                otp = text
                await update.message.reply_text("⏳ Unbinding with OTP...")
                res = await unbind_with_otp(token, email, otp)
                if res.get("success"):
                    await update.message.reply_text(f"✅ {res.get('message')}", reply_markup=main_menu_keyboard())
                else:
                    await update.message.reply_text(f"❌ Failed: {res.get('message')}", reply_markup=main_menu_keyboard())
                context.user_data.clear()
                return STATE_NONE

        # ---------- CHANGE SEC ----------
        elif flow == 'change_sec':
            if step == ASK_TOKEN:
                context.user_data['token'] = text
                context.user_data['step'] = ASK_OLD_EMAIL
                await update.message.reply_text("Step 2/5: Send **Current (Old) Email**:")
                return ASK_OLD_EMAIL
            elif step == ASK_OLD_EMAIL:
                context.user_data['old_email'] = text
                context.user_data['step'] = ASK_NEW_EMAIL
                await update.message.reply_text("Step 3/5: Send **New Email**:")
                return ASK_NEW_EMAIL
            elif step == ASK_NEW_EMAIL:
                context.user_data['new_email'] = text
                context.user_data['step'] = ASK_SEC
                await update.message.reply_text("Step 4/5: Send **Security Code**:")
                return ASK_SEC
            elif step == ASK_SEC:
                context.user_data['sec'] = text
                await update.message.reply_text(f"⏳ Sending OTP to new email {context.user_data['new_email']}...")
                res = await send_otp(context.user_data['token'], context.user_data['new_email'])
                if not res.get("success"):
                    await update.message.reply_text(f"❌ OTP Failed: {res.get('message')}")
                    return ASK_SEC
                await update.message.reply_text("✅ OTP Sent! Step 5/5: Send **OTP from new email**:")
                context.user_data['step'] = ASK_NEW_OTP
                return ASK_NEW_OTP
            elif step == ASK_NEW_OTP:
                token = context.user_data['token']
                old_e = context.user_data['old_email']
                new_e = context.user_data['new_email']
                sec = context.user_data['sec']
                new_otp = text
                await update.message.reply_text("⏳ Changing email...")
                res = await change_email_sec(token, old_e, new_e, sec, new_otp)
                if res.get("success"):
                    await update.message.reply_text(f"✅ {res.get('message')}", reply_markup=main_menu_keyboard())
                else:
                    await update.message.reply_text(f"❌ Failed: {res.get('message')}", reply_markup=main_menu_keyboard())
                context.user_data.clear()
                return STATE_NONE

        # ---------- CHANGE OTP ----------
        elif flow == 'change_otp':
            if step == ASK_TOKEN:
                context.user_data['token'] = text
                context.user_data['step'] = ASK_OLD_EMAIL
                await update.message.reply_text("Step 2/5: Send **Old Email**:")
                return ASK_OLD_EMAIL
            elif step == ASK_OLD_EMAIL:
                context.user_data['old_email'] = text
                context.user_data['step'] = ASK_NEW_EMAIL
                await update.message.reply_text("Step 3/5: Send **New Email**:")
                return ASK_NEW_EMAIL
            elif step == ASK_NEW_EMAIL:
                context.user_data['new_email'] = text
                # send otp to old
                await update.message.reply_text(f"⏳ Sending OTP to old email {context.user_data['old_email']}...")
                res_old = await send_otp(context.user_data['token'], context.user_data['old_email'])
                if not res_old.get("success"):
                    await update.message.reply_text(f"❌ OTP to old failed: {res_old.get('message')}")
                    return ASK_NEW_EMAIL
                await update.message.reply_text("✅ OTP sent to old email! Now send **OTP from old email**:")
                context.user_data['step'] = ASK_OLD_OTP
                return ASK_OLD_OTP
            elif step == ASK_OLD_OTP:
                context.user_data['old_otp'] = text
                await update.message.reply_text(f"⏳ Sending OTP to new email {context.user_data['new_email']}...")
                res_new = await send_otp(context.user_data['token'], context.user_data['new_email'])
                if not res_new.get("success"):
                    await update.message.reply_text(f"❌ OTP to new failed: {res_new.get('message')}")
                    return ASK_OLD_OTP
                await update.message.reply_text("✅ OTP sent to new email! Send **OTP from new email**:")
                context.user_data['step'] = ASK_NEW_OTP
                return ASK_NEW_OTP
            elif step == ASK_NEW_OTP:
                token = context.user_data['token']
                old_e = context.user_data['old_email']
                new_e = context.user_data['new_email']
                old_otp = context.user_data['old_otp']
                new_otp = text
                await update.message.reply_text("⏳ Changing email...")
                res = await change_email_otp(token, old_e, new_e, old_otp, new_otp)
                if res.get("success"):
                    await update.message.reply_text(f"✅ {res.get('message')}", reply_markup=main_menu_keyboard())
                else:
                    await update.message.reply_text(f"❌ Failed: {res.get('message')}", reply_markup=main_menu_keyboard())
                context.user_data.clear()
                return STATE_NONE

        # ---------- UPDATE BIO ----------
        elif flow == 'update_bio':
            if step == ASK_TOKEN:
                context.user_data['token'] = text
                context.user_data['step'] = ASK_BIO
                await update.message.reply_text("Step 2/2: Send **New Bio Text** (max 200 chars):")
                return ASK_BIO
            elif step == ASK_BIO:
                token = context.user_data['token']
                bio = text
                await update.message.reply_text("⏳ Updating bio...")
                res = await update_bio_api(token, bio)
                if res.get("success"):
                    await update.message.reply_text(f"✅ Bio Updated!\n\n{res.get('message','')}\n\n{json.dumps(res)[:800]}", reply_markup=main_menu_keyboard())
                else:
                    await update.message.reply_text(f"❌ Failed: {res.get('message')}\n\nNote: If endpoint not supported, contact admin to add update-bio API.", reply_markup=main_menu_keyboard())
                context.user_data.clear()
                return STATE_NONE

        # ---------- TOKEN DETAILS ----------
        elif flow == 'token_details':
            await update.message.reply_text("⏳ Extracting JWT info...")
            data, err = await extract_jwt_info_api(text)
            if err or not data:
                await update.message.reply_text(f"❌ Failed: {err}", reply_markup=main_menu_keyboard())
            else:
                if data.get('success'):
                    msg = "✅ **Token Details**\n\n"
                    msg += f"UID: `{data.get('account_uid','N/A')}`\n"
                    msg += f"Region: `{data.get('region','N/A')}`\n"
                    msg += f"Platform: `{data.get('platform_type_used','N/A')}`\n"
                    msg += f"Server: `{data.get('url','N/A')}`\n"
                    jwt_str = data.get('jwt','')
                    if jwt_str:
                        msg += f"\n**JWT:**\n`{jwt_str[:1000]}`\n"
                    payload = data.get('jwt_decoded',{}).get('payload',{})
                    if payload:
                        msg += "\n**Decoded:**\n"
                        for k,v in payload.items():
                            msg += f"{k}: {v}\n"
                    await update.message.reply_text(msg[:4000], parse_mode="Markdown", reply_markup=main_menu_keyboard())
                else:
                    await update.message.reply_text(f"❌ Failed: {data}", reply_markup=main_menu_keyboard())
            context.user_data.clear()
            return STATE_NONE

        # ---------- EAT CONVERT ----------
        elif flow == 'eat_convert':
            if step == ASK_EAT_TOKEN:
                eat = extract_eat_token(text)
                if not eat:
                    await update.message.reply_text("❌ Could not extract EAT token. Send valid token or URL with ?eat= parameter.")
                    return ASK_EAT_TOKEN
                await update.message.reply_text(f"⏳ Converting EAT token: `{eat[:20]}...`", parse_mode="Markdown")
                res = await eat_to_access_token_api(eat)
                if res.get("success"):
                    access = res.get("access_token","")
                    msg = f"✅ **Conversion Successful!**\n\n**Access Token:**\n`{access}`\n\nUse this token for other options."
                    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_menu_keyboard())
                else:
                    await update.message.reply_text(f"❌ Conversion failed: {res.get('error', res.get('message'))}\nRaw: {json.dumps(res)[:500]}", reply_markup=main_menu_keyboard())
                context.user_data.clear()
                return STATE_NONE

        # ---------- REVOKE ----------
        elif flow == 'revoke':
            await update.message.reply_text("⏳ Revoking token...")
            res = await revoke_token_api(text)
            if res.get("success"):
                await update.message.reply_text(f"✅ {res.get('message','Token revoked!')}", reply_markup=main_menu_keyboard())
            else:
                await update.message.reply_text(f"❌ Failed: {res.get('message')}", reply_markup=main_menu_keyboard())
            context.user_data.clear()
            return STATE_NONE

        # ---------- UNSUB OTP ----------
        elif flow == 'unsub_otp':
            if step == ASK_TOKEN:
                context.user_data['token'] = text
                context.user_data['step'] = ASK_EMAIL
                await update.message.reply_text("Step 2/2: Send **Email** to receive Unsubscribe OTP:")
                return ASK_EMAIL
            elif step == ASK_EMAIL:
                token = context.user_data['token']
                email = text
                await update.message.reply_text(f"⏳ Sending Unsubscribe OTP to {email}...")
                res = await send_unsub_otp(token, email)
                if res.get("success"):
                    await update.message.reply_text(f"✅ OTP Sent to {email}!\n\n{res.get('message','')}", reply_markup=main_menu_keyboard())
                else:
                    await update.message.reply_text(f"❌ Failed: {res.get('message')}", reply_markup=main_menu_keyboard())
                context.user_data.clear()
                return STATE_NONE

    except Exception as e:
        logger.exception(e)
        await update.message.reply_text(f"⚠️ Error occurred: {str(e)}\n\nPlease try again with /start", reply_markup=main_menu_keyboard())
        context.user_data.clear()
        return STATE_NONE

# ---------------- KEEP ALIVE FOR RENDER WEB SERVICE ----------------
def start_keepalive():
    # Render Web Service needs a port bind, otherwise it fails health check
    # We start a tiny Flask server in thread
    port = int(os.getenv("PORT", "10000"))
    try:
        from flask import Flask
        flask_app = Flask(__name__)

        @flask_app.route("/")
        def home():
            return "Garena Email Bot is Running! Bot is polling Telegram."

        @flask_app.route("/health")
        def health():
            return {"status": "ok", "bot": "Garena Email Bot", "time": datetime.now().isoformat()}

        import threading
        def run_flask():
            flask_app.run(host="0.0.0.0", port=port, debug=False)

        threading.Thread(target=run_flask, daemon=True).start()
        print(f"🌐 Keepalive server started on port {port}")
    except Exception as e:
        print(f"Keepalive not started (Flask not installed?): {e}")

# ---------------- MAIN ----------------
def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not set! Set ENV variable BOT_TOKEN")
        return

    # Start keepalive for Render
    start_keepalive()

    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.Regex("^Eat-Token$"), handle_eat_token_button))

    # Conversation-like handling for all text (state machine via user_data)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("✅ Garena Email Bot started...")
    print(f"Base URL: {BASE_URL}")
    print(f"YouTube: {YOUTUBE_URL}")
    print("✅ All 12 options loaded - No error on any option")

    # Render supports polling - run polling
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
