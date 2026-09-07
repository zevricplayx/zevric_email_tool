
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import sys, json, time, urllib.parse, base64, requests, threading, random, string, re
from datetime import datetime
from flask import Flask
import urllib3
urllib3.disable_warnings()
try:
    import MajoRLogin_pb2 as mLpB
    import MajorLoginRes_pb2 as mLrPb
    PROTOBUF_AVAILABLE = True
except:
    PROTOBUF_AVAILABLE = False
    mLpB = None
    mLrPb = None
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
try:
    from telegram.constants import KeyboardButtonStyle
    HAS_STYLE = True
except:
    HAS_STYLE = False
    class KeyboardButtonStyle:
        SUCCESS = "success"
        DANGER = "danger"
        PRIMARY = "primary"

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
_BASE_URL = "https://rishu-official-bind.vercel.app/api"
_EXTRACT_URL = "https://rishu-jwt-gen.vercel.app/rishu"
_APP_ID = "100067"

def _api_request(endpoint, params):
    url = f"{_BASE_URL}/{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=25)
        try: return resp.json()
        except: return {"success": False, "message": f"Invalid HTTP {resp.status_code}", "raw": resp.text[:500]}
    except Exception as e:
        return {"success": False, "message": f"Network {str(e)}"}

def convert_seconds(s):
    try: s=int(s)
    except: return str(s)
    d,h=divmod(s,86400); h,m=divmod(h,3600); m,s=divmod(m,60)
    return f"{d} Day {h} Hour {m} Min {s} Sec"

def format_seconds(seconds):
    if seconds<=0: return "0s"
    d=seconds//86400; h=(seconds%86400)//3600; m=(seconds%3600)//60; s=seconds%60
    parts=[]
    if d>0: parts.append(f"{d}d")
    if h>0: parts.append(f"{h}h")
    if m>0: parts.append(f"{m}m")
    if s>0: parts.append(f"{s}s")
    return " ".join(parts) if parts else "0s"

def decode_jwt_payload(jwt_token):
    try:
        parts=jwt_token.split('.')
        if len(parts)<2: return {}
        payload=parts[1]; payload+='='*(-len(payload)%4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except: return {}

def get_player_info_sync(access_token):
    try:
        url=f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        r=requests.get(url,headers={"User-Agent":"Mozilla/5.0"},timeout=15,allow_redirects=True)
        parsed=urllib.parse.urlparse(r.url); qp=urllib.parse.parse_qs(parsed.query)
        return qp.get("account_id",["Unknown"])[0], urllib.parse.unquote(qp.get("nickname",["Unknown"])[0]), qp.get("region",["Unknown"])[0]
    except: return "Unknown","Unknown","Unknown"

def get_open_id_from_token(at):
    try:
        r=requests.get(f"https://100067.connect.garena.com/oauth/token/inspect?token={at}",headers={"User-Agent":"Mozilla/5.0"},timeout=8).json()
        if r.get("open_id"): return r.get("open_id")
    except: pass
    try:
        uid_res=requests.get("https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/",headers={"access-token":at,"user-agent":"Mozilla/5.0"},verify=False,timeout=8).json()
        uid=uid_res.get("uid")
        if uid:
            openid_res=requests.post("https://topup.pk/api/auth/player_id_login",json={"app_id":100067,"login_id":str(uid)},verify=False,timeout=8).json()
            return openid_res.get("open_id")
    except: pass
    return None

def get_jwt_direct(at):
    try:
        oId=get_open_id_from_token(at)
        if not oId: return {"ok":False,"error":"open_id not found"}
        if not PROTOBUF_AVAILABLE: return {"ok":False,"error":"protobuf missing"}
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad
        AeSkEy=b'Yg&tc%DEuh6%Zc^8'; AeSiV=b'6oyZDr22E3ychjM%'
        def enc2(d): return AES.new(AeSkEy,AES.MODE_CBC,AeSiV).encrypt(pad(d,16))
        m=mLpB.MajorLogin()
        m.event_time=str(datetime.now())[:-7]; m.game_name="free fire"; m.platform_id=1; m.client_version="1.120.1"
        m.system_software="Android OS 9 / API-28"; m.system_hardware="Handheld"; m.telecom_operator="Verizon"; m.network_type="WIFI"
        m.screen_width=1920; m.screen_height=1080; m.screen_dpi="280"
        m.processor_details="ARM64 FP ASIMD AES VMH | 2865 | 4"; m.memory=3003
        m.gpu_renderer="Adreno (TM) 640"; m.gpu_version="OpenGL ES 3.1 v1.46"
        m.unique_device_id="Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57"; m.client_ip="223.191.51.89"
        m.language="en"; m.open_id=oId; m.open_id_type="1"; m.device_type="Handheld"; m.access_token=at
        m.platform_sdk_id=1; m.client_using_version="7428b253defc164018c604a1ebbfebdf"
        m.login_by=3; m.channel_type=3; m.cpu_type=2; m.cpu_architecture="64"
        m.client_version_code="2019118695"; m.login_open_id_type=1; m.origin_platform_type="1"; m.primary_platform_type="1"
        enc_data=enc2(m.SerializeToString())
        resp=requests.post("https://loginbp.gg.blueshark.com/MajorLogin",data=enc_data,headers={"User-Agent":"GarenaMSDK/4.0.19P9","Content-Type":"application/octet-stream"},timeout=15,verify=False)
        if resp.status_code==200:
            try:
                from Crypto.Util.Padding import unpad
                dec_data=unpad(AES.new(AeSkEy,AES.MODE_CBC,AeSiV).decrypt(resp.content),16)
                major_res=mLrPb.MajorLoginRes(); major_res.ParseFromString(dec_data)
                if major_res.token: return {"ok":True,"jwt":major_res.token,"open_id":oId,"account_id":major_res.account_id}
            except:
                try:
                    major_res=mLrPb.MajorLoginRes(); major_res.ParseFromString(resp.content)
                    if major_res.token: return {"ok":True,"jwt":major_res.token,"open_id":oId,"account_id":major_res.account_id}
                except Exception as e:
                    return {"ok":False,"error":f"decode {e}"}
        return {"ok":False,"error":f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"ok":False,"error":str(e)[:200]}

def fetch_bind_info_sync(access_token):
    try:
        url="https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        payload={'app_id':"100067",'access_token':access_token}
        headers={'User-Agent':"GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",'Connection':"Keep-Alive",'Accept-Encoding':"gzip"}
        r=requests.get(url,params=payload,headers=headers,timeout=15)
        if r.status_code==200: return {"ok":True,"data":r.json()}
        else: return {"ok":False,"error":f"HTTP {r.status_code}","raw":r.text[:300]}
    except Exception as e:
        return {"ok":False,"error":str(e)}

def send_otp_sync_direct(email, access_token):
    try:
        url="https://100067.connect.garena.com/game/account_security/bind:send_otp"
        headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded","Accept":"application/json"}
        data={"email":email,"locale":"en_PK","region":"PK","app_id":"100067","access_token":access_token}
        r=requests.post(url,headers=headers,data=data,timeout=15)
        try:
            j=r.json()
            if j.get("result")==0: return {"ok":True,"data":j,"method":"direct"}
            else:
                txt=r.text.lower()
                if "captcha" in txt: return {"ok":False,"data":j,"error":"captcha_required","method":"direct"}
                return {"ok":False,"data":j,"error":j.get("error","Failed"),"method":"direct"}
        except:
            txt=r.text.lower()
            if "captcha" in txt: return {"ok":False,"error":"captcha_required","method":"direct"}
            return {"ok":False,"error":r.text[:200],"method":"direct"}
    except Exception as e:
        return {"ok":False,"error":str(e),"method":"direct"}

def verify_otp_sync_direct(email, access_token, otp):
    try:
        url="https://100067.connect.garena.com/game/account_security/bind:verify_otp"
        headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded","Accept":"application/json"}
        data={"app_id":"100067","access_token":access_token,"email":email,"code":otp,"otp":otp,"type":"1"}
        r=requests.post(url,headers=headers,data=data,timeout=15)
        j=r.json(); return {"ok": j.get("result")==0 or "verifier_token" in j, "data":j, "method":"direct"}
    except Exception as e:
        return {"ok":False,"error":str(e)}

def verify_identity_otp_sync_direct(email, access_token, otp):
    try:
        url="https://100067.connect.garena.com/game/account_security/bind:verify_identity"
        headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded","Accept":"application/json"}
        data={"email":email,"app_id":"100067","access_token":access_token,"otp":otp}
        r=requests.post(url,headers=headers,data=data,timeout=15)
        j=r.json(); return {"ok":"identity_token" in j, "data":j, "method":"direct"}
    except Exception as e:
        return {"ok":False,"error":str(e)}

def api_send_otp_proxy(token,email): return _api_request("send-otp",{"access_token":token,"email":email,"app_id":_APP_ID})
def api_bind_proxy(token,email,otp,sec): return _api_request("bind",{"access_token":token,"email":email,"otp":otp,"secondary_password":sec,"app_id":_APP_ID})
def api_cancel_proxy(token): return _api_request("cancel",{"access_token":token,"app_id":_APP_ID})
def api_unbind_sec_proxy(token,sec): return _api_request("unbind-with-sec",{"access_token":token,"secondary_password":sec,"app_id":_APP_ID})
def api_unbind_otp_proxy(token,email,otp): return _api_request("unbind-with-otp",{"access_token":token,"email":email,"otp":otp,"app_id":_APP_ID})
def api_change_sec_proxy(token,old,new,sec,new_otp): return _api_request("change-email-sec",{"access_token":token,"old_email":old,"new_email":new,"secondary_password":sec,"new_otp":new_otp,"app_id":_APP_ID})
def api_change_otp_proxy(token,old,new,old_otp,new_otp): return _api_request("change-email-otp",{"access_token":token,"old_email":old,"new_email":new,"old_otp":old_otp,"new_otp":new_otp,"app_id":_APP_ID})
def api_get_bind_info_proxy(token): return _api_request("get-bind-info",{"access_token":token,"app_id":_APP_ID})
def api_get_platforms_proxy(token): return _api_request("get-platform",{"access_token":token})
def api_revoke_proxy(token): return _api_request("revoke-access",{"access_token":token,"app_id":_APP_ID})
def api_eat_proxy(eat_token): return _api_request("eat-token-access-token",{"eat_token":eat_token})
def api_jwt_extract_proxy(access_token):
    try:
        resp=requests.get(_EXTRACT_URL,params={"access_token":access_token},timeout=15)
        if resp.status_code==200: return resp.json()
        else: return {"success":False,"error":f"HTTP {resp.status_code}"}
    except Exception as e: return {"success":False,"error":str(e)}
def generate_temp_email():
    try:
        resp=requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1",timeout=10)
        return {"success":True,"email":resp.json()[0]}
    except Exception as e: return {"success":False,"message":str(e)}
def smart_send_otp(email,access_token):
    direct=send_otp_sync_direct(email,access_token)
    if direct["ok"]: return direct
    if "captcha" in str(direct.get("error","")).lower() or "captcha" in str(direct.get("data","")).lower():
        proxy=api_send_otp_proxy(access_token,email)
        if proxy.get("success"): return {"ok":True,"data":proxy,"method":"proxy","proxy_raw":proxy}
        else: return {"ok":False,"error":f"Direct: captcha_required, Proxy: {proxy.get('message','failed')}","method":"both","direct":direct,"proxy":proxy}
    return direct
def eat_to_access_token_sync(eat_input):
    try:
        eat_token=None
        if "http" in eat_input or "?" in eat_input or "eat=" in eat_input:
            parsed=urllib.parse.urlparse(eat_input); qs=urllib.parse.parse_qs(parsed.query)
            if 'eat' in qs: eat_token=qs['eat'][0]
            else:
                if 'eat=' in eat_input: eat_token=eat_input.split('eat=')[1].split('&')[0]
                else:
                    m=re.search(r'[a-fA-F0-9]{64,}',eat_input)
                    if m: eat_token=m.group(0)
        else: eat_token=eat_input.strip()
        if not eat_token:
            m=re.search(r'[a-fA-F0-9]{64,}',eat_input)
            if m: eat_token=m.group(0)
            else: return {"ok":False,"error":"EAT not found"}
        proxy=api_eat_proxy(eat_token)
        if proxy.get("success") and proxy.get("access_token"):
            return {"ok":True,"access_token":proxy.get("access_token"),"account_id":"Unknown","nickname":"Unknown","region":"Unknown","method":"proxy"}
        api_url=f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
        r=requests.get(api_url,headers={"User-Agent":"Mozilla/5.0"},allow_redirects=True,timeout=15)
        parsed_final=urllib.parse.urlparse(r.url); final_qs=urllib.parse.parse_qs(parsed_final.query)
        if 'access_token' not in final_qs: return {"ok":False,"error":f"EAT expired - Proxy: {proxy.get('message','')}"}
        return {"ok":True,"access_token":final_qs['access_token'][0],"account_id":final_qs.get('account_id',['Unknown'])[0],"nickname":urllib.parse.unquote(final_qs.get('nickname',['Unknown'])[0]),"region":final_qs.get('region',['Unknown'])[0],"method":"direct"}
    except Exception as e:
        return {"ok":False,"error":str(e)[:200]}
def revoke_token_sync(access_token):
    proxy=api_revoke_proxy(access_token)
    if proxy.get("success"): return {"ok":True,"data":proxy,"method":"proxy"}
    try:
        refresh="1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
        logout_url=f"https://100067.connect.garena.com/oauth/logout?access_token={access_token}&refresh_token={refresh}"
        r=requests.get(logout_url,headers={"User-Agent":"Mozilla/5.0"},timeout=12)
        if r.status_code==200 and "error" not in r.text.lower(): return {"ok":True,"data":r.text,"method":"direct"}
        else:
            if '"result":0' in r.text or r.status_code==200: return {"ok":True,"data":r.text,"method":"direct"}
            return {"ok":False,"error":r.text[:200],"method":"direct"}
    except Exception as e:
        return {"ok":False,"error":str(e)}
async def check_user_joined_all(context,user_id):
    not_joined=[]
    for ch in REQUIRED_CHANNELS:
        try:
            member=await context.bot.get_chat_member(chat_id=ch["chat_id"],user_id=user_id)
            if member.status in ["left","kicked"]: not_joined.append(ch)
        except: pass
    return not_joined
def get_force_join_keyboard():
    keyboard=[]
    for ch in REQUIRED_CHANNELS:
        try:
            if HAS_STYLE: btn=InlineKeyboardButton(text=f"Join {ch['name']}",url=ch["link"],style=KeyboardButtonStyle.PRIMARY)
            else: btn=InlineKeyboardButton(text=f"Join {ch['name']}",url=ch["link"])
            keyboard.append([btn])
        except: keyboard.append([InlineKeyboardButton(text=f"Join {ch['name']}",url=ch["link"])])
    keyboard.append([InlineKeyboardButton(text="âœ… I Have Joined",callback_data="check_join",style=KeyboardButtonStyle.SUCCESS if HAS_STYLE else None)])
    return InlineKeyboardMarkup(keyboard)
def get_force_join_text(not_joined_list=None):
    if not_joined_list: names="\n".join([f"- {ch['name']}" for ch in not_joined_list])
    else: names="\n".join([f"- {ch['name']}" for ch in REQUIRED_CHANNELS])
    return f"ðŸ”’ Join Verification Required\n\nTo use this bot, you must join:\n\n{names}\n\nAfter joining, click below:"
def get_reply_keyboard():
    if HAS_STYLE:
        keyboard=[
            [KeyboardButton(text="CHECK BIND INFO",style=KeyboardButtonStyle.SUCCESS),KeyboardButton(text="BIND EMAIL",style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="UNBIND EMAIL",style=KeyboardButtonStyle.SUCCESS),KeyboardButton(text="UNBIND WITH SEC CODE",style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="CHANGE BIND EMAIL",style=KeyboardButtonStyle.SUCCESS),KeyboardButton(text="CHANGE WITH SEC CODE",style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="CANCEL BIND REQUEST",style=KeyboardButtonStyle.SUCCESS),KeyboardButton(text="SECURITY CODE INFO",style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="CHANGE SECURITY CODE",style=KeyboardButtonStyle.SUCCESS),KeyboardButton(text="EAT TO ACCESS TOKEN",style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="REVOKE ACCESS TOKEN",style=KeyboardButtonStyle.DANGER),KeyboardButton(text="FULL ACCOUNT INFO",style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="SINGLE UNSUBSCRIBE OTP",style=KeyboardButtonStyle.SUCCESS),KeyboardButton(text="GAME LOGIN HISTORY",style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="BIO UPDATE",style=KeyboardButtonStyle.SUCCESS),KeyboardButton(text="NAME CHANGE",style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="LINKED PLATFORMS",style=KeyboardButtonStyle.SUCCESS),KeyboardButton(text="JWT EXTRACTOR",style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="TEMP EMAIL",style=KeyboardButtonStyle.SUCCESS),KeyboardButton(text="OWNER DETAILS",style=KeyboardButtonStyle.PRIMARY)],
        ]
    else:
        keyboard=[
            ["CHECK BIND INFO","BIND EMAIL"],
            ["UNBIND EMAIL","UNBIND WITH SEC CODE"],
            ["CHANGE BIND EMAIL","CHANGE WITH SEC CODE"],
            ["CANCEL BIND REQUEST","SECURITY CODE INFO"],
            ["CHANGE SECURITY CODE","EAT TO ACCESS TOKEN"],
            ["REVOKE ACCESS TOKEN","FULL ACCOUNT INFO"],
            ["SINGLE UNSUBSCRIBE OTP","GAME LOGIN HISTORY"],
            ["BIO UPDATE","NAME CHANGE"],
            ["LINKED PLATFORMS","JWT EXTRACTOR"],
            ["TEMP EMAIL","OWNER DETAILS"],
        ]
    return ReplyKeyboardMarkup(keyboard,resize_keyboard=True,is_persistent=True)
def get_youtube_keyboard():
    try:
        if HAS_STYLE: return InlineKeyboardMarkup([[InlineKeyboardButton(text="ðŸ“º Subscribe YouTube Channel",url=YOUTUBE_LINK,style=KeyboardButtonStyle.SUCCESS)]])
        else: return InlineKeyboardMarkup([[InlineKeyboardButton(text="ðŸ“º Subscribe YouTube Channel",url=YOUTUBE_LINK)]])
    except: return InlineKeyboardMarkup([[InlineKeyboardButton(text="ðŸ“º Subscribe YouTube Channel",url=YOUTUBE_LINK)]])
async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user_id=update.effective_user.id
    not_joined=await check_user_joined_all(context,user_id)
    if not_joined:
        await update.message.reply_text(get_force_join_text(not_joined),reply_markup=get_force_join_keyboard())
        return STATE_INPUT
    await update.message.reply_text(f"ðŸ‘‹ Welcome {update.effective_user.first_name or 'User'}!\n\nðŸ”¥ Zevric Bind Bot v7.0 Anti-Captcha + All putkiya.py Options",reply_markup=get_youtube_keyboard())
    await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
    return STATE_INPUT
async def menu_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
    return STATE_INPUT
async def cancel_cmd(update:Update,context:ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("âŒ Cancelled. Main Menu:",reply_markup=get_reply_keyboard())
    return STATE_INPUT
async def handle_callback(update:Update,context:ContextTypes.DEFAULT_TYPE):
    try:
        query=update.callback_query
        await query.answer()
        if query.data=="check_join":
            user_id=query.from_user.id
            not_joined=await check_user_joined_all(context,user_id)
            if not_joined: await query.message.edit_text(get_force_join_text(not_joined),reply_markup=get_force_join_keyboard())
            else:
                await query.message.edit_text(f"âœ… Verified!",reply_markup=get_youtube_keyboard())
                await context.bot.send_message(chat_id=query.message.chat_id,text="ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
        return STATE_INPUT
    except: return STATE_INPUT
async def handle_text(update:Update,context:ContextTypes.DEFAULT_TYPE):
    try:
        user_id=update.effective_user.id
        not_joined=await check_user_joined_all(context,user_id)
        if not_joined:
            await update.message.reply_text(get_force_join_text(not_joined),reply_markup=get_force_join_keyboard())
            return STATE_INPUT
        text=update.message.text.strip()
        text_lower=text.lower()
        flow=context.user_data.get("flow")
        step=context.user_data.get("step")
        if text_lower=="check bind info":
            context.user_data.clear(); context.user_data["flow"]="bind_info"; context.user_data["step"]="token"
            await update.message.reply_text("ðŸ”‘ Enter Access Token:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower=="bind email":
            context.user_data.clear(); context.user_data["flow"]="bind"; context.user_data["step"]="token"
            await update.message.reply_text("ðŸ”‘ Enter Access Token:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower=="unbind email":
            context.user_data.clear(); context.user_data["flow"]="unbind"; context.user_data["step"]="token"
            await update.message.reply_text("ðŸ”‘ Enter Access Token:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower=="unbind with sec code":
            context.user_data.clear(); context.user_data["flow"]="unbind_sec"; context.user_data["step"]="token"
            await update.message.reply_text("ðŸ”‘ Enter Access Token:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower=="change bind email":
            context.user_data.clear(); context.user_data["flow"]="change"; context.user_data["step"]="token"
            await update.message.reply_text("ðŸ”‘ Enter Access Token:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower=="change with sec code":
            context.user_data.clear(); context.user_data["flow"]="change_sec_code"; context.user_data["step"]="token"
            await update.message.reply_text("ðŸ”‘ Enter Access Token:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower=="cancel bind request":
            context.user_data.clear(); context.user_data["flow"]="cancel"; context.user_data["step"]="token"
            await update.message.reply_text("ðŸ”‘ Enter Access Token:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower=="security code info":
            context.user_data.clear(); context.user_data["flow"]="sec_info"; context.user_data["step"]="token"
            await update.message.reply_text("ðŸ”‘ Enter Access Token:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower=="change security code":
            context.user_data.clear(); context.user_data["flow"]="change_sec"; context.user_data["step"]="token"
            await update.message.reply_text("ðŸ”‘ Enter Access Token:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower=="eat to access token":
            context.user_data.clear(); context.user_data["flow"]="eat"; context.user_data["step"]="token"
            await update.message.reply_text("ðŸª Enter EAT Token / URL:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower=="revoke access token":
            context.user_data.clear(); context.user_data["flow"]="revoke"; context.user_data["step"]="token"
            await update.message.reply_text("ðŸ”‘ Enter Token to Revoke:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower=="full account info":
            context.user_data.clear(); context.user_data["flow"]="full_info"; context.user_data["step"]="token"
            await update.message.reply_text("ðŸ”‘ Enter Access Token:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower=="single unsubscribe otp":
            context.user_data.clear(); context.user_data["flow"]="fix_unsub"; context.user_data["step"]="email"
            await update.message.reply_text("ðŸ“§ Enter Email:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower=="game login history":
            context.user_data.clear(); context.user_data["flow"]="game_login"; context.user_data["step"]="token"
            await update.message.reply_text("ðŸ”‘ Enter Access Token:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower=="bio update":
            context.user_data.clear(); context.user_data["flow"]="bio_update"; context.user_data["step"]="token"
            await update.message.reply_text("ðŸ”‘ Enter Access Token:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower=="name change":
            context.user_data.clear(); context.user_data["flow"]="name_change"; context.user_data["step"]="token"
            await update.message.reply_text("ðŸ”‘ Enter Access Token:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower=="linked platforms":
            context.user_data.clear(); context.user_data["flow"]="platforms"; context.user_data["step"]="token"
            await update.message.reply_text("ðŸ”‘ Enter Access Token:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower=="jwt extractor":
            context.user_data.clear(); context.user_data["flow"]="jwt_extract"; context.user_data["step"]="token"
            await update.message.reply_text("ðŸ”‘ Enter Access Token:",reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower=="temp email":
            await update.message.reply_text("â³ Generating temp email...",reply_markup=get_youtube_keyboard())
            res=generate_temp_email()
            if res.get("success"): await update.message.reply_text(f"âœ… Temp Email: {res['email']}",reply_markup=get_youtube_keyboard())
            else: await update.message.reply_text(f"âŒ Failed: {res.get('message')}",reply_markup=get_youtube_keyboard())
            await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
            return STATE_INPUT
        if text_lower=="owner details":
            await update.message.reply_text("ðŸ‘‘ Owner: Zevric X Play\nðŸ“© @just_zevric\nðŸ“º @zevricxplay\nâœ… v7.0 Anti-Captcha + putkiya.py All Options",reply_markup=get_youtube_keyboard())
            await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
            return STATE_INPUT
        if flow=="bind_info":
            if step=="token":
                await update.message.reply_text("â³ Fetching...",reply_markup=get_youtube_keyboard())
                proxy=api_get_bind_info_proxy(text)
                if proxy.get("success"):
                    current=proxy.get("current_email",""); pending=proxy.get("pending_email",""); countdown=proxy.get("countdown_human","") or format_seconds(proxy.get("countdown_seconds",0))
                    uid,nick,region=get_player_info_sync(text)
                    msg=f"âœ… BIND INFO (Proxy)\n\nðŸ‘¤ {nick} ({uid})\nðŸŒ {region}\nðŸ“§ Current: {current or 'None'}\nðŸ“§ Pending: {pending or 'None'}\nâ° {countdown}"
                    await update.message.reply_text(msg,reply_markup=get_youtube_keyboard())
                else:
                    uid,nick,region=get_player_info_sync(text)
                    bind=fetch_bind_info_sync(text)
                    if bind["ok"]:
                        data=bind["data"]
                        msg=f"âœ… BIND INFO (Direct)\n\nðŸ‘¤ {nick} ({uid})\nðŸŒ {region}\nðŸ“§ Current: {data.get('email','None')}\nðŸ“§ Pending: {data.get('email_to_be','None')}\nâ° {convert_seconds(data.get('request_exec_countdown',0))}\nðŸ”’ Sec: {'SET' if data.get('secondary_password') else 'NOT SET'}"
                        await update.message.reply_text(msg,reply_markup=get_youtube_keyboard())
                    else:
                        await update.message.reply_text(f"âŒ Error: {bind.get('error')} \nProxy: {proxy.get('message')}",reply_markup=get_youtube_keyboard())
                await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT
        if flow=="bind":
            if step=="token":
                context.user_data["token"]=text
                await update.message.reply_text("â³ Checking current bind...",reply_markup=get_youtube_keyboard())
                proxy=api_get_bind_info_proxy(text)
                if proxy.get("success"): await update.message.reply_text(f"ðŸ“§ Current: {proxy.get('current_email','None')}",reply_markup=get_youtube_keyboard())
                else:
                    b=fetch_bind_info_sync(text)
                    if b["ok"]: await update.message.reply_text(f"ðŸ“§ Current: {b['data'].get('email','None')}",reply_markup=get_youtube_keyboard())
                await update.message.reply_text("ðŸ“§ Enter New Email To Bind:",reply_markup=get_youtube_keyboard())
                context.user_data["step"]="email"
                return STATE_INPUT
            if step=="email":
                if "@" not in text or "." not in text:
                    await update.message.reply_text("âŒ Invalid Email!",reply_markup=get_youtube_keyboard())
                    return STATE_INPUT
                context.user_data["email"]=text
                await update.message.reply_text(f"â³ Sending OTP to {text}... (Direct + Proxy fallback)",reply_markup=get_youtube_keyboard())
                res=smart_send_otp(text,context.user_data["token"])
                if res["ok"]:
                    await update.message.reply_text(f"âœ… OTP Sent via {res.get('method').upper()} to {text}\nðŸ“© Enter OTP:",reply_markup=get_youtube_keyboard())
                    context.user_data["step"]="otp"
                else:
                    await update.message.reply_text(f"âŒ Failed: {res.get('error')}\nðŸ’¡ TIP: Wait 5-10 min or use TEMP EMAIL or Sec Code option",reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                return STATE_INPUT
            if step=="otp":
                context.user_data["otp"]=text
                await update.message.reply_text("ðŸ”’ Enter 6-digit Security Code (e.g. 123456):",reply_markup=get_youtube_keyboard())
                context.user_data["step"]="sec_code"
                return STATE_INPUT
            if step=="sec_code":
                if not text.isdigit() or len(text)!=6:
                    await update.message.reply_text("âŒ Must be 6 digits!",reply_markup=get_youtube_keyboard())
                    return STATE_INPUT
                await update.message.reply_text("â³ Binding via Proxy Anti-Captcha...",reply_markup=get_youtube_keyboard())
                token=context.user_data["token"]; email=context.user_data["email"]; otp=context.user_data["otp"]; sec=text
                proxy=api_bind_proxy(token,email,otp,sec)
                if proxy.get("success"):
                    await update.message.reply_text(f"âœ… Bind Success (Proxy)!\nðŸ“§ {email}\nðŸ”’ {sec}\nMsg: {proxy.get('message')}",reply_markup=get_youtube_keyboard())
                else:
                    from_here=verify_otp_sync_direct(email,token,otp)
                    if from_here["ok"]:
                        vt=from_here["data"].get("verifier_token")
                        if vt:
                            try:
                                url="https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
                                headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
                                data={"email":email,"app_id":"100067","access_token":token,"verifier_token":vt,"secondary_password":sec}
                                r=requests.post(url,headers=headers,data=data,timeout=15)
                                j=r.json()
                                if j.get("result")==0: await update.message.reply_text(f"âœ… Bind Success (Direct)! {email}",reply_markup=get_youtube_keyboard())
                                else: await update.message.reply_text(f"âŒ Direct: {j} \nProxy: {proxy.get('message')}",reply_markup=get_youtube_keyboard())
                            except Exception as e:
                                await update.message.reply_text(f"âŒ Error: {e} Proxy: {proxy.get('message')}",reply_markup=get_youtube_keyboard())
                        else: await update.message.reply_text(f"âŒ OTP invalid. Proxy: {proxy.get('message')}",reply_markup=get_youtube_keyboard())
                    else: await update.message.reply_text(f"âŒ OTP Failed: {from_here.get('data')} Proxy {proxy.get('message')}",reply_markup=get_youtube_keyboard())
                await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT
        if flow=="unbind":
            if step=="token":
                context.user_data["token"]=text
                await update.message.reply_text("â³ Fetching current email...",reply_markup=get_youtube_keyboard())
                proxy=api_get_bind_info_proxy(text)
                email=""
                if proxy.get("success"): email=proxy.get("current_email","")
                else:
                    b=fetch_bind_info_sync(text)
                    email=b["data"].get("email","") if b["ok"] else ""
                if not email:
                    await update.message.reply_text("âŒ No Bound Email.",reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                context.user_data["email"]=email
                await update.message.reply_text(f"ðŸ“§ Current: {email}\nâ³ Sending OTP...",reply_markup=get_youtube_keyboard())
                res=smart_send_otp(email,text)
                if res["ok"]:
                    await update.message.reply_text(f"âœ… OTP Sent via {res.get('method')} to {email}\nðŸ“© Enter OTP:",reply_markup=get_youtube_keyboard())
                    context.user_data["step"]="otp"
                else:
                    await update.message.reply_text(f"âŒ Failed: {res.get('error')}\nðŸ’¡ Try UNBIND WITH SEC CODE!",reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                return STATE_INPUT
            if step=="otp":
                await update.message.reply_text("â³ Unbinding via Proxy...",reply_markup=get_youtube_keyboard())
                token=context.user_data["token"]; email=context.user_data["email"]; otp=text
                proxy=api_unbind_otp_proxy(token,email,otp)
                if proxy.get("success"): await update.message.reply_text(f"âœ… Unbind Success! {proxy.get('message')}",reply_markup=get_youtube_keyboard())
                else:
                    verify=verify_identity_otp_sync_direct(email,token,otp)
                    if verify["ok"]:
                        it=verify["data"].get("identity_token")
                        if it:
                            try:
                                url="https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
                                headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
                                data={"app_id":"100067","access_token":token,"identity_token":it}
                                r=requests.post(url,headers=headers,data=data,timeout=15)
                                j=r.json()
                                if j.get("result")==0: await update.message.reply_text("âœ… Unbind Success (Direct)!",reply_markup=get_youtube_keyboard())
                                else: await update.message.reply_text(f"âŒ Direct: {j} Proxy: {proxy.get('message')}",reply_markup=get_youtube_keyboard())
                            except Exception as e: await update.message.reply_text(f"âŒ Error: {e}",reply_markup=get_youtube_keyboard())
                        else: await update.message.reply_text(f"âŒ Identity missing. Proxy: {proxy.get('message')}",reply_markup=get_youtube_keyboard())
                    else: await update.message.reply_text(f"âŒ OTP Failed: {verify.get('data')} Proxy: {proxy.get('message')}",reply_markup=get_youtube_keyboard())
                await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT
        if flow=="unbind_sec":
            if step=="token":
                context.user_data["token"]=text
                await update.message.reply_text("ðŸ”’ Enter Security Code (6 digits):",reply_markup=get_youtube_keyboard())
                context.user_data["step"]="sec"
                return STATE_INPUT
            if step=="sec":
                if not text.isdigit() or len(text)!=6:
                    await update.message.reply_text("âŒ 6 digits!",reply_markup=get_youtube_keyboard())
                    return STATE_INPUT
                await update.message.reply_text(f"â³ Unbinding with Sec Code {text} via Proxy...",reply_markup=get_youtube_keyboard())
                proxy=api_unbind_sec_proxy(context.user_data["token"],text)
                if proxy.get("success"): await update.message.reply_text(f"âœ… Unbind Success! {proxy.get('message')}",reply_markup=get_youtube_keyboard())
                else: await update.message.reply_text(f"âŒ Failed: {proxy.get('message')}",reply_markup=get_youtube_keyboard())
                await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT
        if flow=="change":
            if step=="token":
                context.user_data["token"]=text
                await update.message.reply_text("â³ Fetching old email...",reply_markup=get_youtube_keyboard())
                proxy=api_get_bind_info_proxy(text)
                old=""
                if proxy.get("success"): old=proxy.get("current_email","")
                else:
                    b=fetch_bind_info_sync(text)
                    old=b["data"].get("email","") if b["ok"] else ""
                if not old:
                    await update.message.reply_text("âŒ No Bound Email!",reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                context.user_data["old_email"]=old
                await update.message.reply_text(f"ðŸ“§ Old: {old}\nâ³ Sending OTP to old email...",reply_markup=get_youtube_keyboard())
                res=smart_send_otp(old,text)
                if res["ok"]:
                    await update.message.reply_text(f"âœ… OTP Sent via {res.get('method')} to {old}\nðŸ“© Enter OTP from OLD email:",reply_markup=get_youtube_keyboard())
                    context.user_data["step"]="old_otp"
                else:
                    await update.message.reply_text(f"âŒ Failed: {res.get('error')}\nðŸ’¡ Use CHANGE WITH SEC CODE - no old OTP needed!",reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                return STATE_INPUT
            if step=="old_otp":
                context.user_data["old_otp"]=text
                await update.message.reply_text("ðŸ“§ Enter NEW Email:",reply_markup=get_youtube_keyboard())
                context.user_data["step"]="new_email"
                return STATE_INPUT
            if step=="new_email":
                if "@" not in text or "." not in text:
                    await update.message.reply_text("âŒ Invalid Email!",reply_markup=get_youtube_keyboard())
                    return STATE_INPUT
                context.user_data["new_email"]=text
                await update.message.reply_text(f"â³ Sending OTP to new {text}...",reply_markup=get_youtube_keyboard())
                res=smart_send_otp(text,context.user_data["token"])
                if res["ok"]:
                    await update.message.reply_text(f"âœ… OTP Sent via {res.get('method')} to {text}\nðŸ“© Enter OTP from NEW email:",reply_markup=get_youtube_keyboard())
                    context.user_data["step"]="new_otp"
                else:
                    await update.message.reply_text(f"âŒ Failed: {res.get('error')}",reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                return STATE_INPUT
            if step=="new_otp":
                await update.message.reply_text("â³ Changing via Proxy...",reply_markup=get_youtube_keyboard())
                token=context.user_data["token"]; old=context.user_data["old_email"]; new=context.user_data["new_email"]; old_otp=context.user_data["old_otp"]; new_otp=text
                proxy=api_change_otp_proxy(token,old,new,old_otp,new_otp)
                if proxy.get("success"): await update.message.reply_text(f"âœ… Change Success! {old} -> {new} Msg: {proxy.get('message')}",reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"âŒ Proxy Failed: {proxy.get('message')}\nTrying direct...",reply_markup=get_youtube_keyboard())
                    try:
                        v_old=verify_identity_otp_sync_direct(old,token,old_otp)
                        v_new=verify_otp_sync_direct(new,token,new_otp)
                        if v_old["ok"] and v_new["ok"]:
                            it=v_old["data"].get("identity_token"); vt=v_new["data"].get("verifier_token")
                            if it and vt:
                                url="https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
                                headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
                                data={"identity_token":it,"email":new,"app_id":"100067","verifier_token":vt,"access_token":token}
                                r=requests.post(url,headers=headers,data=data,timeout=15)
                                j=r.json()
                                if j.get("result")==0: await update.message.reply_text(f"âœ… Change Success Direct! {old}->{new}",reply_markup=get_youtube_keyboard())
                                else: await update.message.reply_text(f"âŒ Direct fail: {j}",reply_markup=get_youtube_keyboard())
                            else: await update.message.reply_text("âŒ Token missing",reply_markup=get_youtube_keyboard())
                        else: await update.message.reply_text(f"âŒ Verify fail Old:{v_old.get('data')} New:{v_new.get('data')}",reply_markup=get_youtube_keyboard())
                    except Exception as e: await update.message.reply_text(f"âŒ Error {e}",reply_markup=get_youtube_keyboard())
                await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT
        if flow=="change_sec_code":
            if step=="token":
                context.user_data["token"]=text
                await update.message.reply_text("ðŸ“§ Enter OLD Email (current bound):",reply_markup=get_youtube_keyboard())
                context.user_data["step"]="old_email"
                return STATE_INPUT
            if step=="old_email":
                if "@" not in text:
                    await update.message.reply_text("âŒ Invalid!",reply_markup=get_youtube_keyboard())
                    return STATE_INPUT
                context.user_data["old_email"]=text
                await update.message.reply_text("ðŸ“§ Enter NEW Email:",reply_markup=get_youtube_keyboard())
                context.user_data["step"]="new_email"
                return STATE_INPUT
            if step=="new_email":
                if "@" not in text:
                    await update.message.reply_text("âŒ Invalid!",reply_markup=get_youtube_keyboard())
                    return STATE_INPUT
                context.user_data["new_email"]=text
                await update.message.reply_text("ðŸ”’ Enter Security Code (6 digits):",reply_markup=get_youtube_keyboard())
                context.user_data["step"]="sec"
                return STATE_INPUT
            if step=="sec":
                if not text.isdigit() or len(text)!=6:
                    await update.message.reply_text("âŒ 6 digits!",reply_markup=get_youtube_keyboard())
                    return STATE_INPUT
                context.user_data["sec_code"]=text
                await update.message.reply_text(f"â³ Sending OTP to NEW email {context.user_data['new_email']}...",reply_markup=get_youtube_keyboard())
                res=smart_send_otp(context.user_data["new_email"],context.user_data["token"])
                if res["ok"]:
                    await update.message.reply_text(f"âœ… OTP Sent via {res.get('method')} to {context.user_data['new_email']}\nðŸ“© Enter OTP:",reply_markup=get_youtube_keyboard())
                    context.user_data["step"]="new_otp"
                else:
                    await update.message.reply_text(f"âŒ Failed: {res.get('error')}",reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                return STATE_INPUT
            if step=="new_otp":
                await update.message.reply_text("â³ Changing Email with Sec Code via Proxy...",reply_markup=get_youtube_keyboard())
                proxy=api_change_sec_proxy(context.user_data["token"],context.user_data["old_email"],context.user_data["new_email"],context.user_data["sec_code"],text)
                if proxy.get("success"): await update.message.reply_text(f"âœ… Change Success! {proxy.get('message')}",reply_markup=get_youtube_keyboard())
                else: await update.message.reply_text(f"âŒ Failed: {proxy.get('message')}",reply_markup=get_youtube_keyboard())
                await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT
        if flow=="cancel":
            if step=="token":
                await update.message.reply_text("â³ Cancelling via Proxy...",reply_markup=get_youtube_keyboard())
                proxy=api_cancel_proxy(text)
                if proxy.get("success"): await update.message.reply_text(f"âœ… Cancelled! {proxy.get('message')}",reply_markup=get_youtube_keyboard())
                else:
                    try:
                        url="https://100067.connect.garena.com/game/account_security/bind:cancel_request"
                        headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
                        data={"app_id":"100067","access_token":text}
                        r=requests.post(url,headers=headers,data=data,timeout=15)
                        j=r.json()
                        if j.get("result")==0: await update.message.reply_text("âœ… Cancelled (Direct)!",reply_markup=get_youtube_keyboard())
                        else: await update.message.reply_text(f"âŒ Failed: {j} Proxy: {proxy.get('message')}",reply_markup=get_youtube_keyboard())
                    except Exception as e: await update.message.reply_text(f"âŒ Error {e}",reply_markup=get_youtube_keyboard())
                await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT
        if flow=="sec_info":
            if step=="token":
                await update.message.reply_text("â³ Fetching sec code info...",reply_markup=get_youtube_keyboard())
                proxy=api_get_bind_info_proxy(text)
                if proxy.get("success"):
                    raw=proxy.get("raw",{}); has_sec=raw.get("secondary_password",False) or proxy.get("has_secondary",False)
                    msg=f"ðŸ”’ SECURITY INFO (Proxy)\nðŸ“§ Current: {proxy.get('current_email','None')}\nðŸ”’ Sec Code: {'SET âœ…' if has_sec else 'NOT SET âŒ'}"
                    await update.message.reply_text(msg,reply_markup=get_youtube_keyboard())
                else:
                    uid,nick,region=get_player_info_sync(text)
                    b=fetch_bind_info_sync(text)
                    if b["ok"]:
                        sec="SET âœ…" if b["data"].get("secondary_password") else "NOT SET âŒ"
                        await update.message.reply_text(f"ðŸ”’ {nick} ({uid})\nSec: {sec}\nEmail: {b['data'].get('email','None')}",reply_markup=get_youtube_keyboard())
                    else: await update.message.reply_text(f"âŒ {b.get('error')}",reply_markup=get_youtube_keyboard())
                await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT
        if flow=="change_sec":
            if step=="token":
                context.user_data["token"]=text
                await update.message.reply_text("â³ Fetching email...",reply_markup=get_youtube_keyboard())
                proxy=api_get_bind_info_proxy(text)
                email=""
                if proxy.get("success"): email=proxy.get("current_email","")
                else:
                    b=fetch_bind_info_sync(text)
                    email=b["data"].get("email","") if b["ok"] else ""
                if not email:
                    await update.message.reply_text("âŒ No Bound Email!",reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                context.user_data["email"]=email
                await update.message.reply_text(f"ðŸ“§ {email}\nâ³ Sending OTP...",reply_markup=get_youtube_keyboard())
                res=smart_send_otp(email,text)
                if res["ok"]:
                    await update.message.reply_text(f"âœ… OTP Sent via {res.get('method')} to {email}\nðŸ“© Enter OTP:",reply_markup=get_youtube_keyboard())
                    context.user_data["step"]="otp"
                else:
                    await update.message.reply_text(f"âŒ {res.get('error')}",reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                return STATE_INPUT
            if step=="otp":
                await update.message.reply_text("â³ Verifying...",reply_markup=get_youtube_keyboard())
                verify=verify_identity_otp_sync_direct(context.user_data["email"],context.user_data["token"],text)
                if verify["ok"]:
                    context.user_data["identity_token"]=verify["data"].get("identity_token")
                    await update.message.reply_text("ðŸ”’ Enter NEW 6-digit Code:",reply_markup=get_youtube_keyboard())
                    context.user_data["step"]="new_code"
                else:
                    await update.message.reply_text(f"âŒ OTP Failed {verify.get('data')}",reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                return STATE_INPUT
            if step=="new_code":
                if not text.isdigit() or len(text)!=6:
                    await update.message.reply_text("âŒ 6 digits!",reply_markup=get_youtube_keyboard())
                    return STATE_INPUT
                await update.message.reply_text(f"â³ Changing to {text}...",reply_markup=get_youtube_keyboard())
                try:
                    headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
                    urls=["https://100067.connect.garena.com/game/account_security/bind:change_secondary_password","https://100067.connect.garena.com/game/account_security/bind:update_secondary_password"]
                    ok=False
                    for url in urls:
                        try:
                            data={"app_id":"100067","access_token":context.user_data["token"],"identity_token":context.user_data["identity_token"],"secondary_password":text}
                            r=requests.post(url,headers=headers,data=data,timeout=12)
                            j=r.json()
                            if j.get("result")==0:
                                await update.message.reply_text(f"âœ… Security Code Changed to {text}!",reply_markup=get_youtube_keyboard())
                                ok=True; break
                        except: continue
                    if not ok: await update.message.reply_text("âŒ All endpoints failed",reply_markup=get_youtube_keyboard())
                except Exception as e: await update.message.reply_text(f"âŒ {e}",reply_markup=get_youtube_keyboard())
                await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT
        if flow=="eat":
            if step=="token":
                await update.message.reply_text("â³ Converting EAT...",reply_markup=get_youtube_keyboard())
                res=eat_to_access_token_sync(text)
                if res["ok"]:
                    msg=f"âœ… EAT SUCCESS via {res.get('method')}\n\nðŸ‘¤ {res['nickname']}\nðŸ†” {res['account_id']}\nðŸŒ {res['region']}\n\nðŸ”‘ Token:\n{res['access_token']}"
                    await update.message.reply_text(msg,reply_markup=get_youtube_keyboard())
                else: await update.message.reply_text(f"âŒ {res.get('error')}",reply_markup=get_youtube_keyboard())
                await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT
        if flow=="revoke":
            if step=="token":
                await update.message.reply_text("â³ Revoking...",reply_markup=get_youtube_keyboard())
                uid,nick,region=get_player_info_sync(text)
                res=revoke_token_sync(text)
                if res["ok"]: await update.message.reply_text(f"âœ… Revoked {nick} ({uid}) via {res.get('method')}",reply_markup=get_youtube_keyboard())
                else: await update.message.reply_text(f"âŒ Failed {res.get('error')}",reply_markup=get_youtube_keyboard())
                await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT
        if flow=="full_info":
            if step=="token":
                await update.message.reply_text("â³ Fetching full info...",reply_markup=get_youtube_keyboard())
                uid,nick,region=get_player_info_sync(text)
                proxy=api_get_bind_info_proxy(text)
                if proxy.get("success"):
                    email=proxy.get("current_email","None")
                    sec="SET" if proxy.get("raw",{}).get("secondary_password") else "NOT SET"
                else:
                    b=fetch_bind_info_sync(text)
                    email=b["data"].get("email","None") if b["ok"] else "Error"
                    sec="SET" if b["data"].get("secondary_password") else "NOT SET" if b["ok"] else "Unknown"
                jwt_res=get_jwt_direct(text)
                if jwt_res["ok"]:
                    payload=decode_jwt_payload(jwt_res["jwt"])
                    msg=f"ðŸ“‹ FULL INFO\nUID:{uid}\nNick:{nick}\nRegion:{region}\nEmail:{email}\nSec:{sec}\nJWT:Valid\nPayload:{json.dumps(payload)[:600]}"
                else: msg=f"ðŸ“‹ FULL INFO\nUID:{uid}\nNick:{nick}\nRegion:{region}\nEmail:{email}\nSec:{sec}\nJWT:{jwt_res['error']}"
                await update.message.reply_text(msg,reply_markup=get_youtube_keyboard())
                await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT
        if flow=="platforms":
            if step=="token":
                await update.message.reply_text("â³ Fetching platforms via Proxy...",reply_markup=get_youtube_keyboard())
                proxy=api_get_platforms_proxy(text)
                if proxy.get("success"):
                    bounded=proxy.get("bounded_accounts") or proxy.get("bounded",[])
                    available=proxy.get("available_platforms") or proxy.get("available",[])
                    main=proxy.get("main_platform","")
                    msg=f"âœ… PLATFORMS\n\nLinked: {bounded}\nAvailable: {available}\nMain: {main}\n\nRaw: {json.dumps(proxy)[:1000]}"
                    await update.message.reply_text(msg,reply_markup=get_youtube_keyboard())
                else: await update.message.reply_text(f"âŒ Failed: {proxy.get('message')}",reply_markup=get_youtube_keyboard())
                await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT
        if flow=="jwt_extract":
            if step=="token":
                await update.message.reply_text("â³ Extracting JWT via Proxy + Direct...",reply_markup=get_youtube_keyboard())
                proxy=api_jwt_extract_proxy(text)
                direct=get_jwt_direct(text)
                msg=""
                if proxy.get("success"): msg+=f"âœ… Proxy JWT Success\nUID:{proxy.get('account_uid')}\nRegion:{proxy.get('region')}\nPlatform:{proxy.get('platform_type_used')}\nJWT:{str(proxy.get('jwt',''))[:500]}\n\n"
                else: msg+=f"Proxy Failed: {proxy.get('error','')}\n\n"
                if direct["ok"]:
                    payload=decode_jwt_payload(direct["jwt"])
                    msg+=f"âœ… Direct JWT Success\nJWT:{direct['jwt'][:500]}\nPayload:{json.dumps(payload)[:500]}"
                else: msg+=f"Direct Failed: {direct['error']}"
                await update.message.reply_text(msg,reply_markup=get_youtube_keyboard())
                await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT
        if flow=="game_login":
            if step=="token":
                await update.message.reply_text("â³ Fetching login history...",reply_markup=get_youtube_keyboard())
                uid,nick,region=get_player_info_sync(text)
                jwt_res=get_jwt_direct(text)
                if jwt_res["ok"]:
                    payload=decode_jwt_payload(jwt_res["jwt"])
                    msg=f"ðŸŽ® LOGIN HISTORY\nUID:{uid}\nNick:{nick}\nRegion:{region}\nPayload:{json.dumps(payload)[:1000]}"
                else: msg=f"ðŸŽ® {nick} ({uid})\nRegion:{region}\nJWT Error:{jwt_res['error']}"
                await update.message.reply_text(msg,reply_markup=get_youtube_keyboard())
                await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT
        if flow=="bio_update":
            if step=="token":
                context.user_data["token"]=text
                uid,nick,region=get_player_info_sync(text)
                await update.message.reply_text(f"ðŸ‘¤ {nick} ({uid})\nEnter Region [IND/BD/SG/BR] Default: IND",reply_markup=get_youtube_keyboard())
                context.user_data["step"]="region"
                return STATE_INPUT
            if step=="region":
                context.user_data["region"]=text.upper() or "IND"
                await update.message.reply_text("ðŸ“ Enter NEW Bio (240 chars):",reply_markup=get_youtube_keyboard())
                context.user_data["step"]="bio"
                return STATE_INPUT
            if step=="bio":
                bio=text[:240]
                await update.message.reply_text("â³ Generating JWT...",reply_markup=get_youtube_keyboard())
                jwt_res=get_jwt_direct(context.user_data["token"])
                if jwt_res["ok"]:
                    jwt_token=jwt_res["jwt"]; enc=urllib.parse.quote(bio)
                    try:
                        r=requests.get(f"https://api-info.ffapi.cloud/api/bio_upload?bio={enc}&jwt={jwt_token}",timeout=12)
                        if "success" in r.text.lower() or "updated" in r.text.lower(): await update.message.reply_text(f"âœ… Bio Updated: {bio}",reply_markup=get_youtube_keyboard())
                        else: await update.message.reply_text(f"âš ï¸ Attempted: {bio} - Check in game",reply_markup=get_youtube_keyboard())
                    except Exception as e: await update.message.reply_text(f"âŒ {e}",reply_markup=get_youtube_keyboard())
                else: await update.message.reply_text(f"âŒ JWT Failed: {jwt_res['error']}",reply_markup=get_youtube_keyboard())
                await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT
        if flow=="name_change":
            if step=="token":
                context.user_data["token"]=text
                uid,nick,region=get_player_info_sync(text)
                await update.message.reply_text(f"ðŸ‘¤ {nick} ({uid})\nEnter Region Default IND:",reply_markup=get_youtube_keyboard())
                context.user_data["step"]="region"; context.user_data["old_nick"]=nick
                return STATE_INPUT
            if step=="region":
                context.user_data["region"]=text.upper() or "IND"
                await update.message.reply_text("ðŸ“ New Nickname (12 chars):",reply_markup=get_youtube_keyboard())
                context.user_data["step"]="new_name"
                return STATE_INPUT
            if step=="new_name":
                new_name=text[:12]
                if len(new_name)<3:
                    await update.message.reply_text("âŒ Min 3 chars!",reply_markup=get_youtube_keyboard())
                    return STATE_INPUT
                await update.message.reply_text("â³ Changing name...",reply_markup=get_youtube_keyboard())
                jwt_res=get_jwt_direct(context.user_data["token"])
                if jwt_res["ok"]:
                    jwt_token=jwt_res["jwt"]; enc=urllib.parse.quote(new_name)
                    try:
                        r=requests.get(f"https://api-info.ffapi.cloud/api/nickname_change?new_nickname={enc}&jwt={jwt_token}",timeout=12)
                        if "success" in r.text.lower() or "changed" in r.text.lower(): await update.message.reply_text(f"âœ… Name Changed to {new_name}",reply_markup=get_youtube_keyboard())
                        else: await update.message.reply_text(f"âš ï¸ Needs Card 39D+200GT: {context.user_data['old_nick']} -> {new_name}",reply_markup=get_youtube_keyboard())
                    except Exception as e: await update.message.reply_text(f"âŒ {e}",reply_markup=get_youtube_keyboard())
                else: await update.message.reply_text(f"âŒ JWT Failed: {jwt_res['error']}",reply_markup=get_youtube_keyboard())
                await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT
        if flow=="fix_unsub":
            if step=="email":
                email=text.strip()
                if "@" not in email or "." not in email:
                    await update.message.reply_text("âŒ Invalid Email!",reply_markup=get_youtube_keyboard())
                    return STATE_INPUT
                await update.message.reply_text(f"â³ Sending OTP to {email}...",reply_markup=get_youtube_keyboard())
                try:
                    session=requests.Session()
                    headers_base={"User-Agent":"Mozilla/5.0","Referer":"https://sso.garena.com/universal/register?locale=en-SG","Origin":"https://sso.garena.com"}
                    random_user="ZEVRICX"+ "".join(random.choices(string.ascii_uppercase+string.digits,k=4))
                    random_pass=".Nm5TGMfA7JyUyh"+ "".join(random.choices(string.ascii_letters+string.digits,k=2))
                    try: session.get("https://sso.garena.com/universal/register?locale=en-SG",headers=headers_base,timeout=10)
                    except: pass
                    api_url="https://sso.garena.com/api/account/send_verification_code"
                    payload={"email":email,"username":random_user,"password":random_pass,"confirm_password":random_pass,"locale":"en-SG","region":"SG"}
                    resp=session.post(api_url,headers={**headers_base, "Content-Type":"application/json"},json=payload,timeout=12)
                    await update.message.reply_text(f"âœ… OTP Sent to {email} Check inbox+Spam",reply_markup=get_youtube_keyboard())
                except Exception as e:
                    await update.message.reply_text(f"âœ… Attempted {email} Error:{str(e)[:100]}",reply_markup=get_youtube_keyboard())
                await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT
        await update.message.reply_text("ðŸ“‹ Main Menu:",reply_markup=get_reply_keyboard())
        return STATE_INPUT
    except Exception as e:
        print(f"handle_text error: {e}")
        import traceback; traceback.print_exc()
        try: await update.message.reply_text("âŒ Error Use /start",reply_markup=get_reply_keyboard())
        except: pass
        context.user_data.clear()
        return STATE_INPUT

flask_app=Flask(__name__)
@flask_app.route('/')
def home(): return "âœ… Bot Running - v7.0 Anti Captcha + All putkiya.py Options - Fixed"
@flask_app.route('/health')
def health(): return "OK"
app=flask_app
def run_bot():
    if BOT_TOKEN=="YOUR_BOT_TOKEN_HERE": print("BOT_TOKEN not set!"); return
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
        print(f"Bot run_polling failed: {e}"); import traceback; traceback.print_exc(); raise
def _auto_start_bot():
    if BOT_TOKEN=="YOUR_BOT_TOKEN_HERE": return
    def bot_thread_func():
        while True:
            try: run_bot()
            except Exception as e:
                print(f"Bot crash {e} restart 5 sec"); time.sleep(5)
    try: t=threading.Thread(target=bot_thread_func,daemon=True); t.start()
    except: pass
if os.getenv("PORT") or os.getenv("RENDER"):
    _auto_start_bot()
if __name__=="__main__":
    bot_thread=threading.Thread(target=run_bot,daemon=True)
    bot_thread.start()
    port=int(os.environ.get("PORT",10000))
    flask_app.run(host="0.0.0.0",port=port)
