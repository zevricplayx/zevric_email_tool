#!/usr/bin/env python3
"""
Zevric Final - RAO.py Deep Research + Captcha Handling + Single Green Button
Based on rao.py logic, handles Garena captcha
"""

import os, asyncio, logging, threading, urllib.parse, re
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

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
        server = HTTPServer(("0.0.0.0", port), H)
        threading.Thread(target=server.serve_forever, daemon=True).start()
    except: pass

async def http_get(url, params=None, headers=None, timeout=20):
    return await asyncio.to_thread(lambda: requests.get(url, params=params, headers=headers or {}, timeout=timeout, allow_redirects=True))
async def http_post(url, data=None, headers=None, timeout=20):
    return await asyncio.to_thread(lambda: requests.post(url, data=data, headers=headers or {}, timeout=timeout))

def sub_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🟢 Subscribe YouTube Channel", url=YT_LINK)]])

def main_menu():
    kb = [
        [KeyboardButton("🟢 Check Bind Info"), KeyboardButton("🟢 Eat To Access Token")],
        [KeyboardButton("🟢 Bind Email"), KeyboardButton("🟢 Unbind Email")],
        [KeyboardButton("🟢 Change Bind Email"), KeyboardButton("🟢 Cancel Bind")],
        [KeyboardButton("🔴 Revoke Access Token"), KeyboardButton("🔵 Owner")],
        [KeyboardButton("🔵 Help")],
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

(CBI_TOKEN, EAT_INPUT, BIND_TOKEN, BIND_EMAIL, BIND_OTP, BIND_SECURITY, UNBIND_TOKEN, UNBIND_OTP, CHANGE_TOKEN, CHANGE_OTP_OLD, CHANGE_NEW_EMAIL, CHANGE_OTP_NEW, CANCEL_TOKEN, REVOKE_TOKEN) = range(14)

async def get_player_info(access_token):
    try:
        url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        r = await http_get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        parsed = urllib.parse.urlparse(r.url)
        qs = urllib.parse.parse_qs(parsed.query)
        acc = qs.get("account_id", ["Unknown"])[0]
        nick = urllib.parse.unquote(qs.get("nickname", ["Unknown"])[0])
        region = qs.get("region", ["IND"])[0]
        return acc, nick, region
    except:
        return "Unknown", "Unknown", "IND"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Welcome to Garena Email Tool\n\nOwner: {OWNER_NAME}\nTelegram: @{OWNER_TG}\nYouTube: {OWNER_YT}", reply_markup=main_menu())
    await update.message.reply_text(f"📢 {OWNER_YT}", reply_markup=sub_keyboard())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 Use buttons below:", reply_markup=main_menu())

async def owner_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"👑 Developer: {OWNER_NAME}\n✈️ Telegram: @{OWNER_TG}\n▶️ YouTube: {OWNER_YT}\n🔗 {YT_LINK}", reply_markup=sub_keyboard())

async def check_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please enter your access token:")
    return CBI_TOKEN

async def cbi_token_recv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip()
    await update.message.reply_text("Fetching info...")
    try:
        acc_id, nick, region = await get_player_info(token)
        url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        # RAO.py style headers
        headers = {"User-Agent": "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)", "Connection": "Keep-Alive", "Accept-Encoding": "gzip"}
        r = await http_get(url, params={"app_id":"100067","access_token":token}, headers=headers)
        d = r.json()
        cur = d.get("email") or "None"
        pend = d.get("pending_email") or d.get("email_to_be") or "None"
        cd = int(d.get("countdown") or d.get("request_exec_countdown") or 0)
        days, rem = divmod(cd, 86400)
        hrs, rem = divmod(rem, 3600)
        mins, secs = divmod(rem, 60)
        msg = f"----- Bind Info -----\nNickname : {nick}\nAccount ID : {acc_id}\nRegion : {region}\nCurrent Email: {cur}\nPending Email: {pend}\nCountdown : {days}D {hrs}H {mins}M {secs}S"
        await update.message.reply_text(msg, reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
    await update.message.reply_text("Main Menu:", reply_markup=main_menu())
    return ConversationHandler.END

async def eat_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send EAT URL or EAT token:")
    return EAT_INPUT

async def eat_recv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    try:
        m = re.search(r"eat=([^&\s]+)", txt)
        eat_token = m.group(1) if m else (txt if len(txt)>50 else None)
        if not eat_token:
            await update.message.reply_text("❌ EAT not found.", reply_markup=sub_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=main_menu())
            return ConversationHandler.END
        api_url = f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
        res = await http_get(api_url, headers={"User-Agent": "Mozilla/5.0"})
        parsed = urllib.parse.urlparse(res.url)
        params = urllib.parse.parse_qs(parsed.query)
        access_token = params.get("access_token", [None])[0]
        account_id = params.get("account_id", ["Unknown"])[0]
        nickname = urllib.parse.unquote(params.get("nickname", ["Unknown"])[0])
        region = params.get("region", ["Unknown"])[0]
        if access_token:
            await update.message.reply_text(f"✅ Converted!\nNickname: {nickname}\nID: {account_id}\nRegion: {region}\n\nToken:\n{access_token}", reply_markup=sub_keyboard())
        else:
            await update.message.reply_text(f"❌ Failed.", reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
    await update.message.reply_text("Main Menu:", reply_markup=main_menu())
    return ConversationHandler.END

# RAO style headers for bind operations
def rao_headers():
    return {
        "User-Agent": "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }

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
    acc, nick, region = await get_player_info(token)
    url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    data = {"email":email,"locale":"en_US","region":region,"app_id":"100067","access_token":token}
    try:
        r = await http_post(url, data=data, headers=rao_headers())
        j = r.json()
        # Captcha check
        if "url" in j and "captcha" in j.get("url",""):
            captcha_url = j["url"]
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("🧩 Solve Captcha", url=captcha_url)], [InlineKeyboardButton("🟢 Subscribe YouTube Channel", url=YT_LINK)]])
            await update.message.reply_text(f"⚠️ Garena ne Captcha laga diya!\n\nIska matlab bahut requests ho gayi hain.\n\n1. Niche Captcha button pe click karke captcha solve karo\n2. Fir 5 min wait karke /cancel_bind karke dobara try karo\n\nCaptcha URL: {captcha_url}", reply_markup=kb)
            await update.message.reply_text("Main Menu:", reply_markup=main_menu())
            return ConversationHandler.END
        if j.get("error") == "error_ongoing_request":
            await update.message.reply_text(f"❌ Pending request hai. /cancel_bind karo.", reply_markup=sub_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=main_menu())
            return ConversationHandler.END
        await update.message.reply_text(f"✅ OTP sent to {email}. Check Spam/Promotions.\nEnter OTP:", reply_markup=sub_keyboard())
        return BIND_OTP
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
        await update.message.reply_text("Main Menu:", reply_markup=main_menu())
        return ConversationHandler.END
async def bind_otp_recv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp = update.message.text.strip()
    token = context.user_data["token"]
    email = context.user_data["email"]
    url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
    data = {"app_id":"100067","access_token":token,"email":email,"code":otp,"otp":otp,"type":"1"}
    try:
        r = await http_post(url, data=data, headers=rao_headers())
        vt = r.json().get("verifier_token")
        if not vt:
            await update.message.reply_text(f"❌ Verify failed: {r.json()}", reply_markup=sub_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=main_menu())
            return ConversationHandler.END
        context.user_data["vt"] = vt
        await update.message.reply_text("Enter 6-digit security code:")
        return BIND_SECURITY
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
        await update.message.reply_text("Main Menu:", reply_markup=main_menu())
        return ConversationHandler.END
async def bind_sec_recv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    token = context.user_data["token"]
    email = context.user_data["email"]
    vt = context.user_data["vt"]
    url = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
    data = {"email":email,"app_id":"100067","access_token":token,"verifier_token":vt,"secondary_password":code}
    try:
        r = await http_post(url, data=data, headers=rao_headers())
        await update.message.reply_text(f"✅ Bind: {r.json()}", reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
    await update.message.reply_text("Main Menu:", reply_markup=main_menu())
    context.user_data.clear()
    return ConversationHandler.END

async def unbind_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please enter your access token:")
    return UNBIND_TOKEN
async def unbind_tok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip()
    context.user_data["token"] = token
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        r = await http_get(url, params={"app_id":"100067","access_token":token}, headers={"User-Agent": "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"})
        email = r.json().get("email","")
    except:
        email = ""
    if not email:
        await update.message.reply_text("❌ No bound email.", reply_markup=sub_keyboard())
        await update.message.reply_text("Main Menu:", reply_markup=main_menu())
        return ConversationHandler.END
    context.user_data["email"] = email
    acc, nick, region = await get_player_info(token)
    url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    data = {"email":email,"locale":"en_US","region":region,"app_id":"100067","access_token":token}
    try:
        r = await http_post(url, data=data, headers=rao_headers())
        j = r.json()
        if "url" in j and "captcha" in j.get("url",""):
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("🧩 Solve Captcha", url=j["url"])], [InlineKeyboardButton("🟢 Subscribe", url=YT_LINK)]])
            await update.message.reply_text(f"⚠️ Captcha! Solve karke 5 min wait karo.\n{j['url']}", reply_markup=kb)
            await update.message.reply_text("Main Menu:", reply_markup=main_menu())
            return ConversationHandler.END
        await update.message.reply_text(f"✅ OTP sent to {email}. Enter OTP:", reply_markup=sub_keyboard())
        return UNBIND_OTP
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
        await update.message.reply_text("Main Menu:", reply_markup=main_menu())
        return ConversationHandler.END
async def unbind_otp_recv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp = update.message.text.strip()
    token = context.user_data["token"]
    email = context.user_data["email"]
    url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
    data = {"email":email,"app_id":"100067","access_token":token,"otp":otp}
    try:
        r = await http_post(url, data=data, headers=rao_headers())
        it = r.json().get("identity_token")
        if not it:
            await update.message.reply_text(f"❌ Verify failed: {r.json()}", reply_markup=sub_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=main_menu())
            return ConversationHandler.END
        url2 = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
        r2 = await http_post(url2, data={"app_id":"100067","access_token":token,"identity_token":it}, headers=rao_headers())
        await update.message.reply_text(f"✅ Unbind: {r2.json()}", reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
    await update.message.reply_text("Main Menu:", reply_markup=main_menu())
    context.user_data.clear()
    return ConversationHandler.END

async def change_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please enter your access token:")
    return CHANGE_TOKEN
async def change_tok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip()
    context.user_data["token"] = token
    await update.message.reply_text("⏳ Cancelling old pending (2 sec)...")
    try:
        await http_post("https://100067.connect.garena.com/game/account_security/bind:cancel_request", data={"app_id":"100067","access_token":token}, headers=rao_headers())
        await asyncio.sleep(2)
    except: pass
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        r = await http_get(url, params={"app_id":"100067","access_token":token}, headers={"User-Agent": "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"})
        old = r.json().get("email","")
    except:
        old = ""
    if not old:
        await update.message.reply_text("❌ No bound email.", reply_markup=sub_keyboard())
        await update.message.reply_text("Main Menu:", reply_markup=main_menu())
        return ConversationHandler.END
    context.user_data["old"] = old
    acc, nick, region = await get_player_info(token)
    context.user_data["region"] = region
    url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    data = {"email":old,"locale":"en_US","region":region,"app_id":"100067","access_token":token}
    try:
        r = await http_post(url, data=data, headers=rao_headers())
        j = r.json()
        if "url" in j and "captcha" in j.get("url",""):
            captcha_url = j["url"]
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("🧩 Solve Captcha", url=captcha_url)], [InlineKeyboardButton("🟢 Subscribe YouTube Channel", url=YT_LINK)]])
            await update.message.reply_text(f"⚠️ Garena Captcha!\n\nOLD email {old} pe OTP nahi bhej paya.\n\nCaptcha solve karna hoga:\n1. Niche Captcha button pe click karo\n2. Browser me captcha solve karo\n3. 10 min wait karke /cancel_bind karke dobara try karo\n\nYa 30 min wait karo auto hat jayega.", reply_markup=kb)
            await update.message.reply_text("Main Menu:", reply_markup=main_menu())
            return ConversationHandler.END
        if j.get("result") == 0 or "sent" in str(j).lower():
            await update.message.reply_text(f"✅ OTP sent to OLD email: {old}\n⚠️ Check Spam/Promotions, 2-5 min lag sakta hai.\nEnter OTP from old email:", reply_markup=sub_keyboard())
            return CHANGE_OTP_OLD
        else:
            await update.message.reply_text(f"❌ Garena response: {j}\n30 min wait karke try karo.", reply_markup=sub_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=main_menu())
            return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
        await update.message.reply_text("Main Menu:", reply_markup=main_menu())
        return ConversationHandler.END
async def change_old_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp = update.message.text.strip()
    token = context.user_data["token"]
    old = context.user_data["old"]
    url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
    data = {"email":old,"app_id":"100067","access_token":token,"otp":otp}
    try:
        r = await http_post(url, data=data, headers=rao_headers())
        j = r.json()
        it = j.get("identity_token")
        if not it:
            await update.message.reply_text(f"❌ Old OTP wrong: {j}", reply_markup=sub_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=main_menu())
            return ConversationHandler.END
        context.user_data["it"] = it
        await update.message.reply_text("Enter NEW email:")
        return CHANGE_NEW_EMAIL
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
        await update.message.reply_text("Main Menu:", reply_markup=main_menu())
        return ConversationHandler.END
async def change_new_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new = update.message.text.strip()
    context.user_data["new"] = new
    token = context.user_data["token"]
    region = context.user_data.get("region","IND")
    url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    data = {"email":new,"locale":"en_US","region":region,"app_id":"100067","access_token":token}
    try:
        r = await http_post(url, data=data, headers=rao_headers())
        j = r.json()
        if "url" in j and "captcha" in j.get("url",""):
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("🧩 Solve Captcha", url=j["url"])], [InlineKeyboardButton("🟢 Subscribe", url=YT_LINK)]])
            await update.message.reply_text(f"⚠️ NEW email {new} pe captcha! Solve karo.", reply_markup=kb)
            await update.message.reply_text("Main Menu:", reply_markup=main_menu())
            return ConversationHandler.END
        await update.message.reply_text(f"✅ OTP sent to NEW email: {new}\nEnter OTP from new email:", reply_markup=sub_keyboard())
        return CHANGE_OTP_NEW
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
        await update.message.reply_text("Main Menu:", reply_markup=main_menu())
        return ConversationHandler.END
async def change_new_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp = update.message.text.strip()
    token = context.user_data["token"]
    new = context.user_data["new"]
    url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
    data = {"email":new,"app_id":"100067","access_token":token,"otp":otp}
    try:
        r = await http_post(url, data=data, headers=rao_headers())
        j = r.json()
        vt = j.get("verifier_token")
        if not vt:
            await update.message.reply_text(f"❌ New OTP failed: {j}", reply_markup=sub_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=main_menu())
            return ConversationHandler.END
        url2 = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
        payload = {"identity_token":context.user_data["it"],"email":new,"app_id":"100067","verifier_token":vt,"access_token":token}
        r2 = await http_post(url2, data=payload, headers=rao_headers())
        await update.message.reply_text(f"✅ Rebind: {r2.json()}", reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
    await update.message.reply_text("Main Menu:", reply_markup=main_menu())
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please enter your access token:")
    return CANCEL_TOKEN
async def cancel_tok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip()
    url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
    try:
        r = await http_post(url, data={"app_id":"100067","access_token":token}, headers=rao_headers())
        await update.message.reply_text(f"✅ Cancel: {r.json()}", reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
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
        await update.message.reply_text(f"✅ Revoke: {r.text[:500]}", reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
    await update.message.reply_text("Main Menu:", reply_markup=main_menu())
    return ConversationHandler.END

async def cancel_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Cancelled.", reply_markup=main_menu())
    return ConversationHandler.END

def main():
    start_health_server()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    conv_cbi = ConversationHandler(entry_points=[CommandHandler("check_bind_info", check_start), MessageHandler(filters.Regex(r"^🟢 Check Bind Info$|^Check Bind Info$"), check_start)], states={CBI_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, cbi_token_recv)]}, fallbacks=[CommandHandler("cancel", cancel_all)], per_user=True, per_chat=True)
    conv_eat = ConversationHandler(entry_points=[CommandHandler("eat_to_access_token", eat_start), MessageHandler(filters.Regex(r"^🟢 Eat To Access Token$|^Eat To Access Token$"), eat_start)], states={EAT_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, eat_recv)]}, fallbacks=[CommandHandler("cancel", cancel_all)], per_user=True, per_chat=True)
    conv_bind = ConversationHandler(entry_points=[CommandHandler("bind_email", bind_start), MessageHandler(filters.Regex(r"^🟢 Bind Email$|^Bind Email$"), bind_start)], states={BIND_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, bind_tok)], BIND_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, bind_email_recv)], BIND_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, bind_otp_recv)], BIND_SECURITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, bind_sec_recv)]}, fallbacks=[CommandHandler("cancel", cancel_all)], per_user=True, per_chat=True)
    conv_unbind = ConversationHandler(entry_points=[CommandHandler("unbind_email", unbind_start), MessageHandler(filters.Regex(r"^🟢 Unbind Email$|^Unbind Email$"), unbind_start)], states={UNBIND_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, unbind_tok)], UNBIND_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, unbind_otp_recv)]}, fallbacks=[CommandHandler("cancel", cancel_all)], per_user=True, per_chat=True)
    conv_change = ConversationHandler(entry_points=[CommandHandler("change_bind_email", change_start), MessageHandler(filters.Regex(r"^🟢 Change Bind Email$|^Change Bind Email$"), change_start)], states={CHANGE_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_tok)], CHANGE_OTP_OLD: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_old_otp)], CHANGE_NEW_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_new_email)], CHANGE_OTP_NEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_new_otp)]}, fallbacks=[CommandHandler("cancel", cancel_all)], per_user=True, per_chat=True)
    conv_cancel = ConversationHandler(entry_points=[CommandHandler("cancel_bind", cancel_start), MessageHandler(filters.Regex(r"^🟢 Cancel Bind$|^Cancel Bind$"), cancel_start)], states={CANCEL_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, cancel_tok)]}, fallbacks=[CommandHandler("cancel", cancel_all)], per_user=True, per_chat=True)
    conv_revoke = ConversationHandler(entry_points=[CommandHandler("revoke_access_token", revoke_start), MessageHandler(filters.Regex(r"^🔴 Revoke Access Token$|^Revoke Access Token$"), revoke_start)], states={REVOKE_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, revoke_tok)]}, fallbacks=[CommandHandler("cancel", cancel_all)], per_user=True, per_chat=True)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("owner", owner_cmd))
    app.add_handler(MessageHandler(filters.Regex(r"^🔵 Owner$|^Owner$"), owner_cmd))
    app.add_handler(MessageHandler(filters.Regex(r"^🔵 Help$|^Help$"), help_cmd))
    app.add_handler(conv_cbi)
    app.add_handler(conv_eat)
    app.add_handler(conv_bind)
    app.add_handler(conv_unbind)
    app.add_handler(conv_change)
    app.add_handler(conv_cancel)
    app.add_handler(conv_revoke)
    logger.info("Bot starting...")
    app.run_polling(allowed_updates=["message"])

if __name__ == "__main__":
    main()
