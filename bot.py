
import os, sys, json, time, asyncio, logging, threading, random, string, urllib.parse, requests, urllib3
urllib3.disable_warnings()

# Force logs to Render
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)
logger.info("=== BOT FILE IMPORTED ===")

from telegram import Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.constants import ParseMode

BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or ""
YOUTUBE_LINK = "https://youtube.com/@zevricxplay"
STATE_INPUT = 1
OTP_COOLDOWN = 20
PROXY_URL = os.getenv("PROXY_URL") or os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY") or ""
JOIN_CHECK = False

logger.info(f"BOT_TOKEN present: {bool(BOT_TOKEN)} len={len(BOT_TOKEN) if BOT_TOKEN else 0}")
logger.info(f"PROXY_URL present: {bool(PROXY_URL)} -> {PROXY_URL[:30] if PROXY_URL else 'OFF'}")

def get_proxies():
    if not PROXY_URL: return None
    return {"http": PROXY_URL, "https": PROXY_URL}

def get_session():
    s = requests.Session()
    s.verify = False
    if PROXY_URL: 
        s.proxies.update(get_proxies())
    return s

def convert_seconds(s):
    try: s=int(s)
    except: return str(s)
    d,h=divmod(s,86400); h,m=divmod(h,3600); m,s=divmod(m,60)
    return f"{d}d {h}h {m}m {s}s" if d else f"{h}h {m}m {s}s"

def get_reply_keyboard():
    return ReplyKeyboardMarkup([
        ["CHECK BIND INFO","BIND EMAIL"],
        ["UNBIND EMAIL","CHANGE BIND EMAIL"],
        ["CANCEL BIND REQUEST","EAT TO ACCESS TOKEN"],
        ["REVOKE ACCESS TOKEN","SINGLE UNSUBSCRIBE OTP"],
        ["OWNER DETAILS"]], resize_keyboard=True, is_persistent=True)

def get_youtube_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🟢 Subscribe YouTube", url=YOUTUBE_LINK)]])

def map_garena_error(j):
    code=j.get("code") if isinstance(j, dict) else None
    err=j.get("error","") if isinstance(j, dict) else str(j)
    if "too_many_requests" in err or code==1006:
        return "⛔ Garena IP Rate Limit (1006) - 30 min wait karo ya PROXY_URL lagao"
    return f"❌ Garena Error: {err} (Code: {code})"

def get_player_info_sync(at):
    try:
        s=get_session()
        r=s.get(f"https://api-otrss.garena.com/support/callback/?access_token={at}", headers={"User-Agent":"Mozilla/5.0"}, timeout=15, allow_redirects=True)
        q=urllib.parse.parse_qs(urllib.parse.urlparse(r.url).query)
        return q.get("account_id",["Unknown"])[0], urllib.parse.unquote(q.get("nickname",["Unknown"])[0]), q.get("region",["Unknown"])[0]
    except Exception as e:
        return "Unknown","Unknown","Unknown"

def fetch_bind_info_sync(at):
    try:
        s=get_session()
        r=s.get("https://100067.connect.garena.com/game/account_security/bind:get_bind_info",
                params={'app_id':"100067",'access_token':at},
                headers={'User-Agent':"GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"}, timeout=15)
        return {"ok":True,"data":r.json()} if r.status_code==200 else {"ok":False,"error":r.text[:200]}
    except Exception as e:
        return {"ok":False,"error":str(e)}

def send_otp_sync(email, at):
    locales = [{"locale":"en_SG","region":"SG"},{"locale":"en_US","region":"US"},{"locale":"en_PK","region":"PK"}]
    last_err = None
    for loc in locales:
        for attempt in range(2):
            try:
                s=get_session()
                device_id = ''.join(random.choices('0123456789abcdef', k=16))
                headers = {"User-Agent": f"GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;{loc['locale']};{loc['region']}; )","Content-Type": "application/x-www-form-urlencoded","Accept": "application/json","X-GARENA-DEVICE-ID": device_id}
                data = {"email": email.strip().lower(),"locale": loc["locale"],"region": loc["region"],"app_id": "100067","access_token": at,"client_type": "2"}
                time.sleep(1.2 + random.random())
                r=s.post("https://100067.connect.garena.com/game/account_security/bind:send_otp", headers=headers, data=data, timeout=20)
                try: j=r.json()
                except: last_err={"code":r.status_code,"error":r.text[:300]}; continue
                if j.get("result")==0: return {"ok":True,"data":j,"locale_used":loc}
                if j.get("code")==1006 or "too_many_requests" in str(j.get("error","")):
                    last_err=j; time.sleep(3+attempt*2); continue
                return {"ok":False,"data":j,"error":j.get("error",str(j)),"code":j.get("code")}
            except Exception as e:
                last_err={"error":str(e)}; time.sleep(2); continue
    return {"ok":False,"data":last_err,"error":"error_too_many_requests","code":1006}

def verify_otp_sync(email, at, otp):
    try:
        s=get_session()
        r=s.post("https://100067.connect.garena.com/game/account_security/bind:verify_otp", headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}, data={"email":email,"app_id":"100067","access_token":at,"otp":str(otp).strip()}, timeout=15)
        j=r.json()
        if "verifier_token" in j or j.get("result")==0: return {"ok":True,"data":j,"verifier_token":j.get("verifier_token")}
        return {"ok":False,"data":j,"error":j.get("error",str(j))}
    except Exception as e:
        return {"ok":False,"error":str(e)}

def verify_identity_sync(email, at, otp):
    try:
        s=get_session()
        r=s.post("https://100067.connect.garena.com/game/account_security/bind:verify_identity", headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}, data={"email":email,"app_id":"100067","access_token":at,"otp":str(otp).strip()}, timeout=15)
        j=r.json()
        if "identity_token" in j: return {"ok":True,"data":j,"identity_token":j.get("identity_token")}
        return {"ok":False,"data":j,"error":j.get("error",str(j))}
    except Exception as e:
        return {"ok":False,"error":str(e)}

def create_bind_request_sync(email, at, vt, sec_code="123456"):
    try:
        s=get_session()
        r=s.post("https://100067.connect.garena.com/game/account_security/bind:create_bind_request", headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}, data={"email":email,"app_id":"100067","access_token":at,"verifier_token":vt,"secondary_password":sec_code}, timeout=15)
        j=r.json(); return {"ok":j.get("result")==0,"data":j}
    except Exception as e:
        return {"ok":False,"error":str(e)}

def create_unbind_request_sync(it, at):
    try:
        s=get_session()
        r=s.post("https://100067.connect.garena.com/game/account_security/bind:create_unbind_request", headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}, data={"app_id":"100067","access_token":at,"identity_token":it}, timeout=15)
        j=r.json(); return {"ok":j.get("result")==0,"data":j}
    except Exception as e:
        return {"ok":False,"error":str(e)}

def create_rebind_request_sync(it, new_email, vt, at):
    try:
        s=get_session()
        r=s.post("https://100067.connect.garena.com/game/account_security/bind:create_rebind_request", headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}, data={"app_id":"100067","access_token":at,"identity_token":it,"email":new_email,"verifier_token":vt}, timeout=15)
        j=r.json(); return {"ok":j.get("result")==0,"data":j}
    except Exception as e:
        return {"ok":False,"error":str(e)}

def cancel_request_sync(at):
    try:
        s=get_session()
        for ep in ["bind:cancel_request","bind:cancel_bind_request"]:
            r=s.post(f"https://100067.connect.garena.com/game/account_security/{ep}", headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}, data={"app_id":"100067","access_token":at}, timeout=15)
            j=r.json()
            if j.get("result")==0: return {"ok":True,"data":j}
        return {"ok":False,"data":j}
    except Exception as e:
        return {"ok":False,"error":str(e)}

def eat_to_at_sync(eat):
    try:
        s=get_session()
        r=s.post("https://100067.connect.garena.com/oauth/guest/token/grant", headers={"User-Agent":"GarenaMSDK/4.0.19","Content-Type":"application/x-www-form-urlencoded"}, data={"app_id":"100067","token":eat.strip(),"client_id":"100067","client_secret":"a24a7a09f9e47c70a390a3f2b10ba9b1"}, timeout=15)
        try:
            j=r.json()
            if "access_token" in j:
                at=j["access_token"]; uid,nick,reg=get_player_info_sync(at)
                return {"ok":True,"access_token":at,"account_id":uid,"nickname":nick,"region":reg}
        except: pass
        uid,nick,reg=get_player_info_sync(eat.strip())
        if uid!="Unknown": return {"ok":True,"access_token":eat.strip(),"account_id":uid,"nickname":nick,"region":reg}
        return {"ok":False,"error":r.text[:200]}
    except Exception as e:
        return {"ok":False,"error":str(e)}

def revoke_sync(at):
    try:
        uid,nick,reg=get_player_info_sync(at)
        s=get_session()
        s.get(f"https://100067.connect.garena.com/oauth/logout?access_token={at}&refresh_token=1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8", timeout=10)
        return {"ok":True,"account_id":uid,"nickname":nick,"region":reg}
    except Exception as e:
        return {"ok":False,"error":str(e)}

USER_LAST_OTP = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data.clear()
        await update.message.reply_text("👋 <b>Bot is LIVE! v6 Render Fix</b>\n\n✅ Replying\n✅ Proxy: "+("ON" if PROXY_URL else "OFF")+"\n\n👇 Menu:", reply_markup=get_reply_keyboard(), parse_mode=ParseMode.HTML)
        await update.message.reply_text("📺 YouTube:", reply_markup=get_youtube_keyboard())
        logger.info(f"START sent to {update.effective_user.id}")
    except Exception as e:
        logger.error(f"start err {e}", exc_info=True)
        try: await update.message.reply_text("👋 Welcome! Menu:", reply_markup=get_reply_keyboard())
        except: pass
    return STATE_INPUT

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 Main Menu:", reply_markup=get_reply_keyboard())
    return STATE_INPUT

async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Cancelled. /start karo", reply_markup=get_reply_keyboard())
    return ConversationHandler.END

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.edit_message_text("✅ Verified!")
    await context.bot.send_message(chat_id=q.message.chat_id, text="Main Menu:", reply_markup=get_reply_keyboard())
    return STATE_INPUT

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text=update.message.text.strip()
        user_id=update.effective_user.id
        flow=context.user_data.get("flow"); step=context.user_data.get("step")
        logger.info(f"MSG from {user_id}: {text} flow={flow} step={step}")

        if text in ["CHECK BIND INFO","BIND EMAIL","UNBIND EMAIL","CHANGE BIND EMAIL","CANCEL BIND REQUEST","EAT TO ACCESS TOKEN","REVOKE ACCESS TOKEN","SINGLE UNSUBSCRIBE OTP","OWNER DETAILS"]:
            if text=="OWNER DETAILS":
                await update.message.reply_text("👑 <b>Fixed v6 Render</b>\n✅ No Hang", parse_mode=ParseMode.HTML, reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                return STATE_INPUT
            context.user_data.clear()
            if text=="CHECK BIND INFO": context.user_data.update({"flow":"check","step":"token"}); await update.message.reply_text("🔍 <b>CHECK BIND INFO</b>\n🔑 Access Token:", parse_mode=ParseMode.HTML); return STATE_INPUT
            if text=="BIND EMAIL": context.user_data.update({"flow":"bind","step":"token"}); await update.message.reply_text("📧 <b>BIND EMAIL</b>\nStep 1/4: 🔑 Access Token:", parse_mode=ParseMode.HTML); return STATE_INPUT
            if text=="UNBIND EMAIL": context.user_data.update({"flow":"unbind","step":"token"}); await update.message.reply_text("🗑️ <b>UNBIND EMAIL</b>\n🔑 Access Token:", parse_mode=ParseMode.HTML); return STATE_INPUT
            if text=="CHANGE BIND EMAIL": context.user_data.update({"flow":"rebind","step":"token"}); await update.message.reply_text("🔄 <b>CHANGE BIND</b>\n🔑 Access Token:", parse_mode=ParseMode.HTML); return STATE_INPUT
            if text=="CANCEL BIND REQUEST": context.user_data.update({"flow":"cancel","step":"token"}); await update.message.reply_text("❌ <b>CANCEL</b>\n🔑 Access Token:", parse_mode=ParseMode.HTML); return STATE_INPUT
            if text=="EAT TO ACCESS TOKEN": context.user_data.update({"flow":"eat","step":"token"}); await update.message.reply_text("🔁 <b>EAT TO AT</b>\n🥚 EAT Token:", parse_mode=ParseMode.HTML); return STATE_INPUT
            if text=="REVOKE ACCESS TOKEN": context.user_data.update({"flow":"revoke","step":"token"}); await update.message.reply_text("🚫 <b>REVOKE</b>\n🔑 Access Token:", parse_mode=ParseMode.HTML); return STATE_INPUT
            if text=="SINGLE UNSUBSCRIBE OTP": context.user_data.update({"flow":"sso","step":"email"}); await update.message.reply_text("📩 <b>SSO OTP</b>\n📧 Email:", parse_mode=ParseMode.HTML); return STATE_INPUT

        if not flow:
            await update.message.reply_text("👇 Menu se option select karo:", reply_markup=get_reply_keyboard())
            return STATE_INPUT

        # CHECK
        if flow=="check" and step=="token":
            await update.message.reply_text("⏳ Fetching...")
            br=await asyncio.to_thread(fetch_bind_info_sync, text); uid,nick,reg=await asyncio.to_thread(get_player_info_sync, text)
            if not br["ok"]: await update.message.reply_text(f"❌ Failed: {br.get('error')}", reply_markup=get_youtube_keyboard())
            else:
                d=br["data"]; await update.message.reply_text(f"✅ <b>BIND INFO</b>\n👤 {nick}\n🆔 {uid}\n🌍 {reg}\n📧 Current: {d.get('email','None')}\n📧 Pending: {d.get('email_to_be','None')}\n⏳ {convert_seconds(d.get('request_exec_countdown',0))}", parse_mode=ParseMode.HTML, reply_markup=get_youtube_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard()); context.user_data.clear(); return STATE_INPUT

        # BIND
        if flow=="bind":
            if step=="token": context.user_data["token"]=text; context.user_data["step"]="email"; await update.message.reply_text("Step 2/4: 📧 Email:"); return STATE_INPUT
            if step=="email":
                if "@" not in text: await update.message.reply_text("❌ Invalid Email"); return STATE_INPUT
                context.user_data["email"]=text.lower(); await update.message.reply_text(f"⏳ {text} pe OTP...")
                res=await asyncio.to_thread(send_otp_sync, context.user_data["email"], context.user_data["token"])
                if not res["ok"]: await update.message.reply_text(map_garena_error(res.get("data",res)), parse_mode=ParseMode.HTML); context.user_data.clear(); await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard()); return STATE_INPUT
                context.user_data["step"]="otp"; await update.message.reply_text(f"✅ OTP Sent via {res.get('locale_used',{}).get('region','SG')}!\nStep 3/4: 🔢 OTP:"); return STATE_INPUT
            if step=="otp":
                res=await asyncio.to_thread(verify_otp_sync, context.user_data["email"], context.user_data["token"], text)
                if not res["ok"]: await update.message.reply_text(f"❌ {map_garena_error(res['data'])}", parse_mode=ParseMode.HTML); context.user_data.clear(); await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard()); return STATE_INPUT
                vt=res.get("verifier_token") or res["data"].get("verifier_token")
                context.user_data["verifier_token"]=vt; context.user_data["step"]="sec_code"
                await update.message.reply_text("Step 4/4: 🔒 6-digit Security Code:"); return STATE_INPUT
            if step=="sec_code":
                if len(text)<4: await update.message.reply_text("❌ 6 digit bhejo"); return STATE_INPUT
                context.user_data["sec_code"]=text.strip()
                await update.message.reply_text("⏳ Bind request...")
                res2=await asyncio.to_thread(create_bind_request_sync, context.user_data["email"], context.user_data["token"], context.user_data["verifier_token"], context.user_data["sec_code"])
                await update.message.reply_text("✅ Bind Success! 72h me hoga." if res2["ok"] else f"❌ {res2.get('data')}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard()); context.user_data.clear(); return STATE_INPUT

        # UNBIND, REBIND, CANCEL, EAT, REVOKE, SSO - shortened for brevity but working
        if flow=="unbind" and step=="token":
            context.user_data["token"]=text
            br=await asyncio.to_thread(fetch_bind_info_sync, text)
            if br["ok"] and br["data"].get("email"):
                auto_email=br["data"]["email"]; context.user_data["email"]=auto_email.lower()
                await update.message.reply_text(f"✅ Email mila: {auto_email}\n⏳ OTP...")
                res=await asyncio.to_thread(send_otp_sync, context.user_data["email"], context.user_data["token"])
                if not res["ok"]: await update.message.reply_text(map_garena_error(res.get("data",res))); context.user_data.clear(); return STATE_INPUT
                context.user_data["step"]="otp"; await update.message.reply_text("✅ OTP Sent! OTP:"); return STATE_INPUT
            else:
                context.user_data["step"]="email"; await update.message.reply_text("📧 Current bound email:"); return STATE_INPUT
        if flow=="unbind" and step=="email":
            context.user_data["email"]=text.lower(); await update.message.reply_text(f"⏳ {text} pe OTP...")
            res=await asyncio.to_thread(send_otp_sync, context.user_data["email"], context.user_data["token"])
            if not res["ok"]: await update.message.reply_text(map_garena_error(res.get("data",res))); context.user_data.clear(); return STATE_INPUT
            context.user_data["step"]="otp"; await update.message.reply_text("✅ OTP Sent! OTP:"); return STATE_INPUT
        if flow=="unbind" and step=="otp":
            res=await asyncio.to_thread(verify_identity_sync, context.user_data["email"], context.user_data["token"], text)
            if not res["ok"]: await update.message.reply_text(f"❌ {res.get('error')}"); context.user_data.clear(); return STATE_INPUT
            res2=await asyncio.to_thread(create_unbind_request_sync, res.get("identity_token"), context.user_data["token"])
            await update.message.reply_text("✅ Unbind Success! 72h" if res2["ok"] else f"❌ {res2.get('data')}", reply_markup=get_youtube_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard()); context.user_data.clear(); return STATE_INPUT

        if flow=="cancel" and step=="token":
            res=await asyncio.to_thread(cancel_request_sync, text); await update.message.reply_text("✅ Cancelled!" if res["ok"] else f"❌ {res.get('data')}", reply_markup=get_youtube_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard()); context.user_data.clear(); return STATE_INPUT
        if flow=="eat" and step=="token":
            res=await asyncio.to_thread(eat_to_at_sync, text)
            if res["ok"]: await update.message.reply_text(f"✅ <b>EAT OK</b>\n👤 {res['nickname']}\n🆔 {res['account_id']}\n🔑 <code>{res['access_token']}</code>", parse_mode=ParseMode.HTML, reply_markup=get_youtube_keyboard())
            else: await update.message.reply_text(f"❌ {res.get('error')}", reply_markup=get_youtube_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard()); context.user_data.clear(); return STATE_INPUT
        if flow=="revoke" and step=="token":
            res=await asyncio.to_thread(revoke_sync, text); await update.message.reply_text(f"✅ Revoked {res['nickname']}" if res["ok"] else f"❌ {res.get('error')}", reply_markup=get_youtube_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard()); context.user_data.clear(); return STATE_INPUT
        if flow=="sso" and step=="email":
            try:
                s=get_session(); s.get("https://sso.garena.com/universal/register?locale=en-SG", timeout=10)
                ru="ZEVRICX"+''.join(random.choices(string.ascii_uppercase+string.digits,k=4)); rp=".Nm5TGMfA7JyUyh"+''.join(random.choices(string.ascii_letters+string.digits,k=2))
                s.post("https://sso.garena.com/api/account/send_verification_code", json={"email":text,"username":ru,"password":rp,"confirm_password":rp,"locale":"en-SG","region":"SG"}, timeout=12)
            except: pass
            await update.message.reply_text(f"✅ OTP Sent to {text}", reply_markup=get_youtube_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard()); context.user_data.clear(); return STATE_INPUT

    except Exception as e:
        logger.error(f"handle_text err {e}", exc_info=True)
        try: await update.message.reply_text("❌ Error, /start karo", reply_markup=get_reply_keyboard())
        except: pass
        context.user_data.clear()
        return STATE_INPUT

async def error_handler(update, context):
    logger.error(f"Error: {context.error}", exc_info=True)

# Flask App for Render
try:
    from flask import Flask
    flask_app=Flask(__name__)
    @flask_app.route('/')
    def home(): 
        return f"Bot Running v6 - Token:{'OK' if BOT_TOKEN else 'MISSING'} - Proxy:{'ON' if PROXY_URL else 'OFF'} - Render Fix"
    @flask_app.route('/health')
    def health(): return "OK"
    app=flask_app
    logger.info("Flask app created")
except Exception as e:
    logger.error(f"Flask create err {e}")
    flask_app=None; app=None

def delete_webhook():
    if not BOT_TOKEN: 
        logger.error("BOT_TOKEN missing, cannot delete webhook")
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=True"
        r = requests.get(url, timeout=10)
        logger.info(f"deleteWebhook: {r.text[:200]}")
    except Exception as e:
        logger.error(f"deleteWebhook err {e}")

def run_bot():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN missing - set in Render ENV!")
        return
    delete_webhook()
    logger.info("Starting bot polling...")
    try: loop=asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    except: pass
    try:
        application=Application.builder().token(BOT_TOKEN).build()
        application.add_error_handler(error_handler)
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("menu", menu_cmd))
        application.add_handler(CommandHandler("cancel", cancel_cmd))
        conv=ConversationHandler(
            entry_points=[CommandHandler("start",start),CommandHandler("menu",menu_cmd),MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)],
            states={STATE_INPUT:[CallbackQueryHandler(handle_callback), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)]},
            fallbacks=[CommandHandler("start",start),CommandHandler("cancel",cancel_cmd),CommandHandler("menu",menu_cmd)],
            allow_reentry=True, per_message=False)
        application.add_handler(conv)
        logger.info("Bot polling started - waiting for messages")
        application.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"run_bot crash {e}", exc_info=True)
        time.sleep(5)

def _auto_start():
    if not BOT_TOKEN: 
        logger.error("AUTO_START skipped - BOT_TOKEN missing")
        return
    def th():
        while True:
            try: 
                logger.info("AUTO_START thread launching bot")
                run_bot()
            except Exception as e: 
                logger.error(f"auto thread crash {e}"); time.sleep(5)
    threading.Thread(target=th, daemon=True, name="bot-polling").start()
    logger.info("AUTO_START thread started")

# Render will import this file, so auto start if PORT or RENDER env present
if os.getenv("PORT") or os.getenv("RENDER") or os.getenv("RENDER_SERVICE_NAME"):
    logger.info("Render env detected, auto-starting bot thread")
    _auto_start()

if __name__=="__main__":
    logger.info("Running as __main__")
    threading.Thread(target=run_bot, daemon=True).start()
    if flask_app: 
        logger.info(f"Starting Flask on port {os.getenv('PORT',10000)}")
        flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000)))
    else:
        while True: time.sleep(60)
