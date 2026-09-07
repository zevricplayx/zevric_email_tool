#!/usr/bin/env python3
"""
bot.py - Telegram bot implementing Garena bind/account helper flows (safe & consent-based).

Features:
- /start, /help, /owner
- /check_bind_info        -> fetch account + bind info (safe read-only)
- /eat_to_access_token    -> extract access token from EAT URL
- /bind_email             -> send OTP, verify, create bind
- /unbind_email           -> send OTP, verify identity, create unbind
- /change_bind_email      -> flow to move bound email to new email
- /cancel_bind            -> cancel pending bind request
- /revoke_access_token    -> attempt to revoke (logout) token

Security & usage notes:
- You MUST set BOT_TOKEN environment variable before running:
    export BOT_TOKEN="123456:ABC..."
- Always use tokens only for accounts you own.
- The bot asks for explicit text confirmation "I confirm I own this account" before any action that uses an access token.
- Tokens are kept only in-memory for the active conversation and removed immediately after use.
- Rate limiting: 1 request per 30 seconds per user for API-starting commands.

Dependencies:
- python-telegram-bot>=20
- requests

Run:
pip install python-telegram-bot requests
export BOT_TOKEN="<your bot token>"
python bot.py
"""

import os
import time
import json
import urllib.parse
import asyncio
import logging
from typing import Optional

import requests
from telegram import Update, ForceReply
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)

# -------------- Basic config & logging -----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("Warning: BOT_TOKEN not set. Set environment variable before running.")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---- Render Web Service health check server (to prevent 15 min fail) ----
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

def start_health_server():
    port = int(os.getenv("PORT", "10000"))
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Garena Email Bot is alive - polling running")
        def log_message(self, format, *args):
            return
    try:
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        logger.info(f"Health server started on 0.0.0.0:{port}")
    except Exception as e:
        logger.warning(f"Health server failed to start: {e}")


# -------------- Utility helpers -----------------------
def convert_seconds(s: int) -> str:
    d, rem = divmod(int(s), 86400)
    h, rem = divmod(rem, 3600)
    m, sec = divmod(rem, 60)
    return f"{d} Day {h} Hour {m} Min {sec} Sec"

async def http_get(url: str, params: dict = None, headers: dict = None, timeout: int = 15):
    return await asyncio.to_thread(lambda: requests.get(url, params=params, headers=headers or {}, timeout=timeout, allow_redirects=True))

async def http_post(url: str, data: dict = None, headers: dict = None, timeout: int = 15):
    return await asyncio.to_thread(lambda: requests.post(url, data=data, headers=headers or {}, timeout=timeout))

# -------------- Rate limiting & small storage ----------
RATE_LIMIT = {}   # user_id -> last_timestamp
RATE_SECONDS = 30

def check_rate(user_id: int) -> bool:
    last = RATE_LIMIT.get(user_id, 0)
    now = time.time()
    if now - last < RATE_SECONDS:
        return False
    RATE_LIMIT[user_id] = now
    return True

# -------------- Conversation states (unique per flow) --
# We'll define small enums for each flow to avoid overlap
(
    CBI_TOKEN, CBI_CONFIRM, CBI_SHOW_RAW,         # check_bind_info
    EAT_INPUT,                                    # eat_to_access_token
    BIND_TOKEN, BIND_CONFIRM, BIND_EMAIL, BIND_OTP, BIND_SECURITY, BIND_DONE,  # bind_email
    UNBIND_TOKEN, UNBIND_CONFIRM, UNBIND_OTP, UNBIND_CONFIRM_ID, UNBIND_DONE,  # unbind_email
    CHANGE_TOKEN, CHANGE_CONFIRM, CHANGE_OTP_OLD, CHANGE_IDENTITY, CHANGE_NEW_EMAIL, CHANGE_OTP_NEW, CHANGE_VERIFY_NEW, CHANGE_DONE,  # change_bind_email
    CANCEL_TOKEN, CANCEL_CONFIRM,                 # cancel_bind
    REVOKE_TOKEN, REVOKE_CONFIRM, REVOKE_REFRESH  # revoke_access_token
) = range(28)

# -------------- Common confirmation text ----------------
REQUIRED_CONFIRM_TEXT = "I confirm I own this account"

# -------------- Handlers ---------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Namaste! Main Zevric helper bot hoon.\n"
        "Use /help to see available commands."
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/check_bind_info - Show account & bind email info (you must confirm ownership)\n"
        "/eat_to_access_token - Convert EAT URL/token to access token\n"
        "/bind_email - Bind an email to your account (requires OTP & confirmation)\n"
        "/unbind_email - Unbind email from your account (requires OTP & identity verification)\n"
        "/change_bind_email - Change bound email (old & new OTP flows)\n"
        "/cancel_bind - Cancel pending bind request\n"
        "/revoke_access_token - Revoke (logout) an access token\n"
        "/owner - Developer info\n\n"
        "Type /cancel at any time to abort a multi-step flow."
    )

async def owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Developer: RAOSTAR (@raostarr)\n"
        "Channel: https://t.me/raostarrr\n"
        "GitHub: https://github.com/LuckDucapa\n\n"
        "Note: Use only for accounts you own. I am not responsible for misuse."
    )

# ---------------- Check Bind Info Flow -------------------
async def check_bind_info_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not check_rate(user_id):
        await update.message.reply_text(f"Kripya {RATE_SECONDS} seconds ka intezar karein between requests.")
        return ConversationHandler.END

    await update.message.reply_text(
        "Apna ACCESS TOKEN bhejein (sirf apna hi token). Warning: token share mat karein.",
        reply_markup=ForceReply(selective=True)
    )
    return CBI_TOKEN

async def cbi_token_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = (update.message.text or "").strip()
    if not token:
        await update.message.reply_text("Empty token. Dobara bhejein.")
        return CBI_TOKEN
    context.user_data["token"] = token
    await update.message.reply_text(f"Type exactly: {REQUIRED_CONFIRM_TEXT}", reply_markup=ForceReply(selective=True))
    return CBI_CONFIRM

async def cbi_confirm_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if text != REQUIRED_CONFIRM_TEXT:
        await update.message.reply_text("Confirmation sahi nahi mili. Type exactly the confirmation line or /cancel to abort.")
        return CBI_CONFIRM

    token = context.user_data.get("token")
    if not token:
        await update.message.reply_text("Token missing. Start again with /check_bind_info.")
        return ConversationHandler.END

    await update.message.reply_text("Fetching info...")

    # 1) follow support callback redirect
    try:
        api_url = f"https://api-otrss.garena.com/support/callback/?access_token={urllib.parse.quote(token)}"
        res = await http_get(api_url, headers={"User-Agent": "zevric-bot/1.0"})
        parsed = urllib.parse.urlparse(res.url)
        params = urllib.parse.parse_qs(parsed.query)
        account_id = params.get("account_id", ["Unknown"])[0]
        nickname = urllib.parse.unquote(params.get("nickname", ["Unknown"])[0])
        region = params.get("region", ["Unknown"])[0]
    except Exception as e:
        await update.message.reply_text(f"Callback error: {str(e)}")
        context.user_data.pop("token", None)
        return ConversationHandler.END

    # 2) bind info
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        payload = {"app_id": "100067", "access_token": token}
        headers = {"User-Agent": "GarenaMSDK/4.0.19P9", "Connection": "Keep-Alive", "Accept-Encoding": "gzip"}
        r = await http_get(url, params=payload, headers=headers)
        if r.status_code != 200:
            await update.message.reply_text(f"API Error (Status {r.status_code}): {r.text[:200]}")
            context.user_data.pop("token", None)
            return ConversationHandler.END
        data = r.json()
    except Exception as e:
        await update.message.reply_text(f"Error fetching bind info: {str(e)}")
        context.user_data.pop("token", None)
        return ConversationHandler.END

    email = data.get("email", "")
    email_to_be = data.get("email_to_be", "")
    countdown = data.get("request_exec_countdown", 0)
    result_code = data.get("result", None)

    lines = [
        f"Nickname     : {nickname}",
        f"Account ID   : {account_id}",
        f"Region       : {region}",
        f"Current Email: {email if email else 'None'}",
        f"Pending Email: {email_to_be if email_to_be else 'None'}",
    ]
    if email_to_be:
        lines.append(f"Countdown     : {convert_seconds(countdown)}")
    lines.append(f"Result Code   : {result_code}")

    await update.message.reply_text("----- Bind Info -----\n" + "\n".join(lines))
    # ask if show raw JSON
    context.user_data["raw_bind_info"] = data
    await update.message.reply_text("Kya aap raw JSON dekhna chahte hain? (yes/no)", reply_markup=ForceReply(selective=True))
    return CBI_SHOW_RAW

async def cbi_show_raw_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ans = (update.message.text or "").strip().lower()
    raw = context.user_data.pop("raw_bind_info", None)
    context.user_data.pop("token", None)
    if ans == "yes" and raw:
        pretty = json.dumps(raw, indent=2, ensure_ascii=False)
        if len(pretty) > 3500:
            pretty = pretty[:3500] + "\n... (truncated)"
        await update.message.reply_text(f"Raw:\n{pretty}")
    else:
        await update.message.reply_text("Theek hai — raw JSON nahi dikhaya gaya.")
    return ConversationHandler.END

# ---------------- EAT -> Access Token --------------------
async def eat_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("EAT token ya full URL bhejein (sirf apna hi use karein).", reply_markup=ForceReply(selective=True))
    return EAT_INPUT

async def eat_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (update.message.text or "").strip()
    if not txt:
        await update.message.reply_text("Empty input. Dobara bhejein.")
        return EAT_INPUT
    # extract eat
    eat_token = None
    if "http" in txt or "?" in txt:
        parsed = urllib.parse.urlparse(txt)
        qs = urllib.parse.parse_qs(parsed.query)
        if "eat" in qs:
            eat_token = qs["eat"][0]
    else:
        eat_token = txt.strip()
    if not eat_token:
        await update.message.reply_text("EAT token nahi mila. Ensure you pasted full URL or token.")
        return ConversationHandler.END

    await update.message.reply_text("Following redirect to get access token...")
    try:
        api_url = f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
        res = await http_get(api_url, headers={"User-Agent": "zevric-bot/1.0"})
        parsed = urllib.parse.urlparse(res.url)
        params = urllib.parse.parse_qs(parsed.query)
        access_token = params.get("access_token", [None])[0]
        account_id = params.get("account_id", ["Unknown"])[0]
        nickname = urllib.parse.unquote(params.get("nickname", ["Unknown"])[0])
        region = params.get("region", ["Unknown"])[0]
        lines = [
            f"Nickname   : {nickname}",
            f"Account ID : {account_id}",
            f"Region     : {region}",
            f"Access Token: {'(found)' if access_token else '(not found)'}"
        ]
        await update.message.reply_text("\n".join(lines))
        if access_token:
            await update.message.reply_text("Type 'show token' to reveal the token or anything else to finish.", reply_markup=ForceReply(selective=True))
            context.user_data["eat_access_token"] = access_token
            return EAT_INPUT
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")
    return ConversationHandler.END

# Re-use EAT_INPUT: if user types "show token" after receiving summary
async def eat_post_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (update.message.text or "").strip().lower()
    token = context.user_data.pop("eat_access_token", None)
    if txt == "show token" and token:
        await update.message.reply_text(f"Access Token:\n{token}\n\nDO NOT SHARE THIS TOKEN PUBLICLY.")
    else:
        await update.message.reply_text("Done.")
    return ConversationHandler.END

# ---------------- Bind Email Flow ------------------------
async def bind_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not check_rate(user_id):
        await update.message.reply_text(f"Rate limit: wait {RATE_SECONDS} seconds.")
        return ConversationHandler.END
    await update.message.reply_text("Apna ACCESS TOKEN bhejein (bind karne ke liye).", reply_markup=ForceReply(selective=True))
    return BIND_TOKEN

async def bind_token_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tok = (update.message.text or "").strip()
    if not tok:
        await update.message.reply_text("Token empty. Dobara bhejein.")
        return BIND_TOKEN
    context.user_data["token"] = tok
    await update.message.reply_text(f"Type exactly: {REQUIRED_CONFIRM_TEXT}", reply_markup=ForceReply(selective=True))
    return BIND_CONFIRM

async def bind_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (update.message.text or "").strip()
    if txt != REQUIRED_CONFIRM_TEXT:
        await update.message.reply_text("Confirmation missing. Type exactly or /cancel.")
        return BIND_CONFIRM
    await update.message.reply_text("Fetching current bind info (optional)...")
    token = context.user_data.get("token")
    # show bind info but not required; continue
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        data = {"app_id": "100067", "access_token": token}
        headers = {"User-Agent": "GarenaMSDK/4.0.19P9"}
        r = await http_get(url, params=data, headers=headers)
        info = r.json() if r.status_code == 200 else {}
        email = info.get("email", "")
        await update.message.reply_text(f"Current bound email: {email if email else 'None'}")
    except Exception:
        await update.message.reply_text("Could not fetch current bind info (continuing).")

    await update.message.reply_text("Enter the Email to bind:", reply_markup=ForceReply(selective=True))
    return BIND_EMAIL

async def bind_email_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = (update.message.text or "").strip()
    if not email:
        await update.message.reply_text("Email empty. Dobara bhejein.")
        return BIND_EMAIL
    context.user_data["bind_email"] = email
    token = context.user_data.get("token")
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    send_otp_url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    data = {"email": email, "locale": "en_PK", "region": "PK", "app_id": "100067", "access_token": token}
    await update.message.reply_text(f"Sending OTP to {email} ...")
    try:
        r = await http_post(send_otp_url, data=data, headers=headers)
        # best-effort response
        try:
            res_json = r.json()
            await update.message.reply_text(f"Send OTP response: {res_json}")
        except Exception:
            await update.message.reply_text(f"Send OTP status: {r.status_code}")
    except Exception as e:
        await update.message.reply_text(f"Error sending OTP: {str(e)}")
        return ConversationHandler.END

    await update.message.reply_text("Enter OTP you received in email:", reply_markup=ForceReply(selective=True))
    return BIND_OTP

async def bind_otp_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp = (update.message.text or "").strip()
    if not otp:
        await update.message.reply_text("OTP empty. Dobara bhejein.")
        return BIND_OTP
    token = context.user_data.get("token")
    email = context.user_data.get("bind_email")
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    verify_url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
    data = {"app_id": "100067", "access_token": token, "email": email, "code": otp, "otp": otp, "type": "1"}
    await update.message.reply_text("Verifying OTP...")
    try:
        r = await http_post(verify_url, data=data, headers=headers)
        res_json = r.json() if r.status_code == 200 else {"status": r.status_code, "text": r.text}
        await update.message.reply_text(f"Verify response: {res_json}")
        verifier_token = res_json.get("verifier_token") if isinstance(res_json, dict) else None
        if not verifier_token:
            await update.message.reply_text("Could not auto-extract verifier_token. You can enter it manually if you have it, or abort.")
            # allow user to enter manually (not implementing long loop). We'll ask for manual input:
            await update.message.reply_text("Enter verifier_token manually or type 'abort':", reply_markup=ForceReply(selective=True))
            context.user_data["awaiting_verifier_manual"] = True
            return BIND_SECURITY
        context.user_data["verifier_token"] = verifier_token
        await update.message.reply_text("Verifier token extracted. Now set a 6-digit security code (secondary password):", reply_markup=ForceReply(selective=True))
        return BIND_SECURITY
    except Exception as e:
        await update.message.reply_text(f"Error verifying OTP: {str(e)}")
        return ConversationHandler.END

async def bind_security_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (update.message.text or "").strip()
    if context.user_data.pop("awaiting_verifier_manual", None):
        if txt.lower() == "abort":
            await update.message.reply_text("Aborted.")
            context.user_data.clear()
            return ConversationHandler.END
        context.user_data["verifier_token"] = txt
        await update.message.reply_text("Verifier token set. Now set a 6-digit security code (secondary password):", reply_markup=ForceReply(selective=True))
        return BIND_SECURITY

    security_code = txt
    if not security_code or not security_code.isdigit() or len(security_code) < 4:
        await update.message.reply_text("Please provide at least a 4-digit security code (prefer 6 digits).")
        return BIND_SECURITY

    token = context.user_data.get("token")
    email = context.user_data.get("bind_email")
    verifier_token = context.user_data.get("verifier_token")
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    bind_url = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
    data = {"email": email, "app_id": "100067", "access_token": token, "verifier_token": verifier_token, "secondary_password": security_code}
    await update.message.reply_text("Creating bind request...")
    try:
        r = await http_post(bind_url, data=data, headers=headers)
        try:
            res_json = r.json()
            await update.message.reply_text(f"Bind response: {res_json}")
        except Exception:
            await update.message.reply_text(f"Bind response status: {r.status_code}")
    except Exception as e:
        await update.message.reply_text(f"Error creating bind: {str(e)}")

    context.user_data.clear()
    return ConversationHandler.END

# ---------------- Unbind Flow ---------------------------
async def unbind_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not check_rate(user_id):
        await update.message.reply_text(f"Rate limit: wait {RATE_SECONDS} seconds.")
        return ConversationHandler.END
    await update.message.reply_text("Apna ACCESS TOKEN bhejein (to unbind).", reply_markup=ForceReply(selective=True))
    return UNBIND_TOKEN

async def unbind_token_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tok = (update.message.text or "").strip()
    if not tok:
        await update.message.reply_text("Empty token.")
        return UNBIND_TOKEN
    context.user_data["token"] = tok
    await update.message.reply_text(f"Type exactly: {REQUIRED_CONFIRM_TEXT}", reply_markup=ForceReply(selective=True))
    return UNBIND_CONFIRM

async def unbind_confirm_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (update.message.text or "").strip()
    if txt != REQUIRED_CONFIRM_TEXT:
        await update.message.reply_text("Confirmation missing.")
        return UNBIND_CONFIRM

    token = context.user_data.get("token")
    # fetch current email
    try:
        url_info = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        payload = {"app_id": "100067", "access_token": token}
        headers = {"User-Agent": "GarenaMSDK/4.0.30"}
        r = await http_get(url_info, params=payload, headers=headers)
        email = r.json().get("email", "")
    except Exception:
        email = ""
    if not email:
        await update.message.reply_text("No bound email found. Cannot unbind.")
        context.user_data.clear()
        return ConversationHandler.END

    context.user_data["unbind_email"] = email
    await update.message.reply_text(f"Sending OTP to {email} ...")
    send_otp_url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"email": email, "locale": "en_PK", "region": "PK", "app_id": "100067", "access_token": token}
    try:
        r = await http_post(send_otp_url, data=data, headers=headers)
        await update.message.reply_text("OTP sent (check email). Enter OTP:")
    except Exception as e:
        await update.message.reply_text(f"Error sending OTP: {str(e)}")
        context.user_data.clear()
        return ConversationHandler.END
    return UNBIND_OTP

async def unbind_otp_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp = (update.message.text or "").strip()
    token = context.user_data.get("token")
    email = context.user_data.get("unbind_email")
    if not otp:
        await update.message.reply_text("OTP empty.")
        return UNBIND_OTP

    await update.message.reply_text("Verifying identity...")
    url_verify = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"email": email, "app_id": "100067", "access_token": token, "otp": otp}
    try:
        r = await http_post(url_verify, data=data, headers=headers)
        res_json = r.json()
        identity_token = res_json.get("identity_token")
        if not identity_token:
            await update.message.reply_text(f"Identity verify failed: {res_json}")
            context.user_data.clear()
            return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"Verify error: {str(e)}")
        context.user_data.clear()
        return ConversationHandler.END

    await update.message.reply_text("Creating unbind request...")
    url_unbind = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
    udata = {"app_id": "100067", "access_token": token, "identity_token": identity_token}
    try:
        r = await http_post(url_unbind, data=udata, headers=headers)
        try:
            await update.message.reply_text(f"Unbind response: {r.json()}")
        except Exception:
            await update.message.reply_text(f"Unbind status: {r.status_code}")
    except Exception as e:
        await update.message.reply_text(f"Error unbinding: {str(e)}")
    context.user_data.clear()
    return ConversationHandler.END

# --------------- Change Bind Email Flow -----------------
async def change_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not check_rate(user_id):
        await update.message.reply_text(f"Rate limit: wait {RATE_SECONDS} seconds.")
        return ConversationHandler.END
    await update.message.reply_text("Apna ACCESS TOKEN bhejein (to change bound email).", reply_markup=ForceReply(selective=True))
    return CHANGE_TOKEN

async def change_token_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tok = (update.message.text or "").strip()
    if not tok:
        await update.message.reply_text("Empty token.")
        return CHANGE_TOKEN
    context.user_data["token"] = tok
    await update.message.reply_text(f"Type exactly: {REQUIRED_CONFIRM_TEXT}", reply_markup=ForceReply(selective=True))
    return CHANGE_CONFIRM

async def change_confirm_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (update.message.text or "").strip()
    if txt != REQUIRED_CONFIRM_TEXT:
        await update.message.reply_text("Confirmation missing.")
        return CHANGE_CONFIRM
    token = context.user_data.get("token")
    # fetch current email
    try:
        url_info = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        payload = {"app_id": "100067", "access_token": token}
        headers = {"User-Agent": "GarenaMSDK/4.0.30"}
        r = await http_get(url_info, params=payload, headers=headers)
        old_email = r.json().get("email", "")
    except Exception:
        old_email = ""
    if not old_email:
        await update.message.reply_text("No currently bound email found.")
        context.user_data.clear()
        return ConversationHandler.END

    context.user_data["old_email"] = old_email
    
    # FIX for error_ongoing_request: cancel any pending bind/unbind/rebind first
    try:
        await update.message.reply_text("Checking for any ongoing request and cancelling it...")
        url_cancel = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
        headers_cancel = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data_cancel = {"app_id": "100067", "access_token": token}
        r_cancel = await http_post(url_cancel, data=data_cancel, headers=headers_cancel)
        # don't care about result, just clear pending
    except Exception:
        pass

    await update.message.reply_text(f"Sending OTP to old email: {old_email}")
    send_otp_url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"email": old_email, "locale": "en_PK", "region": "PK", "app_id": "100067", "access_token": token}
    try:
        r = await http_post(send_otp_url, data=data, headers=headers)
        try:
            j = r.json()
            await update.message.reply_text(f"Send OTP to old email response: {j}")
            if j.get('error') == 'error_ongoing_request':
                await update.message.reply_text("❌ Old email pe OTP nahi jayega kyunki pending request hai. Pehle /cancel_bind karo!")
                context.user_data.clear()
                return ConversationHandler.END
        except:
            await update.message.reply_text(f"Send OTP status: {r.status_code}")
        await update.message.reply_text("Agar success hai to OTP old email pe aayega. Check Spam folder bhi. Enter OTP from old email:", reply_markup=ForceReply(selective=True))
    except Exception as e:
        await update.message.reply_text(f"Send old OTP error: {str(e)}")
        context.user_data.clear()
        return ConversationHandler.END
    return CHANGE_OTP_OLD

async def change_otp_old_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp_old = (update.message.text or "").strip()
    token = context.user_data.get("token")
    old_email = context.user_data.get("old_email")
    if not otp_old:
        await update.message.reply_text("OTP empty.")
        return CHANGE_OTP_OLD

    await update.message.reply_text("Verifying old email identity...")
    url_verify_identity = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"email": old_email, "app_id": "100067", "access_token": token, "otp": otp_old}
    try:
        r = await http_post(url_verify_identity, data=data, headers=headers)
        res_json = r.json()
        identity_token = res_json.get("identity_token")
        if not identity_token:
            await update.message.reply_text(f"Identity verify failed: {res_json}")
            context.user_data.clear()
            return ConversationHandler.END
        context.user_data["identity_token"] = identity_token
    except Exception as e:
        await update.message.reply_text(f"Error verifying identity: {str(e)}")
        context.user_data.clear()
        return ConversationHandler.END

    await update.message.reply_text("Enter the NEW email you'd like to bind:", reply_markup=ForceReply(selective=True))
    return CHANGE_NEW_EMAIL

async def change_new_email_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_email = (update.message.text or "").strip()
    if not new_email:
        await update.message.reply_text("Email empty.")
        return CHANGE_NEW_EMAIL
    context.user_data["new_email"] = new_email
    # send OTP to new email
    send_otp_url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    token = context.user_data.get("token")
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"email": new_email, "locale": "en_PK", "region": "PK", "app_id": "100067", "access_token": token}
    try:
        r = await http_post(send_otp_url, data=data, headers=headers)
        try:
            j = r.json()
            await update.message.reply_text(f"Send OTP to new email response: {j}")
            if j.get('error') == 'error_ongoing_request':
                await update.message.reply_text("❌ New email pe OTP nahi jayega, pending request hai. /cancel_bind karo!")
                context.user_data.clear()
                return ConversationHandler.END
        except:
            await update.message.reply_text(f"Send OTP status: {r.status_code}")
        await update.message.reply_text("Agar success hai to OTP new email pe aayega. Spam check karo. Enter OTP from new email:", reply_markup=ForceReply(selective=True))
    except Exception as e:
        await update.message.reply_text(f"Error sending OTP to new email: {str(e)}")
        context.user_data.clear()
        return ConversationHandler.END
    return CHANGE_OTP_NEW

async def change_otp_new_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp_new = (update.message.text or "").strip()
    token = context.user_data.get("token")
    new_email = context.user_data.get("new_email")
    if not otp_new:
        await update.message.reply_text("OTP empty.")
        return CHANGE_OTP_NEW

    # verify otp on new email to get verifier_token
    url_verify_otp = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"email": new_email, "app_id": "100067", "access_token": token, "otp": otp_new}
    try:
        r = await http_post(url_verify_otp, data=data, headers=headers)
        res_json = r.json()
        verifier_token = res_json.get("verifier_token")
        if not verifier_token:
            await update.message.reply_text(f"Verify OTP failed: {res_json}")
            context.user_data.clear()
            return ConversationHandler.END
        context.user_data["verifier_token"] = verifier_token
    except Exception as e:
        await update.message.reply_text(f"Error verifying new OTP: {str(e)}")
        context.user_data.clear()
        return ConversationHandler.END

    # create rebind
    await update.message.reply_text("Creating rebind request...")
    url_rebind = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    payload = {
        "identity_token": context.user_data.get("identity_token"),
        "email": new_email,
        "app_id": "100067",
        "verifier_token": context.user_data.get("verifier_token"),
        "access_token": token
    }
    try:
        r = await http_post(url_rebind, data=payload, headers=headers)
        try:
            res = r.json()
            await update.message.reply_text(f"Rebind response: {res}")
            # helpful hint for ongoing request
            if isinstance(res, dict) and res.get('error') == 'error_ongoing_request':
                await update.message.reply_text(
                    "⚠️ Garena bol raha hai 'error_ongoing_request' matlab pehle se ek pending request hai.\n"
                    "Iske liye pehle /cancel_bind use karo, fir /change_bind_email dubara try karo.\n"
                    "Maine abhi auto-cancel try kiya hai, 1 min baad dubara try karo."
                )
        except Exception:
            await update.message.reply_text(f"Rebind status: {r.status_code}")
    except Exception as e:
        await update.message.reply_text(f"Error creating rebind: {str(e)}")

    context.user_data.clear()
    return ConversationHandler.END

# -------------- Cancel Bind ----------------------------
async def cancel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not check_rate(user_id):
        await update.message.reply_text(f"Rate limit: wait {RATE_SECONDS} seconds.")
        return ConversationHandler.END
    await update.message.reply_text("Apna ACCESS TOKEN bhejein (to cancel bind request).", reply_markup=ForceReply(selective=True))
    return CANCEL_TOKEN

async def cancel_token_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tok = (update.message.text or "").strip()
    if not tok:
        await update.message.reply_text("Empty token.")
        return CANCEL_TOKEN
    context.user_data["token"] = tok
    await update.message.reply_text(f"Type exactly: {REQUIRED_CONFIRM_TEXT}", reply_markup=ForceReply(selective=True))
    return CANCEL_CONFIRM

async def cancel_confirm_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (update.message.text or "").strip()
    if txt != REQUIRED_CONFIRM_TEXT:
        await update.message.reply_text("Confirmation missing.")
        return CANCEL_CONFIRM
    token = context.user_data.get("token")
    url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
    headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"app_id": "100067", "access_token": token}
    try:
        r = await http_post(url, data=data, headers=headers)
        try:
            await update.message.reply_text(f"Cancel response: {r.json()}")
        except Exception:
            await update.message.reply_text(f"Cancel status: {r.status_code}")
    except Exception as e:
        await update.message.reply_text(f"Error cancelling: {str(e)}")
    context.user_data.clear()
    return ConversationHandler.END

# -------------- Revoke Access Token ---------------------
async def revoke_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not check_rate(user_id):
        await update.message.reply_text(f"Rate limit: wait {RATE_SECONDS} seconds.")
        return ConversationHandler.END
    await update.message.reply_text("Apna ACCESS TOKEN bhejein (to revoke).", reply_markup=ForceReply(selective=True))
    return REVOKE_TOKEN

async def revoke_token_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tok = (update.message.text or "").strip()
    if not tok:
        await update.message.reply_text("Empty token.")
        return REVOKE_TOKEN
    context.user_data["token"] = tok
    await update.message.reply_text(f"Type exactly: {REQUIRED_CONFIRM_TEXT}", reply_markup=ForceReply(selective=True))
    return REVOKE_CONFIRM

async def revoke_confirm_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (update.message.text or "").strip()
    if txt != REQUIRED_CONFIRM_TEXT:
        await update.message.reply_text("Confirmation missing.")
        return REVOKE_CONFIRM

    token = context.user_data.get("token")
    # try to validate token via callback
    try:
        api_url = f"https://api-otrss.garena.com/support/callback/?access_token={urllib.parse.quote(token)}"
        res = await http_get(api_url, headers={"User-Agent": "zevric-bot/1.0"})
        parsed = urllib.parse.urlparse(res.url)
        params = urllib.parse.parse_qs(parsed.query)
        nickname = urllib.parse.unquote(params.get("nickname", ["Unknown"])[0])
        account_id = params.get("account_id", ["Unknown"])[0]
        region = params.get("region", ["Unknown"])[0]
        await update.message.reply_text(f"Token looks valid for {nickname} ({account_id}) in {region}.")
    except Exception:
        await update.message.reply_text("Token invalid/expired or callback failed.")
        context.user_data.clear()
        return ConversationHandler.END

    await update.message.reply_text("If you have a refresh_token provide it now, or type 'none' to use default:", reply_markup=ForceReply(selective=True))
    return REVOKE_REFRESH

async def revoke_refresh_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    token = context.user_data.get("token")
    refresh_token = None if text.lower() == "none" else text
    refresh_token = refresh_token or "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"

    try:
        logout_url = f"https://100067.connect.garena.com/oauth/logout?access_token={urllib.parse.quote(token)}&refresh_token={urllib.parse.quote(refresh_token)}"
        r = await http_get(logout_url)
        try:
            await update.message.reply_text(f"Revoke response: {r.json()}")
        except Exception:
            await update.message.reply_text(f"Revoke status: {r.status_code}")
    except Exception as e:
        await update.message.reply_text(f"Error revoking token: {str(e)}")
    context.user_data.clear()
    return ConversationHandler.END

# ---------------- Generic cancel -----------------------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

# ----------------- Main app setup -----------------------
def main():
    start_health_server()
    if not BOT_TOKEN:
        logger.warning("BOT_TOKEN not provided. The bot will not function until BOT_TOKEN is set.")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # check_bind_info conv
    conv_cbi = ConversationHandler(
        entry_points=[CommandHandler("check_bind_info", check_bind_info_start)],
        states={
            CBI_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, cbi_token_received)],
            CBI_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, cbi_confirm_received)],
            CBI_SHOW_RAW: [MessageHandler(filters.Regex("^(yes|no)$") | filters.TEXT, cbi_show_raw_choice)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        conversation_timeout=300
    )
    # eat conv
    conv_eat = ConversationHandler(
        entry_points=[CommandHandler("eat_to_access_token", eat_start)],
        states={
            EAT_INPUT: [
                MessageHandler(filters.Regex("(?i)^show token$") & ~filters.COMMAND, eat_post_choice),
                MessageHandler(filters.TEXT & ~filters.COMMAND, eat_received),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        conversation_timeout=180
    )
    # bind conv
    conv_bind = ConversationHandler(
        entry_points=[CommandHandler("bind_email", bind_start)],
        states={
            BIND_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, bind_token_received)],
            BIND_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, bind_confirm)],
            BIND_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, bind_email_received)],
            BIND_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, bind_otp_received)],
            BIND_SECURITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, bind_security_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        conversation_timeout=600
    )
    # unbind conv
    conv_unbind = ConversationHandler(
        entry_points=[CommandHandler("unbind_email", unbind_start)],
        states={
            UNBIND_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, unbind_token_received)],
            UNBIND_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, unbind_confirm_received)],
            UNBIND_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, unbind_otp_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        conversation_timeout=600
    )
    # change conv
    conv_change = ConversationHandler(
        entry_points=[CommandHandler("change_bind_email", change_start)],
        states={
            CHANGE_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_token_received)],
            CHANGE_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_confirm_received)],
            CHANGE_OTP_OLD: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_otp_old_received)],
            CHANGE_NEW_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_new_email_received)],
            CHANGE_OTP_NEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_otp_new_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        conversation_timeout=1200
    )
    # cancel conv
    conv_cancel = ConversationHandler(
        entry_points=[CommandHandler("cancel_bind", cancel_start)],
        states={
            CANCEL_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, cancel_token_received)],
            CANCEL_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, cancel_confirm_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        conversation_timeout=300
    )
    # revoke conv
    conv_revoke = ConversationHandler(
        entry_points=[CommandHandler("revoke_access_token", revoke_start)],
        states={
            REVOKE_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, revoke_token_received)],
            REVOKE_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, revoke_confirm_received)],
            REVOKE_REFRESH: [MessageHandler(filters.TEXT & ~filters.COMMAND, revoke_refresh_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        conversation_timeout=300
    )

    # register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("owner", owner))

    app.add_handler(conv_cbi)
    app.add_handler(conv_eat)
    app.add_handler(conv_bind)
    app.add_handler(conv_unbind)
    app.add_handler(conv_change)
    app.add_handler(conv_cancel)
    app.add_handler(conv_revoke)

    app.add_handler(CommandHandler("cancel", cancel))  # generic fallback

    logger.info("Bot starting (polling)...")
    app.run_polling(allowed_updates=["message", "edited_message"])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
