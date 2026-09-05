import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import sys
import json
import time
import urllib.parse
import base64
import hashlib
import urllib3
import requests
import threading
from datetime import datetime
from flask import Flask

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import MajoRLogin_pb2 as mLpB
    import MajorLoginRes_pb2 as mLrPb
    PROTOBUF_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Protobuf disabled: {e}")
    PROTOBUF_AVAILABLE = False
    mLpB = None
    mLrPb = None

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.constants import ParseMode

BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN_HERE"

AeSkEy = b'Yg&tc%DEuh6%Zc^8'
AeSiV  = b'6oyZDr22E3ychjM%'

PLATFORM_MAP_SIMPLE = {3: "Facebook", 4: "Guest", 5: "VK", 6: "Huawei", 8: "Google", 11: "X (Twitter)", 13: "AppleId"}
PLATFORM_MAP_FULL = {1: "Garena", 3: "Facebook", 4: "Guest", 5: "VK", 6: "Huawei", 7: "Apple", 8: "Google", 10: "GameCenter / Line", 11: "X (Twitter)", 13: "Apple ID", 28: "Line", 35: "TikTok"}

STATE_INPUT = 1

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    def enc(d: bytes) -> bytes: 
        return AES.new(AeSkEy, AES.MODE_CBC, AeSiV).encrypt(pad(d, 16))
    def dec(d: bytes) -> bytes: 
        return unpad(AES.new(AeSkEy, AES.MODE_CBC, AeSiV).decrypt(d), 16)
except Exception:
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
    except Exception as e:
        print(f"build_majorlogin error: {e}")
        return None

def fetch_player_info_sync(access_token):
    try:
        url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15, allow_redirects=True)
        parsed = urllib.parse.urlparse(r.url); qs = urllib.parse.parse_qs(parsed.query)
        return {"uid": qs.get("account_id", ["Unknown"])[0], "nickname": urllib.parse.unquote(qs.get("nickname", ["Unknown"])[0]), "region": qs.get("region", ["Unknown"])[0], "ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def fetch_bind_info_sync(access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        payload = {'app_id': "100067", 'access_token': access_token}
        r = requests.get(url, params=payload, headers={'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"}, timeout=15)
        if r.status_code == 200: return {"ok": True, "data": r.json()}
        else: return {"ok": False, "error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def send_otp_sync(email, access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "locale": "en_PK", "region": "PK", "app_id": "100067", "access_token": access_token}
        r = requests.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result") == 0, "data": j, "raw": r.text}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def verify_otp_sync(email, access_token, otp):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"app_id": "100067", "access_token": access_token, "email": email, "code": otp, "otp": otp, "type": "1"}
        r = requests.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result") == 0 or "verifier_token" in j, "data": j, "raw": r.text}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def verify_identity_otp_sync(email, access_token, otp):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "app_id": "100067", "access_token": access_token, "otp": otp}
        r = requests.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": "identity_token" in j, "data": j, "raw": r.text}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def verify_identity_sec_sync(email, access_token, sec_code):
    try:
        import hashlib
        hashed = hashlib.sha256(sec_code.encode('utf-8')).hexdigest()
        url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "app_id": "100067", "access_token": access_token, "secondary_password": hashed}
        r = requests.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": "identity_token" in j, "data": j, "raw": r.text}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_bind_request_sync(email, access_token, verifier_token, sec_code):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "app_id": "100067", "access_token": access_token, "verifier_token": verifier_token, "secondary_password": sec_code}
        r = requests.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result")==0, "data": j, "raw": r.text}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_rebind_request_sync(identity_token, new_email, verifier_token, access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"identity_token": identity_token, "email": new_email, "app_id": "100067", "verifier_token": verifier_token, "access_token": access_token}
        r = requests.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result")==0, "data": j, "raw": r.text}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_unbind_request_sync(identity_token, access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"app_id": "100067", "access_token": access_token, "identity_token": identity_token}
        r = requests.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result")==0, "data": j, "raw": r.text}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def cancel_request_sync(access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"app_id": "100067", "access_token": access_token}
        r = requests.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result")==0, "data": j, "raw": r.text}
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
        r = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=15)
        parsed_final = urllib.parse.urlparse(r.url); final_qs = urllib.parse.parse_qs(parsed_final.query)
        if 'access_token' in final_qs:
            return {"ok": True, "access_token": final_qs['access_token'][0], "account_id": final_qs.get('account_id',['Unknown'])[0], "nickname": urllib.parse.unquote(final_qs.get('nickname',['Unknown'])[0]), "region": final_qs.get('region',['Unknown'])[0]}
        else: return {"ok": False, "error": "Access token not found - expired"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def revoke_token_sync(access_token):
    try:
        api_url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        r = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=15)
        parsed = urllib.parse.urlparse(r.url); qs = urllib.parse.parse_qs(parsed.query)
        if 'access_token' not in qs: return {"ok": False, "error": "Token already invalid"}
        nickname = urllib.parse.unquote(qs.get('nickname',['Unknown'])[0]); account_id = qs.get('account_id',['Unknown'])[0]; region = qs.get('region',['Unknown'])[0]
        refresh_token = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
        logout_url = f"https://100067.connect.garena.com/oauth/logout?access_token={access_token}&refresh_token={refresh_token}"
        logout_res = requests.get(logout_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if logout_res.status_code==200 and "error" not in logout_res.text: return {"ok": True, "nickname": nickname, "account_id": account_id, "region": region}
        else: return {"ok": False, "error": f"Revoke failed: {logout_res.text[:200]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def fetch_platform_binds_sync(access_token):
    try:
        url = "https://100067.connect.garena.com/bind/app/platform/info/get"
        params = {"access_token": access_token}
        r = requests.get(url, params=params, headers={"User-Agent": "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"}, timeout=10)
        if r.status_code!=200: return {"ok": False, "error": f"HTTP {r.status_code}"}
        d = r.json()
        return {"ok": True, "bounded": d.get("bounded_accounts",[]), "available": d.get("available_platforms",[])}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def fetch_login_history_sync(token_input):
    if not PROTOBUF_AVAILABLE: return {"ok": False, "error": "Protobuf missing - Login History disabled"}
    try:
        jwt_token = None
        if token_input.startswith("ey") and "." in token_input: jwt_token = token_input
        else:
            oId = None
            try:
                r = requests.get(f"https://100067.connect.garena.com/oauth/token/inspect?token={token_input}", headers={"User-Agent": "Mozilla/5.0"}, timeout=5).json()
                oId = r.get("open_id")
            except: pass
            if not oId:
                try:
                    uid_headers = {"access-token": token_input, "user-agent": "Mozilla/5.0"}
                    uid_res = requests.get("https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/", headers=uid_headers, verify=False, timeout=5).json()
                    uid = uid_res.get("uid")
                    if uid:
                        openid_res = requests.post("https://topup.pk/api/auth/player_id_login", json={"app_id": 100067, "login_id": str(uid)}, verify=False, timeout=5).json()
                        oId = openid_res.get("open_id")
                except: pass
            if not oId: return {"ok": False, "error": "Open ID extract failed"}
            for p_type in [8,3,4,6]:
                pl = build_majorlogin(token_input, oId, p_type)
                if not pl: continue
                try:
                    mLhDr = {"User-Agent": "Dalvik/2.1.0", "Content-Type": "application/octet-stream", "Expect": "100-continue", "X-GA": "v1 1", "X-Unity-Version": "2018.4.11f1", "ReleaseVersion": "OB52"}
                    x = requests.post("https://loginbp.ggpolarbear.com/MajorLogin", headers=mLhDr, data=pl, timeout=10, verify=False)
                    if x.status_code==200:
                        res = mLrPb.MajorLoginRes()
                        try: res.ParseFromString(dec(x.content))
                        except: res.ParseFromString(x.content)
                        if res.token: jwt_token = res.token; break
                except: continue
            if not jwt_token: return {"ok": False, "error": "MajorLogin failed"}
        try:
            payload_b64 = jwt_token.split('.')[1]; payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
            decoded = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
            name = urllib.parse.unquote(decoded.get("nickname","Unknown")); uid = decoded.get("account_id","Unknown")
            region = decoded.get("lock_region","Unknown"); p_id = decoded.get("external_type",0)
            platform = PLATFORM_MAP_SIMPLE.get(p_id, f"Unknown ({p_id})")
        except: name=uid=region=platform="Unknown"
        hH = {"Expect": "100-continue", "Authorization": f"Bearer {jwt_token}", "X-Unity-Version": "2018.4.11f1", "X-GA": "v1 1", "ReleaseVersion": "OB52", "Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Dalvik/2.1.0", "Host": "client.ind.freefiremobile.com", "Connection": "close"}
        r = requests.post("https://client.ind.freefiremobile.com/GetLoginHistory", headers=hH, data=enc(b""), timeout=15, verify=False)
        if r.status_code!=200: return {"ok": False, "error": f"HTTP {r.status_code}"}
        try: d = dec(r.content)
        except: d = r.content
        records = parse_history_protobuf(d)
        return {"ok": True, "records": records, "player": {"name": name, "uid": uid, "region": region, "platform": platform}}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("1️⃣ CHECK BIND INFO", callback_data="main_1"), InlineKeyboardButton("2️⃣ BIND EMAIL", callback_data="main_2")],
        [InlineKeyboardButton("3️⃣ UNBIND EMAIL", callback_data="main_3"), InlineKeyboardButton("4️⃣ CHANGE EMAIL", callback_data="main_4")],
        [InlineKeyboardButton("5️⃣ CANCEL REQUEST", callback_data="main_5"), InlineKeyboardButton("6️⃣ EAT → TOKEN", callback_data="main_6")],
        [InlineKeyboardButton("7️⃣ REVOKE TOKEN", callback_data="main_7"), InlineKeyboardButton("8️⃣ LOGIN HISTORY", callback_data="main_8")],
        [InlineKeyboardButton("9️⃣ BOUND ACCOUNTS", callback_data="main_9"), InlineKeyboardButton("🔟 OWNER DETAILS", callback_data="main_10")],
        [InlineKeyboardButton("❌ CANCEL", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_unbind_method_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Via OTP 📩", callback_data="unbind_otp"), InlineKeyboardButton("Via Sec Code 🔒", callback_data="unbind_sec")],[InlineKeyboardButton("⬅️ Back", callback_data="back_menu")]])

def get_change_method_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Via OTP 📩", callback_data="change_otp"), InlineKeyboardButton("Via Sec Code 🔒", callback_data="change_sec")],[InlineKeyboardButton("⬅️ Back", callback_data="back_menu")]])

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text="🔥 <b>Zevric Email Tool</b> 🔥\n\nSelect an option:"):
    if update.callback_query: await update.callback_query.message.reply_text(text, reply_markup=get_main_menu_keyboard(), parse_mode=ParseMode.HTML)
    else: await update.message.reply_text(text, reply_markup=get_main_menu_keyboard(), parse_mode=ParseMode.HTML)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    welcome = "⚡ <b>Zevric Email Tool - Telegram Bot</b> ⚡\n\n👨‍💻 Developer: Zevric | @just_zevric\n📺 YouTube: zevricxplay\n🔐 Status: SAFE & SECURE\n\nNeeche diye gaye options me se choose karo 👇"
    await update.message.reply_text(welcome, reply_markup=get_main_menu_keyboard(), parse_mode=ParseMode.HTML)
    return STATE_INPUT

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update, context); return STATE_INPUT

async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("✅ Operation cancelled. /start se menu kholo.", parse_mode=ParseMode.HTML)
    await show_main_menu(update, context, "Main Menu:"); return STATE_INPUT

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); data = query.data
    if data == "cancel":
        context.user_data.clear(); await query.edit_message_text("❌ Cancelled. /start se dubara menu kholo."); return STATE_INPUT
    if data == "back_menu":
        context.user_data.clear(); await query.edit_message_text("🔥 <b>Zevric Email Tool</b> 🔥\n\nSelect an option:", reply_markup=get_main_menu_keyboard(), parse_mode=ParseMode.HTML); return STATE_INPUT
    if data.startswith("main_"):
        num = data.split("_")[1]
        if num == "10":
            text = "👨‍💻 <b>ZEVRIC INFO</b>\n\n⊛ Developer Name: <b>ZEVRIC</b>\n⊛ Telegram: @just_zevric\n⊛ YouTube: zevricxplay\n⊛ Tool Version: <b>v2.0 (Premium)</b>\n\n💬 <i>Thank you for using Zevric Bot!</i>"
            await query.message.reply_text(text, parse_mode=ParseMode.HTML); await show_main_menu(update, context, "Wapas menu 👇"); return STATE_INPUT
        if num == "3":
            context.user_data.clear(); context.user_data['flow'] = 'unbind'; await query.message.reply_text("🔧 <b>UNBIND EMAIL</b> - Method choose karo:", reply_markup=get_unbind_method_keyboard(), parse_mode=ParseMode.HTML); return STATE_INPUT
        if num == "4":
            context.user_data.clear(); context.user_data['flow'] = 'change'; await query.message.reply_text("🔧 <b>CHANGE BIND EMAIL</b> - Method choose karo:", reply_markup=get_change_method_keyboard(), parse_mode=ParseMode.HTML); return STATE_INPUT
        flow_map = {"1": "bind_info", "2": "bind_email", "5": "cancel_req", "6": "eat_token", "7": "revoke", "8": "login_history", "9": "bound_accounts"}
        flow = flow_map.get(num)
        context.user_data.clear(); context.user_data['flow'] = flow; context.user_data['step'] = 'token'
        prompts = {"bind_info": "🔍 <b>CHECK BIND INFO</b>\n\nApna <b>Access Token</b> bhejo:", "bind_email": "📧 <b>BIND EMAIL</b>\n\nPehle apna <b>Access Token</b> bhejo:", "cancel_req": "🚫 <b>CANCEL BIND REQUEST</b>\n\nApna <b>Access Token</b> bhejo:", "eat_token": "🔗 <b>EAT TO ACCESS TOKEN</b>\n\nApna <b>EAT Token ya pura EAT URL</b> bhejo:", "revoke": "🔒 <b>REVOKE ACCESS TOKEN</b>\n\nJis token ko revoke karna hai wo bhejo:", "login_history": "📜 <b>GET LOGIN HISTORY</b>\n\nApna <b>Access Token ya JWT Token</b> bhejo:", "bound_accounts": "🔗 <b>CHECK BOUND ACCOUNTS</b>\n\nApna <b>Access Token</b> bhejo:"}
        await query.message.reply_text(prompts[flow], parse_mode=ParseMode.HTML); return STATE_INPUT
    if data.startswith("unbind_"):
        method = data.split("_")[1]; context.user_data['method'] = method; context.user_data['step'] = 'token'; await query.message.reply_text(f"🔧 UNBIND via {'OTP' if method=='otp' else 'Security Code'}\n\nApna <b>Access Token</b> bhejo:", parse_mode=ParseMode.HTML); return STATE_INPUT
    if data.startswith("change_"):
        method = data.split("_")[1]; context.user_data['method'] = method; context.user_data['step'] = 'token'; await query.message.reply_text(f"🔧 CHANGE via {'OTP' if method=='otp' else 'Security Code'}\n\nApna <b>Access Token</b> bhejo:", parse_mode=ParseMode.HTML); return STATE_INPUT
    return STATE_INPUT

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'flow' not in context.user_data:
        await show_main_menu(update, context, "Pehle menu se option select karo 👇"); return STATE_INPUT
    flow = context.user_data['flow']; step = context.user_data.get('step', 'token'); text = update.message.text.strip()

    if flow == 'bind_info' and step == 'token':
        await update.message.reply_text("⏳ Fetching bind info...")
        player = fetch_player_info_sync(text); bind = fetch_bind_info_sync(text)
        if not bind['ok']:
            await update.message.reply_text(f"❌ Error: {bind['error']}"); await show_main_menu(update, context); context.user_data.clear(); return STATE_INPUT
        d = bind['data']; email = d.get("email",""); email_to_be = d.get("email_to_be",""); countdown = d.get("request_exec_countdown",0)
        p_text = f"👤 <b>Player Info</b>\n• UID: <code>{player['uid']}</code>\n• Nick: {player['nickname']}\n• Region: {player['region']}\n\n" if player['ok'] else ""
        b_text = f"{p_text}📧 <b>Bind Info</b>\n• Current Email: <code>{email if email else 'None'}</code>\n• Pending Email: <code>{email_to_be if email_to_be else 'None'}</code>\n• Countdown: {convert_seconds(countdown) if email_to_be else 'N/A'}\n• Result: {d.get('result')}"
        await update.message.reply_text(b_text, parse_mode=ParseMode.HTML); await show_main_menu(update, context, "Ho gaya! Agla option 👇"); context.user_data.clear(); return STATE_INPUT

    if flow == 'bind_email':
        if step == 'token':
            context.user_data['token'] = text; await update.message.reply_text("⏳ Checking current bind info...")
            bind = fetch_bind_info_sync(text)
            if bind['ok']: d = bind['data']; await update.message.reply_text(f"Current: <code>{d.get('email') or 'None'}</code>\nPending: <code>{d.get('email_to_be') or 'None'}</code>\n\nAb <b>jis email ko bind karna hai</b> wo bhejo:", parse_mode=ParseMode.HTML)
            else: await update.message.reply_text("Token thoda doubt me hai but continue karte hain.\n\nBind karne wala <b>Email</b> bhejo:", parse_mode=ParseMode.HTML)
            context.user_data['step'] = 'email'; return STATE_INPUT
        if step == 'email':
            context.user_data['email'] = text; await update.message.reply_text(f"⏳ OTP bhej raha hu {text} pe..."); res = send_otp_sync(text, context.user_data['token'])
            if res['ok']: await update.message.reply_text(f"✅ OTP Sent!\n\nEmail pe aaya hua <b>OTP</b> bhejo:", parse_mode=ParseMode.HTML); context.user_data['step'] = 'otp'
            else: await update.message.reply_text(f"❌ OTP Send Failed: {res.get('data')}\n\nEmail sahi hai? Dubara email bhejo ya /cancel")
            return STATE_INPUT
        if step == 'otp':
            context.user_data['otp'] = text; await update.message.reply_text("⏳ OTP verify kar raha hu..."); res = verify_otp_sync(context.user_data['email'], context.user_data['token'], text)
            if res['ok']:
                vt = res['data'].get('verifier_token','')
                if vt: context.user_data['verifier_token'] = vt; await update.message.reply_text("✅ OTP Verified! Verifier token mil gaya.\n\nAb <b>6-digit Security Code</b> set karo:", parse_mode=ParseMode.HTML); context.user_data['step'] = 'sec_code'
                else: await update.message.reply_text(f"⚠️ OTP to sahi hai par verifier_token auto extract nahi hua.\n\nRaw:\n<code>{str(res['data'])[:1000]}</code>\n\nVerifier token bhejo:", parse_mode=ParseMode.HTML); context.user_data['step'] = 'verifier_manual'
            else: await update.message.reply_text(f"❌ OTP Verify Failed: {res['data']}\n\nOTP dubara bhejo:")
            return STATE_INPUT
        if step == 'verifier_manual':
            context.user_data['verifier_token'] = text; await update.message.reply_text("OK, ab <b>6-digit Security Code</b> bhejo:", parse_mode=ParseMode.HTML); context.user_data['step'] = 'sec_code'; return STATE_INPUT
        if step == 'sec_code':
            context.user_data['sec_code'] = text; await update.message.reply_text("⏳ Final bind request bana raha hu..."); res = create_bind_request_sync(context.user_data['email'], context.user_data['token'], context.user_data['verifier_token'], text)
            if res['ok']: await update.message.reply_text(f"✅ <b>BIND SUCCESS!</b>\n\n{res['data']}", parse_mode=ParseMode.HTML)
            else: await update.message.reply_text(f"❌ Bind Failed: {res['data']}", parse_mode=ParseMode.HTML)
            await show_main_menu(update, context, "Done! Next option 👇"); context.user_data.clear(); return STATE_INPUT

    if flow == 'cancel_req' and step == 'token':
        await update.message.reply_text("⏳ Cancel request bhej raha hu..."); res = cancel_request_sync(text)
        if res['ok']: await update.message.reply_text(f"✅ Cancel Success: {res['data']}", parse_mode=ParseMode.HTML)
        else: await update.message.reply_text(f"❌ Cancel Failed: {res['data'] if 'data' in res else res['error']}", parse_mode=ParseMode.HTML)
        await show_main_menu(update, context); context.user_data.clear(); return STATE_INPUT

    if flow == 'eat_token' and step == 'token':
        await update.message.reply_text("⏳ EAT ko Access Token me convert kar raha hu..."); res = eat_to_token_sync(text)
        if res['ok']: msg = f"✅ <b>SUCCESS</b>\n\n👤 Nick: {res['nickname']}\n🆔 Account ID: <code>{res['account_id']}</code>\n🌍 Region: {res['region']}\n\n🔑 Access Token:\n<code>{res['access_token']}</code>"; await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
        else: await update.message.reply_text(f"❌ Failed: {res['error']}")
        await show_main_menu(update, context); context.user_data.clear(); return STATE_INPUT

    if flow == 'revoke' and step == 'token':
        await update.message.reply_text("⏳ Token check + revoke kar raha hu..."); res = revoke_token_sync(text)
        if res['ok']: await update.message.reply_text(f"✅ <b>REVOKED</b>\n\n👤 {res['nickname']}\n🆔 {res['account_id']}\n🌍 {res['region']}\nStatus: Logged Out & Revoked", parse_mode=ParseMode.HTML)
        else: await update.message.reply_text(f"❌ {res['error']}")
        await show_main_menu(update, context); context.user_data.clear(); return STATE_INPUT

    if flow == 'bound_accounts' and step == 'token':
        await update.message.reply_text("⏳ Platform bind data la raha hu..."); res = fetch_platform_binds_sync(text)
        if res['ok']:
            bound = res['bounded']; avail = res['available']
            b_text = "✅ <b>PLATFORM BINDS</b>\n\n<b>Bound Accounts:</b>\n"
            if not bound: b_text += "• None\n"
            else:
                for pid in bound: b_text += f"• {PLATFORM_MAP_FULL.get(pid, f'Unknown ({pid})')}\n"
            b_text += "\n<b>Available Platforms:</b>\n"
            if not avail: b_text += "• None\n"
            else:
                for pid in avail: b_text += f"• {PLATFORM_MAP_FULL.get(pid, f'Unknown ({pid})')}\n"
            await update.message.reply_text(b_text, parse_mode=ParseMode.HTML)
        else: await update.message.reply_text(f"❌ Failed: {res['error']}")
        await show_main_menu(update, context); context.user_data.clear(); return STATE_INPUT

    if flow == 'login_history' and step == 'token':
        await update.message.reply_text("⏳ Login history fetch kar raha hu (thoda time lagega)..."); res = fetch_login_history_sync(text)
        if not res['ok']: await update.message.reply_text(f"❌ {res['error']}"); await show_main_menu(update, context); context.user_data.clear(); return STATE_INPUT
        player = res['player']; header = f"👤 <b>PLAYER INFO</b>\n• Name: {player['name']}\n• ID: <code>{player['uid']}</code>\n• Platform: {player['platform']}\n• Region: {player['region']}\n\n📜 <b>LOGIN HISTORY</b> ({len(res['records'])} records)\n\n"
        body = ""
        if not res['records']: body = "No records found."
        else:
            for i, rec in enumerate(res['records'], 1):
                ts_raw = rec.get('ts',0)
                try: date_str = datetime.fromtimestamp(ts_raw).strftime('%Y-%m-%d %H:%M:%S')
                except: date_str = "Invalid"
                dev = rec.get('dev','Unknown'); arch = rec.get('arch','Unknown'); ram = rec.get('ram',0)
                body += f"<b>#{i}</b> - {date_str}\n• Dev: {dev}\n• Arch: {arch}\n• RAM: {ram} MB\n\n"
                if len(body) > 3000: body += f"... and {len(res['records'])-i} more"; break
        await update.message.reply_text(header+body, parse_mode=ParseMode.HTML); await show_main_menu(update, context); context.user_data.clear(); return STATE_INPUT

    if flow == 'unbind':
        method = context.user_data.get('method')
        if step == 'token':
            context.user_data['token'] = text; bind = fetch_bind_info_sync(text)
            if not bind['ok'] or not bind['data'].get('email'): await update.message.reply_text("❌ Is token pe koi bound email nahi mila."); await show_main_menu(update, context); context.user_data.clear(); return STATE_INPUT
            email = bind['data'].get('email'); context.user_data['email'] = email
            if method == 'otp':
                await update.message.reply_text(f"Current Email: <code>{email}</code>\n\n⏳ OTP bhej raha hu...", parse_mode=ParseMode.HTML); res = send_otp_sync(email, text)
                if res['ok']: await update.message.reply_text(f"✅ OTP sent to {email}\n\nOTP bhejo:", parse_mode=ParseMode.HTML); context.user_data['step'] = 'otp'
                else: await update.message.reply_text(f"❌ OTP send fail: {res['data']}")
            else: await update.message.reply_text("🔒 Apna <b>6-digit Security Code</b> bhejo:", parse_mode=ParseMode.HTML); context.user_data['step'] = 'sec_code'
            return STATE_INPUT
        if step == 'otp':
            await update.message.reply_text("⏳ Identity verify kar raha hu OTP se..."); res = verify_identity_otp_sync(context.user_data['email'], context.user_data['token'], text)
            if res['ok']:
                id_token = res['data'].get('identity_token'); context.user_data['identity_token'] = id_token; await update.message.reply_text("✅ Identity verified. Ab unbind kar raha hu...")
                unr = create_unbind_request_sync(id_token, context.user_data['token'])
                if unr['ok']: await update.message.reply_text(f"✅ <b>UNBIND SUCCESS</b>\n{unr['data']}", parse_mode=ParseMode.HTML)
                else: await update.message.reply_text(f"❌ Unbind fail: {unr['data']}", parse_mode=ParseMode.HTML)
                await show_main_menu(update, context); context.user_data.clear()
            else: await update.message.reply_text(f"❌ Verify fail: {res['data']}\nOTP dubara bhejo:")
            return STATE_INPUT
        if step == 'sec_code':
            await update.message.reply_text("⏳ Identity verify via sec code..."); res = verify_identity_sec_sync(context.user_data['email'], context.user_data['token'], text)
            if res['ok']:
                id_token = res['data'].get('identity_token'); unr = create_unbind_request_sync(id_token, context.user_data['token'])
                if unr['ok']: await update.message.reply_text(f"✅ <b>UNBIND SUCCESS</b>\n{unr['data']}", parse_mode=ParseMode.HTML)
                else: await update.message.reply_text(f"❌ Unbind fail: {unr['data']}", parse_mode=ParseMode.HTML)
                await show_main_menu(update, context); context.user_data.clear()
            else: await update.message.reply_text(f"❌ Verify fail: {res['data']}\nSec code dubara bhejo:")
            return STATE_INPUT

    if flow == 'change':
        method = context.user_data.get('method')
        if step == 'token':
            context.user_data['token'] = text; bind = fetch_bind_info_sync(text)
            if not bind['ok'] or not bind['data'].get('email'): await update.message.reply_text("❌ No bound email found, change nahi kar sakte."); await show_main_menu(update, context); context.user_data.clear(); return STATE_INPUT
            old_email = bind['data'].get('email'); context.user_data['old_email'] = old_email; await update.message.reply_text(f"Current Email: <code>{old_email}</code>\n", parse_mode=ParseMode.HTML)
            if method == 'otp':
                await update.message.reply_text(f"⏳ OTP bhej raha hu {old_email} pe..."); res = send_otp_sync(old_email, text)
                if res['ok']: await update.message.reply_text("✅ OTP sent! Old email ka OTP bhejo:", parse_mode=ParseMode.HTML); context.user_data['step'] = 'old_otp'
                else: await update.message.reply_text(f"❌ OTP fail: {res['data']}")
            else: await update.message.reply_text("🔒 Apna <b>6-digit Security Code</b> bhejo (old email ke liye):", parse_mode=ParseMode.HTML); context.user_data['step'] = 'sec_code'
            return STATE_INPUT
        if step == 'sec_code':
            await update.message.reply_text("⏳ Verifying identity via sec code..."); res = verify_identity_sec_sync(context.user_data['old_email'], context.user_data['token'], text)
            if res['ok']: context.user_data['identity_token'] = res['data'].get('identity_token'); await update.message.reply_text("✅ Identity verified!\n\nAb <b>New Email</b> bhejo jisme change karna hai:", parse_mode=ParseMode.HTML); context.user_data['step'] = 'new_email'
            else: await update.message.reply_text(f"❌ Verify fail: {res['data']}\nSec code dubara bhejo:")
            return STATE_INPUT
        if step == 'old_otp':
            await update.message.reply_text("⏳ Old email identity verify kar raha hu..."); res = verify_identity_otp_sync(context.user_data['old_email'], context.user_data['token'], text)
            if res['ok']: context.user_data['identity_token'] = res['data'].get('identity_token'); await update.message.reply_text("✅ Old email verified!\n\nAb <b>New Email</b> bhejo:", parse_mode=ParseMode.HTML); context.user_data['step'] = 'new_email'
            else: await update.message.reply_text(f"❌ Verify fail: {res['data']}\nOTP dubara bhejo:")
            return STATE_INPUT
        if step == 'new_email':
            context.user_data['new_email'] = text; await update.message.reply_text(f"⏳ OTP bhej raha hu {text} pe..."); res = send_otp_sync(text, context.user_data['token'])
            if res['ok']: await update.message.reply_text(f"✅ OTP sent to new email {text}\n\nNew email ka <b>OTP</b> bhejo:", parse_mode=ParseMode.HTML); context.user_data['step'] = 'new_otp'
            else: await update.message.reply_text(f"❌ OTP send fail: {res['data']}\nEmail dubara bhejo:")
            return STATE_INPUT
        if step == 'new_otp':
            await update.message.reply_text("⏳ New email OTP verify..."); res = verify_otp_sync(context.user_data['new_email'], context.user_data['token'], text)
            if res['ok'] and res['data'].get('verifier_token'):
                context.user_data['verifier_token'] = res['data'].get('verifier_token'); await update.message.reply_text("✅ New email verified!\n\n⏳ Rebind request bana raha hu...")
                rebind = create_rebind_request_sync(context.user_data['identity_token'], context.user_data['new_email'], context.user_data['verifier_token'], context.user_data['token'])
                if rebind['ok']: await update.message.reply_text(f"✅ <b>CHANGE SUCCESS</b>\n{rebind['data']}", parse_mode=ParseMode.HTML)
                else: await update.message.reply_text(f"❌ Change fail: {rebind['data']}", parse_mode=ParseMode.HTML)
                await show_main_menu(update, context); context.user_data.clear()
            else: await update.message.reply_text(f"❌ Verify fail or no verifier_token: {res.get('data')}\nOTP dubara bhejo ya /cancel")
            return STATE_INPUT

    await update.message.reply_text("Samajh nahi aaya. /start se menu kholo."); return STATE_INPUT

# Flask for Render
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "✅ Bot is Running - Zevric Email Tool - Use /start on Telegram"
@flask_app.route('/health')
def health(): return "OK"
app = flask_app

def run_bot():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ BOT_TOKEN not set!")
        return
    application = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("menu", menu_cmd)],
        states={STATE_INPUT: [CallbackQueryHandler(handle_callback), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)]},
        fallbacks=[CommandHandler("cancel", cancel_cmd), CommandHandler("start", start)], allow_reentry=True
    )
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("cancel", cancel_cmd))
    print("🤖 Bot starting polling...")
    application.run_polling()

# Auto-start for gunicorn
def _auto_start_bot():
    if BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
        try:
            t = threading.Thread(target=run_bot, daemon=True)
            t.start()
            print("🤖 Bot thread auto-started for gunicorn")
        except Exception as e:
            print(f"Failed to auto-start: {e}")

# Start when imported by gunicorn or PORT env exists
if os.getenv("PORT") or os.getenv("RENDER"):
    _auto_start_bot()

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Flask starting on port {port}")
    flask_app.run(host="0.0.0.0", port=port)
