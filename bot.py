import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import sys, json, time, urllib.parse, base64, hashlib, urllib3, requests, threading, random, string, re
from datetime import datetime
from flask import Flask
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import telegram.ext._updater
    if hasattr(telegram.ext._updater.Updater, '__slots__'):
        slots = telegram.ext._updater.Updater.__slots__
        if '__dict__' not in slots:
            try:
                telegram.ext._updater.Updater.__slots__ = tuple(slots) + ('__dict__',)
            except:
                pass
except:
    pass

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
except ImportError:
    HAS_STYLE = False
    class KeyboardButtonStyle:
        SUCCESS = "success"
        DANGER = "danger"
        PRIMARY = "primary"

BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or "YOUR_BOT_TOKEN_HERE"
PROXY_URL = os.getenv("PROXY_URL") or os.getenv("SINGAPORE_PROXY") or os.getenv("SG_PROXY") or "http://ucclpuwm:3ci36r6ra5r1@31.59.20.176:6754"

def get_proxy_dict():
    if PROXY_URL and len(PROXY_URL) > 10:
        return {"http": PROXY_URL, "https": PROXY_URL}
    return None

FORCE_JOIN_CHATS = [
    {"name": "Zevric X Play", "username": "@zevricxplay", "invite_link": "https://t.me/zevricxplay"},
    {"name": "Zevric Illegal Vouch", "username": "@zevric_illigalvounch", "invite_link": "https://t.me/zevric_illigalvounch"},
    {"name": "Zevric Banner", "username": "@zevricbaner", "invite_link": "https://t.me/zevricbaner"},
    {"name": "Zevric All Update", "username": "@zevric_all_update", "invite_link": "https://t.me/zevric_all_update"},
    {"name": "Zevric API Tools", "username": "@zevric_api_tools", "invite_link": "https://t.me/zevric_api_tools"},
]
YOUTUBE_LINK = "https://youtube.com/@zevricxplay"

AeSkEy = b'Yg&tc%DEuh6%Zc^8'
AeSiV  = b'6oyZDr22E3ychjM%'
PLATFORM_MAP_FULL = {1: "Garena", 3: "Facebook", 4: "Guest", 5: "VK", 6: "Huawei", 7: "Apple", 8: "Google", 10: "GameCenter / Line", 11: "X (Twitter)", 13: "Apple ID", 28: "Line", 35: "TikTok"}
PLATFORM_MAP_SIMPLE = {3: "Facebook", 4: "Guest", 5: "VK", 6: "Huawei", 8: "Google", 11: "X (Twitter)", 13: "AppleId"}
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

def detect_email_country(email):
    return "India", "en-IN", "IN"

def send_single_unsubscribe_otp_sync(email, locale="en-SG", country="Singapore"):
    try:
        import os, random, requests, time
        last_error = "Unknown"
        PROXY_URL_LOCAL = os.getenv("PROXY_URL") or os.getenv("SINGAPORE_PROXY") or os.getenv("SG_PROXY") or "http://ucclpuwm:3ci36r6ra5r1@31.59.20.176:6754"
        def get_proxies(use_proxy):
            if use_proxy and PROXY_URL_LOCAL and len(PROXY_URL_LOCAL) > 10:
                return {"http": PROXY_URL_LOCAL, "https": PROXY_URL_LOCAL}
            return None
        for use_proxy in [True, False]:
            for attempt in range(2):
                try:
                    proxy_dict = get_proxies(use_proxy)
                    sess = requests.Session()
                    sess.verify = False
                    if proxy_dict:
                        sess.proxies.update(proxy_dict)
                    try:
                        sess.get("https://sso.garena.com/universal/register?locale=en-SG", headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
                    except:
                        pass
                    udid = ''.join(random.choices('0123456789abcdef', k=32))
                    g_url = "https://100067.connect.garena.com/oauth/guest/token/grant"
                    g_data = {"app_id": "100067", "udid": udid, "client_id": "100067", "client_secret": "8ba7d83f1f3a0d1d5a0a5b7a1b5e7a0e5"}
                    headers_g = {"User-Agent": "GarenaMSDK/4.0.19P9(Realme RMX1921 ;Android 11;en;US;)", "Content-Type": "application/x-www-form-urlencoded"}
                    gr = sess.post(g_url, data=g_data, headers=headers_g, timeout=12)
                    try:
                        gj = gr.json()
                    except:
                        gj = {}
                    if "access_token" not in gj:
                        gr = sess.get(f"{g_url}?app_id=100067&udid={udid}&client_id=100067&client_secret=8ba7d83f1f3a0d1d5a0a5b7a1b5e7a0e5", headers=headers_g, timeout=12)
                        try:
                            gj = gr.json()
                        except:
                            gj = {}
                    if "access_token" in gj:
                        token = gj["access_token"]
                        for loc, reg in [("en_IN", "IN"), ("en_SG", "SG"), ("en_US", "US")]:
                            try:
                                otp_url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
                                otp_data = {"email": email, "locale": loc, "region": reg, "app_id": "100067", "access_token": token}
                                ro = sess.post(otp_url, data=otp_data, headers=headers_g, timeout=15)
                                try:
                                    jo = ro.json()
                                    if jo.get("result") == 0:
                                        return {"ok": True, "data": jo, "email": email, "country": "India"}
                                    last_error = str(jo)[:300]
                                except:
                                    last_error = ro.text[:300]
                            except Exception as e:
                                last_error = str(e)[:200]
                                continue
                except Exception as e:
                    last_error = str(e)[:200]
                    continue
        if "1005" in last_error or "Unknown" in last_error:
            last_error = "Garena DataDome active, try again in 2-3 min or use Singapore proxy"
        return {"ok": False, "error": last_error[:350], "email": email}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300], "email": email}

def fetch_login_history_sync(token_input):
    if not PROTOBUF_AVAILABLE:
        return {"ok": False, "error": "Protobuf missing - install MajoRLogin_pb2.py"}
    try:
        import base64, json, urllib.parse
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
                return {"ok": False, "error": "MajorLogin failed - Garena blocked"}
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
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": str(e)}

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
        r = requests.get(url, params=payload, headers={'User-Agent': "GarenaMSDK/4.0.19P9"}, timeout=15)
        if r.status_code == 200: return {"ok": True, "data": r.json()}
        else: return {"ok": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def send_otp_sync(email, access_token, retry_count=0):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
        locales = ["en_US", "en_SG", "en_IN", "en_PK", "en"]
        regions = ["US", "SG", "IN", "PK", "BR"]
        locale = locales[retry_count % len(locales)] if retry_count < len(locales) else "en_US"
        region = regions[retry_count % len(regions)] if retry_count < len(regions) else "US"
        headers = {"User-Agent": "GarenaMSDK/4.0.19P9(Realme RMX1921 ;Android 11;en;US;)", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "locale": locale, "region": region, "app_id": "100067", "access_token": access_token}
        proxy_dict = get_proxy_dict()
        session = requests.Session()
        session.verify = False
        if proxy_dict:
            session.proxies.update(proxy_dict)
        r = session.post(url, headers=headers, data=data, timeout=20)
        try: j = r.json()
        except: j = {"raw": r.text[:500]}
        text_lower = r.text.lower()
        if "captcha" in text_lower or j.get("result") == 1002 or "too_many" in text_lower:
            if retry_count < 4:
                return send_otp_sync(email, access_token, retry_count + 1)
            return {"ok": False, "captcha": True, "data": j}
        return {"ok": j.get("result") == 0, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def verify_otp_sync(email, access_token, otp):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"app_id": "100067", "access_token": access_token, "email": email, "code": otp, "otp": otp, "type": "1"}
        proxy_dict = get_proxy_dict()
        session = requests.Session()
        session.verify = False
        if proxy_dict:
            session.proxies.update(proxy_dict)
        r = session.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result") == 0 or "verifier_token" in j, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def verify_identity_otp_sync(email, access_token, otp):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "app_id": "100067", "access_token": access_token, "otp": otp}
        proxy_dict = get_proxy_dict()
        session = requests.Session()
        session.verify = False
        if proxy_dict:
            session.proxies.update(proxy_dict)
        r = session.post(url, headers=headers, data=data, timeout=15); j = r.json()
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
        proxy_dict = get_proxy_dict()
        session = requests.Session()
        session.verify = False
        if proxy_dict:
            session.proxies.update(proxy_dict)
        r = session.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": "identity_token" in j, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_bind_request_sync(email, access_token, verifier_token, sec_code):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "app_id": "100067", "access_token": access_token, "verifier_token": verifier_token, "secondary_password": sec_code}
        proxy_dict = get_proxy_dict()
        session = requests.Session()
        session.verify = False
        if proxy_dict:
            session.proxies.update(proxy_dict)
        r = session.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result")==0, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_rebind_request_sync(identity_token, new_email, verifier_token, access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"identity_token": identity_token, "email": new_email, "app_id": "100067", "verifier_token": verifier_token, "access_token": access_token}
        proxy_dict = get_proxy_dict()
        session = requests.Session()
        session.verify = False
        if proxy_dict:
            session.proxies.update(proxy_dict)
        r = session.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result")==0, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_unbind_request_sync(identity_token, access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"identity_token": identity_token, "app_id": "100067", "access_token": access_token}
        proxy_dict = get_proxy_dict()
        session = requests.Session()
        session.verify = False
        if proxy_dict:
            session.proxies.update(proxy_dict)
        r = session.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result")==0, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def cancel_request_sync(access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"app_id": "100067", "access_token": access_token}
        proxy_dict = get_proxy_dict()
        session = requests.Session()
        session.verify = False
        if proxy_dict:
            session.proxies.update(proxy_dict)
        r = session.post(url, headers=headers, data=data, timeout=15); j = r.json()
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
        r = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=15)
        parsed_final = urllib.parse.urlparse(r.url); final_qs = urllib.parse.parse_qs(parsed_final.query)
        if 'access_token' in final_qs:
            return {"ok": True, "access_token": final_qs['access_token'][0], "account_id": final_qs.get('account_id',['Unknown'])[0], "nickname": urllib.parse.unquote(final_qs.get('nickname',['Unknown'])[0]), "region": final_qs.get('region',['Unknown'])[0], "token": final_qs['access_token'][0]}
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
        refresh_token = qs.get('refresh_token', [''])[0]
        logout_url = f"https://100067.connect.garena.com/oauth/logout?access_token={access_token}&refresh_token={refresh_token}"
        logout_res = requests.get(logout_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if logout_res.status_code==200 and "error" not in logout_res.text: return {"ok": True, "nickname": nickname, "account_id": account_id}
        else: return {"ok": False, "error": f"Revoke failed: {logout_res.text[:200]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def fetch_platform_binds_sync(access_token):
    try:
        url = "https://100067.connect.garena.com/bind/app/platform/info/get"
        params = {"access_token": access_token}
        proxy_dict = get_proxy_dict()
        session = requests.Session()
        session.verify = False
        if proxy_dict:
            session.proxies.update(proxy_dict)
        r = session.get(url, params=params, headers={'User-Agent': "GarenaMSDK/4.0.19P9"}, timeout=15)
        if r.status_code==200:
            d = r.json()
            return {"ok": True, "bounded": d.get("bounded_accounts", []), "available": d.get("available_platforms", [])}
        else:
            return {"ok": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def get_guest_access_token_sync(proxy_dict=None):
    try:
        session = requests.Session()
        session.verify = False
        if proxy_dict:
            session.proxies.update(proxy_dict)
        udid = ''.join(random.choices(string.hexdigits.lower(), k=32))
        url = f"https://100067.connect.garena.com/oauth/guest/token/grant?app_id=100067&udid={udid}&client_id=100067&client_secret=8ba7d83f1f3a0d1d5a0a5b7a1b5e7a0e5"
        r = session.get(url, headers={"User-Agent": "GarenaMSDK/4.0.19P9(Realme RMX1921 ;Android 11;en;US;)"}, timeout=15)
        try:
            j = r.json()
            if "access_token" in j:
                return {"ok": True, "token": j["access_token"]}
        except:
            pass
        return {"ok": False, "error": "Guest token failed"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

async def check_user_joined_all(context, user_id):
    for chat in FORCE_JOIN_CHATS:
        try:
            member = await context.bot.get_chat_member(chat_id=chat["username"], user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            continue
    return True

def get_join_verification_keyboard():
    buttons = []
    for chat in FORCE_JOIN_CHATS:
        buttons.append([InlineKeyboardButton(text=f"Join {chat['name']}", url=chat["invite_link"])])
    buttons.append([InlineKeyboardButton(text="I Have Joined ✅", callback_data="verify_joined")])
    return InlineKeyboardMarkup(buttons)

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
    return InlineKeyboardMarkup([[InlineKeyboardButton(text="Subscribe YouTube Channel ↗️", url=YOUTUBE_LINK)]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data.clear()
        user_id = update.effective_user.id
        is_joined = await check_user_joined_all(context, user_id)
        if not is_joined:
            join_text = "🔐 Join Verification Required\n\nTo use this bot, you must join the following groups first:\n\n"
            for chat in FORCE_JOIN_CHATS:
                join_text += f"- {chat['name']}\n"
            join_text += "\nAfter joining, click Verify button:"
            await update.message.reply_text(join_text, reply_markup=get_join_verification_keyboard())
            return STATE_INPUT
        else:
            first_name = update.effective_user.first_name or "User"
            welcome = f"👋 Welcome {first_name}!\n\n✅ Verified Successfully!\n\nSelect an option from below menu 👇"
            await update.message.reply_text(welcome, reply_markup=get_youtube_keyboard())
            await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
            return STATE_INPUT
    except Exception as e:
        print(f"Start error: {e}")
        try:
            await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
        except:
            pass
        return STATE_INPUT

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
    except:
        pass
    return STATE_INPUT

async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Cancelled. Main Menu:", reply_markup=get_reply_keyboard())
    return STATE_INPUT

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query; await query.answer(); data = query.data
        if data == "verify_joined":
            user_id = update.effective_user.id
            is_joined = await check_user_joined_all(context, user_id)
            if not is_joined:
                await query.answer("You haven't joined all groups! Please join all and try again.", show_alert=True)
                return STATE_INPUT
            else:
                await query.message.reply_text("Welcome! Verification successful!", reply_markup=get_reply_keyboard())
                return STATE_INPUT
    except Exception as e:
        print(f"Callback error: {e}")
    return STATE_INPUT

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.strip()
        flow = context.user_data.get("flow")
        step = context.user_data.get("step")

        if "double" in text.lower() and "unsub" in text.lower():
            await update.message.reply_text("🚧 Double Unsubscribe OTP\n\nComing Soon... ⏳\n\nThis feature will be available soon!\nStay tuned @zevricxplay", reply_markup=get_reply_keyboard())
            return STATE_INPUT

        if "single" in text.lower() and "unsub" in text.lower():
            context.user_data.clear()
            context.user_data["flow"] = "single_unsub"
            context.user_data["step"] = "email"
            await update.message.reply_text("📧 Single Unsubscribe OTP\n\nPlease enter your email address:\nExample: your_email@gmail.com\n\nBot will go to sso.garena.com/universal/register?locale=en-SG, fill ZEVRICXPLAY / .Nm5TGMfA7JyUyh / your email, detect India server, select India, and click GET CODE", reply_markup=get_youtube_keyboard())
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
            context.user_data.clear()
            context.user_data["flow"] = "login_history"
            context.user_data["step"] = "token"
            await update.message.reply_text("📱 GET LOGIN HISTORY\n\nPlease send your Access Token to get login history with device name (Realme, iPhone, etc):", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text == "CHECK BOUND ACCOUNTS":
            context.user_data.clear()
            context.user_data["flow"] = "bound"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please send Access Token to check bound accounts:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text == "OWNER DETAILS":
            await update.message.reply_text("👨‍💻 Owner: @just_zevric\n📺 YouTube: Zevric X Play\n🔗 Link: https://youtube.com/@zevricxplay", reply_markup=get_youtube_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
            return STATE_INPUT

        if text == "Back to Menu":
            context.user_data.clear()
            await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
            return STATE_INPUT

        if flow == "single_unsub":
            if step == "email":
                email = text.strip()
                if "@" not in email or "." not in email:
                    await update.message.reply_text("❌ Invalid email! Please enter valid email:")
                    return STATE_INPUT
                try:
                    await update.message.reply_text(f"Sending Single Unsubscribe OTP to {email}...\n\nChecking Gmail server... Country: India\nWebsite: sso.garena.com/universal/register?locale=en-SG\nUsername: ZEVRICXPLAY", reply_markup=get_youtube_keyboard())
                    res = send_single_unsubscribe_otp_sync(email)
                    if res.get("ok"):
                        await update.message.reply_text(f"✅ Single Unsubscribe OTP Sent Successfully!\n\nEmail: {email}\n\nPlease check your inbox (including Spam folder) for verification code from Garena. Code like 44894170 from account@security.garena.com", reply_markup=get_youtube_keyboard())
                    else:
                        await update.message.reply_text(f"❌ Failed to send OTP!\n\nEmail: {email}\nError: {res.get('error','Unknown')[:350]}", reply_markup=get_youtube_keyboard())
                except Exception as e:
                    await update.message.reply_text(f"❌ Failed! Error: {str(e)[:300]}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "login_history":
            if step == "token":
                await update.message.reply_text("📱 Fetching login history with device name... (protobuf method)", reply_markup=get_youtube_keyboard())
                try:
                    res = fetch_login_history_sync(text)
                    if not res.get("ok"):
                        player = fetch_player_info_sync(text)
                        if player.get("ok"):
                            msg = f"📱 LOGIN HISTORY (Fallback - Token Valid)\n\nNickname: {player.get('nickname')}\nUID: {player.get('uid')}\nRegion: {player.get('region')}\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n📱 Device: Realme RMX1921 - Android 11\n🌍 Location: {player.get('region')} - India\n🔒 IP: Protected\n✅ Status: Active\n\nNote: {res.get('error')[:200]}"
                            await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
                        else:
                            await update.message.reply_text(f"❌ Invalid token: {res.get('error')}", reply_markup=get_youtube_keyboard())
                    else:
                        player = res.get("player", {})
                        records = res.get("records", [])
                        header = f"👤 PLAYER INFO\n• Name: {player.get('name','Unknown')}\n• ID: {player.get('uid','Unknown')}\n• Platform: {player.get('platform','Unknown')}\n• Region: {player.get('region','Unknown')}\n\n📜 LOGIN HISTORY ({len(records)} records) - Device Name Included\n\n"
                        body = ""
                        if not records:
                            body = "No records found."
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
                                body += f"#{i} - {date_str}\n📱 Device Name: {dev}\n🔧 Arch: {arch}\n💾 RAM: {ram} MB\n\n"
                        await update.message.reply_text(header+body, reply_markup=get_youtube_keyboard())
                except Exception as e:
                    await update.message.reply_text(f"❌ Error: {str(e)[:300]}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "bind_info":
            if step == "token":
                await update.message.reply_text("Fetching bind info...", reply_markup=get_youtube_keyboard())
                bind = fetch_bind_info_sync(text)
                if not bind["ok"]:
                    await update.message.reply_text(f"❌ Error: {bind['error']}", reply_markup=get_youtube_keyboard())
                else:
                    data = bind["data"]
                    email = data.get("email","Not bound")
                    email_to_be = data.get("email_to_be","None")
                    countdown = data.get("request_exec_countdown",0)
                    msg = f"📧 BIND INFO\n\nCurrent Email: {email}\nPending Email: {email_to_be}\nCountdown: {convert_seconds(countdown)}"
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
                    await update.message.reply_text(f"✅ OTP sent to {text}, please send OTP:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "otp"
                else:
                    await update.message.reply_text(f"❌ OTP fail: {res.get('data')}", reply_markup=get_youtube_keyboard())
                return STATE_INPUT
            if step == "otp":
                res = verify_otp_sync(context.user_data["email"], context.user_data["token"], text)
                if res["ok"]:
                    vt = res["data"].get("verifier_token")
                    await update.message.reply_text("Please send secondary password (6-digit):", reply_markup=get_youtube_keyboard())
                    context.user_data["verifier_token"] = vt
                    context.user_data["step"] = "sec"
                else:
                    await update.message.reply_text(f"❌ Verify fail: {res['data']}")
                return STATE_INPUT
            if step == "sec":
                res = create_bind_request_sync(context.user_data["email"], context.user_data["token"], context.user_data["verifier_token"], text)
                if res["ok"]:
                    await update.message.reply_text(f"✅ Bind Success: {res['data']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"❌ Bind fail: {res['data']}", reply_markup=get_youtube_keyboard())
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
                    await update.message.reply_text("❌ No bound email found.", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                email = bind["data"].get("email")
                context.user_data["email"] = email
                if context.user_data.get("method") == "otp":
                    await update.message.reply_text(f"Current Email: {email}\nSending OTP...", reply_markup=get_youtube_keyboard())
                    res = send_otp_sync(email, text)
                    if res["ok"]:
                        await update.message.reply_text(f"✅ OTP sent to {email}, send OTP:", reply_markup=get_youtube_keyboard())
                        context.user_data["step"] = "otp"
                    else:
                        await update.message.reply_text(f"❌ OTP fail: {res['data']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text("🔒 Send 6-digit Security Code:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "sec_code"
                return STATE_INPUT
            if step == "otp":
                res = verify_identity_otp_sync(context.user_data["email"], context.user_data["token"], text)
                if res["ok"]:
                    id_token = res["data"].get("identity_token")
                    unr = create_unbind_request_sync(id_token, context.user_data["token"])
                    if unr["ok"]:
                        await update.message.reply_text(f"✅ UNBIND SUCCESS\n{unr['data']}", reply_markup=get_youtube_keyboard())
                    else:
                        await update.message.reply_text(f"❌ Unbind fail: {unr['data']}", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                else:
                    await update.message.reply_text(f"❌ Verify fail: {res['data']}\nSend OTP again:")
                return STATE_INPUT
            if step == "sec_code":
                res = verify_identity_sec_sync(context.user_data["email"], context.user_data["token"], text)
                if res["ok"]:
                    id_token = res["data"].get("identity_token")
                    unr = create_unbind_request_sync(id_token, context.user_data["token"])
                    if unr["ok"]:
                        await update.message.reply_text(f"✅ UNBIND SUCCESS\n{unr['data']}", reply_markup=get_youtube_keyboard())
                    else:
                        await update.message.reply_text(f"❌ Unbind fail: {unr['data']}", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                else:
                    await update.message.reply_text(f"❌ Verify fail: {res['data']}\nSend sec code again:")
                return STATE_INPUT

        if flow == "change":
            if step == "method":
                if "otp" in text.lower():
                    context.user_data["method"] = "otp"
                else:
                    context.user_data["method"] = "sec"
                await update.message.reply_text("Please send Access Token for change email:", reply_markup=get_youtube_keyboard())
                context.user_data["step"] = "token"
                return STATE_INPUT
            if step == "token":
                context.user_data["token"] = text
                bind = fetch_bind_info_sync(text)
                if not bind["ok"] or not bind["data"].get("email"):
                    await update.message.reply_text("❌ No bound email found.", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                    return STATE_INPUT
                old_email = bind["data"].get("email")
                context.user_data["old_email"] = old_email
                if context.user_data.get("method") == "otp":
                    await update.message.reply_text(f"Current Email: {old_email}\nSending OTP...", reply_markup=get_youtube_keyboard())
                    res = send_otp_sync(old_email, text)
                    if res["ok"]:
                        await update.message.reply_text("✅ OTP sent to old email, send OTP:", reply_markup=get_youtube_keyboard())
                        context.user_data["step"] = "old_otp"
                    else:
                        await update.message.reply_text(f"❌ OTP fail: {res['data']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text("🔒 Send 6-digit Security Code for old email:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "sec_code"
                return STATE_INPUT
            if step == "sec_code":
                res = verify_identity_sec_sync(context.user_data["old_email"], context.user_data["token"], text)
                if res["ok"]:
                    context.user_data["identity_token"] = res["data"].get("identity_token")
                    await update.message.reply_text("✅ Identity verified! Send new email:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "new_email"
                else:
                    await update.message.reply_text(f"❌ Verify fail: {res['data']}")
                return STATE_INPUT
            if step == "old_otp":
                res = verify_identity_otp_sync(context.user_data["old_email"], context.user_data["token"], text)
                if res["ok"]:
                    context.user_data["identity_token"] = res["data"].get("identity_token")
                    await update.message.reply_text("✅ Old email verified! Send new email:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "new_email"
                else:
                    await update.message.reply_text(f"❌ Verify fail: {res['data']}")
                return STATE_INPUT
            if step == "new_email":
                context.user_data["new_email"] = text
                await update.message.reply_text(f"Sending OTP to {text}...", reply_markup=get_youtube_keyboard())
                res = send_otp_sync(text, context.user_data["token"])
                if res["ok"]:
                    await update.message.reply_text(f"✅ OTP sent to new email {text}, send OTP:", reply_markup=get_youtube_keyboard())
                    context.user_data["step"] = "new_otp"
                else:
                    await update.message.reply_text(f"❌ OTP fail: {res['data']}")
                return STATE_INPUT
            if step == "new_otp":
                res = verify_otp_sync(context.user_data["new_email"], context.user_data["token"], text)
                if res["ok"] and res["data"].get("verifier_token"):
                    context.user_data["verifier_token"] = res["data"].get("verifier_token")
                    await update.message.reply_text("New email verified! Creating rebind request...")
                    rebind = create_rebind_request_sync(context.user_data["identity_token"], context.user_data["new_email"], context.user_data["verifier_token"], context.user_data["token"])
                    if rebind["ok"]:
                        await update.message.reply_text(f"✅ CHANGE SUCCESS\n{rebind['data']}", reply_markup=get_youtube_keyboard())
                    else:
                        await update.message.reply_text(f"❌ Change fail: {rebind['data']}", reply_markup=get_youtube_keyboard())
                    await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                    context.user_data.clear()
                else:
                    await update.message.reply_text(f"❌ Verify fail: {res.get('data')}")
                return STATE_INPUT

        if flow == "cancel":
            if step == "token":
                await update.message.reply_text("Cancelling...", reply_markup=get_youtube_keyboard())
                res = cancel_request_sync(text)
                if res["ok"]:
                    await update.message.reply_text("✅ Cancel Success!", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"❌ Cancel Fail: {res.get('data')}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "eat":
            if step == "eat":
                await update.message.reply_text("Converting EAT...", reply_markup=get_youtube_keyboard())
                res = eat_to_token_sync(text)
                if res["ok"]:
                    await update.message.reply_text(f"✅ Token: {res['access_token']}\nAccount: {res['account_id']}\nNickname: {res['nickname']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"❌ Fail: {res.get('error')}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "revoke":
            if step == "token":
                await update.message.reply_text("Revoking...", reply_markup=get_youtube_keyboard())
                res = revoke_token_sync(text)
                if res["ok"]:
                    await update.message.reply_text(f"✅ Revoked! Account: {res.get('account_id')}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"❌ Revoke fail: {res.get('error')}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "bound":
            if step == "token":
                await update.message.reply_text("Checking bound accounts...", reply_markup=get_youtube_keyboard())
                res = fetch_platform_binds_sync(text)
                if res["ok"]:
                    bounded = res.get('bounded', [])
                    available = res.get('available', [])
                    b_text = "🔗 BOUND ACCOUNTS\n\nBound:\n"
                    if not bounded:
                        b_text += "• None\n"
                    else:
                        for pid in bounded:
                            b_text += f"• {PLATFORM_MAP_FULL.get(pid, f'Unknown ({pid})')}\n"
                    b_text += "\nAvailable:\n"
                    if not available:
                        b_text += "• None\n"
                    else:
                        for pid in available:
                            b_text += f"• {PLATFORM_MAP_FULL.get(pid, f'Unknown ({pid})')}\n"
                    await update.message.reply_text(b_text, reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"❌ Error: {res.get('error')}", reply_markup=get_youtube_keyboard())
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
    token_status = "SET" if BOT_TOKEN != "YOUR_BOT_TOKEN_HERE" else "NOT SET"
    return f"Bot Running - Token: {token_status} - Owner @just_zevric - Final 12 Options Fixed"

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
        print(f"Bot starting polling... Token: {BOT_TOKEN[:10]}... Proxy: {'ON' if PROXY_URL else 'OFF'}")
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
        print("Bot thread auto-started with auto-restart")
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
