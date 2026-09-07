#!/usr/bin/env python3
"""
WORLD DEEP RESEARCH - Each option API checked vs rao.py + OTP not coming fix + Region dynamic + Captcha handling
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
    res=""
    for ch in text:
        if 'A' <= ch <= 'Z':
            res+=chr(BASE_UPPER+ord(ch)-65)
        elif 'a' <= ch <= 'z':
            res+=chr(BASE_LOWER+ord(ch)-97)
        elif '0' <= ch <= '9':
            res+=chr(BASE_DIGIT+ord(ch)-48)
        else:
            res+=ch
    return res

def unfancy(text):
    res=""
    for ch in text:
        code=ord(ch)
        if BASE_UPPER <= code <= BASE_UPPER+25:
            res+=chr(65+code-BASE_UPPER)
        elif BASE_LOWER <= code <= BASE_LOWER+25:
            res+=chr(97+code-BASE_LOWER)
        elif BASE_DIGIT <= code <= BASE_DIGIT+9:
            res+=chr(48+code-BASE_DIGIT)
        else:
            res+=ch
    return res

class FancyButtonFilter(MessageFilter):
    def __init__(self, k):
        super().__init__()
        self.keyword=k.lower()
    def filter(self, m):
        if not m.text: return False
        import re
        norm=unfancy(m.text).lower()
        cleaned=re.sub(r'[^a-z ]', ' ', norm)
        cleaned=' '.join(cleaned.split())
        # Exact match to avoid 'bind email' matching 'change bind email'
        return cleaned == self.keyword

def start_health_server():
    port=int(os.getenv("PORT","10000"))
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200); self.send_header("Content-type","text/plain"); self.end_headers(); self.wfile.write(b"Zevric Bot Alive")
        def log_message(self,*a): return
    try:
        HTTPServer(("0.0.0.0",port),H).serve_forever
        threading.Thread(target=HTTPServer(("0.0.0.0",port),H).serve_forever,daemon=True).start()
    except: pass
    try:
        server=HTTPServer(("0.0.0.0",port),H)
        threading.Thread(target=server.serve_forever,daemon=True).start()
    except: pass

async def http_get(url, params=None, headers=None, timeout=20):
    return await asyncio.to_thread(lambda: requests.get(url, params=params, headers=headers or {}, timeout=timeout, allow_redirects=True))
async def http_post(url, data=None, headers=None, timeout=20):
    return await asyncio.to_thread(lambda: requests.post(url, data=data, headers=headers or {}, timeout=timeout))

def sub_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🟢 "+fancy("Subscribe YouTube Channel"), url=YT_LINK)]])

def main_menu():
    kb=[
        [KeyboardButton("🟢 "+fancy("Check Bind Info")), KeyboardButton("🟢 "+fancy("Eat To Access Token"))],
        [KeyboardButton("🟢 "+fancy("Bind Email")), KeyboardButton("🟢 "+fancy("Unbind Email"))],
        [KeyboardButton("🟢 "+fancy("Change Bind Email")), KeyboardButton("🟢 "+fancy("Cancel Bind"))],
        [KeyboardButton("🔴 "+fancy("Revoke Access Token")), KeyboardButton("🔵 "+fancy("Owner"))],
        [KeyboardButton("🔵 "+fancy("How To Use"))],
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

(CBI_TOKEN, EAT_INPUT, BIND_TOKEN, BIND_EMAIL, BIND_OTP, BIND_SECURITY,
 UNBIND_TOKEN, UNBIND_OTP,
 CHANGE_TOKEN, CHANGE_OTP_OLD, CHANGE_NEW_EMAIL, CHANGE_OTP_NEW,
 CANCEL_TOKEN, REVOKE_TOKEN)=range(14)

# Exact headers from rao.py
def headers_get_bind():
    return {'User-Agent':"GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",'Connection':"Keep-Alive",'Accept-Encoding':"gzip"}
def headers_post():
    return {"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded","Accept":"application/json"}

async def get_player_info(token):
    try:
        url=f"https://api-otrss.garena.com/support/callback/?access_token={token}"
        r=await http_get(url, headers={"User-Agent":"Mozilla/5.0"})
        parsed=urllib.parse.urlparse(r.url)
        qs=urllib.parse.parse_qs(parsed.query)
        acc=qs.get("account_id",["Unknown"])[0]
        nick=urllib.parse.unquote(qs.get("nickname",["Unknown"])[0])
        region=qs.get("region",["Unknown"])[0]
        return acc,nick,region
    except:
        return "Unknown","Unknown","IND"

async def get_bind_info_api(token):
    try:
        url="https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        r=await http_get(url, params={"app_id":"100067","access_token":token}, headers=headers_get_bind())
        return r.json()
    except:
        return {}

# Deep researched send_otp with region fallback and captcha detection
async def send_otp_smart(email, token, player_region):
    # Try order: player's region first (IND for your screenshot), then PK (rao.py default)
    regions_to_try=[player_region, "PK", "IND"]
    locales={"PK":"en_PK","IND":"en_US","US":"en_US"}
    tried=set()
    for region in regions_to_try:
        if region in tried or not region or region=="Unknown":
            continue
        tried.add(region)
        locale=locales.get(region,"en_PK")
        url="https://100067.connect.garena.com/game/account_security/bind:send_otp"
        data={"email":email,"locale":locale,"region":region,"app_id":"100067","access_token":token}
        try:
            r=await http_post(url, data=data, headers=headers_post())
            j=r.json()
            # Captcha detection - rao.py ignores but we need to handle
            if "url" in j and "captcha" in str(j.get("url","")).lower():
                return {"result":"captcha","url":j.get("url"),"region":region,"raw":j}
            if j.get("result")==0:
                return {"result":0,"region":region,"locale":locale,"raw":j}
            else:
                # If error is not captcha, try next region
                last=j
        except Exception as e:
            last={"error":str(e)}
    return last

OTP_HELP=fancy("OTP Solution:")+"\n- Garena mail Primary me aata hai (teri screenshot Primary me hai)\n- Check Primary & Spam\n- Wait 2 min\n- Countdown 0 hona chahiye\n- Bar-bar OTP mat maango, 10 min wait + Cancel Bind"

async def start(update, context):
    user=update.effective_user
    name=user.first_name or user.username or "User"
    welcome=fancy(f"Welcome, {name}!")+"\n\n"+fancy("Welcome to Garena Email Tool")+f"\n\nBot: {BOT_USERNAME}\nOwner: zevric x play\nTelegram: @just_zevric"
    await update.message.reply_text(welcome, reply_markup=sub_keyboard())
    await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())

async def help_cmd(update, context):
    txt=f"""{fancy('How To Use')} {BOT_USERNAME}

{fancy('OTP Kyu Nahi Aata - Deep Research:')}
{fancy('rao.py me OTP aata hai kyunki wo local PC IP se request bhejta hai. Bot Render US server se bhejta hai, Garena IP check karta hai.')}
{fancy('Fix: Bot ab player ka region (IND) use karega PK ki jagah, jisse Garena ko lagega sahi region se request hai.')}
{fancy('1. Check Primary inbox - teri screenshot me Primary me aata hai')}
{fancy('2. Agar countdown >0 ho to Cancel Bind karke 10 min wait')}
{fancy('3. Ek hi baar OTP maango, spam karne pe Garena captcha dega')}
{fancy('4. Agar captcha aaye to bot bolega Garena busy, 10 min baad try karo')}
{fancy('5. Gmail use karo, temp mail block hai')}

{fancy('Bind:')} Token -> Check no email -> Email -> OTP (region smart) -> Verify (code+otp+type1) -> 6-digit -> Bind
{fancy('Change:')} Token -> OLD email auto -> OTP OLD (region smart) -> verify_identity -> NEW email -> OTP NEW -> verify_otp only otp -> rebind
{fancy('Unbind:')} Token -> OTP current -> verify_identity -> unbind
{fancy('Cancel:')} Token -> cancel_request
{fancy('Check:')} Token -> player info + bind info
{fancy('Eat:')} EAT URL -> access_token parse
{fancy('Revoke:')} Token -> logout
"""
    await update.message.reply_text(txt, reply_markup=sub_keyboard())
    await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())

async def owner_cmd(update, context):
    await update.message.reply_text(f"👑 zevric x play\n✈️ @just_zevric\n▶️ zevricxplay\n🔗 {YT_LINK}\nBot: {BOT_USERNAME}", reply_markup=sub_keyboard())

async def check_start(update, context):
    await update.message.reply_text(fancy("Please Enter Your Access Token:"), reply_markup=sub_keyboard())
    return CBI_TOKEN
async def cbi_token_recv(update, context):
    token=update.message.text.strip()
    await update.message.reply_text(fancy("Fetching info..."), reply_markup=sub_keyboard())
    try:
        acc,nick,region=await get_player_info(token)
        d=await get_bind_info_api(token)
        cur=d.get("email") or "None"
        pend=d.get("email_to_be") or "None"
        cd=int(d.get("request_exec_countdown") or 0)
        days,rem=divmod(cd,86400); hrs,rem=divmod(rem,3600); mins,secs=divmod(rem,60)
        msg=f"{fancy('----- Bind Info -----')}\n{fancy('Nickname')} : {nick}\n{fancy('Account ID')} : {acc}\n{fancy('Region')} : {region}\n{fancy('Current Email')}: {cur}\n{fancy('Pending Email')}: {pend}\n{fancy('Countdown')} : {days}D {hrs}H {mins}M {secs}S"
        if cd>0:
            msg+=f"\n\n{fancy('OTP nahi ayega, countdown 0 hone tak wait karo ya Cancel Bind karo')}"
        await update.message.reply_text(msg, reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
    await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
    return ConversationHandler.END

async def eat_start(update, context):
    await update.message.reply_text(fancy("Please Enter Your EAT URL or EAT Token:"), reply_markup=sub_keyboard())
    return EAT_INPUT
async def eat_recv(update, context):
    txt=update.message.text.strip()
    try:
        m=re.search(r"eat=([^&\s]+)",txt)
        eat_tok=m.group(1) if m else (txt if len(txt)>50 else None)
        if not eat_tok:
            await update.message.reply_text(fancy("EAT not found."), reply_markup=sub_keyboard())
            await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
            return ConversationHandler.END
        api_url=f"https://api-otrss.garena.com/support/callback/?access_token={eat_tok}"
        res=await http_get(api_url, headers={"User-Agent":"Mozilla/5.0"})
        parsed=urllib.parse.urlparse(res.url)
        params=urllib.parse.parse_qs(parsed.query)
        access_token=params.get("access_token",[None])[0]
        acc=params.get("account_id",["Unknown"])[0]
        nick=urllib.parse.unquote(params.get("nickname",["Unknown"])[0])
        reg=params.get("region",["Unknown"])[0]
        if access_token:
            await update.message.reply_text(f"✅ {fancy('Converted!')}\n{fancy('Nickname')}: {nick}\nID: {acc}\nRegion: {reg}\n\nToken:\n{access_token}", reply_markup=sub_keyboard())
        else:
            await update.message.reply_text(fancy("Failed. Token expired."), reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
    await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
    return ConversationHandler.END

async def bind_start(update, context):
    await update.message.reply_text(fancy("Please Enter Your Access Token:"), reply_markup=sub_keyboard())
    return BIND_TOKEN
async def bind_tok(update, context):
    token=update.message.text.strip()
    context.user_data["token"]=token
    acc,nick,player_region=await get_player_info(token)
    context.user_data["player_region"]=player_region
    d=await get_bind_info_api(token)
    cur=d.get("email") or ""
    cd=int(d.get("request_exec_countdown") or 0)
    if cur:
        await update.message.reply_text(fancy(f"Already has email: {cur}. Use Change Bind Email."), reply_markup=sub_keyboard())
        await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
        return ConversationHandler.END
    if cd>0:
        await update.message.reply_text(fancy(f"Countdown {cd}s running. Cancel Bind first."), reply_markup=sub_keyboard())
        await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
        return ConversationHandler.END
    await update.message.reply_text(fancy("Please Enter Your Email To Bind:"), reply_markup=sub_keyboard())
    return BIND_EMAIL
async def bind_email_recv(update, context):
    email=update.message.text.strip()
    context.user_data["email"]=email
    token=context.user_data["token"]
    player_region=context.user_data.get("player_region","IND")
    res=await send_otp_smart(email, token, player_region)
    if res.get("result")=="captcha":
        await update.message.reply_text(fancy(f"Garena busy/captcha (region {res.get('region')}). 10 min wait + Cancel Bind karke try karo.")+f"\nURL: {res.get('url')}", reply_markup=sub_keyboard())
        await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
        return ConversationHandler.END
    if res.get("result")!=0:
        await update.message.reply_text(f"❌ {fancy('Send OTP failed')}: {res.get('raw',res)}", reply_markup=sub_keyboard())
        await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
        return ConversationHandler.END
    await update.message.reply_text(fancy(f"OTP Sent To {email} via region {res.get('region')} {res.get('locale')}.")+"\n"+fancy("Check Primary inbox, wait 2 min.")+"\n\n"+fancy("Please Enter OTP:")+"\n"+OTP_HELP, reply_markup=sub_keyboard())
    return BIND_OTP
async def bind_otp_recv(update, context):
    otp=update.message.text.strip()
    token=context.user_data["token"]; email=context.user_data["email"]
    url="https://100067.connect.garena.com/game/account_security/bind:verify_otp"
    data={"app_id":"100067","access_token":token,"email":email,"code":otp,"otp":otp,"type":"1"}
    try:
        r=await http_post(url, data=data, headers=headers_post())
        j=r.json()
        if j.get("result")!=0:
            await update.message.reply_text(f"❌ {fancy('Verify failed')}: {j}", reply_markup=sub_keyboard())
            await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
            return ConversationHandler.END
        vt=j.get("verifier_token")
        if not vt:
            await update.message.reply_text(f"❌ {fancy('No verifier token')}: {j}", reply_markup=sub_keyboard())
            await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
            return ConversationHandler.END
        context.user_data["vt"]=vt
        await update.message.reply_text(fancy("Please Enter Your 6-Digits Security Code:"), reply_markup=sub_keyboard())
        return BIND_SECURITY
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
        await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
        return ConversationHandler.END
async def bind_sec_recv(update, context):
    code=update.message.text.strip()
    token=context.user_data["token"]; email=context.user_data["email"]; vt=context.user_data["vt"]
    url="https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
    data={"email":email,"app_id":"100067","access_token":token,"verifier_token":vt,"secondary_password":code}
    try:
        r=await http_post(url, data=data, headers=headers_post())
        await update.message.reply_text(f"✅ {fancy('Bind Result')}: {r.json()}", reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
    await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
    context.user_data.clear()
    return ConversationHandler.END

async def unbind_start(update, context):
    await update.message.reply_text(fancy("Please Enter Your Access Token:"), reply_markup=sub_keyboard())
    return UNBIND_TOKEN
async def unbind_tok(update, context):
    token=update.message.text.strip()
    context.user_data["token"]=token
    acc,nick,player_region=await get_player_info(token)
    context.user_data["player_region"]=player_region
    d=await get_bind_info_api(token)
    email=d.get("email","")
    if not email:
        await update.message.reply_text(fancy("No bound email!"), reply_markup=sub_keyboard())
        await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
        return ConversationHandler.END
    context.user_data["email"]=email
    res=await send_otp_smart(email, token, player_region)
    if res.get("result")=="captcha":
        await update.message.reply_text(fancy(f"Garena busy captcha. Wait 10 min."), reply_markup=sub_keyboard())
        await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
        return ConversationHandler.END
    if res.get("result")!=0:
        await update.message.reply_text(f"❌ {fancy('Send OTP failed')}: {res}", reply_markup=sub_keyboard())
        await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
        return ConversationHandler.END
    await update.message.reply_text(fancy(f"OTP Sent To {email} via {res.get('region')}. Check Primary.")+"\n\n"+fancy("Please Enter OTP:")+"\n"+OTP_HELP, reply_markup=sub_keyboard())
    return UNBIND_OTP
async def unbind_otp_recv(update, context):
    otp=update.message.text.strip()
    token=context.user_data["token"]; email=context.user_data["email"]
    url="https://100067.connect.garena.com/game/account_security/bind:verify_identity"
    data={"email":email,"app_id":"100067","access_token":token,"otp":otp}
    try:
        r=await http_post(url, data=data, headers=headers_post())
        j=r.json()
        if j.get("result")!=0:
            await update.message.reply_text(f"❌ {fancy('Verify failed')}: {j}", reply_markup=sub_keyboard())
            await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
            return ConversationHandler.END
        it=j.get("identity_token")
        if not it:
            await update.message.reply_text(f"❌ {fancy('No identity token')}: {j}", reply_markup=sub_keyboard())
            await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
            return ConversationHandler.END
        url2="https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
        r2=await http_post(url2, data={"app_id":"100067","access_token":token,"identity_token":it}, headers=headers_post())
        await update.message.reply_text(f"✅ {fancy('Unbind Result')}: {r2.json()}", reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
    await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
    context.user_data.clear()
    return ConversationHandler.END

async def change_start(update, context):
    await update.message.reply_text(fancy("Please Enter Your Access Token:"), reply_markup=sub_keyboard())
    return CHANGE_TOKEN
async def change_tok(update, context):
    token=update.message.text.strip()
    context.user_data["token"]=token
    acc,nick,player_region=await get_player_info(token)
    context.user_data["player_region"]=player_region
    d=await get_bind_info_api(token)
    old_email=d.get("email","")
    if not old_email:
        await update.message.reply_text(fancy("No bound email! Use Bind Email first."), reply_markup=sub_keyboard())
        await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
        return ConversationHandler.END
    context.user_data["old"]=old_email
    res=await send_otp_smart(old_email, token, player_region)
    if res.get("result")=="captcha":
        await update.message.reply_text(fancy("Garena busy captcha on OLD email. Wait 10 min + Cancel Bind."), reply_markup=sub_keyboard())
        await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
        return ConversationHandler.END
    if res.get("result")!=0:
        await update.message.reply_text(f"❌ {fancy('Send OTP OLD failed')}: {res}", reply_markup=sub_keyboard())
        await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
        return ConversationHandler.END
    await update.message.reply_text(fancy(f"OTP Sent To OLD Email {old_email} via {res.get('region')}. Check Primary.")+"\n\n"+fancy("Please Enter OTP From Old Email:")+"\n"+OTP_HELP, reply_markup=sub_keyboard())
    return CHANGE_OTP_OLD
async def change_old_otp(update, context):
    otp=update.message.text.strip()
    token=context.user_data["token"]; old=context.user_data["old"]
    url="https://100067.connect.garena.com/game/account_security/bind:verify_identity"
    data={"email":old,"app_id":"100067","access_token":token,"otp":otp}
    try:
        r=await http_post(url, data=data, headers=headers_post())
        j=r.json()
        if j.get("result")!=0:
            await update.message.reply_text(f"❌ {fancy('Old OTP failed')}: {j}", reply_markup=sub_keyboard())
            await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
            return ConversationHandler.END
        it=j.get("identity_token")
        if not it:
            await update.message.reply_text(f"❌ {fancy('No identity token')}: {j}", reply_markup=sub_keyboard())
            await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
            return ConversationHandler.END
        context.user_data["it"]=it
        await update.message.reply_text(fancy("Please Enter New Email:"), reply_markup=sub_keyboard())
        return CHANGE_NEW_EMAIL
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
        await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
        return ConversationHandler.END
async def change_new_email(update, context):
    new=update.message.text.strip()
    context.user_data["new"]=new
    token=context.user_data["token"]
    player_region=context.user_data.get("player_region","IND")
    res=await send_otp_smart(new, token, player_region)
    if res.get("result")=="captcha":
        await update.message.reply_text(fancy("Garena busy captcha on NEW email. Wait 10 min."), reply_markup=sub_keyboard())
        await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
        return ConversationHandler.END
    if res.get("result")!=0:
        await update.message.reply_text(f"❌ {fancy('Send OTP NEW failed')}: {res}", reply_markup=sub_keyboard())
        await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
        return ConversationHandler.END
    await update.message.reply_text(fancy(f"OTP Sent To NEW Email {new} via {res.get('region')}. Check Primary.")+"\n\n"+fancy("Please Enter OTP From New Email:")+"\n"+OTP_HELP, reply_markup=sub_keyboard())
    return CHANGE_OTP_NEW
async def change_new_otp(update, context):
    otp=update.message.text.strip()
    token=context.user_data["token"]; new=context.user_data["new"]
    url="https://100067.connect.garena.com/game/account_security/bind:verify_otp"
    data={"email":new,"app_id":"100067","access_token":token,"otp":otp}
    try:
        r=await http_post(url, data=data, headers=headers_post())
        j=r.json()
        if j.get("result")!=0:
            await update.message.reply_text(f"❌ {fancy('New OTP failed')}: {j}", reply_markup=sub_keyboard())
            await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
            return ConversationHandler.END
        vt=j.get("verifier_token")
        if not vt:
            await update.message.reply_text(f"❌ {fancy('No verifier token')}: {j}", reply_markup=sub_keyboard())
            await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
            return ConversationHandler.END
        url_rebind="https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
        payload={"identity_token":context.user_data["it"],"email":new,"app_id":"100067","verifier_token":vt,"access_token":token}
        r2=await http_post(url_rebind, data=payload, headers=headers_post())
        await update.message.reply_text(f"✅ {fancy('Rebind Result')}: {r2.json()}", reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
    await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_start(update, context):
    await update.message.reply_text(fancy("Please Enter Your Access Token:"), reply_markup=sub_keyboard())
    return CANCEL_TOKEN
async def cancel_tok(update, context):
    token=update.message.text.strip()
    url="https://100067.connect.garena.com/game/account_security/bind:cancel_request"
    try:
        r=await http_post(url, data={"app_id":"100067","access_token":token}, headers=headers_post())
        await update.message.reply_text(f"✅ {fancy('Cancel Result')}: {r.json()}", reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
    await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
    return ConversationHandler.END

async def revoke_start(update, context):
    await update.message.reply_text(fancy("Please Enter Your Access Token:"), reply_markup=sub_keyboard())
    return REVOKE_TOKEN
async def revoke_tok(update, context):
    token=update.message.text.strip()
    url=f"https://100067.connect.garena.com/oauth/logout?access_token={token}&refresh_token=1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
    try:
        r=await http_get(url)
        await update.message.reply_text(f"✅ {fancy('Revoke Result')}: {r.text[:500]}", reply_markup=sub_keyboard())
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_markup=sub_keyboard())
    await update.message.reply_text(fancy("Main Menu:"), reply_markup=main_menu())
    return ConversationHandler.END

async def cancel_all(update, context):
    context.user_data.clear()
    await update.message.reply_text(fancy("Cancelled."), reply_markup=main_menu())
    return ConversationHandler.END

def main():
    start_health_server()
    app=ApplicationBuilder().token(BOT_TOKEN).build()
    conv_cbi=ConversationHandler(entry_points=[CommandHandler("check_bind_info", check_start), MessageHandler(FancyButtonFilter("check bind info"), check_start)], states={CBI_TOKEN:[MessageHandler(filters.TEXT & ~filters.COMMAND, cbi_token_recv)]}, fallbacks=[CommandHandler("cancel", cancel_all)], per_user=True, per_chat=True)
    conv_eat=ConversationHandler(entry_points=[CommandHandler("eat_to_access_token", eat_start), MessageHandler(FancyButtonFilter("eat to access token"), eat_start)], states={EAT_INPUT:[MessageHandler(filters.TEXT & ~filters.COMMAND, eat_recv)]}, fallbacks=[CommandHandler("cancel", cancel_all)], per_user=True, per_chat=True)
    conv_bind=ConversationHandler(entry_points=[CommandHandler("bind_email", bind_start), MessageHandler(FancyButtonFilter("bind email"), bind_start)], states={BIND_TOKEN:[MessageHandler(filters.TEXT & ~filters.COMMAND, bind_tok)], BIND_EMAIL:[MessageHandler(filters.TEXT & ~filters.COMMAND, bind_email_recv)], BIND_OTP:[MessageHandler(filters.TEXT & ~filters.COMMAND, bind_otp_recv)], BIND_SECURITY:[MessageHandler(filters.TEXT & ~filters.COMMAND, bind_sec_recv)]}, fallbacks=[CommandHandler("cancel", cancel_all)], per_user=True, per_chat=True)
    conv_unbind=ConversationHandler(entry_points=[CommandHandler("unbind_email", unbind_start), MessageHandler(FancyButtonFilter("unbind email"), unbind_start)], states={UNBIND_TOKEN:[MessageHandler(filters.TEXT & ~filters.COMMAND, unbind_tok)], UNBIND_OTP:[MessageHandler(filters.TEXT & ~filters.COMMAND, unbind_otp_recv)]}, fallbacks=[CommandHandler("cancel", cancel_all)], per_user=True, per_chat=True)
    conv_change=ConversationHandler(entry_points=[CommandHandler("change_bind_email", change_start), MessageHandler(FancyButtonFilter("change bind email"), change_start)], states={CHANGE_TOKEN:[MessageHandler(filters.TEXT & ~filters.COMMAND, change_tok)], CHANGE_OTP_OLD:[MessageHandler(filters.TEXT & ~filters.COMMAND, change_old_otp)], CHANGE_NEW_EMAIL:[MessageHandler(filters.TEXT & ~filters.COMMAND, change_new_email)], CHANGE_OTP_NEW:[MessageHandler(filters.TEXT & ~filters.COMMAND, change_new_otp)]}, fallbacks=[CommandHandler("cancel", cancel_all)], per_user=True, per_chat=True)
    conv_cancel=ConversationHandler(entry_points=[CommandHandler("cancel_bind", cancel_start), MessageHandler(FancyButtonFilter("cancel bind"), cancel_start)], states={CANCEL_TOKEN:[MessageHandler(filters.TEXT & ~filters.COMMAND, cancel_tok)]}, fallbacks=[CommandHandler("cancel", cancel_all)], per_user=True, per_chat=True)
    conv_revoke=ConversationHandler(entry_points=[CommandHandler("revoke_access_token", revoke_start), MessageHandler(FancyButtonFilter("revoke access token"), revoke_start)], states={REVOKE_TOKEN:[MessageHandler(filters.TEXT & ~filters.COMMAND, revoke_tok)]}, fallbacks=[CommandHandler("cancel", cancel_all)], per_user=True, per_chat=True)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("howtouse", help_cmd))
    app.add_handler(CommandHandler("owner", owner_cmd))
    app.add_handler(MessageHandler(FancyButtonFilter("owner"), owner_cmd))
    app.add_handler(MessageHandler(FancyButtonFilter("how to use"), help_cmd))
    app.add_handler(MessageHandler(FancyButtonFilter("help"), help_cmd))
    app.add_handler(conv_cbi); app.add_handler(conv_eat); app.add_handler(conv_bind); app.add_handler(conv_unbind); app.add_handler(conv_change); app.add_handler(conv_cancel); app.add_handler(conv_revoke)
    app.run_polling(allowed_updates=["message"])

if __name__=="__main__":
    main()
