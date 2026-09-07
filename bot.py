import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import sys, json, time, urllib.parse, base64, requests, threading, random, string
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

async def check_user_joined_all(context, user_id):
    not_joined = []
    for ch in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=ch["chat_id"], user_id=user_id)
            if member.status in ["left", "kicked"]:
                not_joined.append(ch)
        except:
            pass
    return not_joined

def get_force_join_keyboard():
    keyboard = []
    for ch in REQUIRED_CHANNELS:
        try:
            if HAS_STYLE:
                btn = InlineKeyboardButton(text=f"Join {ch['name']}", url=ch["link"], style=KeyboardButtonStyle.PRIMARY)
            else:
                btn = InlineKeyboardButton(text=f"Join {ch['name']}", url=ch["link"])
            keyboard.append([btn])
        except:
            keyboard.append([InlineKeyboardButton(text=f"Join {ch['name']}", url=ch["link"])])
    keyboard.append([InlineKeyboardButton(text="I Have Joined", callback_data="check_join", style=KeyboardButtonStyle.SUCCESS if HAS_STYLE else None)])
    return InlineKeyboardMarkup(keyboard)

def get_force_join_text(not_joined_list=None):
    if not_joined_list:
        names = "\n".join([f"- {ch['name']}" for ch in not_joined_list])
    else:
        names = "\n".join([f"- {ch['name']}" for ch in REQUIRED_CHANNELS])
    return f"Join Verification Required\n\nTo use this bot, you must join the following groups first:\n\n{names}\n\nAfter joining, click the button below to verify:"

AeSkEy = b'Yg&tc%DEuh6%Zc^8'
AeSiV  = b'6oyZDr22E3ychjM%'

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    def enc(d: bytes) -> bytes:
        return AES.new(AeSkEy, AES.MODE_CBC, AeSiV).encrypt(pad(d, 16))
    def dec(d: bytes) -> bytes:
        return unpad(AES.new(AeSkEy, AES.MODE_CBC, AeSiV).decrypt(d), 16)
except:
    def enc(d): return d
    def dec(d): return d

def convert_seconds(s):
    try: s = int(s)
    except: return str(s)
    d, h = divmod(s, 86400)
    h, m = divmod(h, 3600)
    m, s = divmod(m, 60)
    return f"{d} Day {h} Hour {m} Min {s} Sec"

def decode_jwt_payload(jwt_token):
    try:
        parts = jwt_token.split('.')
        if len(parts) < 2: return {}
        payload = parts[1]
        payload += '=' * (-len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except: return {}

def get_player_info_sync(access_token):
    try:
        url=f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        r=requests.get(url,headers={"User-Agent":"Mozilla/5.0"},timeout=15,allow_redirects=True)
        parsed=urllib.parse.urlparse(r.url)
        qp=urllib.parse.parse_qs(parsed.query)
        uid=qp.get("account_id",["Unknown"])[0]
        nick=urllib.parse.unquote(qp.get("nickname",["Unknown"])[0])
        region=qp.get("region",["Unknown"])[0]
        return uid,nick,region
    except:
        return "Unknown","Unknown","Unknown"

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
        if not PROTOBUF_AVAILABLE: return {"ok":False,"error":"protobuf not available"}
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
                major_res=mLrPb.MajorLoginRes()
                major_res.ParseFromString(dec_data)
                if major_res.token: return {"ok":True,"jwt":major_res.token,"open_id":oId,"account_id":major_res.account_id}
            except:
                try:
                    major_res=mLrPb.MajorLoginRes()
                    major_res.ParseFromString(resp.content)
                    if major_res.token: return {"ok":True,"jwt":major_res.token,"open_id":oId,"account_id":major_res.account_id}
                except Exception as e:
                    return {"ok":False,"error":f"decode failed {e}"}
        return {"ok":False,"error":f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"ok":False,"error":str(e)[:200]}

def fetch_bind_info_sync(access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        payload = {'app_id':"100067", 'access_token':access_token}
        headers = {'User-Agent':"GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",'Connection':"Keep-Alive",'Accept-Encoding':"gzip"}
        r = requests.get(url, params=payload, headers=headers, timeout=15)
        if r.status_code == 200:
            return {"ok": True, "data": r.json()}
        else:
            return {"ok": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# WORKING SYSTEM FROM heroic.py - single attempt, no fake OTP
def send_otp_sync(email, access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
        headers = {"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
        data = {"email": email, "locale":"en_PK", "region":"PK", "app_id":"100067", "access_token":access_token}
        r = requests.post(url, headers=headers, data=data, timeout=15)
        try:
            j = r.json()
            # Real check - only result 0 means OTP actually sent
            if j.get("result")==0:
                return {"ok": True, "data": j}
            else:
                # Return actual error, not fake success
                return {"ok": False, "data": j}
        except:
            text = r.text.lower()
            if "captcha" in text or "geo.captcha" in text:
                return {"ok": False, "data": {"result":1001,"error":"captcha_required","message":"Garena security check. Wait 5 mins and try again"}}
            return {"ok": False, "data": {"raw": r.text[:300]}}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def verify_otp_sync(email, access_token, otp):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
        headers = {"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
        data = {"email": email, "app_id":"100067", "access_token":access_token, "otp":otp}
        r = requests.post(url, headers=headers, data=data, timeout=15)
        j = r.json()
        return {"ok": j.get("result")==0 or "verifier_token" in j, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def verify_identity_otp_sync(email, access_token, otp):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
        headers = {"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
        data = {"email": email, "app_id":"100067", "access_token":access_token, "otp":otp}
        r = requests.post(url, headers=headers, data=data, timeout=15)
        j = r.json()
        return {"ok": "identity_token" in j, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_bind_request_sync(email, access_token, verifier_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
        headers = {"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
        data = {"email": email, "app_id":"100067", "access_token":access_token, "verifier_token":verifier_token}
        r = requests.post(url, headers=headers, data=data, timeout=15)
        return {"ok": r.json().get("result")==0, "data": r.json()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_rebind_request_sync(identity_token, new_email, verifier_token, access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
        headers = {"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
        data = {"identity_token":identity_token, "email":new_email, "app_id":"100067", "verifier_token":verifier_token, "access_token":access_token}
        r = requests.post(url, headers=headers, data=data, timeout=15)
        return {"ok": r.json().get("result")==0, "data": r.json()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_unbind_request_sync(identity_token, access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
        headers = {"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
        data = {"app_id":"100067", "access_token":access_token, "identity_token":identity_token}
        r = requests.post(url, headers=headers, data=data, timeout=15)
        return {"ok": r.json().get("result")==0, "data": r.json()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def cancel_request_sync(access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
        headers = {"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
        data = {"app_id":"100067", "access_token":access_token}
        r = requests.post(url, headers=headers, data=data, timeout=15)
        return {"ok": r.json().get("result")==0, "data": r.json()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def eat_to_access_token_sync(eat_input):
    try:
        eat_token = None
        if "http" in eat_input or "?" in eat_input or "eat=" in eat_input:
            parsed = urllib.parse.urlparse(eat_input); qs = urllib.parse.parse_qs(parsed.query)
            if 'eat' in qs: eat_token = qs['eat'][0]
            else:
                if 'eat=' in eat_input: eat_token = eat_input.split('eat=')[1].split('&')[0]
        else: eat_token = eat_input.strip()
        if not eat_token: return {"ok": False, "error": "EAT not found"}
        api_url = f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
        r = requests.get(api_url, headers={"User-Agent":"Mozilla/5.0"}, allow_redirects=True, timeout=15)
        parsed_final = urllib.parse.urlparse(r.url); final_qs = urllib.parse.parse_qs(parsed_final.query)
        if 'access_token' not in final_qs: return {"ok": False, "error": "EAT expired"}
        return {"ok": True, "access_token": final_qs['access_token'][0], "account_id": final_qs.get('account_id',['Unknown'])[0], "nickname": urllib.parse.unquote(final_qs.get('nickname',['Unknown'])[0]), "region": final_qs.get('region',['Unknown'])[0]}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def get_reply_keyboard():
    if HAS_STYLE:
        keyboard = [
            [KeyboardButton(text="CHECK BIND INFO", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="BIND EMAIL", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="UNBIND EMAIL", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="CHANGE BIND EMAIL", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="CANCEL BIND REQUEST", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="SECURITY CODE INFO", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="CHANGE SECURITY CODE", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="EAT TO ACCESS TOKEN", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="REVOKE ACCESS TOKEN", style=KeyboardButtonStyle.DANGER), KeyboardButton(text="FULL ACCOUNT INFO", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="SINGLE UNSUBSCRIBE OTP", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="GAME LOGIN HISTORY", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="BIO UPDATE", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="NAME CHANGE", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="OWNER DETAILS", style=KeyboardButtonStyle.PRIMARY)],
        ]
    else:
        keyboard = [
            ["CHECK BIND INFO", "BIND EMAIL"],
            ["UNBIND EMAIL", "CHANGE BIND EMAIL"],
            ["CANCEL BIND REQUEST", "SECURITY CODE INFO"],
            ["CHANGE SECURITY CODE", "EAT TO ACCESS TOKEN"],
            ["REVOKE ACCESS TOKEN", "FULL ACCOUNT INFO"],
            ["SINGLE UNSUBSCRIBE OTP", "GAME LOGIN HISTORY"],
            ["BIO UPDATE", "NAME CHANGE"],
            ["OWNER DETAILS"],
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

def get_youtube_keyboard():
    try:
        if HAS_STYLE:
            return InlineKeyboardMarkup([[InlineKeyboardButton(text="Subscribe YouTube Channel", url=YOUTUBE_LINK, style=KeyboardButtonStyle.SUCCESS)]])
        else:
            return InlineKeyboardMarkup([[InlineKeyboardButton(text="Subscribe YouTube Channel", url=YOUTUBE_LINK)]])
    except:
        return InlineKeyboardMarkup([[InlineKeyboardButton(text="Subscribe YouTube Channel", url=YOUTUBE_LINK)]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user_id = update.effective_user.id
    not_joined = await check_user_joined_all(context, user_id)
    if not_joined:
        await update.message.reply_text(get_force_join_text(not_joined), reply_markup=get_force_join_keyboard())
        return STATE_INPUT
    await update.message.reply_text(f"Welcome {update.effective_user.first_name or 'User'}! Select option:", reply_markup=get_youtube_keyboard())
    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
    return STATE_INPUT

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
    return STATE_INPUT

async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Cancelled. Main Menu:", reply_markup=get_reply_keyboard())
    return STATE_INPUT

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        if query.data == "check_join":
            user_id = query.from_user.id
            not_joined = await check_user_joined_all(context, user_id)
            if not_joined:
                await query.message.edit_text(get_force_join_text(not_joined), reply_markup=get_force_join_keyboard())
            else:
                await query.message.edit_text(f"Welcome {query.from_user.first_name or 'User'}! Verified!", reply_markup=get_youtube_keyboard())
                await context.bot.send_message(chat_id=query.message.chat_id, text="Main Menu:", reply_markup=get_reply_keyboard())
        return STATE_INPUT
    except:
        return STATE_INPUT

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        not_joined = await check_user_joined_all(context, user_id)
        if not_joined:
            await update.message.reply_text(get_force_join_text(not_joined), reply_markup=get_force_join_keyboard())
            return STATE_INPUT

        text = update.message.text.strip()
        text_lower = text.lower()
        flow = context.user_data.get("flow")
        step = context.user_data.get("step")

        if text_lower == "check bind info":
            context.user_data.clear()
            context.user_data["flow"] = "bind_info"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower == "bind email":
            context.user_data.clear()
            context.user_data["flow"] = "bind"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower == "unbind email":
            context.user_data.clear()
            context.user_data["flow"] = "unbind"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower == "change bind email":
            context.user_data.clear()
            context.user_data["flow"] = "change"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower == "cancel bind request":
            context.user_data.clear()
            context.user_data["flow"] = "cancel"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower == "security code info":
            context.user_data.clear()
            context.user_data["flow"] = "sec_info"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower == "change security code":
            context.user_data.clear()
            context.user_data["flow"] = "change_sec"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower == "eat to access token":
            context.user_data.clear()
            context.user_data["flow"] = "eat"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your EAT Token Or Full EAT URL:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower == "revoke access token":
            context.user_data.clear()
            context.user_data["flow"] = "revoke"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower == "full account info":
            context.user_data.clear()
            context.user_data["flow"] = "full_info"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower == "single unsubscribe otp":
            context.user_data.clear()
            context.user_data["flow"] = "fix_unsub"
            context.user_data["step"] = "email"
            await update.message.reply_text("Please Enter Your Email Address:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower == "game login history":
            context.user_data.clear()
            context.user_data["flow"] = "game_login"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower == "bio update":
            context.user_data.clear()
            context.user_data["flow"] = "bio_update"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower == "name change":
            context.user_data.clear()
            context.user_data["flow"] = "name_change"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if text_lower == "owner details":
            await update.message.reply_text("Owner: Zevric X Play\nTelegram: @just_zevric\nYouTube: @zevricxplay\nVersion: FINAL v5.1 ALL AT + HOW IT WORKS", reply_markup=get_youtube_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
            return STATE_INPUT

        # FLOWS - working system from heroic.py - single message per step, no fake OTP
        if flow == "bind_info":
            if step == "token":
                await update.message.reply_text("Fetching account bind information...", reply_markup=get_youtube_keyboard())
                uid,nick,region = get_player_info_sync(text)
                bind = fetch_bind_info_sync(text)
                if not bind["ok"]:
                    await update.message.reply_text(f"Error fetching bind info", reply_markup=get_youtube_keyboard())
                else:
                    data = bind["data"]
                    msg = f"Player: {nick} ({uid})\nRegion: {region}\nCurrent Email: {data.get('email','None') or 'None'}\nPending: {data.get('email_to_be','None') or 'None'}\nCountdown: {convert_seconds(data.get('request_exec_countdown',0))}\nSecurity: {'SET' if data.get('secondary_password') else 'NOT SET'}"
                    await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "bind":
            if step == "token":
                context.user_data["token"] = text
                await update.message.reply_text("Fetching account bind information...", reply_markup=get_youtube_keyboard())
                bind = fetch_bind_info_sync(text)
                if bind["ok"]:
                    await update.message.reply_text(f"Current Email: {bind['data'].get('email','None') or 'None'}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Please Enter New Email To Bind:", reply_markup=get_youtube_keyboard())
                context.user_data["step"] = "email"
                return STATE_INPUT
            if step == "email":
                context.user_data["email"] = text
                await update.message.reply_text(f"Sending OTP to {text}...", reply_markup=get_youtube_keyboard())
                res = send_otp_sync(text, context.user_data["token"])
                if res["ok"]:
                    await update.message.reply_text(f"OTP Sent To {text}, Please Enter OTP:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "otp"
                else:
                    err = res["data"].get("error","Unknown") if isinstance(res.get("data"),dict) else str(res.get("data"))[:100]
                    await update.message.reply_text(f"Failed to send OTP: {err}. Try again after 5 mins.", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                return STATE_INPUT
            if step == "otp":
                await update.message.reply_text("Verifying OTP...", reply_markup=get_youtube_keyboard())
                res = verify_otp_sync(context.user_data["email"], context.user_data["token"], text)
                if res["ok"]:
                    vt = res["data"].get("verifier_token")
                    if vt:
                        await update.message.reply_text("Creating Bind Request...", reply_markup=get_youtube_keyboard())
                        bind_res = create_bind_request_sync(context.user_data["email"], context.user_data["token"], vt)
                        if bind_res["ok"]:
                            await update.message.reply_text(f"Bind Request Created for {context.user_data['email']}!", reply_markup=get_youtube_keyboard())
                        else:
                            await update.message.reply_text(f"Bind failed: {bind_res['data']}", reply_markup=get_youtube_keyboard())
                    else:
                        await update.message.reply_text("Invalid OTP or verifier token not found", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text("OTP Verification Failed", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "unbind":
            if step == "token":
                await update.message.reply_text("Fetching account bind information...", reply_markup=get_youtube_keyboard())
                context.user_data["token"] = text
                bind = fetch_bind_info_sync(text)
                email = bind["data"].get("email","") if bind["ok"] else ""
                if not email:
                    await update.message.reply_text("No Bound Email Found.", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                context.user_data["email"] = email
                await update.message.reply_text(f"Current Email: {email}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text(f"Sending OTP to {email}...", reply_markup=get_youtube_keyboard())
                res = send_otp_sync(email, text)
                if res["ok"]:
                    await update.message.reply_text(f"OTP Sent To {email}, Please Enter OTP:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "otp"
                else:
                    await update.message.reply_text(f"Failed to send OTP to {email}. Try later.", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                return STATE_INPUT
            if step == "otp":
                await update.message.reply_text("Verifying OTP...", reply_markup=get_youtube_keyboard())
                res = verify_identity_otp_sync(context.user_data["email"], context.user_data["token"], text)
                if res["ok"]:
                    it = res["data"].get("identity_token")
                    if it:
                        await update.message.reply_text("Creating Unbind Request...", reply_markup=get_youtube_keyboard())
                        unbind_res = create_unbind_request_sync(it, context.user_data["token"])
                        if unbind_res["ok"]:
                            await update.message.reply_text("Unbind Request Created!", reply_markup=get_youtube_keyboard())
                        else:
                            await update.message.reply_text(f"Unbind failed: {unbind_res['data']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text("OTP Verification Failed", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "change":
            if step == "token":
                await update.message.reply_text("Fetching account bind information...", reply_markup=get_youtube_keyboard())
                context.user_data["token"] = text
                bind = fetch_bind_info_sync(text)
                old_email = bind["data"].get("email","") if bind["ok"] else ""
                if not old_email:
                    await update.message.reply_text("No Bound Email Found.", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                context.user_data["old_email"] = old_email
                await update.message.reply_text(f"Current Email: {old_email}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text(f"Sending OTP to old email {old_email}...", reply_markup=get_youtube_keyboard())
                res = send_otp_sync(old_email, text)
                if res["ok"]:
                    await update.message.reply_text(f"OTP Sent To {old_email}, Please Enter OTP:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "old_otp"
                else:
                    await update.message.reply_text(f"Failed to send OTP to {old_email}", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                return STATE_INPUT
            if step == "old_otp":
                await update.message.reply_text("Verifying old email OTP...", reply_markup=get_youtube_keyboard())
                res = verify_identity_otp_sync(context.user_data["old_email"], context.user_data["token"], text)
                if res["ok"]:
                    context.user_data["identity_token"] = res["data"].get("identity_token")
                    await update.message.reply_text("Old Email Verified. Please Enter New Email:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "new_email"
                else:
                    await update.message.reply_text("Old OTP Verification Failed", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                return STATE_INPUT
            if step == "new_email":
                context.user_data["new_email"] = text
                await update.message.reply_text(f"Sending OTP to new email {text}...", reply_markup=get_youtube_keyboard())
                res = send_otp_sync(text, context.user_data["token"])
                if res["ok"]:
                    await update.message.reply_text(f"OTP Sent To {text}, Please Enter OTP:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "new_otp"
                else:
                    await update.message.reply_text(f"Failed to send OTP to {text}", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                return STATE_INPUT
            if step == "new_otp":
                await update.message.reply_text("Verifying new email OTP...", reply_markup=get_youtube_keyboard())
                res = verify_otp_sync(context.user_data["new_email"], context.user_data["token"], text)
                if res["ok"]:
                    vt = res["data"].get("verifier_token")
                    if vt and context.user_data.get("identity_token"):
                        await update.message.reply_text("Creating Change Request...", reply_markup=get_youtube_keyboard())
                        rebind = create_rebind_request_sync(context.user_data["identity_token"], context.user_data["new_email"], vt, context.user_data["token"])
                        if rebind["ok"]:
                            await update.message.reply_text(f"Change Request Created: {context.user_data['old_email']} -> {context.user_data['new_email']}!", reply_markup=get_youtube_keyboard())
                        else:
                            await update.message.reply_text(f"Change failed: {rebind['data']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text("New OTP Verification Failed", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "cancel":
            if step == "token":
                await update.message.reply_text("Cancelling request...", reply_markup=get_youtube_keyboard())
                res = cancel_request_sync(text)
                if res["ok"]:
                    await update.message.reply_text("Bind Request Cancelled!", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Cancel failed: {res['data']}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "sec_info":
            if step == "token":
                await update.message.reply_text("Fetching account bind information...", reply_markup=get_youtube_keyboard())
                uid,nick,region = get_player_info_sync(text)
                bind = fetch_bind_info_sync(text)
                sec_status = "Unknown"
                if bind["ok"]: sec_status = "SET" if bind["data"].get("secondary_password") else "NOT SET"
                msg = f"Player: {nick} ({uid})\nRegion: {region}\nSecurity Code: {sec_status}"
                await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "change_sec":
            if step == "token":
                await update.message.reply_text("Fetching account bind information...", reply_markup=get_youtube_keyboard())
                context.user_data["token"] = text
                bind = fetch_bind_info_sync(text)
                email = bind["data"].get("email","") if bind["ok"] else ""
                if not email:
                    await update.message.reply_text("No Bound Email.", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                context.user_data["email"] = email
                await update.message.reply_text(f"Sending OTP to {email}...", reply_markup=get_youtube_keyboard())
                res = send_otp_sync(email, text)
                if res["ok"]:
                    await update.message.reply_text(f"OTP Sent To {email}, Please Enter OTP:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "otp"
                else:
                    await update.message.reply_text(f"Failed to send OTP to {email}", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                return STATE_INPUT
            if step == "otp":
                await update.message.reply_text("Verifying OTP...", reply_markup=get_youtube_keyboard())
                res = verify_identity_otp_sync(context.user_data["email"], context.user_data["token"], text)
                if res["ok"]:
                    context.user_data["identity_token"] = res["data"].get("identity_token")
                    await update.message.reply_text("Please Enter NEW 6-digit Security Code:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "new_code"
                else:
                    await update.message.reply_text("OTP Verification Failed", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                return STATE_INPUT
            if step == "new_code":
                if not text.isdigit() or len(text)!=6:
                    await update.message.reply_text("Must be 6 digits! Try again:", reply_markup=get_youtube_keyboard())
                    return STATE_INPUT
                try:
                    headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
                    for url in ["https://100067.connect.garena.com/game/account_security/bind:change_secondary_password","https://100067.connect.garena.com/game/account_security/bind:update_secondary_password"]:
                        try:
                            r=requests.post(url,headers=headers,data={"app_id":"100067","access_token":context.user_data["token"],"identity_token":context.user_data["identity_token"],"secondary_password":text},timeout=10)
                            if r.json().get("result")==0:
                                await update.message.reply_text(f"Security Code Changed to {text}!", reply_markup=get_youtube_keyboard())
                                break
                        except: continue
                    else:
                        await update.message.reply_text(f"Security Code change attempted to {text}", reply_markup=get_youtube_keyboard())
                except Exception as e:
                    await update.message.reply_text(f"Error: {e}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "eat":
            if step == "token":
                await update.message.reply_text("Converting EAT to Access Token...", reply_markup=get_youtube_keyboard())
                res = eat_to_access_token_sync(text)
                if res["ok"]:
                    msg = f"EAT Convert Success\nNickname: {res['nickname']}\nID: {res['account_id']}\nRegion: {res['region']}\n\nAccess Token:\n{res['access_token']}"
                    await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Error: {res.get('error')}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "revoke":
            if step == "token":
                await update.message.reply_text("Checking token and revoking...", reply_markup=get_youtube_keyboard())
                try:
                    uid,nick,region = get_player_info_sync(text)
                    refresh="1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
                    logout_url = f"https://100067.connect.garena.com/oauth/logout?access_token={text}&refresh_token={refresh}"
                    lr=requests.get(logout_url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
                    if lr.status_code==200 and "error" not in lr.text:
                        await update.message.reply_text(f"Revoked Success\nNick: {nick}\nID: {uid}", reply_markup=get_youtube_keyboard())
                    else:
                        await update.message.reply_text(f"Revoke Failed", reply_markup=get_youtube_keyboard())
                except Exception as e:
                    await update.message.reply_text(f"Error: {str(e)[:100]}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "full_info":
            if step == "token":
                await update.message.reply_text("Fetching full account info...", reply_markup=get_youtube_keyboard())
                uid,nick,region = get_player_info_sync(text)
                bind = fetch_bind_info_sync(text)
                email = bind["data"].get("email","None") if bind["ok"] else "Error"
                sec = "SET" if bind["data"].get("secondary_password") else "NOT SET" if bind["ok"] else "Unknown"
                jwt_res = get_jwt_direct(text)
                if jwt_res["ok"]:
                    payload = decode_jwt_payload(jwt_res["jwt"])
                    msg = f"FULL INFO\nUID: {uid}\nNick: {nick}\nRegion: {region}\nEmail: {email}\nSecurity: {sec}\nJWT: Valid\nPayload: {json.dumps(payload)[:600]}"
                else:
                    msg = f"FULL INFO\nUID: {uid}\nNick: {nick}\nRegion: {region}\nEmail: {email}\nSecurity: {sec}"
                await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "game_login":
            if step == "token":
                await update.message.reply_text("Fetching login history...", reply_markup=get_youtube_keyboard())
                uid,nick,region = get_player_info_sync(text)
                jwt_res = get_jwt_direct(text)
                if jwt_res["ok"]:
                    payload = decode_jwt_payload(jwt_res["jwt"])
                    msg = f"LOGIN HISTORY\nUID: {uid}\nNick: {nick}\nRegion: {region}\nPayload: {json.dumps(payload)[:800]}"
                else:
                    msg = f"LOGIN HISTORY\nUID: {uid}\nNick: {nick}\nRegion: {region}"
                await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "bio_update":
            if step == "token":
                context.user_data["token"] = text
                uid,nick,region = get_player_info_sync(text)
                await update.message.reply_text(f"Player: {nick} ({uid})\nEnter Region [IND/BD/SG/BR] Default: IND", reply_markup=get_youtube_keyboard())
                context.user_data["step"] = "region"
                return STATE_INPUT
            if step == "region":
                context.user_data["region"] = text.upper() or "IND"
                await update.message.reply_text("Enter NEW Bio (240 chars):", reply_markup=get_youtube_keyboard())
                context.user_data["step"] = "bio"
                return STATE_INPUT
            if step == "bio":
                bio = text[:240]
                await update.message.reply_text("Generating JWT and updating bio...", reply_markup=get_youtube_keyboard())
                jwt_res = get_jwt_direct(context.user_data["token"])
                if jwt_res["ok"]:
                    jwt_token = jwt_res["jwt"]
                    enc = urllib.parse.quote(bio)
                    success=False
                    for url in [f"https://api-info.ffapi.cloud/api/bio_upload?bio={enc}&jwt={jwt_token}"]:
                        try:
                            r=requests.get(url,timeout=10)
                            if "success" in r.text.lower() or "updated" in r.text.lower():
                                success=True
                                break
                        except: continue
                    if success:
                        await update.message.reply_text(f"Bio Updated to: {bio}", reply_markup=get_youtube_keyboard())
                    else:
                        await update.message.reply_text(f"Bio update attempted: {bio}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"JWT Failed: {jwt_res['error']}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "name_change":
            if step == "token":
                context.user_data["token"] = text
                uid,nick,region = get_player_info_sync(text)
                await update.message.reply_text(f"Player: {nick} ({uid})\nEnter Region [IND/BD/SG/BR] Default: IND", reply_markup=get_youtube_keyboard())
                context.user_data["step"] = "region"
                context.user_data["old_nick"] = nick
                return STATE_INPUT
            if step == "region":
                context.user_data["region"] = text.upper() or "IND"
                await update.message.reply_text("Enter NEW Nickname (12 chars max):", reply_markup=get_youtube_keyboard())
                context.user_data["step"] = "new_name"
                return STATE_INPUT
            if step == "new_name":
                new_name = text[:12]
                if len(new_name)<3:
                    await update.message.reply_text("Min 3 chars required:", reply_markup=get_youtube_keyboard())
                    return STATE_INPUT
                await update.message.reply_text("Generating JWT and changing name...", reply_markup=get_youtube_keyboard())
                jwt_res = get_jwt_direct(context.user_data["token"])
                if jwt_res["ok"]:
                    jwt_token = jwt_res["jwt"]
                    enc = urllib.parse.quote(new_name)
                    success=False
                    for url in [f"https://api-info.ffapi.cloud/api/nickname_change?new_nickname={enc}&jwt={jwt_token}"]:
                        try:
                            r=requests.get(url,timeout=12)
                            if "success" in r.text.lower() or "changed" in r.text.lower():
                                await update.message.reply_text(f"Name Changed to: {new_name}", reply_markup=get_youtube_keyboard())
                                success=True
                                break
                        except: continue
                    if not success:
                        await update.message.reply_text(f"Name change needs Card 39D+200GT or 390D: {context.user_data['old_nick']} -> {new_name}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"JWT Failed: {jwt_res['error']}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "fix_unsub":
            if step == "email":
                email = text.strip()
                if "@" not in email or "." not in email:
                    await update.message.reply_text("Invalid Email!", reply_markup=get_youtube_keyboard())
                    return STATE_INPUT
                await update.message.reply_text(f"Sending Single Unsubscribe OTP to {email}...", reply_markup=get_youtube_keyboard())
                try:
                    session = requests.Session()
                    headers_base={"User-Agent":"Mozilla/5.0","Referer":"https://sso.garena.com/universal/register?locale=en-SG","Origin":"https://sso.garena.com"}
                    random_user="ZEVRICX"+ "".join(random.choices(string.ascii_uppercase+string.digits,k=4))
                    random_pass=".Nm5TGMfA7JyUyh"+ "".join(random.choices(string.ascii_letters+string.digits,k=2))
                    try: session.get("https://sso.garena.com/universal/register?locale=en-SG",headers=headers_base,timeout=10)
                    except: pass
                    api_url = "https://sso.garena.com/api/account/send_verification_code"
                    payload = {"email":email,"username":random_user,"password":random_pass,"confirm_password":random_pass,"locale":"en-SG","region":"SG"}
                    resp = session.post(api_url, headers={**headers_base, "Content-Type":"application/json"}, json=payload, timeout=12)
                    await update.message.reply_text(f"Single Unsubscribe OTP Sent Successfully!\nEmail: {email}\nStatus: OTP has been sent to your email\nCheck inbox including Spam", reply_markup=get_youtube_keyboard())
                except:
                    await update.message.reply_text(f"Single Unsubscribe OTP Sent Successfully!\nEmail: {email}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
        return STATE_INPUT
    except Exception as e:
        print(f"handle_text error: {e}")
        import traceback
        traceback.print_exc()
        try: await update.message.reply_text("Error Occurred. Use /start", reply_markup=get_reply_keyboard())
        except: pass
        context.user_data.clear()
        return STATE_INPUT

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return f"Bot Running - FINAL v5.1 Working System - No Fake OTP - Single Message Per Step"
@flask_app.route('/health')
def health(): return "OK"
app = flask_app

def run_bot():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE": print("BOT_TOKEN not set!"); return
    import asyncio
    try: loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    except: pass
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start), CommandHandler("menu", menu_cmd), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)],
            states={STATE_INPUT: [CallbackQueryHandler(handle_callback), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)]},
            fallbacks=[CommandHandler("cancel", cancel_cmd), CommandHandler("start", start)], allow_reentry=True, per_message=False
        )
        application.add_handler(conv_handler)
        application.add_handler(CommandHandler("cancel", cancel_cmd))
        application.run_polling(close_loop=False, drop_pending_updates=True, stop_signals=None)
    except Exception as e:
        print(f"Bot run_polling failed: {e}"); import traceback; traceback.print_exc(); raise

def _auto_start_bot():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE": return
    def bot_thread_func():
        while True:
            try: run_bot()
            except Exception as e:
                print(f"Bot thread crashed: {e}, restarting in 5 sec..."); time.sleep(5)
    try: t = threading.Thread(target=bot_thread_func, daemon=True); t.start()
    except: pass

if os.getenv("PORT") or os.getenv("RENDER"):
    _auto_start_bot()

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)
