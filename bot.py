import os
import sys
import json
import logging
import urllib.parse
import urllib3
import requests
import asyncio
import threading
from flask import Flask, request

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters, ConversationHandler
from telegram.constants import ParseMode

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    HAS_CRYPTO = True
except:
    HAS_CRYPTO = False

try:
    import MajoRLogin_pb2 as mLpB
    import MajorLoginRes_pb2 as mLrPb
    HAS_PROTOBUF = True
except:
    HAS_PROTOBUF = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip()
PORT = int(os.getenv("PORT", "10000"))

ASK_TOKEN, ASK_EMAIL, ASK_NEW_EMAIL, ASK_OLD_EMAIL, ASK_EAT = range(5)

def convert_seconds(s):
    try:
        s=int(s); d,h=divmod(s,86400); h,m=divmod(h,3600); m,s=divmod(m,60)
        return f"{d}d {h}h {m}m {s}s"
    except: return str(s)

def get_player_info(at):
    try:
        r=requests.get(f"https://api-otrss.garena.com/support/callback/?access_token={at}", headers={"User-Agent":"Mozilla/5.0"}, timeout=15, allow_redirects=True)
        qs=urllib.parse.parse_qs(urllib.parse.urlparse(r.url).query)
        return qs.get("account_id",["Unknown"])[0], qs.get("nickname",["Unknown"])[0], qs.get("region",["Unknown"])[0]
    except: return "Unknown","Unknown","Unknown"

def api_bind_info(token):
    uid,nick,reg=get_player_info(token)
    try:
        r=requests.get("https://100067.connect.garena.com/game/account_security/bind:get_bind_info", params={"app_id":"100067","access_token":token}, headers={"User-Agent":"GarenaMSDK/4.0.19P9"}, timeout=15)
        data=r.json() if r.status_code==200 else {"raw":r.text[:800]}
    except Exception as e: data={"error":str(e)}
    email=data.get("email",""); pend=data.get("email_to_be",""); cd=data.get("request_exec_countdown",0)
    return f"🎮 *Player*\nUID: `{uid}`\nNick: {nick}\nRegion: {reg}\n\n🔗 *Bind*\nCurrent: `{email or 'None'}`\nPending: `{pend or 'None'}`\nCountdown: {convert_seconds(cd)}\nResult: {data.get('result',-1)}"

def api_bound(token):
    try:
        r=requests.get("https://100067.connect.garena.com/bind/app/platform/info/get", params={"access_token":token}, headers={"User-Agent":"GarenaMSDK"}, timeout=10)
        if r.status_code!=200: return f"❌ HTTP {r.status_code}"
        d=r.json()
    except Exception as e: return f"❌ {e}"
    mp={1:"Garena",3:"Facebook",4:"Guest",5:"VK",6:"Huawei",7:"Apple",8:"Google",10:"GameCenter",11:"X",13:"Apple ID",28:"Line",35:"TikTok"}
    msg="🔗 *Bound*\n"; 
    for pid in d.get("bounded_accounts",[]): msg+=f"• {mp.get(pid,pid)}\n"
    msg+="\n📋 *Available*\n"
    for pid in d.get("available_platforms",[]): msg+=f"• {mp.get(pid,pid)}\n"
    return msg

def api_bind_email(token,email):
    try:
        r=requests.post("https://100067.connect.garena.com/game/account_security/bind:request_bind", json={"app_id":"100067","access_token":token,"email":email}, headers={"User-Agent":"GarenaMSDK"}, timeout=15)
        return f"📧 Bind {email}\n`{r.text[:1200]}`"
    except Exception as e: return f"❌ {e}"
def api_unbind(token):
    try:
        r=requests.get("https://100067.connect.garena.com/game/account_security/bind:unbind", params={"app_id":"100067","access_token":token}, headers={"User-Agent":"GarenaMSDK"}, timeout=15)
        return f"🗑️ Unbind: `{r.text[:1200]}`"
    except Exception as e: return f"❌ {e}"
def api_change(token,old,new):
    try:
        r=requests.post("https://100067.connect.garena.com/game/account_security/bind:change_bind", json={"app_id":"100067","access_token":token,"old_email":old,"new_email":new}, headers={"User-Agent":"GarenaMSDK"}, timeout=15)
        return f"🔄 {old} -> {new}\n`{r.text[:1200]}`"
    except Exception as e: return f"❌ {e}"
def api_cancel(token):
    try:
        r=requests.get("https://100067.connect.garena.com/game/account_security/bind:cancel_request", params={"app_id":"100067","access_token":token}, headers={"User-Agent":"GarenaMSDK"}, timeout=15)
        return f"🚫 Cancel: `{r.text[:1200]}`"
    except Exception as e: return f"❌ {e}"
def api_revoke(token):
    try:
        for u in ["https://100067.connect.garena.com/oauth/guest/revoke","https://100067.connect.garena.com/game/account_security/bind:revoke"]:
            r=requests.get(u, params={"app_id":"100067","access_token":token}, headers={"User-Agent":"GarenaMSDK"}, timeout=15)
            if r.status_code==200: return f"🔒 Revoke: `{r.text[:1200]}`"
        return f"🔒 Last: `{r.text[:1200]}`"
    except Exception as e: return f"❌ {e}"
def eat_to_token(eat):
    if not HAS_PROTOBUF: return "❌ Protobuf files missing - add MajoRLogin_pb2.py"
    try:
        r=requests.post("https://100067.connect.garena.com/oauth/guest/token_grant", json={"app_id":"100067","eat":eat}, headers={"User-Agent":"GarenaMSDK"}, timeout=15)
        try:
            pb=mLrPb.MajorLoginRes(); pb.ParseFromString(r.content)
            return f"✅ Token: `{getattr(pb,'access_token','Not found')}`"
        except: return f"📥 `{r.text[:1500]}`"
    except Exception as e: return f"❌ {e}"
def history(token):
    try:
        r=requests.get("https://100067.connect.garena.com/game/account_security/history:get_history", params={"app_id":"100067","access_token":token}, headers={"User-Agent":"GarenaMSDK"}, timeout=15)
        return f"📜 Size {len(r.content)} bytes\n`{r.text[:1000]}`"
    except Exception as e: return f"❌ {e}"

def menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Bind Info", callback_data="1"), InlineKeyboardButton("📧 Bind Email", callback_data="2")],
        [InlineKeyboardButton("🗑️ Unbind", callback_data="3"), InlineKeyboardButton("🔄 Change", callback_data="4")],
        [InlineKeyboardButton("🚫 Cancel", callback_data="5"), InlineKeyboardButton("🔑 EAT→Token", callback_data="6")],
        [InlineKeyboardButton("🔒 Revoke", callback_data="7"), InlineKeyboardButton("📜 History", callback_data="8")],
        [InlineKeyboardButton("🔗 Bound Acc", callback_data="9"), InlineKeyboardButton("👑 Owner", callback_data="10")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🕷️ *Spidey Bind Tool - Web Edition*\nSelect option:", reply_markup=menu_kb(), parse_mode=ParseMode.MARKDOWN)

async def cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer(); c=q.data
    if c=="1": context.user_data['a']='bind_info'; await q.message.reply_text("🔑 Token bhejo:"); return ASK_TOKEN
    if c=="2": context.user_data['a']='be1'; await q.message.reply_text("🔑 Token bhejo:"); return ASK_TOKEN
    if c=="3": context.user_data['a']='unbind'; await q.message.reply_text("🔑 Token bhejo:"); return ASK_TOKEN
    if c=="4": context.user_data['a']='ch1'; await q.message.reply_text("🔑 Token bhejo:"); return ASK_TOKEN
    if c=="5": context.user_data['a']='cancel'; await q.message.reply_text("🔑 Token bhejo:"); return ASK_TOKEN
    if c=="6": context.user_data['a']='eat'; await q.message.reply_text("🍪 EAT bhejo:"); return ASK_EAT
    if c=="7": context.user_data['a']='revoke'; await q.message.reply_text("🔑 Token bhejo:"); return ASK_TOKEN
    if c=="8": context.user_data['a']='hist'; await q.message.reply_text("🔑 Token bhejo:"); return ASK_TOKEN
    if c=="9": context.user_data['a']='plat'; await q.message.reply_text("🔑 Token bhejo:"); return ASK_TOKEN
    if c=="10": await q.message.reply_text("👑 Dev: @spideyabd & @INDRAJIT_1M", reply_markup=menu_kb(), parse_mode=ParseMode.MARKDOWN)

async def h_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tok=update.message.text.strip(); a=context.user_data.get('a'); await update.message.reply_text("⏳ Processing...")
    mapping={
        'bind_info': lambda: api_bind_info(tok),
        'unbind': lambda: api_unbind(tok),
        'cancel': lambda: api_cancel(tok),
        'revoke': lambda: api_revoke(tok),
        'hist': lambda: history(tok),
        'plat': lambda: api_bound(tok),
    }
    if a in mapping:
        await update.message.reply_text(mapping[a](), parse_mode=ParseMode.MARKDOWN, reply_markup=menu_kb()); return ConversationHandler.END
    if a=='be1':
        context.user_data['tok']=tok; context.user_data['a']='be2'; await update.message.reply_text("📧 Email bhejo:"); return ASK_NEW_EMAIL
    if a=='ch1':
        context.user_data['tok']=tok; context.user_data['a']='ch2'; await update.message.reply_text("📧 Old Email:"); return ASK_OLD_EMAIL

async def h_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    em=update.message.text.strip(); a=context.user_data.get('a'); tok=context.user_data.get('tok')
    if a=='be2':
        await update.message.reply_text(api_bind_email(tok,em), parse_mode=ParseMode.MARKDOWN, reply_markup=menu_kb()); return ConversationHandler.END
    if a=='ch3':
        old=context.user_data.get('old'); await update.message.reply_text(api_change(tok,old,em), parse_mode=ParseMode.MARKDOWN, reply_markup=menu_kb()); return ConversationHandler.END

async def h_old(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['old']=update.message.text.strip(); context.user_data['a']='ch3'; await update.message.reply_text("📧 New Email:"); return ASK_NEW_EMAIL

async def h_eat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Converting..."); await update.message.reply_text(eat_to_token(update.message.text.strip()), parse_mode=ParseMode.MARKDOWN, reply_markup=menu_kb()); return ConversationHandler.END

async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled", reply_markup=menu_kb()); return ConversationHandler.END

# ---- PTB App ----
ptb_app = None
loop = None
lock = threading.Lock()

def get_loop():
    global loop
    with lock:
        if loop is None or loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop

def build_ptb():
    global ptb_app
    if ptb_app: return ptb_app
    if not BOT_TOKEN: raise RuntimeError("BOT_TOKEN env missing")
    b = ApplicationBuilder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(cb)],
        states={
            ASK_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, h_token)],
            ASK_NEW_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, h_new)],
            ASK_OLD_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, h_old)],
            ASK_EAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, h_eat)],
        },
        fallbacks=[CommandHandler("cancel", cancel_cmd)],
        allow_reentry=True
    )
    b.add_handler(CommandHandler("start", start))
    b.add_handler(CommandHandler("menu", start))
    b.add_handler(conv)
    ptb_app = b
    return ptb_app

def init_ptb():
    l=get_loop(); app=build_ptb()
    l.run_until_complete(app.initialize())
    l.run_until_complete(app.start())
    return app

# ---- Flask App (gunicorn needs `app`) ----
flask_app = Flask(__name__)
app = flask_app

@flask_app.route("/", methods=["GET"])
def home():
    return "🕷️ Spidey Bot Running | /setwebhook to activate", 200

@flask_app.route("/setwebhook", methods=["GET"])
def sethook():
    if not WEBHOOK_URL: return "Set WEBHOOK_URL env like https://your-app.onrender.com", 400
    if not BOT_TOKEN: return "BOT_TOKEN missing", 400
    try:
        l=get_loop()
        try: init_ptb()
        except: pass
        async def _set(): await ptb_app.bot.set_webhook(url=f"{WEBHOOK_URL.rstrip('/')}/{BOT_TOKEN}")
        l.run_until_complete(_set())
        return f"✅ Webhook set to {WEBHOOK_URL.rstrip('/')}/{BOT_TOKEN}", 200
    except Exception as e: return f"❌ {e}", 500

@flask_app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    try:
        l=get_loop()
        if ptb_app is None: init_ptb()
        update = Update.de_json(request.get_json(force=True), ptb_app.bot)
        l.run_until_complete(ptb_app.process_update(update))
    except Exception as e:
        logger.error(f"webhook err {e}", exc_info=True)
    return "ok", 200

@flask_app.route("/webhook", methods=["POST"])
def webhook2():
    # alternative without token in url
    return webhook()

def run_polling():
    if not BOT_TOKEN: print("BOT_TOKEN missing"); sys.exit(1)
    a=build_ptb(); a.run_polling()

if __name__ == "__main__":
    if WEBHOOK_URL:
        try: init_ptb()
        except Exception as e: print(e)
        flask_app.run(host="0.0.0.0", port=PORT)
    else:
        run_polling()
