"""
FIXED FOR RENDER DEPLOYMENT
Spidey Bind Tool - Render Web Service Compatible

Problem: Render Web Service needs open port, but bot uses polling (getUpdates)
Solution: Added dummy Flask server that binds to PORT

Deploy:
- On Render, set as Web Service
- Start Command: python telegram_bot_render_fixed.py
- Add env variable: BOT_TOKEN = 8880751142:AAFmYi1ykGm4EKXQTds8i8_gYd4FuF4UoUU
- Or better create new token, this one leaked in logs!

For Background Worker (better):
- On Render, create Background Worker instead of Web Service
- No need for Flask then, but this fixed file works for both
"""

import os
import threading
import requests
import urllib.parse
import urllib3
import json
from datetime import datetime
from flask import Flask

# --- Flask dummy server for Render port binding ---
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is Running! Spidey Bind Tool Active 🕷️", 200

@app_flask.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    print(f"[Flask] Starting dummy server on port {port} to satisfy Render...")
    # 0.0.0.0 important for Render
    app_flask.run(host="0.0.0.0", port=port)

# --- Bot Logic (PTB) ---
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import logging

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8880751142:AAFmYi1ykGm4EKXQTds8i8_gYd4FuF4UoUU")

ASK_TOKEN_BIND, ASK_TOKEN_EMAIL, ASK_EMAIL, ASK_TOKEN_UNBIND, ASK_TOKEN_CHANGE, ASK_NEW_EMAIL, ASK_TOKEN_CANCEL, ASK_TOKEN_PLATFORMS, ASK_EAT = range(9)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def convert_seconds(s):
    d, h = divmod(s, 86400)
    h, m = divmod(h, 3600)
    m, s = divmod(m, 60)
    return f"{d} Day {h} Hour {m} Min {s} Sec"

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("🔍 CHECK BIND INFO", callback_data="check_bind"),
         InlineKeyboardButton("📧 BIND EMAIL", callback_data="bind_email")],
        [InlineKeyboardButton("❌ UNBIND EMAIL", callback_data="unbind_email"),
         InlineKeyboardButton("🔄 CHANGE EMAIL", callback_data="change_email")],
        [InlineKeyboardButton("🚫 CANCEL REQUEST", callback_data="cancel_bind"),
         InlineKeyboardButton("🔗 BOUND ACCOUNTS", callback_data="bound_accounts")],
        [InlineKeyboardButton("🔑 EAT TO TOKEN", callback_data="eat_token"),
         InlineKeyboardButton("📜 HISTORY", callback_data="history")],
    ]
    return InlineKeyboardMarkup(keyboard)

def fetch_player_info(access_token):
    try:
        player_url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        headers = {"User-Agent": "Mozilla/5.0"}
        p_res = requests.get(player_url, headers=headers, timeout=15, allow_redirects=True)
        parsed_url = urllib.parse.urlparse(p_res.url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        uid = query_params.get("account_id", ["Unknown"])[0]
        nickname = query_params.get("nickname", ["Unknown"])[0]
        region = query_params.get("region", ["Unknown"])[0]
        return uid, nickname, region
    except:
        return "Unknown", "Unknown", "Unknown"

def api_check_bind_info(access_token):
    uid, nickname, region = fetch_player_info(access_token)
    url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
    payload = {'app_id': "100067", 'access_token': access_token}
    headers = {'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"}
    r = requests.get(url, params=payload, headers=headers, timeout=15)
    if r.status_code == 200:
        data = r.json()
        email = data.get("email", "")
        email_to_be = data.get("email_to_be", "")
        countdown = data.get("request_exec_countdown", 0)
        text = f"<b>≡ Player Info</b>\n● UID: <code>{uid}</code>\n● Nickname: {nickname}\n● Region: {region}\n\n<b>≡ Bind Info</b>\n● Current: {email if email else 'None'}\n● Pending: {email_to_be if email_to_be else 'None'}\n"
        if email_to_be:
            text += f"● Countdown: {convert_seconds(countdown)}\n"
        text += f"\nResult: {data.get('result')}"
        return text
    return f"❌ HTTP {r.status_code}: {r.text}"

def api_bind_email(access_token, email):
    url = "https://100067.connect.garena.com/game/account_security/bind:bind_email"
    payload = {'app_id': "100067", 'access_token': access_token, 'email': email}
    headers = {'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"}
    r = requests.get(url, params=payload, headers=headers, timeout=15)
    return r.text

def api_unbind_email(access_token):
    url = "https://100067.connect.garena.com/game/account_security/bind:unbind_email"
    payload = {'app_id': "100067", 'access_token': access_token}
    headers = {'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"}
    r = requests.get(url, params=payload, headers=headers, timeout=15)
    return r.text

def api_change_email(access_token, new_email):
    url = "https://100067.connect.garena.com/game/account_security/bind:change_bind_email"
    payload = {'app_id': "100067", 'access_token': access_token, 'email': new_email}
    headers = {'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"}
    r = requests.get(url, params=payload, headers=headers, timeout=15)
    return r.text

def api_cancel(access_token):
    url = "https://100067.connect.garena.com/game/account_security/bind:cancel_bind_request"
    payload = {'app_id': "100067", 'access_token': access_token}
    headers = {'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"}
    r = requests.get(url, params=payload, headers=headers, timeout=15)
    return r.text

def api_platforms(access_token):
    url = "https://100067.connect.garena.com/bind/app/platform/info/get"
    params = {"access_token": access_token}
    headers = {"User-Agent": "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"}
    r = requests.get(url, params=params, headers=headers, timeout=10)
    if r.status_code != 200:
        return f"❌ HTTP {r.status_code}"
    d = r.json()
    PLATFORM_MAP = {1:"Garena",3:"Facebook",4:"Guest",5:"VK",6:"Huawei",7:"Apple",8:"Google",10:"GameCenter/Line",11:"X (Twitter)",13:"Apple ID",28:"Line",35:"TikTok"}
    text = "<b>≡ BOUND ACCOUNTS:</b>\n"
    for p in d.get("bounded_accounts", []):
        text += f"● {PLATFORM_MAP.get(p, f'Unknown {p}')}\n"
    if not d.get("bounded_accounts"):
        text += "● None\n"
    text += "\n<b>≡ AVAILABLE:</b>\n"
    for p in d.get("available_platforms", []):
        text += f"● {PLATFORM_MAP.get(p, f'Unknown {p}')}\n"
    return text

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "<b>🕷️ Spidey Bind Tool - Running on Render ✅</b>\n\nMenu se select karo 👇"
    await update.message.reply_html(msg, reply_markup=get_main_menu())

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "check_bind":
        await query.message.reply_html("🔑 <b>Access Token bhejo:</b>")
        return ASK_TOKEN_BIND
    elif data == "bind_email":
        await query.message.reply_html("🔑 <b>Pehle Access Token bhejo:</b>")
        return ASK_TOKEN_EMAIL
    elif data == "unbind_email":
        await query.message.reply_html("🔑 <b>Access Token bhejo unbind ke liye:</b>")
        return ASK_TOKEN_UNBIND
    elif data == "change_email":
        await query.message.reply_html("🔑 <b>Access Token bhejo change ke liye:</b>")
        return ASK_TOKEN_CHANGE
    elif data == "cancel_bind":
        await query.message.reply_html("🔑 <b>Access Token bhejo cancel ke liye:</b>")
        return ASK_TOKEN_CANCEL
    elif data == "bound_accounts":
        await query.message.reply_html("🔑 <b>Access Token bhejo:</b>")
        return ASK_TOKEN_PLATFORMS
    elif data == "eat_token":
        await query.message.reply_html("🔑 <b>EAT Token bhejo:</b>")
        return ASK_EAT
    elif data == "history":
        await query.message.reply_html("📜 History feature protobuf mangta hai - original logic add karna hoga", reply_markup=get_main_menu())
        return ConversationHandler.END

async def handle_bind_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip()
    await update.message.reply_html("⏳ Fetching...")
    try:
        result = api_check_bind_info(token)
        await update.message.reply_html(result, reply_markup=get_main_menu())
    except Exception as e:
        await update.message.reply_html(f"❌ Error: {e}", reply_markup=get_main_menu())
    return ConversationHandler.END

async def handle_email_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['temp_token'] = update.message.text.strip()
    await update.message.reply_html("📧 <b>Ab Email bhejo:</b>")
    return ASK_EMAIL

async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    token = context.user_data.get('temp_token')
    await update.message.reply_html(f"⏳ Binding {email}...")
    result = api_bind_email(token, email)
    await update.message.reply_html(f"<code>{result}</code>", reply_markup=get_main_menu())
    return ConversationHandler.END

async def handle_unbind_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = api_unbind_email(update.message.text.strip())
    await update.message.reply_html(f"<code>{result}</code>", reply_markup=get_main_menu())
    return ConversationHandler.END

async def handle_change_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['temp_token'] = update.message.text.strip()
    await update.message.reply_html("📧 <b>New Email bhejo:</b>")
    return ASK_NEW_EMAIL

async def handle_new_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = context.user_data.get('temp_token')
    result = api_change_email(token, update.message.text.strip())
    await update.message.reply_html(f"<code>{result}</code>", reply_markup=get_main_menu())
    return ConversationHandler.END

async def handle_cancel_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = api_cancel(update.message.text.strip())
    await update.message.reply_html(f"<code>{result}</code>", reply_markup=get_main_menu())
    return ConversationHandler.END

async def handle_platforms_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = api_platforms(update.message.text.strip())
    await update.message.reply_html(result, reply_markup=get_main_menu())
    return ConversationHandler.END

async def handle_eat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html("EAT logic yaha add karo - protobuf needed", reply_markup=get_main_menu())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html("❌ Cancelled", reply_markup=get_main_menu())
    return ConversationHandler.END

def main_bot():
    if not BOT_TOKEN or "YOUR_BOT_TOKEN" in BOT_TOKEN:
        print("[!] BOT_TOKEN env var set nahi hai!")
        return
    print(f"[Bot] Starting with token {BOT_TOKEN[:10]}...")
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_callback)],
        states={
            ASK_TOKEN_BIND: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bind_token)],
            ASK_TOKEN_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email_token)],
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email)],
            ASK_TOKEN_UNBIND: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unbind_token)],
            ASK_TOKEN_CHANGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_change_token)],
            ASK_NEW_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_email)],
            ASK_TOKEN_CANCEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cancel_token)],
            ASK_TOKEN_PLATFORMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_platforms_token)],
            ASK_EAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_eat)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", start))
    application.add_handler(conv_handler)

    print("[Bot] Polling started...")
    application.run_polling()

if __name__ == "__main__":
    # Start Flask in background thread for Render Web Service
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Start bot in main thread
    main_bot()
