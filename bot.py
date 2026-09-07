#!/usr/bin/env python3
"""
RAO BIND MANAGER - Render Ready Version
Using python-telegram-bot 22.7 + Flask (matches your current requirements.txt)
Developer: @raostarr | RAO ON TOP
All 12 features working
"""

import os
import re
import json
import time
import random
import string
import requests
import asyncio
from urllib.parse import urlparse, parse_qs
from flask import Flask, request

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN", "PASTE_YOUR_BOT_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

_BASE_URL = "https://rishu-official-bind.vercel.app/api"
_EXTRACT_URL = "https://rishu-jwt-gen.vercel.app/rishu"
_APP_ID = "100067"

VERSION = "V2.0 RENDER"

# Flask for Render health check
app = Flask(__name__)

@app.route('/')
def home():
    return f"🤖 RAO BOT {VERSION} is Running! | RAO ON TOP"

@app.route('/health')
def health():
    return "OK", 200

# ================= API CORE =================
def api_request(endpoint, params):
    url = f"{_BASE_URL}/{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=25)
        try:
            return resp.json()
        except:
            return {"success": False, "message": f"Invalid Response HTTP {resp.status_code}", "raw": resp.text[:500]}
    except Exception as e:
        return {"success": False, "message": f"Network Error: {str(e)}"}

def send_otp(token, email): return api_request("send-otp", {"access_token": token, "email": email, "app_id": _APP_ID})
def bind_email_api(token, email, otp, sec_code): return api_request("bind", {"access_token": token, "email": email, "otp": otp, "secondary_password": sec_code, "app_id": _APP_ID})
def cancel_request(token): return api_request("cancel", {"access_token": token, "app_id": _APP_ID})
def unbind_with_sec(token, sec_code): return api_request("unbind-with-sec", {"access_token": token, "secondary_password": sec_code, "app_id": _APP_ID})
def unbind_with_otp_api(token, email, otp): return api_request("unbind-with-otp", {"access_token": token, "email": email, "otp": otp, "app_id": _APP_ID})
def change_email_sec(token, old_email, new_email, sec_code, new_otp): return api_request("change-email-sec", {"access_token": token, "old_email": old_email, "new_email": new_email, "secondary_password": sec_code, "new_otp": new_otp, "app_id": _APP_ID})
def change_email_otp_api(token, old_email, new_email, old_otp, new_otp): return api_request("change-email-otp", {"access_token": token, "old_email": old_email, "new_email": new_email, "old_otp": old_otp, "new_otp": new_otp, "app_id": _APP_ID})
def get_bind_info(token): return api_request("get-bind-info", {"access_token": token, "app_id": _APP_ID})
def get_platforms(token): return api_request("get-platform", {"access_token": token})
def revoke_token_api(token): return api_request("revoke-access", {"access_token": token, "app_id": _APP_ID})

def extract_jwt_info(jwt_token):
    try:
        resp = requests.get(_EXTRACT_URL, params={"access_token": jwt_token}, timeout=15)
        if resp.status_code == 200:
            return resp.json(), None
        else:
            return None, f"HTTP {resp.status_code}"
    except Exception as e:
        return None, str(e)

def extract_eat_token(input_str):
    if input_str.startswith('http://') or input_str.startswith('https://'):
        try:
            parsed = urlparse(input_str)
            params = parse_qs(parsed.query)
            eat_token = params.get('eat', [None])[0]
            if eat_token: return eat_token
        except: pass
        m = re.search(r'[a-fA-F0-9]{64,}', input_str)
        if m: return m.group(0)
    if re.match(r'^[a-fA-F0-9]{64,}$', input_str): return input_str
    m = re.search(r'[a-fA-F0-9]{64,}', input_str)
    return m.group(0) if m else None

def eat_to_access_token_api(eat_token):
    url = f"{_BASE_URL}/eat-token-access-token"
    try:
        r = requests.get(url, params={"eat_token": eat_token}, timeout=30)
        return r.json() if r.status_code==200 else {"success": False, "error": f"HTTP {r.status_code}", "raw": r.text[:500]}
    except Exception as e:
        return {"success": False, "error": str(e)}

def generate_temp_email():
    try:
        r = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1", timeout=10)
        return {"success": True, "email": r.json()[0]}
    except Exception as e:
        return {"success": False, "message": str(e)}

def check_inbox(email):
    try:
        login, domain = email.split('@')
        r = requests.get(f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}", timeout=10)
        return {"success": True, "messages": r.json()}
    except Exception as e:
        return {"success": False, "message": str(e)}

def get_msg(email, msg_id):
    try:
        login, domain = email.split('@')
        r = requests.get(f"https://www.1secmail.com/api/v1/?action=readMessage&login={login}&domain={domain}&id={msg_id}", timeout=10)
        return r.json()
    except: return None

def format_seconds(s):
    if s<=0: return "0s"
    d=s//86400; h=(s%86400)//3600; m=(s%3600)//60; sec=s%60
    p=[]
    if d>0: p.append(f"{d}d")
    if h>0: p.append(f"{h}h")
    if m>0: p.append(f"{m}m")
    if sec>0: p.append(f"{sec}s")
    return " ".join(p)

# ================= KEYBOARDS =================
def main_menu():
    kb = [
        [InlineKeyboardButton("📧 Bind New Email", callback_data="bind"), InlineKeyboardButton("❌ Cancel Request", callback_data="cancel")],
        [InlineKeyboardButton("🔓 Unbind (Sec)", callback_data="unbind_sec"), InlineKeyboardButton("🔑 Unbind (OTP)", callback_data="unbind_otp")],
        [InlineKeyboardButton("🔄 Change (Sec)", callback_data="change_sec"), InlineKeyboardButton("🔄 Change (OTP)", callback_data="change_otp")],
        [InlineKeyboardButton("ℹ️ Bind Info", callback_data="status"), InlineKeyboardButton("🎮 Platforms", callback_data="platforms")],
        [InlineKeyboardButton("🚫 Revoke Token", callback_data="revoke"), InlineKeyboardButton("📮 Temp Mail", callback_data="temp_mail")],
        [InlineKeyboardButton("🔗 EAT → Token", callback_data="eat_convert"), InlineKeyboardButton("🧬 JWT Extractor", callback_data="jwt_extract")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(kb)

def back_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]])

def cancel_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="main_menu")]])

def temp_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 Check Inbox", callback_data="check_inbox"), InlineKeyboardButton("🔄 New Mail", callback_data="temp_mail")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
    ])

START_BANNER = """
<b>██████╗  █████╗  ██████╗<br>██╔══██╗██╔══██╗██╔═══██╗<br>██████╔╝███████║██║   ██║<br>██╔══██╗██╔══██║██║   ██║<br>██║  ██║██║  ██║╚██████╔╝</b>

<b>━► RAO ON TOP ◄━</b>
<b>🤖 RAO BIND MANAGER BOT V2.0 RENDER</b>
<b>◍ DEV:</b> @raostarr
<b>◍ STATUS:</b> ✅ ONLINE
<b>◍ PLATFORM:</b> Render.com

Saare 12 features working hai! Niche button dabao 👇
"""

HELP_TEXT = """
<b>📖 RAO BOT HELP</b>

<b>1. Bind New Email:</b> Token + Email → OTP → Sec Code
<b>2. Cancel:</b> Pending request cancel
<b>3. Unbind Sec:</b> Security code se unbind
<b>4. Unbind OTP:</b> OTP se unbind
<b>5. Change Email Sec:</b> Sec + New OTP
<b>6. Change Email OTP:</b> Old OTP + New OTP
<b>7. Bind Info:</b> Current/pending email
<b>8. Platforms:</b> Linked accounts
<b>9. Revoke:</b> Token revoke
<b>10. Temp Mail:</b> 1secmail generate + inbox check auto OTP extract
<b>11. EAT → Token:</b> EAT URL/token se access token
<b>12. JWT Extractor:</b> UID, Region, Server

<b>Security:</b> /clear se session clear karo
"""

# ================= HANDLERS =================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_html(START_BANNER, reply_markup=main_menu())
    if ADMIN_ID!=0:
        try:
            await context.bot.send_message(ADMIN_ID, f"🟢 New User: {update.effective_user.first_name} @{update.effective_user.username} ID:{update.effective_user.id}")
        except: pass

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(HELP_TEXT, reply_markup=back_menu())

async def clear_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_html("✅ Session cleared!", reply_markup=main_menu())

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data=="main_menu":
        context.user_data.clear()
        await query.edit_message_text(START_BANNER, reply_markup=main_menu(), parse_mode='HTML')
    elif data=="help":
        await query.edit_message_text(HELP_TEXT, reply_markup=back_menu(), parse_mode='HTML')
    elif data=="bind":
        context.user_data['state']='await_token_bind'
        await context.bot.send_message(query.message.chat_id, "<b>📧 BIND NEW EMAIL</b>\n\n🔑 Access Token bhejo:", reply_markup=cancel_menu(), parse_mode='HTML')
    elif data=="cancel":
        context.user_data['state']='await_token_cancel'
        await context.bot.send_message(query.message.chat_id, "<b>❌ CANCEL REQUEST</b>\n\n🔑 Token bhejo:", reply_markup=cancel_menu(), parse_mode='HTML')
    elif data=="unbind_sec":
        context.user_data['state']='await_token_unbind_sec'
        await context.bot.send_message(query.message.chat_id, "<b>🔓 UNBIND SEC CODE</b>\n\n🔑 Token bhejo:", reply_markup=cancel_menu(), parse_mode='HTML')
    elif data=="unbind_otp":
        context.user_data['state']='await_token_unbind_otp'
        await context.bot.send_message(query.message.chat_id, "<b>🔑 UNBIND OTP</b>\n\n🔑 Token bhejo:", reply_markup=cancel_menu(), parse_mode='HTML')
    elif data=="change_sec":
        context.user_data['state']='await_token_change_sec'
        await context.bot.send_message(query.message.chat_id, "<b>🔄 CHANGE EMAIL (SEC)</b>\n\n🔑 Token bhejo:", reply_markup=cancel_menu(), parse_mode='HTML')
    elif data=="change_otp":
        context.user_data['state']='await_token_change_otp'
        await context.bot.send_message(query.message.chat_id, "<b>🔄 CHANGE EMAIL (OTP)</b>\n\n🔑 Token bhejo:", reply_markup=cancel_menu(), parse_mode='HTML')
    elif data=="status":
        context.user_data['state']='await_token_status'
        await context.bot.send_message(query.message.chat_id, "<b>ℹ️ BIND INFO</b>\n\n🔑 Token bhejo:", reply_markup=cancel_menu(), parse_mode='HTML')
    elif data=="platforms":
        context.user_data['state']='await_token_platforms'
        await context.bot.send_message(query.message.chat_id, "<b>🎮 PLATFORMS</b>\n\n🔑 Token bhejo:", reply_markup=cancel_menu(), parse_mode='HTML')
    elif data=="revoke":
        context.user_data['state']='await_token_revoke'
        await context.bot.send_message(query.message.chat_id, "<b>🚫 REVOKE TOKEN</b>\n⚠️ Irreversible!\n\n🔑 Token bhejo:", reply_markup=cancel_menu(), parse_mode='HTML')
    elif data=="temp_mail":
        await handle_temp_mail(query.message.chat_id, context)
    elif data=="check_inbox":
        await handle_check_inbox(query.message.chat_id, context)
    elif data=="eat_convert":
        context.user_data['state']='await_eat'
        await context.bot.send_message(query.message.chat_id, "<b>🔗 EAT → TOKEN</b>\n\n🔗 EAT Token/URL bhejo:", reply_markup=cancel_menu(), parse_mode='HTML')
    elif data=="jwt_extract":
        context.user_data['state']='await_jwt'
        await context.bot.send_message(query.message.chat_id, "<b>🧬 JWT EXTRACTOR</b>\n\n🔑 Token bhejo:", reply_markup=cancel_menu(), parse_mode='HTML')

async def handle_temp_mail(chat_id, context):
    await context.bot.send_message(chat_id, "⏳ Generating temp email...")
    res = generate_temp_email()
    if res.get('success'):
        email = res['email']
        context.user_data['temp_mail']=email
        await context.bot.send_message(chat_id, f"✅ <b>Temp Mail Generated</b>\n\n📧 <code>{email}</code>\n\nInbox check karo:", reply_markup=temp_menu(), parse_mode='HTML')
    else:
        await context.bot.send_message(chat_id, f"❌ Failed: {res.get('message')}", reply_markup=main_menu(), parse_mode='HTML')

async def handle_check_inbox(chat_id, context):
    email = context.user_data.get('temp_mail')
    if not email:
        await context.bot.send_message(chat_id, "❌ Pehle email generate karo", reply_markup=main_menu(), parse_mode='HTML')
        return
    await context.bot.send_message(chat_id, f"⏳ Checking inbox for <code>{email}</code>...", parse_mode='HTML')
    res = check_inbox(email)
    if not res.get('success'):
        await context.bot.send_message(chat_id, f"❌ {res.get('message')}", reply_markup=temp_menu(), parse_mode='HTML')
        return
    msgs = res.get('messages', [])
    if not msgs:
        await context.bot.send_message(chat_id, f"📭 Inbox empty for <code>{email}</code>", reply_markup=temp_menu(), parse_mode='HTML')
        return
    text = f"<b>📥 Inbox for {email}</b>\n\n"
    for m in msgs[:5]:
        text+=f"📩 <b>{m.get('subject')}</b>\nFrom:{m.get('from')}\nDate:{m.get('date')}\nID:{m.get('id')}\n\n"
        if 'otp' in m.get('subject','').lower() or 'code' in m.get('subject','').lower():
            body = get_msg(email, m.get('id'))
            if body:
                bt = body.get('body','') or body.get('textBody','') or body.get('htmlBody','')
                otp = re.search(r'\b\d{4,8}\b', bt)
                if otp: text+=f"🔑 OTP: <code>{otp.group(0)}</code>\n\n"
    await context.bot.send_message(chat_id, text, reply_markup=temp_menu(), parse_mode='HTML')

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    text = update.message.text.strip()
    chat_id = update.effective_chat.id

    if not state:
        if len(text)>50:
            await update.message.reply_html("🔑 Token lag raha hai, option select karo:", reply_markup=main_menu())
        else:
            await update.message.reply_html("👋 Menu se select karo:", reply_markup=main_menu())
        return

    # BIND FLOW
    if state=='await_token_bind':
        if len(text)<20:
            await update.message.reply_html("❌ Chota token, sahi bhejo:", reply_markup=cancel_menu())
            return
        context.user_data['token']=text
        context.user_data['state']='await_email_bind'
        await update.message.reply_html("✅ Token save!\n\n📧 New Email bhejo:", reply_markup=cancel_menu())
    elif state=='await_email_bind':
        if '@' not in text:
            await update.message.reply_html("❌ Sahi email bhejo:", reply_markup=cancel_menu())
            return
        token=context.user_data.get('token')
        await update.message.reply_html(f"⏳ OTP bhej raha hu {text} par...")
        res=send_otp(token, text)
        if not res.get('success'):
            await update.message.reply_html(f"❌ OTP Failed: {res.get('message')}", reply_markup=main_menu())
            context.user_data.clear()
            return
        context.user_data['email']=text
        context.user_data['state']='await_otp_bind'
        await update.message.reply_html(f"✅ OTP bhej diya {text} par!\n\n🔢 OTP bhejo:")
    elif state=='await_otp_bind':
        context.user_data['otp']=text
        context.user_data['state']='await_sec_bind'
        await update.message.reply_html("🔐 Security Code bhejo:", reply_markup=cancel_menu())
    elif state=='await_sec_bind':
        token=context.user_data.get('token'); email=context.user_data.get('email'); otp=context.user_data.get('otp')
        await update.message.reply_html("⏳ Binding...")
        res=bind_email_api(token, email, otp, text)
        msg = f"✅ Success: {res.get('message')}\n📧 {email}" if res.get('success') else f"❌ Failed: {res.get('message')}"
        await update.message.reply_html(msg, reply_markup=main_menu())
        context.user_data.clear()

    # CANCEL
    elif state=='await_token_cancel':
        await update.message.reply_html("⏳ Cancelling...")
        res=cancel_request(text)
        await update.message.reply_html(f"{'✅' if res.get('success') else '❌'} {res.get('message')}", reply_markup=main_menu())
        context.user_data.clear()

    # UNBIND SEC
    elif state=='await_token_unbind_sec':
        context.user_data['token']=text
        context.user_data['state']='await_sec_unbind_sec'
        await update.message.reply_html("🔐 Security Code bhejo:", reply_markup=cancel_menu())
    elif state=='await_sec_unbind_sec':
        token=context.user_data.get('token')
        res=unbind_with_sec(token, text)
        await update.message.reply_html(f"{'✅' if res.get('success') else '❌'} {res.get('message')}", reply_markup=main_menu())
        context.user_data.clear()

    # UNBIND OTP
    elif state=='await_token_unbind_otp':
        context.user_data['token']=text
        context.user_data['state']='await_email_unbind_otp'
        await update.message.reply_html("📧 Email bhejo:", reply_markup=cancel_menu())
    elif state=='await_email_unbind_otp':
        token=context.user_data.get('token')
        await update.message.reply_html(f"⏳ OTP bhej raha hu {text} par...")
        res=send_otp(token, text)
        if not res.get('success'):
            await update.message.reply_html(f"❌ {res.get('message')}", reply_markup=main_menu())
            context.user_data.clear()
            return
        context.user_data['email']=text
        context.user_data['state']='await_otp_unbind_otp'
        await update.message.reply_html("✅ OTP bhej diya! OTP bhejo:")
    elif state=='await_otp_unbind_otp':
        token=context.user_data.get('token'); email=context.user_data.get('email')
        res=unbind_with_otp_api(token, email, text)
        await update.message.reply_html(f"{'✅' if res.get('success') else '❌'} {res.get('message')}", reply_markup=main_menu())
        context.user_data.clear()

    # CHANGE SEC
    elif state=='await_token_change_sec':
        context.user_data['token']=text
        context.user_data['state']='await_old_email_change_sec'
        await update.message.reply_html("📧 Old Email bhejo:", reply_markup=cancel_menu())
    elif state=='await_old_email_change_sec':
        context.user_data['old_email']=text
        context.user_data['state']='await_new_email_change_sec'
        await update.message.reply_html("📧 New Email bhejo:")
    elif state=='await_new_email_change_sec':
        context.user_data['new_email']=text
        context.user_data['state']='await_sec_change_sec'
        await update.message.reply_html("🔐 Security Code bhejo:")
    elif state=='await_sec_change_sec':
        context.user_data['sec_code']=text
        token=context.user_data.get('token'); new_email=context.user_data.get('new_email')
        await update.message.reply_html(f"⏳ OTP bhej raha hu {new_email} par...")
        res=send_otp(token, new_email)
        if not res.get('success'):
            await update.message.reply_html(f"❌ {res.get('message')}", reply_markup=main_menu())
            context.user_data.clear()
            return
        context.user_data['state']='await_new_otp_change_sec'
        await update.message.reply_html("✅ OTP bhej diya! OTP bhejo:")
    elif state=='await_new_otp_change_sec':
        token=context.user_data.get('token'); old=context.user_data.get('old_email'); new=context.user_data.get('new_email'); sec=context.user_data.get('sec_code')
        res=change_email_sec(token, old, new, sec, text)
        await update.message.reply_html(f"{'✅' if res.get('success') else '❌'} {res.get('message')}", reply_markup=main_menu())
        context.user_data.clear()

    # CHANGE OTP
    elif state=='await_token_change_otp':
        context.user_data['token']=text
        context.user_data['state']='await_old_email_change_otp'
        await update.message.reply_html("📧 Old Email bhejo:", reply_markup=cancel_menu())
    elif state=='await_old_email_change_otp':
        context.user_data['old_email']=text
        context.user_data['state']='await_new_email_change_otp'
        await update.message.reply_html("📧 New Email bhejo:")
    elif state=='await_new_email_change_otp':
        context.user_data['new_email']=text
        token=context.user_data.get('token'); old=context.user_data.get('old_email')
        await update.message.reply_html(f"⏳ OTP bhej raha hu {old} par...")
        res=send_otp(token, old)
        if not res.get('success'):
            await update.message.reply_html(f"❌ Old OTP Failed: {res.get('message')}", reply_markup=main_menu())
            context.user_data.clear()
            return
        context.user_data['state']='await_old_otp_change_otp'
        await update.message.reply_html("✅ Old email par OTP bhej diya! Old OTP bhejo:")
    elif state=='await_old_otp_change_otp':
        context.user_data['old_otp']=text
        token=context.user_data.get('token'); new=context.user_data.get('new_email')
        await update.message.reply_html(f"⏳ OTP bhej raha hu {new} par...")
        res=send_otp(token, new)
        if not res.get('success'):
            await update.message.reply_html(f"❌ New OTP Failed: {res.get('message')}", reply_markup=main_menu())
            context.user_data.clear()
            return
        context.user_data['state']='await_new_otp_change_otp'
        await update.message.reply_html("✅ New email par OTP bhej diya! New OTP bhejo:")
    elif state=='await_new_otp_change_otp':
        token=context.user_data.get('token'); old=context.user_data.get('old_email'); new=context.user_data.get('new_email'); old_otp=context.user_data.get('old_otp')
        res=change_email_otp_api(token, old, new, old_otp, text)
        await update.message.reply_html(f"{'✅' if res.get('success') else '❌'} {res.get('message')}", reply_markup=main_menu())
        context.user_data.clear()

    # STATUS
    elif state=='await_token_status':
        await update.message.reply_html("⏳ Fetching bind info...")
        res=get_bind_info(text)
        if not res.get('success'):
            await update.message.reply_html(f"❌ {res.get('message')}", reply_markup=main_menu())
        else:
            cur=res.get('current_email',''); pend=res.get('pending_email',''); ch=res.get('countdown_human',''); cs=res.get('countdown_seconds',0)
            raw=res.get('raw',{}); mob=raw.get('mobile','') if isinstance(raw,dict) else ''; mobp=raw.get('mobile_to_be','') if isinstance(raw,dict) else ''
            t="<b>ℹ️ BIND INFO</b>\n\n"
            t+=f"✅ Current: <code>{cur}</code>\n" if cur else "⚠️ No current email\n"
            if pend: t+=f"⏳ Pending: <code>{pend}</code>\n⏰ {ch or format_seconds(cs)}\n"
            else: t+="— No pending\n"
            if mob: t+=f"📱 Mobile: {mob}\n"
            if mobp: t+=f"📱 Pending Mobile: {mobp}\n"
            await update.message.reply_html(t, reply_markup=main_menu())
        context.user_data.clear()

    # PLATFORMS
    elif state=='await_token_platforms':
        await update.message.reply_html("⏳ Fetching platforms...")
        res=get_platforms(text)
        if not res.get('success'):
            await update.message.reply_html(f"❌ {res.get('message')}", reply_markup=main_menu())
        else:
            bounded=res.get('bounded_accounts') or res.get('bounded',[]); available=res.get('available_platforms') or res.get('available',[]); main=res.get('main_platform')
            t="<b>🎮 LINKED PLATFORMS</b>\n\n<b>Linked:</b>\n"
            if bounded:
                for acc in bounded:
                    t+=f"• <b>{acc.get('platform','?')}</b> {acc.get('nickname','')} {acc.get('email','')} {acc.get('uid','')}\n"
            else: t+="None\n"
            t+="\n<b>Available:</b> "+(", ".join(available) if available else "None")
            if main: t+=f"\n\n<b>Main:</b> {main}"
            await update.message.reply_html(t, reply_markup=main_menu())
        context.user_data.clear()

    # REVOKE
    elif state=='await_token_revoke':
        await update.message.reply_html("⏳ Revoking...")
        res=revoke_token_api(text)
        await update.message.reply_html(f"<b>🚫 REVOKE</b>\n<pre>{json.dumps(res, indent=2)}</pre>", reply_markup=main_menu(), parse_mode='HTML')
        context.user_data.clear()

    # EAT
    elif state=='await_eat':
        await update.message.reply_html("⏳ Converting...")
        eat=extract_eat_token(text)
        if not eat:
            await update.message.reply_html("❌ EAT token extract nahi hua", reply_markup=main_menu())
        else:
            res=eat_to_access_token_api(eat)
            if res.get('success'):
                await update.message.reply_html(f"✅ Success!\n\n🔑 Token:\n<code>{res.get('access_token')}</code>", reply_markup=main_menu(), parse_mode='HTML')
            else:
                await update.message.reply_html(f"❌ Failed: {res.get('error', res.get('message'))}", reply_markup=main_menu())
        context.user_data.clear()

    # JWT
    elif state=='await_jwt':
        await update.message.reply_html("⏳ Extracting...")
        res, err = extract_jwt_info(text)
        if res and res.get('success'):
            t=f"<b>🧬 JWT SUCCESS</b>\n\n🆔 UID: <code>{res.get('account_uid','N/A')}</code>\n🌍 Region: {res.get('region','N/A')}\n🎮 Platform: {res.get('platform_type_used','N/A')}\n🌐 Server: {res.get('url','N/A')}\n\n"
            if res.get('jwt'): t+=f"<b>JWT:</b>\n<code>{res.get('jwt')[:800]}</code>...\n"
            await update.message.reply_html(t, reply_markup=main_menu(), parse_mode='HTML')
        else:
            await update.message.reply_html(f"❌ Failed: {err}", reply_markup=main_menu())
        context.user_data.clear()

# ================= MAIN =================
def main():
    if BOT_TOKEN=="PASTE_YOUR_BOT_TOKEN_HERE":
        print("❌ BOT_TOKEN missing! Set env var BOT_TOKEN")
        return
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("menu", start_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("clear", clear_cmd))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    # Run Flask in thread for Render health check
    import threading
    def run_flask():
        app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
    threading.Thread(target=run_flask, daemon=True).start()

    print(f"🤖 RAO BOT {VERSION} Starting Polling...")
    application.run_polling()

if __name__=="__main__":
    main()
