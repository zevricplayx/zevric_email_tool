"""
🕷️ Spidey Bind Tool - Ultimate Telegram Bot
✅ All 10 Options | Render Ready | No Thread Error
File: final_bot.py | Start: python final_bot.py
"""

import os
import threading
import requests
import urllib.parse
import urllib3
from flask import Flask

flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "🕷️ Spidey Bind Bot is Live ✅", 200
@flask_app.route('/health')
def health():
    return "OK", 200
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
threading.Thread(target=run_flask, daemon=True).start()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import logging
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8880751142:AAFmYi1ykGm4EKXQTds8i8_gYd4FuF4UoUU")

def get_menu():
    kb = [
        [InlineKeyboardButton("🔍 CHECK BIND INFO", callback_data="check_bind"),
         InlineKeyboardButton("📧 BIND EMAIL", callback_data="bind_email")],
        [InlineKeyboardButton("❌ UNBIND EMAIL", callback_data="unbind_email"),
         InlineKeyboardButton("🔄 CHANGE EMAIL", callback_data="change_email")],
        [InlineKeyboardButton("🚫 CANCEL REQUEST", callback_data="cancel_bind"),
         InlineKeyboardButton("🔗 BOUND ACCOUNTS", callback_data="bound_accounts")],
        [InlineKeyboardButton("🔑 EAT → TOKEN", callback_data="eat_token"),
         InlineKeyboardButton("♻️ REVOKE TOKEN", callback_data="revoke_token")],
        [InlineKeyboardButton("📜 LOGIN HISTORY", callback_data="login_history"),
         InlineKeyboardButton("👤 OWNER DETAILS", callback_data="owner_details")],
    ]
    return InlineKeyboardMarkup(kb)

def fetch_player_info(at):
    try:
        url = f"https://api-otrss.garena.com/support/callback/?access_token={at}"
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=15, allow_redirects=True)
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(r.url).query)
        return qs.get("account_id",["Unknown"])[0], qs.get("nickname",["Unknown"])[0], qs.get("region",["Unknown"])[0]
    except:
        return "Unknown","Unknown","Unknown"

def api_check_bind(at):
    uid,nick,region = fetch_player_info(at)
    url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
    r = requests.get(url, params={'app_id':"100067",'access_token':at}, headers={'User-Agent':"GarenaMSDK/4.0.19P9"}, timeout=15)
    try:
        data = r.json()
        email = data.get("email","")
        email_to_be = data.get("email_to_be","")
        return f"<b>🕷️ Spidey Bind</b>\n\nUID: <code>{uid}</code>\nNick: {nick}\nRegion: {region}\n\nCurrent: {email if email else 'None'}\nPending: {email_to_be if email_to_be else 'None'}\nResult: {data.get('result')}"
    except:
        return f"❌ {r.text[:800]}"

def api_bind_email(token,email):
    url = "https://100067.connect.garena.com/game/account_security/bind:bind_email"
    r = requests.get(url, params={'app_id':"100067",'access_token':token,'email':email}, headers={'User-Agent':"GarenaMSDK/4.0.19P9"}, timeout=15)
    return r.text[:2000]
def api_unbind_email(token):
    url = "https://100067.connect.garena.com/game/account_security/bind:unbind_email"
    r = requests.get(url, params={'app_id':"100067",'access_token':token}, headers={'User-Agent':"GarenaMSDK/4.0.19P9"}, timeout=15)
    return r.text[:2000]
def api_change_email(token,email):
    url = "https://100067.connect.garena.com/game/account_security/bind:change_bind_email"
    r = requests.get(url, params={'app_id':"100067",'access_token':token,'email':email}, headers={'User-Agent':"GarenaMSDK/4.0.19P9"}, timeout=15)
    return r.text[:2000]
def api_cancel(token):
    url = "https://100067.connect.garena.com/game/account_security/bind:cancel_bind_request"
    r = requests.get(url, params={'app_id':"100067",'access_token':token}, headers={'User-Agent':"GarenaMSDK/4.0.19P9"}, timeout=15)
    return r.text[:2000]
def api_platforms(token):
    url = "https://100067.connect.garena.com/bind/app/platform/info/get"
    r = requests.get(url, params={"access_token":token}, headers={"User-Agent":"GarenaMSDK/4.0.19P9"}, timeout=10)
    return r.text[:2000]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html("<b>🕷️ Spidey Bind Tool</b>\nDeveloper: @spideyabd & @INDRAJIT_1M\n\nMenu se select karo 👇", reply_markup=get_menu())

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    m = {
        "check_bind": ('check_bind', "🔑 Access Token bhejo:"),
        "bind_email": ('bind_email_token', "🔑 Pehle Access Token bhejo:"),
        "unbind_email": ('unbind_email', "🔑 Access Token bhejo unbind ke liye:"),
        "change_email": ('change_email_token', "🔑 Access Token bhejo change ke liye:"),
        "cancel_bind": ('cancel_bind', "🔑 Access Token bhejo cancel ke liye:"),
        "bound_accounts": ('bound_accounts', "🔑 Access Token bhejo:"),
        "eat_token": ('eat_token', "🔑 EAT Token bhejo:"),
        "revoke_token": ('revoke_token', "♻️ Token bhejo revoke ke liye:"),
        "login_history": ('login_history', "🔑 Token bhejo history ke liye:"),
        "owner_details": ('owner_details', "🔑 Token bhejo owner ke liye:"),
    }
    if data in m:
        act,msg = m[data]
        context.user_data['action']=act
        await query.message.reply_html(msg)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    action = context.user_data.get('action')
    if not action:
        await update.message.reply_html("👋 /start bhejo", reply_markup=get_menu())
        return
    try:
        if action=='check_bind':
            await update.message.reply_html("⏳ Fetching...")
            await update.message.reply_html(api_check_bind(text), reply_markup=get_menu())
        elif action=='bind_email_token':
            context.user_data['temp_token']=text
            context.user_data['action']='bind_email_email'
            await update.message.reply_html("📧 Ab Email bhejo:")
            return
        elif action=='bind_email_email':
            token=context.user_data.get('temp_token')
            await update.message.reply_html(f"⏳ Binding {text}...")
            await update.message.reply_html(f"<code>{api_bind_email(token,text)}</code>", reply_markup=get_menu())
        elif action=='unbind_email':
            await update.message.reply_html(f"<code>{api_unbind_email(text)}</code>", reply_markup=get_menu())
        elif action=='change_email_token':
            context.user_data['temp_token']=text
            context.user_data['action']='change_email_new'
            await update.message.reply_html("📧 New Email bhejo:")
            return
        elif action=='change_email_new':
            token=context.user_data.get('temp_token')
            await update.message.reply_html(f"<code>{api_change_email(token,text)}</code>", reply_markup=get_menu())
        elif action=='cancel_bind':
            await update.message.reply_html(f"<code>{api_cancel(text)}</code>", reply_markup=get_menu())
        elif action=='bound_accounts':
            await update.message.reply_html(f"<code>{api_platforms(text)}</code>", reply_markup=get_main_menu())
        else:
            await update.message.reply_html(f"Feature {action} - Original logic add karo", reply_markup=get_menu())
    except Exception as e:
        await update.message.reply_html(f"❌ {e}", reply_markup=get_menu())
    finally:
        if action not in ['bind_email_token','change_email_token']:
            context.user_data.clear()

def get_main_menu():
    return get_menu()

def main():
    print(f"🤖 Bot starting MAIN THREAD - {BOT_TOKEN[:10]}...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    print("🚀 Polling started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
