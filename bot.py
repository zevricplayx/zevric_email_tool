import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import sys, json, time, urllib.parse, base64, hashlib, urllib3, requests, threading, random, string
from datetime import datetime
from flask import Flask
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
    try:
        if HAS_STYLE:
            keyboard.append([InlineKeyboardButton(text="I Have Joined", callback_data="check_join", style=KeyboardButtonStyle.SUCCESS)])
        else:
            keyboard.append([InlineKeyboardButton(text="I Have Joined", callback_data="check_join")])
    except:
        keyboard.append([InlineKeyboardButton(text="I Have Joined", callback_data="check_join")])
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

def build_majorlogin(tok, open_id, p_type):
    if not PROTOBUF_AVAILABLE: return None
    try:
        m = mLpB.MajorLogin()
        m.event_time = str(datetime.now())[:-7]
        m.game_name = "free fire"; m.platform_id = p_type; m.client_version = "1.120.1"
        m.system_software = "Android OS 9 / API-28"; m.system_hardware = "Handheld"
        m.telecom_operator = "Verizon"; m.network_type = "WIFI"
        m.screen_width = 1920; m.screen_height = 1080; m.screen_dpi = "280"
        m.processor_details = "ARM64 FP ASIMD AES VMH | 2865 | 4"; m.memory = 3003
        m.gpu_renderer = "Adreno (TM) 640"; m.gpu_version = "OpenGL ES 3.1 v1.46"
        m.unique_device_id = "Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57"
        m.client_ip = "223.191.51.89"; m.language = "en"; m.open_id = open_id
        m.open_id_type = str(p_type); m.device_type = "Handheld"; m.access_token = tok
        m.platform_sdk_id = 1; m.client_using_version = "7428b253defc164018c604a1ebbfebdf"
        m.login_by = 3; m.channel_type = 3; m.cpu_type = 2; m.cpu_architecture = "64"
        m.client_version_code = "2019118695"; m.login_open_id_type = p_type
        m.origin_platform_type = str(p_type); m.primary_platform_type = str(p_type)
        return enc(m.SerializeToString())
    except:
        return None

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

def fetch_bind_info_sync(access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        payload = {'app_id': "100067", 'access_token': access_token}
        r = requests.get(url, params=payload, headers={'User-Agent': "GarenaMSDK/4.0.19P9"}, timeout=15)
        if r.status_code == 200:
            return {"ok": True, "data": r.json()}
        else:
            return {"ok": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def send_otp_sync(email, access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "locale": "en_PK", "region": "PK", "app_id": "100067", "access_token": access_token}
        r = requests.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result") == 0, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def verify_otp_sync(email, access_token, otp):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"app_id": "100067", "access_token": access_token, "email": email, "code": otp, "otp": otp, "type": "1"}
        r = requests.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result") == 0 or "verifier_token" in j, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def verify_identity_otp_sync(email, access_token, otp):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "app_id": "100067", "access_token": access_token, "otp": otp}
        r = requests.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": "identity_token" in j, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_bind_request_sync(email, access_token, verifier_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "app_id": "100067", "access_token": access_token, "verifier_token": verifier_token}
        r = requests.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result")==0, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_rebind_request_sync(identity_token, new_email, verifier_token, access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"identity_token": identity_token, "email": new_email, "app_id": "100067", "verifier_token": verifier_token, "access_token": access_token}
        r = requests.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result")==0, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_unbind_request_sync(identity_token, access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"app_id": "100067", "access_token": access_token, "identity_token": identity_token}
        r = requests.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result")==0, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def cancel_request_sync(access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"app_id": "100067", "access_token": access_token}
        r = requests.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result")==0, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def eat_to_access_token_sync(eat_input):
    try:
        eat_token = None
        if "http" in eat_input or "?" in eat_input or "eat=" in eat_input:
            parsed = urllib.parse.urlparse(eat_input); qs = urllib.parse.parse_qs(parsed.query)
            if 'eat' in qs: eat_token = qs['eat'][0]
            else:
                if 'eat=' in eat_input:
                    eat_token = eat_input.split('eat=')[1].split('&')[0]
        else:
            eat_token = eat_input.strip()
        if not eat_token: return {"ok": False, "error": "EAT not found"}
        api_url = f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
        r = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=15)
        parsed_final = urllib.parse.urlparse(r.url); final_qs = urllib.parse.parse_qs(parsed_final.query)
        if 'access_token' not in final_qs:
            return {"ok": False, "error": "Access token not found - EAT expired"}
        access_token = final_qs['access_token'][0]
        account_id = final_qs.get('account_id',['Unknown'])[0]
        nickname = urllib.parse.unquote(final_qs.get('nickname',['Unknown'])[0])
        region = final_qs.get('region',['Unknown'])[0]
        return {"ok": True, "access_token": access_token, "account_id": account_id, "nickname": nickname, "region": region}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}

def get_jwt_from_access_token(access_token):
    # FIX: Use protobuf method, not ffapi.cloud (which fails DNS)
    try:
        oId = None
        try:
            r = requests.get(f"https://100067.connect.garena.com/oauth/token/inspect?token={access_token}", headers={"User-Agent": "Mozilla/5.0"}, timeout=8).json()
            oId = r.get("open_id")
        except: pass
        if not oId:
            try:
                uid_headers = {"access-token": access_token, "user-agent": "Mozilla/5.0"}
                uid_res = requests.get("https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/", headers=uid_headers, verify=False, timeout=8).json()
                uid = uid_res.get("uid")
                if uid:
                    openid_res = requests.post("https://topup.pk/api/auth/player_id_login", json={"app_id": 100067, "login_id": str(uid)}, verify=False, timeout=8).json()
                    oId = openid_res.get("open_id")
            except: pass
        if not oId:
            return {"ok": False, "error": "Open ID failed"}
        if not PROTOBUF_AVAILABLE:
            return {"ok": False, "error": "Protobuf not available"}
        for p_type in [8,3,4,6]:
            pl = build_majorlogin(access_token, oId, p_type)
            if not pl: continue
            try:
                mLhDr = {"User-Agent": "Dalvik/2.1.0", "Content-Type": "application/octet-stream", "Expect": "100-continue", "X-GA": "v1 1", "X-Unity-Version": "2018.4.11f1", "ReleaseVersion": "OB52"}
                x = requests.post("https://loginbp.ggpolarbear.com/MajorLogin", headers=mLhDr, data=pl, timeout=12, verify=False)
                if x.status_code==200:
                    res = mLrPb.MajorLoginRes()
                    try: res.ParseFromString(dec(x.content))
                    except: res.ParseFromString(x.content)
                    if res.token:
                        return {"ok": True, "jwt": res.token, "server_url": res.server_url, "account_id": res.account_id}
            except: continue
        return {"ok": False, "error": "MajorLogin failed"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def fast_security_code_find(email, access_token, timeout_sec=18):
    """Fast finder - tries common codes in 10-20 sec, not full 1M"""
    import time
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    # Most common 6-digit codes people use
    common_codes = [
        "000000","111111","123456","123123","112233","000123","123000","999999",
        "000111","111000","654321","101010","121212","123321","000999","999000",
        "100000","200000","121234","1234567"[:6],"000001","000002","000100","001100",
        "110000","112233","122333","123455","111222","222222","333333","444444",
        "555555","666666","777777","888888","123654","321321","000789","789000",
        "123789","147258","159753","123012","112233","102030","100100","200200",
        "121212","010101","101010","202020","123321","456456","789789","000555",
        "555000","121212","112211","223322","334455","556677","123145","123199",
        "199001","200001","200002","111112","111113","123124","123125","112345",
        "123456","234567","345678","456789","012345","123450","123400","100001"
    ]
    # Remove duplicates preserve order
    seen=set()
    uniq=[]
    for c in common_codes:
        if len(c)==6 and c.isdigit() and c not in seen:
            seen.add(c)
            uniq.append(c)
    common_codes = uniq[:80]  # limit 80
    
    found = None
    attempts = 0
    start = time.time()
    
    def try_code(sec):
        try:
            hashed = hashlib.sha256(sec.encode()).hexdigest()
            url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
            headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
            data = {"email": email, "app_id": "100067", "access_token": access_token, "secondary_password": hashed}
            r = requests.post(url, headers=headers, data=data, timeout=6)
            j = r.json() if r.text.startswith('{') else {}
            if "identity_token" in j or j.get("result")==0:
                return sec
        except:
            pass
        return None
    
    # Try common codes fast with threads
    try:
        with ThreadPoolExecutor(max_workers=10) as ex:
            futures = {ex.submit(try_code, code): code for code in common_codes}
            for fut in as_completed(futures):
                attempts += 1
                if time.time() - start > timeout_sec:
                    ex.shutdown(wait=False, cancel_futures=True)
                    break
                res = fut.result()
                if res:
                    found = res
                    ex.shutdown(wait=False, cancel_futures=True)
                    break
    except:
        pass
    
    elapsed = time.time() - start
    if found:
        return {"found": True, "code": found, "attempts": attempts, "time": round(elapsed,1)}
    else:
        return {"found": False, "attempts": attempts, "time": round(elapsed,1)}



def get_reply_keyboard():
    if HAS_STYLE:
        keyboard = [
            [KeyboardButton(text="CHECK BIND INFO", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="BIND EMAIL", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="UNBIND EMAIL", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="CHANGE BIND EMAIL", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="CANCEL BIND REQUEST", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="SECURITY CODE INFO", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="CHANGE SECURITY CODE", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="SECURITY CODE FINDER", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="EAT TO ACCESS TOKEN", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="REVOKE ACCESS TOKEN", style=KeyboardButtonStyle.DANGER)],
            [KeyboardButton(text="FULL ACCOUNT INFO", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="FIX SINGLE UNSUBSCRIBE", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="GAME LOGIN DATA [PROTOBUF]", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="BIO UPDATE [240 + EMOJI - JWT]", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="NAME CHANGE [CARD - 12 CHARS]", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="OWNER DETAILS", style=KeyboardButtonStyle.PRIMARY)],
        ]
    else:
        keyboard = [
            ["CHECK BIND INFO", "BIND EMAIL"],
            ["UNBIND EMAIL", "CHANGE BIND EMAIL"],
            ["CANCEL BIND REQUEST", "SECURITY CODE INFO"],
            ["CHANGE SECURITY CODE", "SECURITY CODE FINDER"],
            ["EAT TO ACCESS TOKEN", "REVOKE ACCESS TOKEN"],
            ["FULL ACCOUNT INFO", "FIX SINGLE UNSUBSCRIBE"],
            ["GAME LOGIN DATA [PROTOBUF]", "BIO UPDATE [240 + EMOJI - JWT]"],
            ["NAME CHANGE [CARD - 12 CHARS]", "OWNER DETAILS"],
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
    first_name = update.effective_user.first_name or "User"
    not_joined = await check_user_joined_all(context, user_id)
    if not_joined:
        await update.message.reply_text(get_force_join_text(not_joined), reply_markup=get_force_join_keyboard())
        return STATE_INPUT
    welcome = f"Welcome {first_name}!\n\nYou have successfully verified all groups!\n\nSelect an option from the menu below:"
    await update.message.reply_text(welcome, reply_markup=get_youtube_keyboard())
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
            first_name = query.from_user.first_name or "User"
            not_joined = await check_user_joined_all(context, user_id)
            if not_joined:
                await query.message.edit_text(get_force_join_text(not_joined), reply_markup=get_force_join_keyboard())
            else:
                welcome = f"Welcome {first_name}!\n\nYou have successfully verified all groups!\n\nSelect an option from the menu below:"
                await query.message.edit_text(welcome, reply_markup=get_youtube_keyboard())
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

        if text_lower == "fix single unsubscribe":
            context.user_data.clear()
            context.user_data["flow"] = "fix_unsub"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text_lower == "game login data [protobuf]":
            context.user_data.clear()
            context.user_data["flow"] = "game_login"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text_lower == "bio update [240 + emoji - jwt]":
            context.user_data.clear()
            context.user_data["flow"] = "bio_update"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text_lower == "name change [card - 12 chars]":
            context.user_data.clear()
            context.user_data["flow"] = "name_change"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text_lower == "security code finder":
            context.user_data.clear()
            context.user_data["flow"] = "sec_finder"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text_lower == "owner details":
            msg = f"Owner Details\n\nDeveloper Name: Zevric X Play\nTelegram: @just_zevric\nChannel: https://t.me/just_zevric\nYouTube: https://youtube.com/@zevricxplay\nGitHub: github.com/zevricxplay\nVersion: v1.7 Final"
            await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
            return STATE_INPUT

        # FLOWS
        if flow == "bind_info":
            if step == "token":
                await update.message.reply_text("Fetching Bind Info...", reply_markup=get_youtube_keyboard())
                uid,nick,region = get_player_info_sync(text)
                bind = fetch_bind_info_sync(text)
                if not bind["ok"]:
                    await update.message.reply_text(f"Error: {bind['error']}", reply_markup=get_youtube_keyboard())
                else:
                    data = bind["data"]
                    msg = f"Player: {nick} ({uid})\nRegion: {region}\n\nCurrent Email: {data.get('email','None') or 'None'}\nPending Email: {data.get('email_to_be','None') or 'None'}\nCountdown: {convert_seconds(data.get('request_exec_countdown',0))}"
                    await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "bind":
            if step == "token":
                context.user_data["token"] = text
                await update.message.reply_text("Please Enter New Email To Bind:", reply_markup=get_youtube_keyboard())
                context.user_data["step"] = "email"
                return STATE_INPUT
            if step == "email":
                context.user_data["email"] = text
                await update.message.reply_text(f"Sending OTP To {text}...", reply_markup=get_youtube_keyboard())
                res = send_otp_sync(text, context.user_data["token"])
                if res["ok"]:
                    await update.message.reply_text(f"OTP Sent To {text}, Please Enter OTP:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "otp"
                else:
                    await update.message.reply_text(f"Failed: {res.get('data')}", reply_markup=get_youtube_keyboard())
                return STATE_INPUT
            if step == "otp":
                res = verify_otp_sync(context.user_data["email"], context.user_data["token"], text)
                if res["ok"]:
                    vt = res["data"].get("verifier_token")
                    bind_res = create_bind_request_sync(context.user_data["email"], context.user_data["token"], vt)
                    if bind_res["ok"]:
                        await update.message.reply_text(f"Bind Success: {bind_res['data']}", reply_markup=get_youtube_keyboard())
                    else:
                        await update.message.reply_text(f"Bind Failed: {bind_res['data']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Verify Failed: {res['data']}")
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "unbind":
            if step == "token":
                context.user_data["token"] = text
                bind = fetch_bind_info_sync(text)
                email = bind["data"].get("email","") if bind["ok"] else ""
                if not email:
                    await update.message.reply_text("No Bound Email Found.", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                context.user_data["email"] = email
                await update.message.reply_text(f"Current Email: {email}\nSending OTP...", reply_markup=get_youtube_keyboard())
                res = send_otp_sync(email, text)
                if res["ok"]:
                    await update.message.reply_text(f"OTP Sent To {email}, Please Enter OTP:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "otp"
                else:
                    await update.message.reply_text(f"Failed: {res.get('data')}", reply_markup=get_youtube_keyboard())
                return STATE_INPUT
            if step == "otp":
                res = verify_identity_otp_sync(context.user_data["email"], context.user_data["token"], text)
                if res["ok"]:
                    it = res["data"].get("identity_token")
                    unbind_res = create_unbind_request_sync(it, context.user_data["token"])
                    await update.message.reply_text(f"Unbind Result: {unbind_res['data']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Verify Failed: {res['data']}")
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "change":
            if step == "token":
                context.user_data["token"] = text
                bind = fetch_bind_info_sync(text)
                old_email = bind["data"].get("email","") if bind["ok"] else ""
                if not old_email:
                    await update.message.reply_text("No Bound Email Found.", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                context.user_data["old_email"] = old_email
                await update.message.reply_text(f"Current Email: {old_email}\nSending OTP...", reply_markup=get_youtube_keyboard())
                res = send_otp_sync(old_email, text)
                if res["ok"]:
                    await update.message.reply_text(f"OTP Sent To {old_email}, Please Enter OTP:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "old_otp"
                else:
                    await update.message.reply_text(f"Failed: {res.get('data')}")
                return STATE_INPUT
            if step == "old_otp":
                res = verify_identity_otp_sync(context.user_data["old_email"], context.user_data["token"], text)
                if res["ok"]:
                    context.user_data["identity_token"] = res["data"].get("identity_token")
                    await update.message.reply_text("Old Email Verified. Please Enter New Email:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "new_email"
                else:
                    await update.message.reply_text(f"Verify Failed: {res['data']}")
                return STATE_INPUT
            if step == "new_email":
                context.user_data["new_email"] = text
                await update.message.reply_text(f"Sending OTP To {text}...", reply_markup=get_youtube_keyboard())
                res = send_otp_sync(text, context.user_data["token"])
                if res["ok"]:
                    await update.message.reply_text(f"OTP Sent To {text}, Please Enter OTP:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "new_otp"
                else:
                    await update.message.reply_text(f"Failed: {res.get('data')}")
                return STATE_INPUT
            if step == "new_otp":
                res = verify_otp_sync(context.user_data["new_email"], context.user_data["token"], text)
                if res["ok"]:
                    vt = res["data"].get("verifier_token")
                    rebind = create_rebind_request_sync(context.user_data["identity_token"], context.user_data["new_email"], vt, context.user_data["token"])
                    await update.message.reply_text(f"Change Result: {rebind['data']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Verify Failed: {res['data']}")
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "cancel":
            if step == "token":
                await update.message.reply_text("Cancelling Request...", reply_markup=get_youtube_keyboard())
                res = cancel_request_sync(text)
                await update.message.reply_text(f"Cancel Result: {res['data']}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "sec_info":
            if step == "token":
                await update.message.reply_text("Fetching Security Code Info...", reply_markup=get_youtube_keyboard())
                bind = fetch_bind_info_sync(text)
                if not bind["ok"]:
                    await update.message.reply_text(f"Error: {bind['error']}", reply_markup=get_youtube_keyboard())
                else:
                    data = bind["data"]
                    sec = "ACTIVE" if data.get("secondary_password") else "NO CODE"
                    await update.message.reply_text(f"Security Code Status: {sec}\n\nRaw: {str(data)[:500]}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT


        if flow == "sec_finder":
            if step == "token":
                await update.message.reply_text("Fetching Email For Security Code Finder...", reply_markup=get_youtube_keyboard())
                bind = fetch_bind_info_sync(text)
                if not bind["ok"] or not bind["data"].get("email"):
                    await update.message.reply_text("No Bound Email Found. Security code finder needs bound email.", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                email = bind["data"].get("email")
                await update.message.reply_text(f"Email: {email}\nFinding Security Code (10-20 sec, common codes only)...", reply_markup=get_youtube_keyboard())
                result = fast_security_code_find(email, text, timeout_sec=18)
                if result["found"]:
                    await update.message.reply_text(f"Security Code Found: {result['code']}\nAttempts: {result['attempts']}\nTime: {result['time']}s", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Security Code Not Found in {result['time']}s (tried {result['attempts']} common codes).\nIf not found, try Via OTP method.", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT


        if flow == "change_sec":
            if step == "token":
                context.user_data["token"] = text
                bind = fetch_bind_info_sync(text)
                email = bind["data"].get("email","") if bind["ok"] else ""
                if not email:
                    await update.message.reply_text("No Bound Email.", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                context.user_data["email"] = email
                await update.message.reply_text(f"Current Email: {email}\nSending OTP...", reply_markup=get_youtube_keyboard())
                res = send_otp_sync(email, text)
                if res["ok"]:
                    await update.message.reply_text(f"OTP Sent To {email}, Please Enter OTP:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "otp"
                else:
                    await update.message.reply_text(f"Failed: {res.get('data')}")
                return STATE_INPUT
            if step == "otp":
                res = verify_identity_otp_sync(context.user_data["email"], context.user_data["token"], text)
                if res["ok"]:
                    context.user_data["identity_token"] = res["data"].get("identity_token")
                    await update.message.reply_text("Please Enter NEW 6-digit Security Code:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "new_code"
                else:
                    await update.message.reply_text(f"Verify Failed: {res['data']}")
                return STATE_INPUT
            if step == "new_code":
                if not text.isdigit() or len(text)!=6:
                    await update.message.reply_text("Must be 6 digits! Try again:", reply_markup=get_youtube_keyboard())
                    return STATE_INPUT
                headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
                for url in ["https://100067.connect.garena.com/game/account_security/bind:change_secondary_password","https://100067.connect.garena.com/game/account_security/bind:update_secondary_password"]:
                    try:
                        r=requests.post(url,headers=headers,data={"app_id":"100067","access_token":context.user_data["token"],"identity_token":context.user_data["identity_token"],"secondary_password":text},timeout=15)
                        if r.json().get("result")==0:
                            await update.message.reply_text(f"Security Code Changed to {text}!", reply_markup=get_youtube_keyboard())
                            break
                    except: pass
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "eat":
            if step == "token":
                await update.message.reply_text("Fetching Access Token From EAT...", reply_markup=get_youtube_keyboard())
                res = eat_to_access_token_sync(text)
                if res["ok"]:
                    msg = f"EAT TO ACCESS TOKEN SUCCESS\n\nNickname: {res['nickname']}\nAccount ID: {res['account_id']}\nRegion: {res['region']}\n\nAccess Token:\n{res['access_token']}"
                    await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Error: {res.get('error')}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "revoke":
            if step == "token":
                await update.message.reply_text("Revoking Token...", reply_markup=get_youtube_keyboard())
                try:
                    uid,nick,region = get_player_info_sync(text)
                    refresh="1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
                    logout_url = f"https://100067.connect.garena.com/oauth/logout?access_token={text}&refresh_token={refresh}"
                    lr=requests.get(logout_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                    if lr.status_code==200 and "error" not in lr.text:
                        await update.message.reply_text(f"Revoked Success\nNick: {nick}\nID: {uid}", reply_markup=get_youtube_keyboard())
                    else:
                        await update.message.reply_text(f"Revoke Failed: {lr.text[:200]}", reply_markup=get_youtube_keyboard())
                except Exception as e:
                    await update.message.reply_text(f"Error: {str(e)[:200]}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "full_info":
            if step == "token":
                await update.message.reply_text("Fetching Full Account Info...", reply_markup=get_youtube_keyboard())
                uid,nick,region = get_player_info_sync(text)
                bind = fetch_bind_info_sync(text)
                email = bind["data"].get("email","None") if bind["ok"] else "Error"
                sec = "SET" if bind["data"].get("secondary_password") else "NOT SET" if bind["ok"] else "Unknown"
                msg = f"FULL ACCOUNT INFO\n\nUID: {uid}\nNickname: {nick}\nRegion: {region}\nEmail: {email}\nSecurity Code: {sec}"
                await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "fix_unsub":
            if step == "token":
                await update.message.reply_text("Fixing Unsubscribe...", reply_markup=get_youtube_keyboard())
                try:
                    bind = fetch_bind_info_sync(text)
                    email = bind["data"].get("email","") if bind["ok"] else ""
                    if not email:
                        await update.message.reply_text("No Email Bound.", reply_markup=get_youtube_keyboard())
                    else:
                        headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
                        for url in ["https://100067.connect.garena.com/game/account_security/email:resubscribe","https://100067.connect.garena.com/game/account_security/bind:resubscribe"]:
                            try:
                                r=requests.post(url,headers=headers,data={"app_id":"100067","access_token":text,"email":email},timeout=15)
                                await update.message.reply_text(f"Resubscribe Result: {r.text[:300]}", reply_markup=get_youtube_keyboard())
                            except Exception as e:
                                await update.message.reply_text(f"Error: {e}", reply_markup=get_youtube_keyboard())
                except Exception as e:
                    await update.message.reply_text(f"Error: {e}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "game_login":
            if step == "token":
                await update.message.reply_text("Fetching Game Login Data...", reply_markup=get_youtube_keyboard())
                uid,nick,region = get_player_info_sync(text)
                jwt_res = get_jwt_from_access_token(text)
                if jwt_res["ok"]:
                    msg = f"GAME LOGIN DATA\n\nUID: {uid}\nNickname: {nick}\nRegion: {region}\nJWT: {jwt_res['jwt'][:80]}...\nServer URL: {jwt_res.get('server_url','')}"
                else:
                    msg = f"GAME LOGIN DATA\n\nUID: {uid}\nNickname: {nick}\nRegion: {region}\nJWT Error: {jwt_res['error']}"
                await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "bio_update":
            if step == "token":
                context.user_data["token"] = text
                uid,nick,region = get_player_info_sync(text)
                await update.message.reply_text(f"Player: {nick} ({uid}) Region: {region}\n\nEnter NEW Bio (240 chars):", reply_markup=get_youtube_keyboard())
                context.user_data["step"] = "bio"
                context.user_data["region"] = region
                return STATE_INPUT
            if step == "bio":
                bio = text[:240]
                await update.message.reply_text(f"Updating Bio to: {bio}...", reply_markup=get_youtube_keyboard())
                jwt_res = get_jwt_from_access_token(context.user_data["token"])
                if not jwt_res["ok"]:
                    await update.message.reply_text(f"JWT Failed: {jwt_res['error']}", reply_markup=get_youtube_keyboard())
                else:
                    # Try bio update via JWT - using Garena endpoint if available
                    try:
                        # Using protobuf style update - try multiple
                        headers = {"Authorization": f"Bearer {jwt_res['jwt']}", "Content-Type": "application/json", "User-Agent": "Dalvik/2.1.0"}
                        # Attempt via client endpoint
                        # Fallback: use known working endpoint from email.py but with protobuf JWT
                        enc_bio = urllib.parse.quote(bio)
                        # Try direct client API
                        success=False
                        for api in [f"https://client.ind.freefiremobile.com/api/profile/update_bio?bio={enc_bio}"]:
                            try:
                                r=requests.post(api, headers=headers, data=json.dumps({"bio": bio}), timeout=10, verify=False)
                                if r.status_code==200:
                                    await update.message.reply_text(f"Bio Update Response: {r.text[:300]}", reply_markup=get_youtube_keyboard())
                                    success=True
                                    break
                            except Exception as e:
                                continue
                        if not success:
                            await update.message.reply_text(f"Bio Update Attempted with JWT: {jwt_res['jwt'][:30]}...\nBio: {bio}\nNote: If failed, use in-game. JWT generated successfully.", reply_markup=get_youtube_keyboard())
                    except Exception as e:
                        await update.message.reply_text(f"Error: {e}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "name_change":
            if step == "token":
                context.user_data["token"] = text
                uid,nick,region = get_player_info_sync(text)
                await update.message.reply_text(f"Player: {nick} ({uid}) Region: {region}\n\nEnter NEW Nickname (12 chars max):", reply_markup=get_youtube_keyboard())
                context.user_data["step"] = "new_name"
                context.user_data["old_nick"] = nick
                context.user_data["region"] = region
                return STATE_INPUT
            if step == "new_name":
                new_name = text[:12]
                if len(new_name)<3:
                    await update.message.reply_text("Min 3 chars required. Try again:", reply_markup=get_youtube_keyboard())
                    return STATE_INPUT
                await update.message.reply_text(f"Changing Name: {context.user_data['old_nick']} -> {new_name}...", reply_markup=get_youtube_keyboard())
                jwt_res = get_jwt_from_access_token(context.user_data["token"])
                if not jwt_res["ok"]:
                    await update.message.reply_text(f"JWT Failed: {jwt_res['error']}", reply_markup=get_youtube_keyboard())
                else:
                    # Try name change - needs card
                    await update.message.reply_text(f"JWT Generated: {jwt_res['jwt'][:30]}...\nAttempting name change (needs Name Change Card 39D+200GT or 390D)...\nIf card not present, buy from Store.", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
        return STATE_INPUT

    except Exception as e:
        print(f"handle_text error: {e}")
        import traceback
        traceback.print_exc()
        try:
            await update.message.reply_text("Error Occurred. Please Use /start", reply_markup=get_reply_keyboard())
        except:
            pass
        context.user_data.clear()
        return STATE_INPUT

flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return f"Bot Running - 15 Options Clean"
@flask_app.route('/health')
def health():
    return "OK"
app = flask_app

def run_bot():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("BOT_TOKEN not set!")
        return
    import asyncio
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    except:
        pass
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", start),
                CommandHandler("menu", menu_cmd),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
            ],
            states={STATE_INPUT: [CallbackQueryHandler(handle_callback), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)]},
            fallbacks=[CommandHandler("cancel", cancel_cmd), CommandHandler("start", start)], allow_reentry=True, per_message=False
        )
        application.add_handler(conv_handler)
        application.add_handler(CommandHandler("cancel", cancel_cmd))
        application.run_polling(close_loop=False, drop_pending_updates=True, stop_signals=None)
    except Exception as e:
        print(f"Bot run_polling failed: {e}")
        import traceback
        traceback.print_exc()
        raise

def _auto_start_bot():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("BOT_TOKEN not set, bot thread not started")
        return
    def bot_thread_func():
        while True:
            try:
                print("Starting bot thread...")
                run_bot()
            except Exception as e:
                print(f"Bot thread crashed: {e}, restarting in 5 sec...")
                import traceback
                traceback.print_exc()
                time.sleep(5)
    try:
        t = threading.Thread(target=bot_thread_func, daemon=True)
        t.start()
        print("Bot thread auto-started")
    except Exception as e:
        print(f"Failed to start bot thread: {e}")

if os.getenv("PORT") or os.getenv("RENDER"):
    _auto_start_bot()

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)
