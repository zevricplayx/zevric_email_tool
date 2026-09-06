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
PROXY_URL = "http://ucclpuwm:3ci36r6ra5r1@31.59.20.176:6754"

def get_proxy_dict():
    return {"http": PROXY_URL, "https": PROXY_URL}

YOUTUBE_LINK = "https://youtube.com/@zevricxplay"
STATE_INPUT = 1

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

def fetch_bind_info_sync(access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        payload = {'app_id': "100067", 'access_token': access_token}
        headers = {'User-Agent': "GarenaMSDK/4.0.19P9"}
        proxy = get_proxy_dict()
        sess = requests.Session()
        sess.verify = False
        sess.proxies.update(proxy)
        r = sess.get(url, params=payload, headers=headers, timeout=10)
        if r.status_code == 200:
            return {"ok": True, "data": r.json()}
        else:
            return {"ok": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def send_otp_sync(email, access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
        headers = {"User-Agent": "GarenaMSDK/4.0.19P9", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "locale": "en_SG", "region": "SG", "app_id": "100067", "access_token": access_token}
        proxy = get_proxy_dict()
        sess = requests.Session()
        sess.verify = False
        sess.proxies.update(proxy)
        r = sess.post(url, headers=headers, data=data, timeout=10)
        j = r.json()
        return {"ok": j.get("result") == 0, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def send_single_unsubscribe_otp_sync(email, locale="en-SG", country="Singapore"):
    try:
        HARD_PROXY = "http://ucclpuwm:3ci36r6ra5r1@31.59.20.176:6754"
        proxy_options = [
            {"http": HARD_PROXY, "https": HARD_PROXY},
            None
        ]
        guest_headers = {
            "User-Agent": "GarenaMSDK/4.0.19P9(Realme RMX1921 ;Android 11;en;US;)",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        last_error = "No response"
        for proxy_dict in proxy_options:
            for attempt in range(3):
                try:
                    sess = requests.Session()
                    sess.verify = False
                    if proxy_dict:
                        sess.proxies.update(proxy_dict)
                    udid = ''.join(random.choices('0123456789abcdef', k=32))
                    g_url = "https://100067.connect.garena.com/oauth/guest/token/grant"
                    g_data = {"app_id": "100067", "udid": udid, "client_id": "100067", "client_secret": "8ba7d83f1f3a0d1d5a0a5b7a1b5e7a0e5"}
                    try:
                        gr = sess.post(g_url, data=g_data, headers=guest_headers, timeout=10)
                        gj = gr.json()
                    except Exception as e1:
                        last_error = str(e1)[:100]
                        try:
                            gr = sess.get(f"{g_url}?app_id=100067&udid={udid}&client_id=100067&client_secret=8ba7d83f1f3a0d1d5a0a5b7a1b5e7a0e5", headers=guest_headers, timeout=10)
                            gj = gr.json()
                        except Exception as e2:
                            last_error = str(e2)[:100]
                            continue
                    if "access_token" not in gj:
                        last_error = str(gj)[:100]
                        continue
                    token = gj["access_token"]
                    for loc, reg in [("en_SG", "SG"), ("en_IN", "IN")]:
                        try:
                            otp_url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
                            otp_data = {"email": email, "locale": loc, "region": reg, "app_id": "100067", "access_token": token}
                            ro = sess.post(otp_url, data=otp_data, headers=guest_headers, timeout=10)
                            jo = ro.json()
                            if jo.get("result") == 0 or '"result":0' in ro.text:
                                return {"ok": True, "data": jo, "email": email}
                            else:
                                last_error = str(jo)[:100]
                        except Exception as e3:
                            last_error = str(e3)[:100]
                            continue
                except Exception as e4:
                    last_error = str(e4)[:100]
                    continue
        return {"ok": False, "error": last_error, "email": email}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100], "email": email}

def verify_otp_sync(email, access_token, otp):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"app_id": "100067", "access_token": access_token, "email": email, "code": otp, "otp": otp, "type": "1"}
        proxy = get_proxy_dict()
        sess = requests.Session()
        sess.verify = False
        sess.proxies.update(proxy)
        r = sess.post(url, headers=headers, data=data, timeout=10)
        j = r.json()
        return {"ok": j.get("result") == 0 or "verifier_token" in j, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def verify_identity_otp_sync(email, access_token, otp):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "app_id": "100067", "access_token": access_token, "otp": otp}
        proxy = get_proxy_dict()
        sess = requests.Session()
        sess.verify = False
        sess.proxies.update(proxy)
        r = sess.post(url, headers=headers, data=data, timeout=10)
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
        proxy = get_proxy_dict()
        sess = requests.Session()
        sess.verify = False
        sess.proxies.update(proxy)
        r = sess.post(url, headers=headers, data=data, timeout=10)
        j = r.json()
        return {"ok": "identity_token" in j, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_bind_request_sync(email, access_token, verifier_token, sec_code):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "app_id": "100067", "access_token": access_token, "verifier_token": verifier_token, "secondary_password": sec_code}
        proxy = get_proxy_dict()
        sess = requests.Session()
        sess.verify = False
        sess.proxies.update(proxy)
        r = sess.post(url, headers=headers, data=data, timeout=10)
        j = r.json()
        return {"ok": j.get("result")==0, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_rebind_request_sync(identity_token, new_email, verifier_token, access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"identity_token": identity_token, "email": new_email, "app_id": "100067", "verifier_token": verifier_token, "access_token": access_token}
        proxy = get_proxy_dict()
        sess = requests.Session()
        sess.verify = False
        sess.proxies.update(proxy)
        r = sess.post(url, headers=headers, data=data, timeout=10)
        j = r.json()
        return {"ok": j.get("result")==0, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_unbind_request_sync(identity_token, access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"app_id": "100067", "access_token": access_token, "identity_token": identity_token}
        proxy = get_proxy_dict()
        sess = requests.Session()
        sess.verify = False
        sess.proxies.update(proxy)
        r = sess.post(url, headers=headers, data=data, timeout=10)
        j = r.json()
        return {"ok": j.get("result")==0, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def cancel_request_sync(access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"app_id": "100067", "access_token": access_token}
        proxy = get_proxy_dict()
        sess = requests.Session()
        sess.verify = False
        sess.proxies.update(proxy)
        r = sess.post(url, headers=headers, data=data, timeout=10)
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
        headers = {'User-Agent': "GarenaMSDK/4.0.19P9"}
        proxy = get_proxy_dict()
        sess = requests.Session()
        sess.verify = False
        sess.proxies.update(proxy)
        r = sess.get(url, params=params, headers=headers, timeout=10)
        if r.status_code!=200: return {"ok": False, "error": f"HTTP {r.status_code}"}
        d = r.json()
        return {"ok": True, "bounded": d.get("bounded_accounts",[]), "available": d.get("available_platforms",[])}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def fetch_login_history_sync(token_input):
    if not PROTOBUF_AVAILABLE:
        return {"ok": False, "error": "Protobuf missing"}
    try:
        import base64
        jwt_token = None
        if token_input.startswith("ey") and "." in token_input:
            jwt_token = token_input
        else:
            oId = None
            try:
                r = requests.get(f"https://100067.connect.garena.com/oauth/token/inspect?token={token_input}", headers={"User-Agent": "Mozilla/5.0"}, timeout=5).json()
                oId = r.get("open_id")
            except:
                pass
            if not oId:
                try:
                    uid_headers = {"access-token": token_input, "user-agent": "Mozilla/5.0"}
                    uid_res = requests.get("https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/", headers=uid_headers, verify=False, timeout=5).json()
                    uid = uid_res.get("uid")
                    if uid:
                        openid_res = requests.post("https://topup.pk/api/auth/player_id_login", json={"app_id": 100067, "login_id": str(uid)}, verify=False, timeout=5).json()
                        oId = openid_res.get("open_id")
                except:
                    pass
            if not oId:
                return {"ok": False, "error": "Open ID extract failed - token invalid"}
            for p_type in [8,3,4,6]:
                pl = build_majorlogin(token_input, oId, p_type)
                if not pl:
                    continue
                try:
                    mLhDr = {"User-Agent": "Dalvik/2.1.0", "Content-Type": "application/octet-stream", "Expect": "100-continue", "X-GA": "v1 1", "X-Unity-Version": "2018.4.11f1", "ReleaseVersion": "OB52"}
                    x = requests.post("https://loginbp.ggpolarbear.com/MajorLogin", headers=mLhDr, data=pl, timeout=10, verify=False)
                    if x.status_code==200:
                        res = mLrPb.MajorLoginRes()
                        try:
                            res.ParseFromString(dec(x.content))
                        except:
                            res.ParseFromString(x.content)
                        if res.token:
                            jwt_token = res.token
                            break
                except:
                    continue
            if not jwt_token:
                return {"ok": False, "error": "MajorLogin failed"}
        try:
            payload_b64 = jwt_token.split('.')[1]
            payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
            decoded = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
            name = urllib.parse.unquote(decoded.get("nickname","Unknown"))
            uid = decoded.get("account_id","Unknown")
            region = decoded.get("lock_region","Unknown")
            p_id = decoded.get("external_type",0)
            platform = PLATFORM_MAP_SIMPLE.get(p_id, f"Unknown ({p_id})")
        except:
            name=uid=region=platform="Unknown"
        hH = {"Expect": "100-continue", "Authorization": f"Bearer {jwt_token}", "X-Unity-Version": "2018.4.11f1", "X-GA": "v1 1", "ReleaseVersion": "OB52", "Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Dalvik/2.1.0"}
        r = requests.post("https://client.ind.freefiremobile.com/GetLoginHistory", headers=hH, data=enc(b""), timeout=15, verify=False)
        if r.status_code!=200:
            return {"ok": False, "error": f"HTTP {r.status_code}"}
        try:
            d = dec(r.content)
        except:
            d = r.content
        records = parse_history_protobuf(d)
        return {"ok": True, "records": records, "player": {"name": name, "uid": uid, "region": region, "platform": platform}}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def get_reply_keyboard():
    if HAS_STYLE:
        keyboard = [
            [KeyboardButton(text="Check Recovery Email", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="Bind Email", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="Unbind Email", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="Change Bind Email", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="Cancel Bind Request", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="Eat To Access Token", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="Revoke Access Token", style=KeyboardButtonStyle.DANGER), KeyboardButton(text="Get Login History", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="Check Bound Accounts", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="Send Single Unsubscribe Otp", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="Send Double Unsubscribe Otp", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="Owner Details", style=KeyboardButtonStyle.PRIMARY)],
        ]
    else:
        keyboard = [
            ["Check Recovery Email", "Bind Email"],
            ["Unbind Email", "Change Bind Email"],
            ["Cancel Bind Request", "Eat To Access Token"],
            ["Revoke Access Token", "Get Login History"],
            ["Check Bound Accounts", "Send Single Unsubscribe Otp"],
            ["Send Double Unsubscribe Otp", "Owner Details"],
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

def get_method_keyboard():
    if HAS_STYLE:
        keyboard = [
            [KeyboardButton(text="Via Email Otp", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="Via Security Code", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="Back To Menu", style=KeyboardButtonStyle.DANGER)],
        ]
    else:
        keyboard = [["Via Email Otp", "Via Security Code"], ["Back To Menu"]]
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
    first_name = update.effective_user.first_name or "User"
    welcome = f"Welcome {first_name}!\n\nSelect an option from below menu 👇"
    await update.message.reply_text(welcome, reply_markup=get_youtube_keyboard())
    await update.message.reply_text("Main Menu", reply_markup=get_reply_keyboard())
    return STATE_INPUT

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Main Menu", reply_markup=get_reply_keyboard())
    return STATE_INPUT

async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Cancelled. Main Menu", reply_markup=get_reply_keyboard())
    return STATE_INPUT

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return STATE_INPUT

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.strip()
        flow = context.user_data.get("flow")
        step = context.user_data.get("step")

        if "double" in text.lower() and "unsub" in text.lower():
            await update.message.reply_text("Double Unsubscribe OTP\n\nComing Soon...", reply_markup=get_reply_keyboard())
            return STATE_INPUT

        if "single" in text.lower() and "unsub" in text.lower():
            context.user_data.clear()
            context.user_data["flow"] = "single_unsub"
            context.user_data["step"] = "email"
            await update.message.reply_text("Please Enter Your Email Address:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text.lower() in ["check bind info", "check recovery email"]:
            context.user_data.clear()
            context.user_data["flow"] = "bind_info"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text.lower() == "bind email":
            context.user_data.clear()
            context.user_data["flow"] = "bind"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text.lower() == "unbind email":
            context.user_data.clear()
            context.user_data["flow"] = "unbind"
            context.user_data["step"] = "method"
            await update.message.reply_text("Choose Unbind Method:", reply_markup=get_method_keyboard())
            return STATE_INPUT

        if text.lower() == "change bind email":
            context.user_data.clear()
            context.user_data["flow"] = "change"
            context.user_data["step"] = "method"
            await update.message.reply_text("Choose Change Method:", reply_markup=get_method_keyboard())
            return STATE_INPUT

        if text.lower() == "cancel bind request":
            context.user_data.clear()
            context.user_data["flow"] = "cancel"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text.lower() == "eat to access token":
            context.user_data.clear()
            context.user_data["flow"] = "eat"
            context.user_data["step"] = "eat"
            await update.message.reply_text("Please Enter EAT Token Or EAT Link:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text.lower() == "revoke access token":
            context.user_data.clear()
            context.user_data["flow"] = "revoke"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text.lower() == "get login history":
            context.user_data.clear()
            context.user_data["flow"] = "login_history"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text.lower() == "check bound accounts":
            context.user_data.clear()
            context.user_data["flow"] = "bound"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please Enter Your Access Token:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text.lower() == "owner details":
            await update.message.reply_text("Owner: @just_zevric\nYouTube: Zevric X Play", reply_markup=get_youtube_keyboard())
            await update.message.reply_text("Main Menu", reply_markup=get_reply_keyboard())
            return STATE_INPUT

        if text.lower() == "back to menu":
            context.user_data.clear()
            await update.message.reply_text("Main Menu", reply_markup=get_reply_keyboard())
            return STATE_INPUT

        if flow == "single_unsub":
            if step == "email":
                email = text.strip()
                if "@" not in email or "." not in email:
                    await update.message.reply_text("Invalid Email! Please Enter Valid Email:")
                    return STATE_INPUT
                await update.message.reply_text(f"Sending Single Unsubscribe OTP to {email}...", reply_markup=get_youtube_keyboard())
                res = send_single_unsubscribe_otp_sync(email)
                if res.get("ok"):
                    await update.message.reply_text(f"OTP Sent Successfully!\n\nEmail: {email}\n\nPlease Check Your Inbox For Verification Code.", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Failed To Send OTP: {res.get('error','No response')}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "bind_info":
            if step == "token":
                await update.message.reply_text("Fetching Bind Info...", reply_markup=get_youtube_keyboard())
                bind = fetch_bind_info_sync(text)
                if not bind["ok"]:
                    await update.message.reply_text(f"Error: {bind['error']}", reply_markup=get_youtube_keyboard())
                else:
                    data = bind["data"]
                    email = data.get("email", "")
                    email_to_be = data.get("email_to_be", "")
                    countdown = data.get("request_exec_countdown", 0)
                    countdown_human = convert_seconds(countdown)
                    # Font style exactly like screenshot - Title Case, clean
                    if email_to_be:
                        msg = f"Email Information\n\nEmail: {email_to_be}\nConfirm In: {countdown_human}"
                    else:
                        if email:
                            msg = f"Email Information\n\nEmail: {email}\nConfirm In: No Pending Request"
                        else:
                            msg = f"Email Information\n\nEmail: None\nConfirm In: No Pending Request"
                    await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu", reply_markup=get_reply_keyboard())
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
                    await update.message.reply_text(f"Failed To Send OTP: {res.get('data')}", reply_markup=get_youtube_keyboard())
                return STATE_INPUT
            if step == "otp":
                res = verify_otp_sync(context.user_data["email"], context.user_data["token"], text)
                if res["ok"]:
                    vt = res["data"].get("verifier_token")
                    await update.message.reply_text("Please Enter Secondary Password (6-Digit):", reply_markup=get_youtube_keyboard())
                    context.user_data["verifier_token"] = vt
                    context.user_data["step"] = "sec"
                else:
                    await update.message.reply_text(f"Verify Failed: {res['data']}")
                return STATE_INPUT
            if step == "sec":
                res = create_bind_request_sync(context.user_data["email"], context.user_data["token"], context.user_data["verifier_token"], text)
                if res["ok"]:
                    await update.message.reply_text(f"Bind Success: {res['data']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Bind Failed: {res['data']}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "unbind":
            if step == "method":
                if "otp" in text.lower():
                    context.user_data["method"] = "otp"
                else:
                    context.user_data["method"] = "sec"
                await update.message.reply_text("Please Enter Access Token For Unbind:", reply_markup=get_youtube_keyboard())
                context.user_data["step"] = "token"
                return STATE_INPUT
            if step == "token":
                context.user_data["token"] = text
                bind = fetch_bind_info_sync(text)
                if not bind["ok"] or not bind["data"].get("email"):
                    await update.message.reply_text("No Bound Email Found.", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu", reply_markup=get_reply_keyboard())
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
                        await update.message.reply_text(f"Failed To Send OTP: {res['data']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text("Please Enter 6-Digit Security Code:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "sec_code"
                return STATE_INPUT
            if step == "otp":
                res = verify_identity_otp_sync(context.user_data["email"], context.user_data["token"], text)
                if res["ok"]:
                    id_token = res["data"].get("identity_token")
                    unr = create_unbind_request_sync(id_token, context.user_data["token"])
                    if unr["ok"]:
                        await update.message.reply_text(f"Unbind Success\n{unr['data']}", reply_markup=get_youtube_keyboard())
                    else:
                        await update.message.reply_text(f"Unbind Failed: {unr['data']}", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                else:
                    await update.message.reply_text(f"Verify Failed: {res['data']}\nPlease Enter OTP Again:")
                return STATE_INPUT
            if step == "sec_code":
                res = verify_identity_sec_sync(context.user_data["email"], context.user_data["token"], text)
                if res["ok"]:
                    id_token = res["data"].get("identity_token")
                    unr = create_unbind_request_sync(id_token, context.user_data["token"])
                    if unr["ok"]:
                        await update.message.reply_text(f"Unbind Success\n{unr['data']}", reply_markup=get_youtube_keyboard())
                    else:
                        await update.message.reply_text(f"Unbind Failed: {unr['data']}", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                else:
                    await update.message.reply_text(f"Verify Failed: {res['data']}\nPlease Enter Sec Code Again:")
                return STATE_INPUT

        if flow == "change":
            if step == "method":
                if "otp" in text.lower():
                    context.user_data["method"] = "otp"
                else:
                    context.user_data["method"] = "sec"
                await update.message.reply_text("Please Enter Access Token For Change Email:", reply_markup=get_youtube_keyboard())
                context.user_data["step"] = "token"
                return STATE_INPUT
            if step == "token":
                context.user_data["token"] = text
                bind = fetch_bind_info_sync(text)
                if not bind["ok"] or not bind["data"].get("email"):
                    await update.message.reply_text("No Bound Email Found.", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                old_email = bind["data"].get("email")
                context.user_data["old_email"] = old_email
                if context.user_data.get("method") == "otp":
                    await update.message.reply_text(f"Current Email: {old_email}\nSending OTP...", reply_markup=get_youtube_keyboard())
                    res = send_otp_sync(old_email, text)
                    if res["ok"]:
                        await update.message.reply_text("OTP Sent To Old Email, Please Enter OTP:", reply_markup=get_youtube_keyboard())
                        context.user_data["step"] = "old_otp"
                    else:
                        await update.message.reply_text(f"Failed To Send OTP: {res['data']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text("Please Enter 6-Digit Security Code For Old Email:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "sec_code"
                return STATE_INPUT
            if step == "sec_code":
                res = verify_identity_sec_sync(context.user_data["old_email"], context.user_data["token"], text)
                if res["ok"]:
                    context.user_data["identity_token"] = res["data"].get("identity_token")
                    await update.message.reply_text("Identity Verified! Please Enter New Email:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "new_email"
                else:
                    await update.message.reply_text(f"Verify Failed: {res['data']}")
                return STATE_INPUT
            if step == "old_otp":
                res = verify_identity_otp_sync(context.user_data["old_email"], context.user_data["token"], text)
                if res["ok"]:
                    context.user_data["identity_token"] = res["data"].get("identity_token")
                    await update.message.reply_text("Old Email Verified! Please Enter New Email:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "new_email"
                else:
                    await update.message.reply_text(f"Verify Failed: {res['data']}")
                return STATE_INPUT
            if step == "new_email":
                context.user_data["new_email"] = text
                await update.message.reply_text(f"Sending OTP To {text}...", reply_markup=get_youtube_keyboard())
                res = send_otp_sync(text, context.user_data["token"])
                if res["ok"]:
                    await update.message.reply_text(f"OTP Sent To New Email {text}, Please Enter OTP:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "new_otp"
                else:
                    await update.message.reply_text(f"Failed To Send OTP: {res['data']}")
                return STATE_INPUT
            if step == "new_otp":
                res = verify_otp_sync(context.user_data["new_email"], context.user_data["token"], text)
                if res["ok"] and res["data"].get("verifier_token"):
                    context.user_data["verifier_token"] = res["data"].get("verifier_token")
                    rebind = create_rebind_request_sync(context.user_data["identity_token"], context.user_data["new_email"], context.user_data["verifier_token"], context.user_data["token"])
                    if rebind["ok"]:
                        await update.message.reply_text(f"Change Success\n{rebind['data']}", reply_markup=get_youtube_keyboard())
                    else:
                        await update.message.reply_text(f"Change Failed: {rebind['data']}", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                else:
                    await update.message.reply_text(f"Verify Failed: {res.get('data')}")
                return STATE_INPUT

        if flow == "cancel":
            if step == "token":
                await update.message.reply_text("Cancelling...", reply_markup=get_youtube_keyboard())
                res = cancel_request_sync(text)
                if res["ok"]:
                    await update.message.reply_text("Cancel Success!", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Cancel Failed: {res.get('data')}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "eat":
            if step == "eat":
                await update.message.reply_text("Converting EAT...", reply_markup=get_youtube_keyboard())
                res = eat_to_token_sync(text)
                if res["ok"]:
                    await update.message.reply_text(f"Token: {res['access_token']}\nAccount: {res['account_id']}\nNickname: {res['nickname']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Failed: {res.get('error')}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "revoke":
            if step == "token":
                await update.message.reply_text("Revoking...", reply_markup=get_youtube_keyboard())
                res = revoke_token_sync(text)
                if res["ok"]:
                    await update.message.reply_text(f"Revoked! Account: {res.get('account_id')}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Revoke Failed: {res.get('error')}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu", reply_markup=get_reply_keyboard())
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
                await update.message.reply_text("Main Menu", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "login_history":
            if step == "token":
                await update.message.reply_text("Fetching Login History...", reply_markup=get_youtube_keyboard())
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
                await update.message.reply_text("Main Menu", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        await update.message.reply_text("Main Menu", reply_markup=get_reply_keyboard())
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
    return f"Bot Running - Final Fixed No Error"

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
            entry_points=[CommandHandler("start", start), CommandHandler("menu", menu_cmd), MessageHandler(filters.Regex("(?i)^(check recovery email|check bind info|bind email|unbind email|change bind email|cancel bind request|eat to access token|revoke access token|get login history|check bound accounts|owner details|send single unsubscribe otp|single unsubscribe otp|send double unsubscribe otp|double unsubscribe otp)$"), handle_text)],
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
