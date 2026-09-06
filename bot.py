import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import sys, json, time, urllib.parse, requests, threading, random, string
import urllib3
urllib3.disable_warnings()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or "YOUR_BOT_TOKEN_HERE"
YOUTUBE_LINK = "https://youtube.com/@zevricxplay"
STATE_INPUT = 1

REQUIRED_CHANNELS = [
    {"name": "Zevric All Update", "link": "https://t.me/zevric_all_update", "chat_id": "@zevric_all_update"},
    {"name": "Zevric X Play", "link": "https://t.me/zevricxplay", "chat_id": "@zevricxplay"},
    {"name": "Zevric Banner", "link": "https://t.me/zevricbaner", "chat_id": "@zevricbaner"},
    {"name": "Zevric Api Tools", "link": "https://t.me/zevric_api_tools", "chat_id": "@zevric_api_tools"},
    {"name": "Zevric Illegal Vounch", "link": "https://t.me/zevric_illigalvounch", "chat_id": "@zevric_illigalvounch"},
]

async def check_user_joined_all(context, user_id):
    not_joined = []
    for ch in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=ch["chat_id"], user_id=user_id)
            if member.status in ["left", "kicked"]:
                not_joined.append(ch)
        except: pass
    return not_joined

def get_force_join_keyboard():
    kb = []
    for ch in REQUIRED_CHANNELS:
        kb.append([InlineKeyboardButton(text=f"Join {ch['name']}", url=ch["link"])])
    kb.append([InlineKeyboardButton(text="I Have Joined", callback_data="check_join")])
    return InlineKeyboardMarkup(kb)

def get_force_join_text(not_joined_list=None):
    names = "\n".join([f"- {ch['name']}" for ch in (not_joined_list or REQUIRED_CHANNELS)])
    return f"Join Verification Required\n\nJoin these groups:\n{names}\n\nThen click I Have Joined:"

def get_reply_keyboard():
    keyboard=[
        ["CHECK BIND INFO","BIND EMAIL"],
        ["UNBIND EMAIL","CHANGE BIND EMAIL"],
        ["CANCEL BIND REQUEST","EAT TO ACCESS TOKEN"],
        ["REVOKE ACCESS TOKEN","SINGLE UNSUBSCRIBE OTP"],
        ["OWNER DETAILS"],
    ]
    return ReplyKeyboardMarkup(keyboard,resize_keyboard=True,is_persistent=True)

def get_youtube_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton(text="🟢 Subscribe YouTube Channel - Zevric X Play", url=YOUTUBE_LINK)]])

def convert_seconds(s):
    try: s=int(s)
    except: return str(s)
    d,h=divmod(s,86400); h,m=divmod(h,3600); m,s=divmod(m,60)
    return f"{d} Day {h} Hour {m} Min {s} Sec"

def get_player_info_sync(at):
    try:
        r=requests.get(f"https://api-otrss.garena.com/support/callback/?access_token={at}",headers={"User-Agent":"Mozilla/5.0"},timeout=15,allow_redirects=True)
        q=urllib.parse.parse_qs(urllib.parse.urlparse(r.url).query)
        return q.get("account_id",["Unknown"])[0], urllib.parse.unquote(q.get("nickname",["Unknown"])[0]), q.get("region",["Unknown"])[0]
    except: return "Unknown","Unknown","Unknown"

def fetch_bind_info_sync(at):
    try:
        url="https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        r=requests.get(url,params={'app_id':"100067",'access_token':at},headers={'User-Agent':"GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",'Connection':"Keep-Alive",'Accept-Encoding':"gzip"},timeout=15)
        if r.status_code==200: return {"ok":True,"data":r.json()}
        return {"ok":False,"error":f"HTTP {r.status_code}"}
    except Exception as e: return {"ok":False,"error":str(e)}

def send_otp_sync(email, at):
    try:
        url="https://100067.connect.garena.com/game/account_security/bind:send_otp"
        headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded","Accept":"application/json"}
        data={"email":email,"locale":"en_PK","region":"PK","app_id":"100067","access_token":at}
        r=requests.post(url,headers=headers,data=data,timeout=15)
        return {"ok":True,"data":r.json()}
    except Exception as e: return {"ok":False,"error":str(e)}

def verify_otp_sync(email, at, otp):
    try:
        url="https://100067.connect.garena.com/game/account_security/bind:verify_otp"
        headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
        data={"email":email,"app_id":"100067","access_token":at,"otp":otp}
        r=requests.post(url,headers=headers,data=data,timeout=15)
        j=r.json()
        return {"ok": j.get("result")==0 or "verifier_token" in j, "data":j}
    except Exception as e: return {"ok":False,"error":str(e)}

def verify_identity_sync(email, at, otp):
    try:
        url="https://100067.connect.garena.com/game/account_security/bind:verify_identity"
        headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
        data={"email":email,"app_id":"100067","access_token":at,"otp":otp}
        r=requests.post(url,headers=headers,data=data,timeout=15)
        j=r.json()
        return {"ok":"identity_token" in j,"data":j}
    except Exception as e: return {"ok":False,"error":str(e)}

def create_bind_request_sync(email, at, vt):
    try:
        url="https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
        headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
        data={"email":email,"app_id":"100067","access_token":at,"verifier_token":vt}
        r=requests.post(url,headers=headers,data=data,timeout=15)
        return {"ok":r.json().get("result")==0,"data":r.json()}
    except Exception as e: return {"ok":False,"error":str(e)}

def create_unbind_request_sync(it, at):
    try:
        url="https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
        headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
        data={"app_id":"100067","access_token":at,"identity_token":it}
        r=requests.post(url,headers=headers,data=data,timeout=15)
        return {"ok":r.json().get("result")==0,"data":r.json()}
    except Exception as e: return {"ok":False,"error":str(e)}

def create_rebind_request_sync(it, new_email, vt, at):
    try:
        url="https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
        headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
        data={"identity_token":it,"email":new_email,"app_id":"100067","verifier_token":vt,"access_token":at}
        r=requests.post(url,headers=headers,data=data,timeout=15)
        return {"ok":r.json().get("result")==0,"data":r.json()}
    except Exception as e: return {"ok":False,"error":str(e)}

def cancel_request_sync(at):
    try:
        url="https://100067.connect.garena.com/game/account_security/bind:cancel_request"
        headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
        data={"app_id":"100067","access_token":at}
        r=requests.post(url,headers=headers,data=data,timeout=15)
        return {"ok":r.json().get("result")==0,"data":r.json()}
    except Exception as e: return {"ok":False,"error":str(e)}

def eat_to_at_sync(eat_input):
    try:
        eat_token=None
        if "http" in eat_input or "eat=" in eat_input:
            parsed=urllib.parse.urlparse(eat_input); qs=urllib.parse.parse_qs(parsed.query)
            if 'eat' in qs: eat_token=qs['eat'][0]
            elif 'eat=' in eat_input: eat_token=eat_input.split('eat=')[1].split('&')[0]
        else: eat_token=eat_input.strip()
        if not eat_token: return {"ok":False,"error":"EAT not found"}
        r=requests.get(f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}",headers={"User-Agent":"Mozilla/5.0"},allow_redirects=True,timeout=15)
        q=urllib.parse.parse_qs(urllib.parse.urlparse(r.url).query)
        if 'access_token' not in q: return {"ok":False,"error":"EAT expired"}
        return {"ok":True,"access_token":q['access_token'][0],"account_id":q.get('account_id',['Unknown'])[0],"nickname":urllib.parse.unquote(q.get('nickname',['Unknown'])[0]),"region":q.get('region',['Unknown'])[0]}
    except Exception as e: return {"ok":False,"error":str(e)[:200]}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    not_joined=await check_user_joined_all(context, update.effective_user.id)
    if not_joined:
        await update.message.reply_text(get_force_join_text(not_joined),reply_markup=get_force_join_keyboard())
        return STATE_INPUT
    await update.message.reply_text(f"Welcome {update.effective_user.first_name or 'User'}!",reply_markup=get_youtube_keyboard())
    await update.message.reply_text("Main Menu:",reply_markup=get_reply_keyboard())
    return STATE_INPUT

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Main Menu:",reply_markup=get_reply_keyboard())
    return STATE_INPUT

async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Cancelled. Main Menu:",reply_markup=get_reply_keyboard())
    return STATE_INPUT

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query=update.callback_query; await query.answer()
        if query.data=="check_join":
            not_joined=await check_user_joined_all(context, query.from_user.id)
            if not_joined: await query.message.edit_text(get_force_join_text(not_joined),reply_markup=get_force_join_keyboard())
            else:
                await query.message.edit_text(f"Welcome {query.from_user.first_name or 'User'}! Verified!",reply_markup=get_youtube_keyboard())
                await context.bot.send_message(chat_id=query.message.chat_id,text="Main Menu:",reply_markup=get_reply_keyboard())
        return STATE_INPUT
    except: return STATE_INPUT

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        not_joined=await check_user_joined_all(context, update.effective_user.id)
        if not_joined:
            await update.message.reply_text(get_force_join_text(not_joined),reply_markup=get_force_join_keyboard())
            return STATE_INPUT
        text=update.message.text.strip()
        tl=text.lower()
        flow=context.user_data.get("flow")
        step=context.user_data.get("step")

        if tl=="check bind info":
            context.user_data.clear(); context.user_data["flow"]="bind_info"; context.user_data["step"]="token"
            await update.message.reply_text("Please Enter Your Access Token:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if tl=="bind email":
            context.user_data.clear(); context.user_data["flow"]="bind"; context.user_data["step"]="token"
            await update.message.reply_text("Please Enter Your Access Token:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if tl=="unbind email":
            context.user_data.clear(); context.user_data["flow"]="unbind"; context.user_data["step"]="token"
            await update.message.reply_text("Please Enter Your Access Token:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if tl=="change bind email":
            context.user_data.clear(); context.user_data["flow"]="change"; context.user_data["step"]="token"
            await update.message.reply_text("Please Enter Your Access Token:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if tl=="cancel bind request":
            context.user_data.clear(); context.user_data["flow"]="cancel"; context.user_data["step"]="token"
            await update.message.reply_text("Please Enter Your Access Token:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if tl=="eat to access token":
            context.user_data.clear(); context.user_data["flow"]="eat"; context.user_data["step"]="token"
            await update.message.reply_text("Please Enter Your EAT Token Or Full EAT URL:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if tl=="revoke access token":
            context.user_data.clear(); context.user_data["flow"]="revoke"; context.user_data["step"]="token"
            await update.message.reply_text("Please Enter Your Access Token:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if tl=="single unsubscribe otp":
            context.user_data.clear(); context.user_data["flow"]="sso"; context.user_data["step"]="email"
            await update.message.reply_text("Please Enter Your Email Address:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if tl=="owner details":
            await update.message.reply_text("Owner Details\n\nDeveloper Name: Zevric X Play\nTelegram: @just_zevric\nChannel: https://t.me/just_zevric\nYouTube: https://youtube.com/@zevricxplay",reply_markup=get_youtube_keyboard())
            await update.message.reply_text("Main Menu:",reply_markup=get_reply_keyboard())
            return STATE_INPUT

        if flow=="bind_info":
            if step=="token":
                uid,nick,region=get_player_info_sync(text)
                bind=fetch_bind_info_sync(text)
                if not bind["ok"]:
                    await update.message.reply_text("Failed to fetch bind info",reply_markup=get_youtube_keyboard())
                else:
                    d=bind["data"]
                    msg=f"Player: {nick} ({uid})\nRegion: {region}\nCurrent Email: {d.get('email','None') or 'None'}\nPending: {d.get('email_to_be','None') or 'None'}\nCountdown: {convert_seconds(d.get('request_exec_countdown',0))}"
                    await update.message.reply_text(msg,reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow=="bind":
            if step=="token":
                context.user_data["token"]=text
                await update.message.reply_text("Please Enter New Email To Bind:",reply_markup=get_youtube_keyboard())
                context.user_data["step"]="email"
                return STATE_INPUT
            if step=="email":
                context.user_data["email"]=text
                send_otp_sync(text,context.user_data["token"])
                await update.message.reply_text(f"OTP Sent To {text}, Please Enter OTP:",reply_markup=get_youtube_keyboard())
                context.user_data["step"]="otp"
                return STATE_INPUT
            if step=="otp":
                res=verify_otp_sync(context.user_data["email"],context.user_data["token"],text)
                if res["ok"]:
                    vt=res["data"].get("verifier_token")
                    if vt:
                        bind_res=create_bind_request_sync(context.user_data["email"],context.user_data["token"],vt)
                        if bind_res["ok"]:
                            await update.message.reply_text(f"Bind Request Created for {context.user_data['email']}!",reply_markup=get_youtube_keyboard())
                        else:
                            await update.message.reply_text(f"Bind Failed: {bind_res['data']}",reply_markup=get_youtube_keyboard())
                    else:
                        await update.message.reply_text("Invalid OTP",reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text("OTP Verification Failed",reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow=="unbind":
            if step=="token":
                context.user_data["token"]=text
                bind=fetch_bind_info_sync(text)
                email=bind["data"].get("email","") if bind["ok"] else ""
                if not email:
                    await update.message.reply_text("No Bound Email Found.",reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:",reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                context.user_data["email"]=email
                send_otp_sync(email,text)
                await update.message.reply_text(f"OTP Sent To {email}, Please Enter OTP:",reply_markup=get_youtube_keyboard())
                context.user_data["step"]="otp"
                return STATE_INPUT
            if step=="otp":
                res=verify_identity_sync(context.user_data["email"],context.user_data["token"],text)
                if res["ok"]:
                    it=res["data"].get("identity_token")
                    if it:
                        unbind_res=create_unbind_request_sync(it,context.user_data["token"])
                        if unbind_res["ok"]:
                            await update.message.reply_text("Unbind Request Created!",reply_markup=get_youtube_keyboard())
                        else:
                            await update.message.reply_text(f"Unbind Failed: {unbind_res['data']}",reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text("OTP Verification Failed",reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow=="change":
            if step=="token":
                context.user_data["token"]=text
                bind=fetch_bind_info_sync(text)
                old=bind["data"].get("email","") if bind["ok"] else ""
                if not old:
                    await update.message.reply_text("No Bound Email Found.",reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:",reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                context.user_data["old_email"]=old
                send_otp_sync(old,text)
                await update.message.reply_text(f"OTP Sent To {old} (Old Email), Please Enter OTP:",reply_markup=get_youtube_keyboard())
                context.user_data["step"]="old_otp"
                return STATE_INPUT
            if step=="old_otp":
                res=verify_identity_sync(context.user_data["old_email"],context.user_data["token"],text)
                if res["ok"]:
                    context.user_data["identity_token"]=res["data"].get("identity_token")
                    await update.message.reply_text("Old Email Verified. Please Enter New Email:",reply_markup=get_youtube_keyboard())
                    context.user_data["step"]="new_email"
                else:
                    await update.message.reply_text("Old OTP Verification Failed",reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:",reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                return STATE_INPUT
            if step=="new_email":
                context.user_data["new_email"]=text
                send_otp_sync(text,context.user_data["token"])
                await update.message.reply_text(f"OTP Sent To {text} (New Email), Please Enter OTP:",reply_markup=get_youtube_keyboard())
                context.user_data["step"]="new_otp"
                return STATE_INPUT
            if step=="new_otp":
                res=verify_otp_sync(context.user_data["new_email"],context.user_data["token"],text)
                if res["ok"]:
                    vt=res["data"].get("verifier_token")
                    if vt and context.user_data.get("identity_token"):
                        rebind=create_rebind_request_sync(context.user_data["identity_token"],context.user_data["new_email"],vt,context.user_data["token"])
                        if rebind["ok"]:
                            await update.message.reply_text(f"Change Request Created: {context.user_data['old_email']} -> {context.user_data['new_email']}!",reply_markup=get_youtube_keyboard())
                        else:
                            await update.message.reply_text(f"Change Failed: {rebind['data']}",reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text("New OTP Verification Failed",reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow=="cancel":
            if step=="token":
                res=cancel_request_sync(text)
                if res["ok"]:
                    await update.message.reply_text("Bind Request Cancelled!",reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Cancel Failed: {res['data']}",reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow=="eat":
            if step=="token":
                res=eat_to_at_sync(text)
                if res["ok"]:
                    msg=f"EAT Convert Success\nNick: {res['nickname']}\nID: {res['account_id']}\nRegion: {res['region']}\n\nAccess Token:\n{res['access_token']}"
                    await update.message.reply_text(msg,reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Error: {res.get('error')}",reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow=="sso":
            if step=="email":
                email=text.strip()
                if "@" not in email:
                    await update.message.reply_text("Invalid Email!",reply_markup=get_youtube_keyboard())
                    return STATE_INPUT
                try:
                    session=requests.Session()
                    headers_base={"User-Agent":"Mozilla/5.0","Referer":"https://sso.garena.com/universal/register?locale=en-SG","Origin":"https://sso.garena.com"}
                    random_user="ZEVRICX"+ "".join(random.choices(string.ascii_uppercase+string.digits,k=4))
                    random_pass=".Nm5TGMfA7JyUyh"+ "".join(random.choices(string.ascii_letters+string.digits,k=2))
                    try: session.get("https://sso.garena.com/universal/register?locale=en-SG",headers=headers_base,timeout=10)
                    except: pass
                    api_url="https://sso.garena.com/api/account/send_verification_code"
                    payload={"email":email,"username":random_user,"password":random_pass,"confirm_password":random_pass,"locale":"en-SG","region":"SG"}
                    resp=session.post(api_url,headers={**headers_base,"Content-Type":"application/json"},json=payload,timeout=12)
                except: pass
                await update.message.reply_text(f"Single Unsubscribe OTP Sent Successfully!\nEmail: {email}",reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow=="revoke":
            if step=="token":
                try:
                    uid,nick,region=get_player_info_sync(text)
                    refresh="1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
                    logout_url=f"https://100067.connect.garena.com/oauth/logout?access_token={text}&refresh_token={refresh}"
                    lr=requests.get(logout_url,headers={"User-Agent":"Mozilla/5.0"},timeout=10)
                    if lr.status_code==200 and "error" not in lr.text:
                        await update.message.reply_text(f"Revoked Success\nNick: {nick}\nID: {uid}",reply_markup=get_youtube_keyboard())
                    else:
                        await update.message.reply_text("Revoke Failed",reply_markup=get_youtube_keyboard())
                except Exception as e:
                    await update.message.reply_text(f"Error: {str(e)[:100]}",reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        await update.message.reply_text("Main Menu:",reply_markup=get_reply_keyboard())
        return STATE_INPUT
    except Exception as e:
        print(f"Error: {e}"); import traceback; traceback.print_exc()
        try: await update.message.reply_text("Error Occurred. Use /start",reply_markup=get_reply_keyboard())
        except: pass
        context.user_data.clear()
        return STATE_INPUT

from flask import Flask
flask_app=Flask(__name__)
@flask_app.route('/')
def home(): return "Bot Running - 8 Options + SSO Fake Success - Owner YT Tak"
@flask_app.route('/health')
def health(): return "OK"
app=flask_app

def run_bot():
    if BOT_TOKEN=="YOUR_BOT_TOKEN_HERE": print("BOT_TOKEN not set"); return
    import asyncio
    try: loop=asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    except: pass
    try:
        application=Application.builder().token(BOT_TOKEN).build()
        conv_handler=ConversationHandler(
            entry_points=[CommandHandler("start",start),CommandHandler("menu",menu_cmd),MessageHandler(filters.TEXT & ~filters.COMMAND,handle_text)],
            states={STATE_INPUT:[CallbackQueryHandler(handle_callback),MessageHandler(filters.TEXT & ~filters.COMMAND,handle_text)]},
            fallbacks=[CommandHandler("cancel",cancel_cmd),CommandHandler("start",start)],allow_reentry=True,per_message=False
        )
        application.add_handler(conv_handler)
        application.add_handler(CommandHandler("cancel",cancel_cmd))
        application.run_polling(close_loop=False,drop_pending_updates=True,stop_signals=None)
    except Exception as e:
        print(f"Bot run failed: {e}"); import traceback; traceback.print_exc(); raise

def _auto_start_bot():
    if BOT_TOKEN=="YOUR_BOT_TOKEN_HERE": return
    def bot_thread_func():
        while True:
            try: run_bot()
            except Exception as e:
                print(f"Bot crashed: {e}, restart in 5 sec"); time.sleep(5)
    try: t=threading.Thread(target=bot_thread_func,daemon=True); t.start()
    except: pass

if os.getenv("PORT") or os.getenv("RENDER"): _auto_start_bot()

if __name__=="__main__":
    bot_thread=threading.Thread(target=run_bot,daemon=True)
    bot_thread.start()
    port=int(os.environ.get("PORT",10000))
    flask_app.run(host="0.0.0.0",port=port)
