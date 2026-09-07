#!/usr/bin/env python3
"""
Zevric Email Tool - Original options with clean UI
Owner: zevric x play | TG: @just_zevric | YT: zevricxplay
"""

import os
import asyncio
import logging
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level="INFO", format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

OWNER_NAME = "zevric x play"
OWNER_TG = "just_zevric"
OWNER_YT = "zevricxplay"
YT_LINK = "https://youtube.com/@zevricxplay"

def start_health_server():
    port = int(os.getenv("PORT", "10000"))
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type","text/plain")
            self.end_headers()
            self.wfile.write(b"Zevric Bot Alive")
        def log_message(self,*a): return
    try:
        HTTPServer(("0.0.0.0",port), H).serve_forever
        server = HTTPServer(("0.0.0.0", port), H)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        logger.info(f"Health on {port}")
    except: pass

async def http_get(url, params=None, headers=None, timeout=15):
    return await asyncio.to_thread(lambda: requests.get(url, params=params, headers=headers or {}, timeout=timeout, allow_redirects=True))
async def http_post(url, data=None, headers=None, timeout=15):
    return await asyncio.to_thread(lambda: requests.post(url, data=data, headers=headers or {}, timeout=timeout))

def sub_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Subscribe YouTube Channel", url=YT_LINK)]])

def main_menu():
    kb = [
        [KeyboardButton("Check Bind Info"), KeyboardButton("Eat To Access Token")],
        [KeyboardButton("Bind Email"), KeyboardButton("Unbind Email")],
        [KeyboardButton("Change Bind Email"), KeyboardButton("Cancel Bind")],
        [KeyboardButton("Revoke Access Token"), KeyboardButton("Owner")],
        [KeyboardButton("Help")],
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

(
    CBI_TOKEN, CBI_SHOW_RAW,
    EAT_INPUT,
    BIND_TOKEN, BIND_EMAIL, BIND_OTP, BIND_SECURITY,
    UNBIND_TOKEN, UNBIND_OTP,
    CHANGE_TOKEN, CHANGE_OTP_OLD, CHANGE_NEW_EMAIL, CHANGE_OTP_NEW,
    CANCEL_TOKEN,
    REVOKE_TOKEN,
) = range(14)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Welcome to Garena Email Tool\n\nOwner: {OWNER_NAME}\nTelegram: @{OWNER_TG}\nYouTube: {OWNER_YT}\n\nChoose an option:",
        reply_markup=main_menu()
    )
    await update.message.reply_text("Support:", reply_markup=sub_keyboard())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (
        "/check_bind_info - Check account & bind email\n"
        "/eat_to_access_token - Convert EAT to token\n"
        "/bind_email - Bind new email\n"
        "/unbind_email - Unbind current email\n"
        "/change_bind_email - Change old to new email\n"
        "/cancel_bind - Cancel pending request\n"
        "/revoke_access_token - Logout token\n"
        "/owner - My details\n\n"
        "Just tap buttons below."
    )
    await update.message.reply_text(txt, reply_markup=main_menu())

async def owner_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (
        f"Developer: {OWNER_NAME}\n"
        f"Telegram: @{OWNER_TG}\n"
        f"Telegram Link: https://t.me/{OWNER_TG}\n"
        f"YouTube: {OWNER_YT}\n"
        f"YouTube Link: {YT_LINK}"
    )
    await update.message.reply_text(txt, reply_markup=sub_keyboard())

# ---- Check Bind Info ----
async def check_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please enter your access token:")
    return CBI_TOKEN

async def cbi_token_recv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip()
    await update.message.reply_text("Fetching info...")
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        r = await http_get(url, params={"app_id":"100067","access_token":token}, headers={"User-Agent":"GarenaMSDK/4.0.30"})
        d = r.json()
        nick = d.get("nickname","Unknown")
        acc = d.get("account_id","Unknown")
        cur = d.get("email","Not bound")
        pend = d.get("pending_email","None")
        cd = d.get("countdown",0)
        sec = int(cd)
        days, rem = divmod(sec, 86400)
        hrs, rem = divmod(rem, 3600)
        mins, secs = divmod(rem, 60)
        count = f"{days} Day {hrs} Hour {mins} Min {secs} Sec"
        msg = f"----- Bind Info -----\nNickname : {nick}\nAccount ID : {acc}\nCurrent Email: {cur}\nPending Email: {pend}\nCountdown : {count}\nResult Code : 0"
        await update.message.reply_text(msg)
        await update.message.reply_text("Raw JSON dekhna hai? (yes/no)")
        context.user_data["last"] = d
        return CBI_SHOW_RAW
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
        return ConversationHandler.END

async def cbi_raw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() == "yes":
        await update.message.reply_text(f"{context.user_data.get('last')}")
    await update.message.reply_text("Main Menu:", reply_markup=main_menu())
    await update.message.reply_text("Support:", reply_markup=sub_keyboard())
    context.user_data.clear()
    return ConversationHandler.END

# ---- Eat to Token ----
async def eat_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send EAT URL or token:")
    return EAT_INPUT

async def eat_recv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    try:
        # try parse token from URL
        if "access_token=" in txt:
            parsed = urllib.parse.urlparse(txt)
            qs = urllib.parse.parse_qs(parsed.query)
            tok = qs.get("access_token",[txt])[0]
        else:
            tok = txt
        await update.message.reply_text(f"Access Token: {tok}", reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    await update.message.reply_text("Main Menu:", reply_markup=main_menu())
    return ConversationHandler.END

# ---- Bind ----
async def bind_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please enter your access token:")
    return BIND_TOKEN
async def bind_tok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["token"] = update.message.text.strip()
    await update.message.reply_text("Enter email to bind:")
    return BIND_EMAIL
async def bind_email_recv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    context.user_data["email"] = email
    token = context.user_data["token"]
    url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    data = {"email":email,"locale":"en_PK","region":"PK","app_id":"100067","access_token":token}
    h = {"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
    try:
        r = await http_post(url, data=data, headers=h)
        j = r.json()
        if j.get("error") == "error_ongoing_request":
            await update.message.reply_text("Pending request hai. /cancel_bind karo pehle.")
            return ConversationHandler.END
        await update.message.reply_text(f"OTP sent to {email}. Enter OTP:")
        return BIND_OTP
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
        return ConversationHandler.END
async def bind_otp_recv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp = update.message.text.strip()
    token = context.user_data["token"]
    email = context.user_data["email"]
    url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
    data = {"app_id":"100067","access_token":token,"email":email,"code":otp,"otp":otp,"type":"1"}
    h = {"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
    try:
        r = await http_post(url, data=data, headers=h)
        j = r.json()
        vt = j.get("verifier_token")
        if not vt:
            await update.message.reply_text(f"Verify failed: {j}")
            return ConversationHandler.END
        context.user_data["vt"] = vt
        await update.message.reply_text("Enter 6-digit security code:")
        return BIND_SECURITY
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
        return ConversationHandler.END
async def bind_sec_recv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    token = context.user_data["token"]
    email = context.user_data["email"]
    vt = context.user_data["vt"]
    url = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
    data = {"email":email,"app_id":"100067","access_token":token,"verifier_token":vt,"secondary_password":code}
    h = {"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
    try:
        r = await http_post(url, data=data, headers=h)
        await update.message.reply_text(f"Bind response: {r.json()}", reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    await update.message.reply_text("Main Menu:", reply_markup=main_menu())
    context.user_data.clear()
    return ConversationHandler.END

# ---- Unbind ----
async def unbind_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please enter your access token:")
    return UNBIND_TOKEN
async def unbind_tok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip()
    context.user_data["token"] = token
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        r = await http_get(url, params={"app_id":"100067","access_token":token}, headers={"User-Agent":"GarenaMSDK/4.0.30"})
        email = r.json().get("email","")
    except:
        email = ""
    if not email:
        await update.message.reply_text("No bound email.")
        return ConversationHandler.END
    context.user_data["email"] = email
    url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    data = {"email":email,"locale":"en_PK","region":"PK","app_id":"100067","access_token":token}
    h = {"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
    try:
        await http_post(url, data=data, headers=h)
        await update.message.reply_text(f"Sending OTP to {email}. Enter OTP:")
        return UNBIND_OTP
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
        return ConversationHandler.END
async def unbind_otp_recv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp = update.message.text.strip()
    token = context.user_data["token"]
    email = context.user_data["email"]
    url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
    data = {"email":email,"app_id":"100067","access_token":token,"otp":otp}
    h = {"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
    try:
        r = await http_post(url, data=data, headers=h)
        it = r.json().get("identity_token")
        if not it:
            await update.message.reply_text(f"Verify failed: {r.json()}")
            return ConversationHandler.END
        url2 = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
        r2 = await http_post(url2, data={"app_id":"100067","access_token":token,"identity_token":it}, headers=h)
        await update.message.reply_text(f"Unbind response: {r2.json()}", reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    await update.message.reply_text("Main Menu:", reply_markup=main_menu())
    context.user_data.clear()
    return ConversationHandler.END

# ---- Change ----
async def change_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please enter your access token:")
    return CHANGE_TOKEN
async def change_tok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip()
    context.user_data["token"] = token
    # auto cancel pending
    try:
        await http_post("https://100067.connect.garena.com/game/account_security/bind:cancel_request", data={"app_id":"100067","access_token":token}, headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"})
    except: pass
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        r = await http_get(url, params={"app_id":"100067","access_token":token}, headers={"User-Agent":"GarenaMSDK/4.0.30"})
        old = r.json().get("email","")
    except:
        old = ""
    if not old:
        await update.message.reply_text("No bound email.")
        return ConversationHandler.END
    context.user_data["old"] = old
    url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    data = {"email":old,"locale":"en_PK","region":"PK","app_id":"100067","access_token":token}
    h = {"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
    try:
        await http_post(url, data=data, headers=h)
        await update.message.reply_text(f"Sending OTP to old email: {old}\nEnter OTP:")
        return CHANGE_OTP_OLD
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
        return ConversationHandler.END
async def change_old_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp = update.message.text.strip()
    token = context.user_data["token"]
    old = context.user_data["old"]
    url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
    data = {"email":old,"app_id":"100067","access_token":token,"otp":otp}
    h = {"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
    try:
        r = await http_post(url, data=data, headers=h)
        it = r.json().get("identity_token")
        if not it:
            await update.message.reply_text(f"Verify failed: {r.json()}")
            return ConversationHandler.END
        context.user_data["it"] = it
        await update.message.reply_text("Enter NEW email:")
        return CHANGE_NEW_EMAIL
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
        return ConversationHandler.END
async def change_new_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new = update.message.text.strip()
    context.user_data["new"] = new
    token = context.user_data["token"]
    url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    data = {"email":new,"locale":"en_PK","region":"PK","app_id":"100067","access_token":token}
    h = {"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
    try:
        await http_post(url, data=data, headers=h)
        await update.message.reply_text(f"OTP sent to new email: {new}\nEnter OTP:")
        return CHANGE_OTP_NEW
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
        return ConversationHandler.END
async def change_new_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp = update.message.text.strip()
    token = context.user_data["token"]
    new = context.user_data["new"]
    url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
    data = {"email":new,"app_id":"100067","access_token":token,"otp":otp}
    h = {"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
    try:
        r = await http_post(url, data=data, headers=h)
        vt = r.json().get("verifier_token")
        if not vt:
            await update.message.reply_text(f"Verify failed: {r.json()}")
            return ConversationHandler.END
        url2 = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
        payload = {"identity_token":context.user_data["it"],"email":new,"app_id":"100067","verifier_token":vt,"access_token":token}
        r2 = await http_post(url2, data=payload, headers=h)
        await update.message.reply_text(f"Rebind response: {r2.json()}", reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    await update.message.reply_text("Main Menu:", reply_markup=main_menu())
    context.user_data.clear()
    return ConversationHandler.END

# ---- Cancel / Revoke ----
async def cancel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please enter your access token:")
    return CANCEL_TOKEN
async def cancel_tok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip()
    url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
    h = {"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
    try:
        r = await http_post(url, data={"app_id":"100067","access_token":token}, headers=h)
        await update.message.reply_text(f"Cancel response: {r.json()}", reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    await update.message.reply_text("Main Menu:", reply_markup=main_menu())
    return ConversationHandler.END

async def revoke_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please enter your access token:")
    return REVOKE_TOKEN
async def revoke_tok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip()
    url = f"https://100067.connect.garena.com/oauth/logout?access_token={urllib.parse.quote(token)}&refresh_token=1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
    try:
        r = await http_get(url)
        await update.message.reply_text(f"Revoke response: {r.text[:500]}", reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    await update.message.reply_text("Main Menu:", reply_markup=main_menu())
    return ConversationHandler.END

async def cancel_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Cancelled. Main Menu:", reply_markup=main_menu())
    return ConversationHandler.END

def main():
    start_health_server()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_cbi = ConversationHandler(entry_points=[CommandHandler("check_bind_info", check_start), MessageHandler(filters.Regex("^Check Bind Info$"), check_start)], states={CBI_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, cbi_token_recv)], CBI_SHOW_RAW: [MessageHandler(filters.TEXT & ~filters.COMMAND, cbi_raw)]}, fallbacks=[CommandHandler("cancel", cancel_all)])
    conv_eat = ConversationHandler(entry_points=[CommandHandler("eat_to_access_token", eat_start), MessageHandler(filters.Regex("^Eat To Access Token$"), eat_start)], states={EAT_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, eat_recv)]}, fallbacks=[CommandHandler("cancel", cancel_all)])
    conv_bind = ConversationHandler(entry_points=[CommandHandler("bind_email", bind_start), MessageHandler(filters.Regex("^Bind Email$"), bind_start)], states={BIND_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, bind_tok)], BIND_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, bind_email_recv)], BIND_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, bind_otp_recv)], BIND_SECURITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, bind_sec_recv)]}, fallbacks=[CommandHandler("cancel", cancel_all)])
    conv_unbind = ConversationHandler(entry_points=[CommandHandler("unbind_email", unbind_start), MessageHandler(filters.Regex("^Unbind Email$"), unbind_start)], states={UNBIND_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, unbind_tok)], UNBIND_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, unbind_otp_recv)]}, fallbacks=[CommandHandler("cancel", cancel_all)])
    conv_change = ConversationHandler(entry_points=[CommandHandler("change_bind_email", change_start), MessageHandler(filters.Regex("^Change Bind Email$"), change_start)], states={CHANGE_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_tok)], CHANGE_OTP_OLD: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_old_otp)], CHANGE_NEW_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_new_email)], CHANGE_OTP_NEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_new_otp)]}, fallbacks=[CommandHandler("cancel", cancel_all)])
    conv_cancel = ConversationHandler(entry_points=[CommandHandler("cancel_bind", cancel_start), MessageHandler(filters.Regex("^Cancel Bind$"), cancel_start)], states={CANCEL_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, cancel_tok)]}, fallbacks=[CommandHandler("cancel", cancel_all)])
    conv_revoke = ConversationHandler(entry_points=[CommandHandler("revoke_access_token", revoke_start), MessageHandler(filters.Regex("^Revoke Access Token$"), revoke_start)], states={REVOKE_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, revoke_tok)]}, fallbacks=[CommandHandler("cancel", cancel_all)])

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("owner", owner_cmd))
    app.add_handler(conv_cbi)
    app.add_handler(conv_eat)
    app.add_handler(conv_bind)
    app.add_handler(conv_unbind)
    app.add_handler(conv_change)
    app.add_handler(conv_cancel)
    app.add_handler(conv_revoke)
    logger.info("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
