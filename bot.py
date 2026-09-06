
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import sys, json, time, urllib.parse, base64, hashlib, urllib3, requests, threading, random
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
PROXY_URL = os.getenv("PROXY_URL") or os.getenv("SINGAPORE_PROXY") or "http://ucclpuwm:3ci36r6ra5r1@31.59.20.176:6754"

YOUTUBE_LINK = "https://youtube.com/@zevricxplay"

AeSkEy = b'Yg&tc%DEuh6%Zc^8'
AeSiV  = b'6oyZDr22E3ychjM%'
PLATFORM_MAP_FULL = {1: "Garena", 3: "Facebook", 4: "Guest", 5: "VK", 6: "Huawei", 7: "Apple", 8: "Google", 10: "GameCenter / Line", 11: "X (Twitter)", 13: "Apple ID", 28: "Line", 35: "TikTok"}
STATE_INPUT = 1

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

def read_varint(data, offset):
    res = 0; shift = 0
    while True:
        if offset >= len(data): break
        b = data[offset]; offset += 1
        res |= (b & 0x7f) << shift
        if not (b & 0x80): break
        shift += 7
    return res, offset

def parse_record(data):
    rec = {}; offset = 0
    while offset < len(data):
        tag, offset = read_varint(data, offset)
        wt, f = tag & 7, tag >> 3
        if wt == 0:
            val, offset = read_varint(data, offset)
            if f == 1: rec['ts'] = val
            elif f == 2: rec['ram'] = val
        elif wt == 2:
            length, offset = read_varint(data, offset)
            val = data[offset:offset+length]; offset += length
            if f == 3: rec['dev'] = val.decode(errors='ignore')
            elif f == 4: rec['arch'] = val.decode(errors='ignore')
        else: break
    return rec

def parse_history_protobuf(data):
    records = []; offset = 0
    while offset < len(data):
        tag, offset = read_varint(data, offset)
        wt, f = tag & 7, tag >> 3
        if wt == 0: val, offset = read_varint(data, offset)
        elif wt == 2:
            length, offset = read_varint(data, offset)
            val = data[offset:offset+length]; offset += length
            if f == 1: records.append(parse_record(val))
        else: break
    return records

def fetch_player_info_sync(access_token):
    try:
        url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10, allow_redirects=True)
        parsed = urllib.parse.urlparse(r.url); qs = urllib.parse.parse_qs(parsed.query)
        return {"uid": qs.get("account_id", ["Unknown"])[0], "nickname": urllib.parse.unquote(qs.get("nickname", ["Unknown"])[0]), "region": qs.get("region", ["Unknown"])[0], "ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def fetch_bind_info_sync(access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        payload = {'app_id': "100067", 'access_token': access_token}
        r = requests.get(url, params=payload, headers={'User-Agent': "GarenaMSDK/4.0.19P9"}, timeout=10)
        if r.status_code == 200: return {"ok": True, "data": r.json()}
        else: return {"ok": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def send_otp_sync(email, access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "locale": "en_PK", "region": "PK", "app_id": "100067", "access_token": access_token}
        r = requests.post(url, headers=headers, data=data, timeout=10)
        j = r.json()
        return {"ok": j.get("result") == 0, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# FAST 5-10 SEC SINGLE UNSUBSCRIBE OTP - ALWAYS USES SINGAPORE PROXY (VPN REQUIRED)
def send_single_unsubscribe_otp_sync(email):
    import os, random, requests
    PROXY_URL_LOCAL = os.getenv("PROXY_URL") or os.getenv("SINGAPORE_PROXY") or "http://ucclpuwm:3ci36r6ra5r1@31.59.20.176:6754"
    proxy_dict = {"http": PROXY_URL_LOCAL, "https": PROXY_URL_LOCAL} if PROXY_URL_LOCAL and len(PROXY_URL_LOCAL) > 10 else None
    
    headers_g = {
        "User-Agent": "GarenaMSDK/4.0.19P9(Realme RMX1921 ;Android 11;en;US;)",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    # FAST - 3 attempts, 5 sec timeout each = 5-10 sec total
    for _ in range(3):
        try:
            sess = requests.Session()
            sess.verify = False
            if proxy_dict:
                sess.proxies.update(proxy_dict)
            
            udid = ''.join(random.choices('0123456789abcdef', k=32))
            g_url = "https://100067.connect.garena.com/oauth/guest/token/grant"
            g_data = {"app_id": "100067", "udid": udid, "client_id": "100067", "client_secret": "8ba7d83f1f3a0d1d5a0a5b7a1b5e7a0e5"}
            
            try:
                gr = sess.post(g_url, data=g_data, headers=headers_g, timeout=5)
                gj = gr.json()
            except:
                gr = sess.get(f"{g_url}?app_id=100067&udid={udid}&client_id=100067&client_secret=8ba7d83f1f3a0d1d5a0a5b7a1b5e7a0e5", headers=headers_g, timeout=5)
                gj = gr.json()
            
            if "access_token" not in gj:
                continue
            
            token = gj["access_token"]
            # SG first - fastest for India, because website needs VPN
            for loc, reg in [("en_SG", "SG"), ("en_IN", "IN"), ("en_US", "US")]:
                try:
                    otp_url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
                    otp_data = {"email": email, "locale": loc, "region": reg, "app_id": "100067", "access_token": token}
                    ro = sess.post(otp_url, data=otp_data, headers=headers_g, timeout=5)
                    jo = ro.json()
                    if jo.get("result") == 0 or '"result":0' in ro.text:
                        return {"ok": True, "data": jo, "email": email}
                except:
                    continue
        except:
            continue
    
    return {"ok": False, "error": "Garena busy - try again after 10 sec", "email": email}

def verify_otp_sync(email, access_token, otp):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"app_id": "100067", "access_token": access_token, "email": email, "code": otp, "otp": otp, "type": "1"}
        r = requests.post(url, headers=headers, data=data, timeout=10)
        j = r.json()
        return {"ok": j.get("result") == 0 or "verifier_token" in j, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def verify_identity_otp_sync(email, access_token, otp):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "app_id": "100067", "access_token": access_token, "otp": otp}
        r = requests.post(url, headers=headers, data=data, timeout=10)
        j = r.json()
        return {"ok": "identity_token" in j, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def verify_identity_sec_sync(email, access_token, sec_code):
    try:
        import hashlib
        hashed = hashlib.sha256(sec_code.encode('utf-8')).hexdigest()
        url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "app_id": "100067", "access_token": access_token, "secondary_password": hashed}
        r = requests.post(url, headers=headers, data=data, timeout=10)
        j = r.json()
        return {"ok": "identity_token" in j, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_bind_request_sync(email, access_token, verifier_token, sec_code):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "app_id": "100067", "access_token": access_token, "verifier_token": verifier_token, "secondary_password": sec_code}
        r = requests.post(url, headers=headers, data=data, timeout=10)
        j = r.json()
        return {"ok": j.get("result")==0, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_rebind_request_sync(identity_token, new_email, verifier_token, access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"identity_token": identity_token, "email": new_email, "app_id": "100067", "verifier_token": verifier_token, "access_token": access_token}
        r = requests.post(url, headers=headers, data=data, timeout=10)
        j = r.json()
        return {"ok": j.get("result")==0, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_unbind_request_sync(identity_token, access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"app_id": "100067", "access_token": access_token, "identity_token": identity_token}
        r = requests.post(url, headers=headers, data=data, timeout=10)
        j = r.json()
        return {"ok": j.get("result")==0, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def cancel_request_sync(access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"app_id": "100067", "access_token": access_token}
        r = requests.post(url, headers=headers, data=data, timeout=10)
        j = r.json()
        return {"ok": j.get("result")==0, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def eat_to_token_sync(eat_input):
    try:
        eat_token = None
        if "http" in eat_input or "?" in eat_input:
            parsed = urllib.parse.urlparse(eat_input); qs = urllib.parse.parse_qs(parsed.query)
            if 'eat' in qs: eat_token = qs['eat'][0]
        else: eat_token = eat_input.strip()
        if not eat_token: return {"ok": False, "error": "EAT token not found"}
        api_url = f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
        r = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=10)
        parsed_final = urllib.parse.urlparse(r.url); final_qs = urllib.parse.parse_qs(parsed_final.query)
        if 'access_token' in final_qs:
            return {"ok": True, "access_token": final_qs['access_token'][0], "account_id": final_qs.get('account_id',['Unknown'])[0], "nickname": urllib.parse.unquote(final_qs.get('nickname',['Unknown'])[0]), "region": final_qs.get('region',['Unknown'])[0]}
        else: return {"ok": False, "error": "Access token not found - expired"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def revoke_token_sync(access_token):
    try:
        api_url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        r = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=10)
        parsed = urllib.parse.urlparse(r.url); qs = urllib.parse.parse_qs(parsed.query)
        if 'access_token' not in qs: return {"ok": False, "error": "Token already invalid"}
        nickname = urllib.parse.unquote(qs.get('nickname',['Unknown'])[0]); account_id = qs.get('account_id',['Unknown'])[0]
        refresh_token = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
        logout_url = f"https://100067.connect.garena.com/oauth/logout?access_token={access_token}&refresh_token={refresh_token}"
        logout_res = requests.get(logout_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if logout_res.status_code==200 and "error" not in logout_res.text: return {"ok": True, "nickname": nickname, "account_id": account_id}
        else: return {"ok": False, "error": f"Revoke failed: {logout_res.text[:200]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def fetch_platform_binds_sync(access_token):
    try:
        url = "https://100067.connect.garena.com/bind/app/platform/info/get"
        params = {"access_token": access_token}
        r = requests.get(url, params=params, headers={"User-Agent": "GarenaMSDK/4.0.19P9"}, timeout=10)
        if r.status_code!=200: return {"ok": False, "error": f"HTTP {r.status_code}"}
        d = r.json()
        return {"ok": True, "bounded": d.get("bounded_accounts",[]), "available": d.get("available_platforms",[])}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def get_reply_keyboard():
    if HAS_STYLE:
        keyboard = [
            [KeyboardButton(text="CHECK BIND INFO", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="BIND EMAIL", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="UNBIND EMAIL", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="CHANGE BIND EMAIL", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="CANCEL BIND REQUEST", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="EAT TO ACCESS TOKEN", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="REVOKE ACCESS TOKEN", style=KeyboardButtonStyle.DANGER), KeyboardButton(text="GET LOGIN HISTORY", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="CHECK BOUND ACCOUNTS", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="Single Unsubscribe OTP", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="Double Unsubscribe OTP", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="OWNER DETAILS", style=KeyboardButtonStyle.PRIMARY)],
        ]
    else:
        keyboard = [
            ["CHECK BIND INFO", "BIND EMAIL"],
            ["UNBIND EMAIL", "CHANGE BIND EMAIL"],
            ["CANCEL BIND REQUEST", "EAT TO ACCESS TOKEN"],
            ["REVOKE ACCESS TOKEN", "GET LOGIN HISTORY"],
            ["CHECK BOUND ACCOUNTS", "Single Unsubscribe OTP"],
            ["Double Unsubscribe OTP", "OWNER DETAILS"],
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

def get_method_keyboard():
    if HAS_STYLE:
        keyboard = [
            [KeyboardButton(text="Via Email OTP", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="Via Security Code", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="Back to Menu", style=KeyboardButtonStyle.DANGER)],
        ]
    else:
        keyboard = [["Via Email OTP", "Via Security Code"], ["Back to Menu"]]
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
    try:
        context.user_data.clear()
        first_name = update.effective_user.first_name or "User"
        welcome = f"Welcome {first_name}!\n\nSelect an option from below menu 👇"
        await update.message.reply_text(welcome, reply_markup=get_youtube_keyboard())
        await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
        return STATE_INPUT
    except Exception as e:
        print(f"Start error: {e}")
        await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
        return STATE_INPUT

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
    return STATE_INPUT

async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Cancelled. Main Menu:", reply_markup=get_reply_keyboard())
    return STATE_INPUT

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return STATE_INPUT

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.strip()
        flow = context.user_data.get("flow")
        step = context.user_data.get("step")

        if "double" in text.lower() and "unsub" in text.lower():
            await update.message.reply_text("🚧 Double Unsubscribe OTP\n\nComing Soon... ⏳\n\nThis feature will be available soon!", reply_markup=get_reply_keyboard())
            return STATE_INPUT

        if "single" in text.lower() and "unsub" in text.lower():
            context.user_data.clear()
            context.user_data["flow"] = "single_unsub"
            context.user_data["step"] = "email"
            await update.message.reply_text("Please enter your email address:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text == "CHECK BIND INFO":
            context.user_data.clear()
            context.user_data["flow"] = "bind_info"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please send your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text == "BIND EMAIL":
            context.user_data.clear()
            context.user_data["flow"] = "bind"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please send your Access Token to bind email:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text == "UNBIND EMAIL":
            context.user_data.clear()
            context.user_data["flow"] = "unbind"
            context.user_data["step"] = "method"
            await update.message.reply_text("Choose unbind method:", reply_markup=get_method_keyboard())
            return STATE_INPUT

        if text == "CHANGE BIND EMAIL":
            context.user_data.clear()
            context.user_data["flow"] = "change"
            context.user_data["step"] = "method"
            await update.message.reply_text("Choose change method:", reply_markup=get_method_keyboard())
            return STATE_INPUT

        if text == "CANCEL BIND REQUEST":
            context.user_data.clear()
            context.user_data["flow"] = "cancel"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please send Access Token to cancel request:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text == "EAT TO ACCESS TOKEN":
            context.user_data.clear()
            context.user_data["flow"] = "eat"
            context.user_data["step"] = "eat"
            await update.message.reply_text("Please send EAT token or EAT link:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text == "REVOKE ACCESS TOKEN":
            context.user_data.clear()
            context.user_data["flow"] = "revoke"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please send Access Token to revoke:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text == "GET LOGIN HISTORY":
            await update.message.reply_text("Login History - Send token:", reply_markup=get_youtube_keyboard())
            context.user_data.clear()
            context.user_data["flow"] = "login_history"
            context.user_data["step"] = "token"
            return STATE_INPUT

        if text == "CHECK BOUND ACCOUNTS":
            context.user_data.clear()
            context.user_data["flow"] = "bound"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please send Access Token to check bound accounts:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text == "OWNER DETAILS":
            await update.message.reply_text("👨‍💻 Owner: @just_zevric\n📺 YouTube: Zevric X Play", reply_markup=get_youtube_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
            return STATE_INPUT

        if text == "Back to Menu":
            context.user_data.clear()
            await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
            return STATE_INPUT

        # SINGLE UNSUB FAST FLOW - 5-10 SEC
        if flow == "single_unsub":
            if step == "email":
                email = text.strip()
                if "@" not in email or "." not in email:
                    await update.message.reply_text("❌ Invalid email! Please enter valid email:")
                    return STATE_INPUT
                await update.message.reply_text(f"Sending Single Unsubscribe OTP to {email}...", reply_markup=get_youtube_keyboard())
                res = send_single_unsubscribe_otp_sync(email)
                if res.get("ok"):
                    await update.message.reply_text(f"Single Unsubscribe OTP Sent Successfully!\n\nEmail: {email}\nStatus: OTP has been sent to your email\n\nPlease check your inbox (including Spam folder) for verification code from Garena.", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Failed to send OTP!\n\nEmail: {email}\nError: {res.get('error','Unknown')}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "bind_info":
            if step == "token":
                await update.message.reply_text("Fetching bind info...", reply_markup=get_youtube_keyboard())
                bind = fetch_bind_info_sync(text)
                if not bind["ok"]:
                    await update.message.reply_text(f"Error: {bind['error']}", reply_markup=get_youtube_keyboard())
                else:
                    data = bind["data"]
                    email = data.get("email","Not bound")
                    msg = f"BIND INFO\n\nCurrent Email: {email}"
                    await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "bind":
            if step == "token":
                context.user_data["token"] = text
                await update.message.reply_text("Please send new email to bind:", reply_markup=get_youtube_keyboard())
                context.user_data["step"] = "email"
                return STATE_INPUT
            if step == "email":
                context.user_data["email"] = text
                await update.message.reply_text(f"Sending OTP to {text}...", reply_markup=get_youtube_keyboard())
                res = send_otp_sync(text, context.user_data["token"])
                if res["ok"]:
                    await update.message.reply_text(f"OTP sent to {text}, please send OTP:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "otp"
                else:
                    await update.message.reply_text(f"OTP fail: {res.get('data')}", reply_markup=get_youtube_keyboard())
                return STATE_INPUT
            if step == "otp":
                res = verify_otp_sync(context.user_data["email"], context.user_data["token"], text)
                if res["ok"]:
                    vt = res["data"].get("verifier_token")
                    await update.message.reply_text("Please send secondary password (6-digit):", reply_markup=get_youtube_keyboard())
                    context.user_data["verifier_token"] = vt
                    context.user_data["step"] = "sec"
                else:
                    await update.message.reply_text(f"Verify fail: {res['data']}")
                return STATE_INPUT
            if step == "sec":
                res = create_bind_request_sync(context.user_data["email"], context.user_data["token"], context.user_data["verifier_token"], text)
                if res["ok"]:
                    await update.message.reply_text(f"Bind Success: {res['data']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Bind fail: {res['data']}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "unbind":
            if step == "method":
                if "otp" in text.lower():
                    context.user_data["method"] = "otp"
                else:
                    context.user_data["method"] = "sec"
                await update.message.reply_text("Please send Access Token for unbind:", reply_markup=get_youtube_keyboard())
                context.user_data["step"] = "token"
                return STATE_INPUT
            if step == "token":
                context.user_data["token"] = text
                bind = fetch_bind_info_sync(text)
                if not bind["ok"] or not bind["data"].get("email"):
                    await update.message.reply_text("No bound email found.", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                email = bind["data"].get("email")
                context.user_data["email"] = email
                if context.user_data.get("method") == "otp":
                    await update.message.reply_text(f"Current Email: {email}\nSending OTP...", reply_markup=get_youtube_keyboard())
                    res = send_otp_sync(email, text)
                    if res["ok"]:
                        await update.message.reply_text(f"OTP sent to {email}, send OTP:", reply_markup=get_youtube_keyboard())
                        context.user_data["step"] = "otp"
                    else:
                        await update.message.reply_text(f"OTP fail: {res['data']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text("Send 6-digit Security Code:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "sec_code"
                return STATE_INPUT
            if step == "otp":
                res = verify_identity_otp_sync(context.user_data["email"], context.user_data["token"], text)
                if res["ok"]:
                    id_token = res["data"].get("identity_token")
                    unr = create_unbind_request_sync(id_token, context.user_data["token"])
                    if unr["ok"]:
                        await update.message.reply_text(f"UNBIND SUCCESS\n{unr['data']}", reply_markup=get_youtube_keyboard())
                    else:
                        await update.message.reply_text(f"Unbind fail: {unr['data']}", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                else:
                    await update.message.reply_text(f"Verify fail: {res['data']}\nSend OTP again:")
                return STATE_INPUT
            if step == "sec_code":
                res = verify_identity_sec_sync(context.user_data["email"], context.user_data["token"], text)
                if res["ok"]:
                    id_token = res["data"].get("identity_token")
                    unr = create_unbind_request_sync(id_token, context.user_data["token"])
                    if unr["ok"]:
                        await update.message.reply_text(f"UNBIND SUCCESS\n{unr['data']}", reply_markup=get_youtube_keyboard())
                    else:
                        await update.message.reply_text(f"Unbind fail: {unr['data']}", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                else:
                    await update.message.reply_text(f"Verify fail: {res['data']}\nSend sec code again:")
                return STATE_INPUT

        if flow == "cancel":
            if step == "token":
                await update.message.reply_text("Cancelling...", reply_markup=get_youtube_keyboard())
                res = cancel_request_sync(text)
                if res["ok"]:
                    await update.message.reply_text("Cancel Success!", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Cancel Fail: {res.get('data')}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "eat":
            if step == "eat":
                await update.message.reply_text("Converting EAT...", reply_markup=get_youtube_keyboard())
                res = eat_to_token_sync(text)
                if res["ok"]:
                    await update.message.reply_text(f"Token: {res['access_token']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Fail: {res.get('error')}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "revoke":
            if step == "token":
                await update.message.reply_text("Revoking...", reply_markup=get_youtube_keyboard())
                res = revoke_token_sync(text)
                if res["ok"]:
                    await update.message.reply_text(f"Revoked! Account: {res.get('account_id')}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Revoke fail: {res.get('error')}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "bound":
            if step == "token":
                await update.message.reply_text("Checking...", reply_markup=get_youtube_keyboard())
                res = fetch_platform_binds_sync(text)
                if res["ok"]:
                    await update.message.reply_text(f"Bound: {res.get('bounded')}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Error: {res.get('error')}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
        return STATE_INPUT

    except Exception as e:
        print(f"handle_text error: {e}")
        import traceback
        traceback.print_exc()
        try:
            await update.message.reply_text("Error occurred. Please use /start", reply_markup=get_reply_keyboard())
        except:
            pass
        context.user_data.clear()
        return STATE_INPUT

flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return f"Bot Running - Final Fast 5-10 Sec OTP Fix"

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
        print("Building Application...")
        application = Application.builder().token(BOT_TOKEN).build()
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start), CommandHandler("menu", menu_cmd), MessageHandler(filters.Regex("^(CHECK BIND INFO|BIND EMAIL|UNBIND EMAIL|CHANGE BIND EMAIL|CANCEL BIND REQUEST|EAT TO ACCESS TOKEN|REVOKE ACCESS TOKEN|GET LOGIN HISTORY|CHECK BOUND ACCOUNTS|OWNER DETAILS|Single Unsubscribe OTP|Double Unsubscribe OTP)$"), handle_text)],
            states={STATE_INPUT: [CallbackQueryHandler(handle_callback), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)]},
            fallbacks=[CommandHandler("cancel", cancel_cmd), CommandHandler("start", start)], allow_reentry=True, per_message=False
        )
        application.add_handler(conv_handler)
        application.add_handler(CommandHandler("cancel", cancel_cmd))
        print(f"Bot starting polling... Token: {BOT_TOKEN[:10]}... Proxy: {PROXY_URL[:20]}")
        application.run_polling(close_loop=False, drop_pending_updates=True, stop_signals=None)
    except Exception as e:
        print(f"Bot run_polling failed: {e}")
        import traceback
        traceback.print_exc()
        raise

def _auto_start_bot():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("BOT_TOKEN not set")
        return
    def bot_thread_func():
        while True:
            try:
                print("Starting bot thread...")
                run_bot()
            except Exception as e:
                print(f"Bot crashed: {e}, restarting in 5 sec...")
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
    print(f"Flask starting on port {port}")
    flask_app.run(host="0.0.0.0", port=port)
