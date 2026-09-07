#!/usr/bin/env python3
"""
FINAL - Welcome me YouTube text hata ke niche Subscribe button + How To Use + Change Bind fixed
"""

import os, asyncio, logging, threading, urllib.parse, re
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from telegram.ext.filters import MessageFilter

BOT_TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level="INFO")

YT_LINK = "https://youtube.com/@zevricxplay"
BOT_USERNAME = "@GarenaEmailsBot"

BASE_UPPER = 0x1D5D4
BASE_LOWER = 0x1D5EE
BASE_DIGIT = 0x1D7EC

def fancy(text):
    res = ""
    for ch in text:
        if 'A' <= ch <= 'Z':
            res += chr(BASE_UPPER + ord(ch) - ord('A'))
        elif 'a' <= ch <= 'z':
            res += chr(BASE_LOWER + ord(ch) - ord('a'))
        elif '0' <= ch <= '9':
            res += chr(BASE_DIGIT + ord(ch) - ord('0'))
        else:
            res += ch
    return res

def unfancy(text):
    res = ""
    for ch in text:
        code = ord(ch)
        if BASE_UPPER <= code <= BASE_UPPER + 25:
            res += chr(ord('A') + code - BASE_UPPER)
        elif BASE_LOWER <= code <= BASE_LOWER + 25:
            res += chr(ord('a') + code - BASE_LOWER)
        elif BASE_DIGIT <= code <= BASE_DIGIT + 9:
            res += chr(ord('0') + code - BASE_DIGIT)
        else:
            res += ch
    return res

class FancyButtonFilter(MessageFilter):
    def __init__(self, keyword):
        super().__init__()
        self.keyword = keyword.lower()
    def filter(self, message):
        if not message.text:
            return False
        norm = unfancy(message.text).lower()
        return self.keyword in norm

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
    return InlineKeyboardMarkup([[InlineKeyboardButton("🟢 " + fancy("Subscribe YouTube Channel"), url=YT_LINK)]])

def main_menu():
    kb = [
        [KeyboardButton("🟢 " + fancy("Check Bind Info")), KeyboardButton("🟢 " + fancy("Eat To Access Token"))],
        [KeyboardButton("🟢 " + fancy("Bind Email")), KeyboardButton("🟢 " + fancy("Unbind Email"))],
        [KeyboardButton("🟢 " + fancy("Change Bind Email")), KeyboardButton("🟢 " + fancy("Cancel Bind"))],
        [KeyboardButton("🔴 " + fancy("Revoke Access Token")), KeyboardButton("🔵 " + fancy("Owner"))],
        [KeyboardButton("🔵 " + fancy("How To Use"))],
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

(CBI_TOKEN, EAT_INPUT, BIND_TOKEN, BIND_EMAIL, BIND_OTP, BIND_SECURITY,
 UNBIND_TOKEN, UNBIND_OTP,
 CHANGE_TOKEN, CHANGE_OTP_OLD, CHANGE_NEW_EMAIL, CHANGE_OTP_NEW,
 CANCEL_TOKEN, REVOKE_TOKEN) = range(14)

async def get_player_info(access_token):
    try:
        url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        r = await http_get(url, headers={"User-Agent": "Mozilla/5.0"})
        parsed = urllib.parse.urlparse(r.url)
        qs = urllib.parse.parse_qs(parsed.query)
        acc = qs.get("account_id", ["Unknown"])[0]
        nick = urllib.parse.unquote(qs.get("nickname", ["Unknown"])[0])
        region = qs.get("region", ["Unknown"])[0]
        return acc, nick, region
    except:
        return "Unknown", "Unknown", "IND"

def rao_headers():
    return {"User-Agent": "GarenaMSDK/4.0.30","Content-Type": "application/x-www-form-urlencoded","Accept": "application/json"}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_name = user.first_name or user.username or "User"
    # Welcome WITHOUT YouTube line, as requested
    welcome = fancy(f"Welcome, {user_name}!") + "\n\n" + fancy("Welcome to Garena Email Tool") + f"\n\nBot: {BOT_USERNAME}\nOwner: zevric x play\nTelegram: @just_zevric"
    await update.message.reply_text(welcome, reply_markup=sub_keyboard())
    await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    how_to_text = f"""{fancy('How To Use')} {BOT_USERNAME}

{fancy('1. Eat To Access Token:')}
{fancy('Paste EAT URL, bot converts to Access Token.')}

{fancy('2. Check Bind Info:')}
{fancy('Send Token, get Nickname, ID, Region, Email, Pending, Countdown.')}

{fancy('3. Bind Email:')}
{fancy('Token -> Email -> OTP -> 6-digit Code -> Done.')}

{fancy('4. Change Bind Email:')}
{fancy('Token -> Auto OLD email -> OTP OLD -> Verify -> NEW email -> OTP NEW -> Verify -> Rebind Done.')}

{fancy('5. Unbind Email:')}
{fancy('Token -> OTP -> Unbind.')}

{fancy('6. Cancel Bind:')}
{fancy('Cancel pending request.')}

{fancy('7. Revoke Access Token:')}
{fancy('Logout token.')}

Bot: {BOT_USERNAME}
"""
    await update.message.reply_text(how_to_text, reply_markup=sub_keyboard())
    await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())

async def owner_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"👑 zevric x play\n✈️ @just_zevric\n▶️ zevricxplay\n🔗 {YT_LINK}\nBot: {BOT_USERNAME}", reply_markup=sub_keyboard())

async def check_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(fancy("Please Enter Your Access Token:"), reply_markup=sub_keyboard())
    return CBI_TOKEN

async def cbi_token_recv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip()
    await update.message.reply_text(fancy("Fetching info..."), reply_markup=sub_keyboard())
    try:
        acc_id, nick, region = await get_player_info(token)
        url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        r = await http_get(url, params={"app_id":"100067","access_token":token}, headers={"User-Agent": "GarenaMSDK/4.0.30"})
        d = r.json()
        cur = d.get("email") or "None"
        pend = d.get("email_to_be") or "None"
        cd = int(d.get("request_exec_countdown") or 0)
        days, rem = divmod(cd, 86400)
        hrs, rem = divmod(rem, 3600)
        mins, secs = divmod(rem, 60)
        msg = f"{fancy('----- Bind Info -----')}\n{fancy('Nickname')} : {nick}\n{fancy('Account ID')} : {acc_id}\n{fancy('Region')} : {region}\n{fancy('Current Email')}: {cur}\n{fancy('Pending Email')}: {pend}\n{fancy('Countdown')} : {days}D {hrs}H {mins}M {secs}S"
        await update.message.reply_text(msg, reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
    await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
    return ConversationHandler.END

async def eat_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(fancy("Please Enter Your EAT URL or EAT Token:"), reply_markup=sub_keyboard())
    return EAT_INPUT

async def eat_recv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    try:
        m = re.search(r"eat=([^&\s]+)", txt)
        eat_token = m.group(1) if m else (txt if len(txt)>50 else None)
        if not eat_token:
            await update.message.reply_text(fancy("EAT not found."), reply_markup=sub_keyboard())
            await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
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
            await update.message.reply_text(f"✅ {fancy('Converted!')}\n{fancy('Nickname')}: {nickname}\nID: {account_id}\nRegion: {region}\n\nToken:\n{access_token}", reply_markup=sub_keyboard())
        else:
            await update.message.reply_text(fancy("Failed."), reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
    await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
    return ConversationHandler.END

async def bind_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(fancy("Please Enter Your Access Token:"), reply_markup=sub_keyboard())
    return BIND_TOKEN
async def bind_tok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["token"] = update.message.text.strip()
    await update.message.reply_text(fancy("Please Enter Your Email To Bind:"), reply_markup=sub_keyboard())
    return BIND_EMAIL
async def bind_email_recv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    context.user_data["email"] = email
    token = context.user_data["token"]
    url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    data = {"email":email,"locale":"en_PK","region":"PK","app_id":"100067","access_token":token}
    try:
        r = await http_post(url, data=data, headers=rao_headers())
        await update.message.reply_text(fancy(f"OTP Sent To {email}.") + "\n\n" + fancy("Please Enter OTP:"), reply_markup=sub_keyboard())
        return BIND_OTP
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
        await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
        return ConversationHandler.END
async def bind_otp_recv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp = update.message.text.strip()
    token = context.user_data["token"]
    email = context.user_data["email"]
    url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
    data = {"app_id":"100067","access_token":token,"email":email,"code":otp,"otp":otp,"type":"1"}
    try:
        r = await http_post(url, data=data, headers=rao_headers())
        j = r.json()
        vt = j.get("verifier_token")
        if not vt:
            await update.message.reply_text(f"❌ {fancy('Verify failed')}: {j}", reply_markup=sub_keyboard())
            await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
            return ConversationHandler.END
        context.user_data["vt"] = vt
        await update.message.reply_text(fancy("Please Enter Your 6-Digits Security Code:"), reply_markup=sub_keyboard())
        return BIND_SECURITY
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
        await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
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
        await update.message.reply_text(f"✅ {fancy('Bind')}: {r.json()}", reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
    await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
    context.user_data.clear()
    return ConversationHandler.END

async def unbind_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(fancy("Please Enter Your Access Token:"), reply_markup=sub_keyboard())
    return UNBIND_TOKEN
async def unbind_tok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip()
    context.user_data["token"] = token
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        r = await http_get(url, params={"app_id":"100067","access_token":token}, headers={"User-Agent": "GarenaMSDK/4.0.30"})
        email = r.json().get("email","")
    except:
        email = ""
    if not email:
        await update.message.reply_text(fancy("No bound email."), reply_markup=sub_keyboard())
        await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
        return ConversationHandler.END
    context.user_data["email"] = email
    url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    data = {"email":email,"locale":"en_PK","region":"PK","app_id":"100067","access_token":token}
    try:
        r = await http_post(url, data=data, headers=rao_headers())
        await update.message.reply_text(fancy(f"OTP Sent To {email}.") + "\n\n" + fancy("Please Enter OTP:"), reply_markup=sub_keyboard())
        return UNBIND_OTP
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
        await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
        return ConversationHandler.END
async def unbind_otp_recv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp = update.message.text.strip()
    token = context.user_data["token"]
    email = context.user_data["email"]
    url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
    data = {"email":email,"app_id":"100067","access_token":token,"otp":otp}
    try:
        r = await http_post(url, data=data, headers=rao_headers())
        j = r.json()
        it = j.get("identity_token")
        if not it:
            await update.message.reply_text(f"❌ {fancy('Verify failed')}: {j}", reply_markup=sub_keyboard())
            await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
            return ConversationHandler.END
        url2 = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
        r2 = await http_post(url2, data={"app_id":"100067","access_token":token,"identity_token":it}, headers=rao_headers())
        await update.message.reply_text(f"✅ {fancy('Unbind')}: {r2.json()}", reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
    await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
    context.user_data.clear()
    return ConversationHandler.END

async def change_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(fancy("Please Enter Your Access Token:"), reply_markup=sub_keyboard())
    return CHANGE_TOKEN
async def change_tok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip()
    context.user_data["token"] = token
    try:
        url_info = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        r_info = await http_get(url_info, params={"app_id":"100067","access_token":token}, headers={"User-Agent": "GarenaMSDK/4.0.30"})
        old_email = r_info.json().get("email","")
    except:
        old_email = ""
    if not old_email:
        await update.message.reply_text(fancy("No currently bound email found!"), reply_markup=sub_keyboard())
        await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
        return ConversationHandler.END
    context.user_data["old"] = old_email
    url_send = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    data = {"email":old_email,"locale":"en_PK","region":"PK","app_id":"100067","access_token":token}
    try:
        r = await http_post(url_send, data=data, headers=rao_headers())
        await update.message.reply_text(fancy(f"OTP Sent To OLD Email {old_email}") + "\n\n" + fancy("Please Enter OTP From Old Email:"), reply_markup=sub_keyboard())
        return CHANGE_OTP_OLD
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
        await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
        return ConversationHandler.END
async def change_old_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp = update.message.text.strip()
    token = context.user_data["token"]
    old = context.user_data["old"]
    url_verify_identity = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
    data = {"email":old,"app_id":"100067","access_token":token,"otp":otp}
    try:
        r = await http_post(url_verify_identity, data=data, headers=rao_headers())
        j = r.json()
        it = j.get("identity_token")
        if not it:
            await update.message.reply_text(f"❌ {fancy('Old OTP failed')}: {j}", reply_markup=sub_keyboard())
            await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
            return ConversationHandler.END
        context.user_data["it"] = it
        await update.message.reply_text(fancy("Please Enter New Email:"), reply_markup=sub_keyboard())
        return CHANGE_NEW_EMAIL
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
        await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
        return ConversationHandler.END
async def change_new_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new = update.message.text.strip()
    context.user_data["new"] = new
    token = context.user_data["token"]
    url_send = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    data = {"email":new,"locale":"en_PK","region":"PK","app_id":"100067","access_token":token}
    try:
        r = await http_post(url_send, data=data, headers=rao_headers())
        await update.message.reply_text(fancy(f"OTP Sent To NEW Email {new}") + "\n\n" + fancy("Please Enter OTP From New Email:"), reply_markup=sub_keyboard())
        return CHANGE_OTP_NEW
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
        await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
        return ConversationHandler.END
async def change_new_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp = update.message.text.strip()
    token = context.user_data["token"]
    new = context.user_data["new"]
    url_verify_otp = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
    data = {"email":new,"app_id":"100067","access_token":token,"otp":otp}
    try:
        r = await http_post(url_verify_otp, data=data, headers=rao_headers())
        j = r.json()
        vt = j.get("verifier_token")
        if not vt:
            await update.message.reply_text(f"❌ {fancy('New OTP failed')}: {j}", reply_markup=sub_keyboard())
            await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
            return ConversationHandler.END
        context.user_data["vt"] = vt
        url_rebind = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
        payload = {"identity_token":context.user_data["it"],"email":new,"app_id":"100067","verifier_token":vt,"access_token":token}
        r2 = await http_post(url_rebind, data=payload, headers=rao_headers())
        await update.message.reply_text(f"✅ {fancy('Rebind')}: {r2.json()}", reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
    await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(fancy("Please Enter Your Access Token:"), reply_markup=sub_keyboard())
    return CANCEL_TOKEN
async def cancel_tok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip()
    url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
    try:
        r = await http_post(url, data={"app_id":"100067","access_token":token}, headers=rao_headers())
        await update.message.reply_text(f"✅ {fancy('Cancel')}: {r.json()}", reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
    await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
    return ConversationHandler.END

async def revoke_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(fancy("Please Enter Your Access Token:"), reply_markup=sub_keyboard())
    return REVOKE_TOKEN
async def revoke_tok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip()
    url = f"https://100067.connect.garena.com/oauth/logout?access_token={token}&refresh_token=1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
    try:
        r = await http_get(url)
        await update.message.reply_text(f"✅ {fancy('Revoke')}: {r.text[:500]}", reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
    await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
    return ConversationHandler.END

async def cancel_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(fancy("Cancelled."), reply_markup=main_menu())
    return ConversationHandler.END

def main():
    start_health_server()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    conv_cbi = ConversationHandler(entry_points=[CommandHandler("check_bind_info", check_start), MessageHandler(FancyButtonFilter("check bind info"), check_start)], states={CBI_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, cbi_token_recv)]}, fallbacks=[CommandHandler("cancel", cancel_all)], per_user=True, per_chat=True)
    conv_eat = ConversationHandler(entry_points=[CommandHandler("eat_to_access_token", eat_start), MessageHandler(FancyButtonFilter("eat to access token"), eat_start)], states={EAT_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, eat_recv)]}, fallbacks=[CommandHandler("cancel", cancel_all)], per_user=True, per_chat=True)
    conv_bind = ConversationHandler(entry_points=[CommandHandler("bind_email", bind_start), MessageHandler(FancyButtonFilter("bind email"), bind_start)], states={BIND_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, bind_tok)], BIND_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, bind_email_recv)], BIND_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, bind_otp_recv)], BIND_SECURITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, bind_sec_recv)]}, fallbacks=[CommandHandler("cancel", cancel_all)], per_user=True, per_chat=True)
    conv_unbind = ConversationHandler(entry_points=[CommandHandler("unbind_email", unbind_start), MessageHandler(FancyButtonFilter("unbind email"), unbind_start)], states={UNBIND_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, unbind_tok)], UNBIND_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, unbind_otp_recv)]}, fallbacks=[CommandHandler("cancel", cancel_all)], per_user=True, per_chat=True)
    conv_change = ConversationHandler(entry_points=[CommandHandler("change_bind_email", change_start), MessageHandler(FancyButtonFilter("change bind email"), change_start)], states={CHANGE_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_tok)], CHANGE_OTP_OLD: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_old_otp)], CHANGE_NEW_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_new_email)], CHANGE_OTP_NEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_new_otp)]}, fallbacks=[CommandHandler("cancel", cancel_all)], per_user=True, per_chat=True)
    conv_cancel = ConversationHandler(entry_points=[CommandHandler("cancel_bind", cancel_start), MessageHandler(FancyButtonFilter("cancel bind"), cancel_start)], states={CANCEL_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, cancel_tok)]}, fallbacks=[CommandHandler("cancel", cancel_all)], per_user=True, per_chat=True)
    conv_revoke = ConversationHandler(entry_points=[CommandHandler("revoke_access_token", revoke_start), MessageHandler(FancyButtonFilter("revoke access token"), revoke_start)], states={REVOKE_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, revoke_tok)]}, fallbacks=[CommandHandler("cancel", cancel_all)], per_user=True, per_chat=True)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("howtouse", help_cmd))
    app.add_handler(CommandHandler("owner", owner_cmd))
    app.add_handler(MessageHandler(FancyButtonFilter("owner"), owner_cmd))
    app.add_handler(MessageHandler(FancyButtonFilter("how to use"), help_cmd))
    app.add_handler(MessageHandler(FancyButtonFilter("help"), help_cmd))
    app.add_handler(conv_cbi)
    app.add_handler(conv_eat)
    app.add_handler(conv_bind)
    app.add_handler(conv_unbind)
    app.add_handler(conv_change)
    app.add_handler(conv_cancel)
    app.add_handler(conv_revoke)
    app.run_polling(allowed_updates=["message"])

if __name__ == "__main__":
    main()
