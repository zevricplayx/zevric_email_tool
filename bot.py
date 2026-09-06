import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import sys, json, time, urllib.parse, base64, hashlib, urllib3, requests, threading, random, string, re
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
except ImportError:
    HAS_STYLE = False
    class KeyboardButtonStyle:
        SUCCESS = "success"
        DANGER = "danger"
        PRIMARY = "primary"

BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN_HERE"

# Your proxy from screenshot - UK London 31.59.20.176:6754
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


def send_single_unsubscribe_otp_sync(email, locale="en-SG", country="Singapore"):
    """
    REAL SEND - No Fake - Website + Game API both try
    User said: sso.garena.com pe jake ZEVRICXPLAY / .Nm5TGMfA7JyUyh daalke
    gmail check karke India/Singapore select karke GET CODE click
    """
    import traceback
    try:
        proxy_dict = get_proxy_dict()
        print(f"[REAL OTP] Starting for {email} Proxy: {PROXY_URL[:30] if PROXY_URL else 'None'}")
        
        # Check email server/country
        email_lower = email.lower()
        if ".in" in email_lower or "india" in country.lower():
            countries_to_try = ["India", "Singapore"]
            locales_to_try = ["en-IN", "en-SG"]
        else:
            countries_to_try = ["India", "Singapore", "Indonesia", "Thailand", "Philippines"]
            locales_to_try = ["en-IN", "en-SG", "en-ID", "en-TH", "en-PH"]
        
        username = "ZEVRICXPLAY"
        password = ".Nm5TGMfA7JyUyh"
        
        last_error = ""
        
        # METHOD 1: Game API bind:send_otp with guest token - MOST RELIABLE, REAL EMAIL
        # This sends email from account@security.garena.com same as registration
        print("[REAL OTP] Method 1: Guest token + bind:send_otp")
        try:
            session = requests.Session()
            session.verify = False
            if proxy_dict:
                session.proxies.update(proxy_dict)
            
            # Try guest token
            udid = ''.join(random.choices('abcdef0123456789', k=32))
            guest_url = f"https://100067.connect.garena.com/oauth/guest/token/grant?app_id=100067&udid={udid}&client_id=100067&client_secret=8ba7d83f1f3a0d1d5a0a5b7a1b5e7a0e5"
            try:
                r = session.get(guest_url, headers={"User-Agent": "GarenaMSDK/4.0.19P9"}, timeout=15)
                j = r.json()
                if "access_token" in j:
                    guest_token = j["access_token"]
                    print(f"[REAL OTP] Guest token OK: {guest_token[:20]}...")
                    # Now send OTP using guest token - REAL SEND
                    otp_url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
                    for loc in ["en_IN", "en_US", "en_SG"]:
                        for reg in ["IN", "US", "SG"]:
                            try:
                                data = {"email": email, "locale": loc, "region": reg, "app_id": "100067", "access_token": guest_token}
                                r2 = session.post(otp_url, headers={"User-Agent": "GarenaMSDK/4.0.19P9", "Content-Type": "application/x-www-form-urlencoded"}, data=data, timeout=20)
                                try:
                                    j2 = r2.json()
                                except:
                                    j2 = {}
                                print(f"[REAL OTP] Guest OTP {loc}/{reg} -> {r2.status_code} {str(j2)[:200]}")
                                if j2.get("result") == 0:
                                    print("[REAL OTP] REAL SUCCESS via guest token!")
                                    return {"ok": True, "data": j2, "email": email, "real": True, "method": "guest_game_api"}
                                last_error = str(j2)
                            except Exception as e:
                                last_error = str(e)
                                continue
            except Exception as e:
                last_error = str(e)
                print(f"[REAL OTP] Guest method error: {e}")
        except Exception as e:
            last_error = str(e)
        
        # METHOD 2: Direct SSO registration GET CODE - EXACT website flow
        print(f"[REAL OTP] Method 2: SSO website flow {countries_to_try}")
        for idx, country_name in enumerate(countries_to_try):
            locale_code = locales_to_try[idx] if idx < len(locales_to_try) else "en-SG"
            try:
                # Session per country
                sess = requests.Session()
                sess.verify = False
                if proxy_dict:
                    sess.proxies.update(proxy_dict)
                
                reg_url = f"https://sso.garena.com/universal/register?locale={locale_code}"
                try:
                    # Get page for cookies
                    rp = sess.get(reg_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}, timeout=15)
                    print(f"[REAL OTP] Reg page {country_name} {locale_code}: {rp.status_code}")
                except Exception as e:
                    print(f"[REAL OTP] Reg page fail {country_name}: {e}")
                    # Try without proxy if proxy fails
                    try:
                        sess2 = requests.Session()
                        sess2.verify = False
                        rp = sess2.get(reg_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                        print(f"[REAL OTP] Reg page direct {country_name}: {rp.status_code}")
                        sess = sess2
                    except:
                        pass
                
                # All possible GET CODE endpoints (from JS analysis)
                endpoints = [
                    "https://sso.garena.com/api/account/email/verify/send",
                    "https://sso.garena.com/api/account/email/send_code",
                    "https://sso.garena.com/api/register/email/send_code",
                    "https://sso.garena.com/api/account/email/code/send",
                    "https://account.garena.com/api/account/email/verify/send",
                    "https://sso.garena.com/api/account/email/code",
                    "https://sso.garena.com/api/v2/account/email/send",
                    "https://sso.garena.com/api/account/email/send_verify_code",
                ]
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Accept": "application/json, text/plain, */*",
                    "Origin": "https://sso.garena.com",
                    "Referer": reg_url,
                    "X-Requested-With": "XMLHttpRequest",
                }
                
                for ep_url in endpoints:
                    try:
                        # Try different payload formats exactly as website does
                        payloads = [
                            {"email": email, "username": f"{username}{random.randint(100,999)}", "password": password, "password_confirm": password, "country": country_name, "locale": locale_code},
                            {"email": email, "username": username, "password": password, "password2": password, "country": country_name, "locale": locale_code, "account": username},
                            {"email": email, "locale": locale_code, "country": country_name, "username": username, "password": password},
                            {"email": email, "locale": locale_code},
                        ]
                        
                        for pl in payloads:
                            try:
                                r = sess.post(ep_url, headers=headers, data=pl, timeout=20)
                                txt = r.text[:500]
                                print(f"[REAL OTP] {country_name} {ep_url} payload {list(pl.keys())} -> {r.status_code}: {txt[:200]}")
                                try:
                                    j = r.json()
                                except:
                                    j = {}
                                
                                # REAL SUCCESS CHECK - Only result 0 means email actually sent
                                if r.status_code == 200 and (j.get("result") == 0 or j.get("error") == 0 or j.get("code") == 0):
                                    print(f"[REAL OTP] REAL SUCCESS {country_name} via {ep_url}!")
                                    return {"ok": True, "data": j, "email": email, "country": country_name, "real": True, "endpoint": ep_url}
                                # Also check message contains sent
                                lower_txt = txt.lower()
                                if "code has been sent" in lower_txt or "email has been sent" in lower_txt or ("success" in lower_txt and "sent" in lower_txt):
                                    print(f"[REAL OTP] REAL SUCCESS (message) {country_name}!")
                                    return {"ok": True, "data": j, "email": email, "country": country_name, "real": True}
                                
                                last_error = f"{ep_url}: {txt[:200]}"
                            except Exception as e:
                                last_error = str(e)
                                continue
                    except Exception as e:
                        last_error = str(e)
                        continue
            except Exception as e:
                last_error = str(e)
                print(f"[REAL OTP] Country {country_name} exception: {e}")
                traceback.print_exc()
                continue
        
        # If all failed, return real error (not fake success)
        print(f"[REAL OTP] ALL FAILED Last error: {last_error}")
        return {"ok": False, "error": f"Real send failed. Last: {last_error[:300]}. Proxy may be dead (31.59.20.176:6754). Try new proxy from Webshare.", "email": email, "real": False}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": f"Exception: {str(e)}", "email": email, "real": False}


def verify_otp_sync(email, access_token, otp):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "otp": otp, "app_id": "100067", "access_token": access_token}
        proxy_dict = get_proxy_dict()
        session = requests.Session()
        session.verify = False
        if proxy_dict:
            session.proxies.update(proxy_dict)
        r = session.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result")==0 and "verifier_token" in j, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def verify_identity_otp_sync(email, access_token, otp):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity_otp"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "otp": otp, "app_id": "100067", "access_token": access_token}
        proxy_dict = get_proxy_dict()
        session = requests.Session()
        session.verify = False
        if proxy_dict:
            session.proxies.update(proxy_dict)
        r = session.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result")==0 and "identity_token" in j, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def verify_identity_sec_sync(email, access_token, code):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity_sec_code"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "sec_code": code, "app_id": "100067", "access_token": access_token}
        proxy_dict = get_proxy_dict()
        session = requests.Session()
        session.verify = False
        if proxy_dict:
            session.proxies.update(proxy_dict)
        r = session.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result")==0 and "identity_token" in j, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_rebind_request_sync(identity_token, new_email, verifier_token, access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"identity_token": identity_token, "new_email": new_email, "verifier_token": verifier_token, "app_id": "100067", "access_token": access_token}
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

def cancel_bind_request_sync(access_token):
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

def bind_email_sync(email, verifier_token, access_token):
    try:
        url = "https://100067.connect.garena.com/game/account_security/bind:bind_email"
        headers = {"User-Agent": "GarenaMSDK/4.0.30", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"email": email, "verifier_token": verifier_token, "app_id": "100067", "access_token": access_token}
        proxy_dict = get_proxy_dict()
        session = requests.Session()
        session.verify = False
        if proxy_dict:
            session.proxies.update(proxy_dict)
        r = session.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": j.get("result")==0, "data": j}
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
        r = session.get(url, params=params, headers={"User-Agent": "GarenaMSDK/4.0.19P9"}, timeout=10)
        if r.status_code!=200: return {"ok": False, "error": f"HTTP {r.status_code}"}
        d = r.json()
        return {"ok": True, "bounded": d.get("bounded_accounts",[]), "available": d.get("available_platforms",[])}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def eat_to_token_sync(eat):
    try:
        if "access_token=" in eat:
            parsed = urllib.parse.urlparse(eat); qs = urllib.parse.parse_qs(parsed.query)
            eat = qs.get("access_token", [eat])[0]
        url = f"https://100067.connect.garena.com/oauth/token/grant?grant_type=refresh_token&refresh_token={eat}&client_id=100067&client_secret=8ba7d83f1f3a0d1d5a0a5b7a1b5e7a0e5"
        proxy_dict = get_proxy_dict()
        session = requests.Session()
        session.verify = False
        if proxy_dict:
            session.proxies.update(proxy_dict)
        r = session.get(url, headers={"User-Agent": "GarenaMSDK/4.0.19P9"}, timeout=15)
        j = r.json()
        if "access_token" in j: return {"ok": True, "token": j["access_token"], "data": j}
        else: return {"ok": False, "data": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def revoke_token_sync(access_token):
    try:
        url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        proxy_dict = get_proxy_dict()
        session = requests.Session()
        session.verify = False
        if proxy_dict:
            session.proxies.update(proxy_dict)
        r = session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10, allow_redirects=True)
        parsed = urllib.parse.urlparse(r.url); qs = urllib.parse.parse_qs(parsed.query)
        nickname = urllib.parse.unquote(qs.get('nickname',['Unknown'])[0]); account_id = qs.get('account_id',['Unknown'])[0]
        refresh_token = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
        logout_url = f"https://100067.connect.garena.com/oauth/logout?access_token={access_token}&refresh_token={refresh_token}"
        logout_res = session.get(logout_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if logout_res.status_code==200 and "error" not in logout_res.text: return {"ok": True, "nickname": nickname, "account_id": account_id}
        else: return {"ok": False, "error": f"Revoke failed"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def decode_jwt_sync(jwt_token):
    try:
        if jwt_token.count('.') != 2:
            return {"ok": False}
        parts = jwt_token.split('.')
        payload = parts[1]
        payload += '=' * (-len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        data = json.loads(decoded)
        return {"ok": True, "data": data}
    except:
        return {"ok": False}

def get_jwt_from_access_token_sync(access_token):
    try:
        if not PROTOBUF_AVAILABLE:
            return {"ok": False}
        import time
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad, unpad
        major = mLpB.MajorLogin()
        major.event_time = str(int(time.time()))
        major.game_name = "freefire"
        major.platform_id = 4
        major.client_version = "1.108.5"
        major.system_software = "Android OS 13 / API-33"
        major.system_hardware = "qcom"
        major.telecom_operator = "Verizon"
        major.network_type = "Wifi"
        major.screen_width = 1920
        major.screen_height = 1080
        major.screen_dpi = "420"
        major.memory = 4096
        major.access_token = access_token
        major.open_id = ""
        major.open_id_type = ""
        major.device_type = "Handheld"
        major.client_ip = ""
        major.language = "en"
        major.login_by = 1
        major.analytics_detail = b""
        serialized = major.SerializeToString()
        cipher = AES.new(AeSkEy, AES.MODE_CBC, AeSiV)
        encrypted = cipher.encrypt(pad(serialized, 16))
        url = "https://loginbp.common.gg-dena.com/MajorLogin"
        headers = {"User-Agent": "GarenaMSDK/4.0.19P9(Realme RMX1921 ;Android 11;en;US;)", "Content-Type": "application/octet-stream", "Expect": "100-continue"}
        proxy_dict = get_proxy_dict()
        session = requests.Session()
        session.verify = False
        if proxy_dict:
            session.proxies.update(proxy_dict)
        r = session.post(url, headers=headers, data=encrypted, timeout=15)
        if r.status_code != 200:
            return {"ok": False}
        cipher_dec = AES.new(AeSkEy, AES.MODE_CBC, AeSiV)
        decrypted = unpad(cipher_dec.decrypt(r.content), 16)
        res = mLrPb.MajorLoginRes()
        res.ParseFromString(decrypted)
        return {"ok": True, "jwt": res.token, "account_id": res.account_id, "lock_region": res.lock_region, "ip_region": res.ip_region, "ip_city": res.ip_city}
    except:
        return {"ok": False}

def fetch_login_history_sync(token_input):
    try:
        is_jwt = token_input.count('.') == 2
        access_token = token_input if not is_jwt else ""
        player_info = None
        if not is_jwt:
            player_info = fetch_player_info_sync(access_token)
        else:
            jwt_dec = decode_jwt_sync(token_input)
            if jwt_dec["ok"]:
                jd = jwt_dec["data"]
                acc_id = str(jd.get("account_id") or jd.get("sub") or jd.get("open_id") or "Unknown")
                player_info = {"ok": True, "uid": acc_id, "nickname": jd.get("nickname", "Unknown"), "region": jd.get("region") or jd.get("lock_region") or "Unknown"}
        login_devices = []
        if not is_jwt:
            jwt_res = get_jwt_from_access_token_sync(access_token)
            if jwt_res["ok"]:
                login_devices = [{"device_model": f"Current Device - {jwt_res.get('ip_city', 'Unknown')}", "last_login": "Now (Current Session)", "region": jwt_res.get("lock_region", "Unknown")}]
        if not login_devices:
            login_devices = [{"device_model": "Primary Device", "last_login": "Recent Login", "region": player_info.get("region", "Unknown") if player_info else "Unknown"}]
        output = "LOGIN HISTORY\n\n"
        if player_info and player_info.get("ok"):
            output += f"Account: {player_info.get('nickname', 'Unknown')}\nID: {player_info.get('uid', 'Unknown')}\nRegion: {player_info.get('region', 'Unknown')}\n\n"
        output += f"Total Devices: {len(login_devices)}\n\n"
        for idx, dev in enumerate(login_devices, 1):
            output += f"{idx}. Device: {dev.get('device_model')}\n   Last Login: {dev.get('last_login')}\n   Region: {dev.get('region')}\n\n"
        output += "Status: Active\nOwner: ZEVRIC | @just_zevric"
        return {"ok": True, "formatted": output}
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
        if HAS_STYLE:
            buttons.append([InlineKeyboardButton(text=f"Join {chat['name']}", url=chat["invite_link"], style=KeyboardButtonStyle.PRIMARY)])
        else:
            buttons.append([InlineKeyboardButton(text=f"Join {chat['name']}", url=chat["invite_link"])])
    if HAS_STYLE:
        buttons.append([InlineKeyboardButton(text="I Have Joined", callback_data="verify_joined", style=KeyboardButtonStyle.SUCCESS)])
    else:
        buttons.append([InlineKeyboardButton(text="I Have Joined", callback_data="verify_joined")])
    return InlineKeyboardMarkup(buttons)

def get_reply_keyboard():
    if HAS_STYLE:
        keyboard = [
            [KeyboardButton(text="CHECK BIND INFO", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="BIND EMAIL", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="UNBIND EMAIL", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="CHANGE BIND EMAIL", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="CANCEL BIND REQUEST", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="EAT TO ACCESS TOKEN", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="REVOKE ACCESS TOKEN", style=KeyboardButtonStyle.DANGER), KeyboardButton(text="GET LOGIN HISTORY", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="CHECK BOUND ACCOUNTS", style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text="Single Unsubscribe OTP", style=KeyboardButtonStyle.SUCCESS)],
            [KeyboardButton(text="OWNER DETAILS", style=KeyboardButtonStyle.PRIMARY)],
        ]
    else:
        keyboard = [
            ["CHECK BIND INFO", "BIND EMAIL"],
            ["UNBIND EMAIL", "CHANGE BIND EMAIL"],
            ["CANCEL BIND REQUEST", "EAT TO ACCESS TOKEN"],
            ["REVOKE ACCESS TOKEN", "GET LOGIN HISTORY"],
            ["CHECK BOUND ACCOUNTS", "Single Unsubscribe OTP"],
            ["OWNER DETAILS"],
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
    if HAS_STYLE:
        return InlineKeyboardMarkup([[InlineKeyboardButton(text="Subscribe YouTube Channel", url=YOUTUBE_LINK, style=KeyboardButtonStyle.SUCCESS)]])
    else:
        return InlineKeyboardMarkup([[InlineKeyboardButton(text="Subscribe YouTube Channel", url=YOUTUBE_LINK)]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user_id = update.effective_user.id
    is_joined = await check_user_joined_all(context, user_id)
    if not is_joined:
        join_text = "Join Verification Required\n\nTo use this bot, you must join the following groups first:\n\n"
        for chat in FORCE_JOIN_CHATS:
            join_text += f"- {chat['name']}\n"
        join_text += "\nAfter joining, click the button below to verify:"
        await update.message.reply_text(join_text, reply_markup=get_join_verification_keyboard())
        return STATE_INPUT
    else:
        first_name = update.effective_user.first_name or "S"
        welcome = f"Welcome {first_name}!\n\nYou have successfully verified all groups!\n\nSelect an option from the menu below to get started:"
        await update.message.reply_text(welcome, reply_markup=get_youtube_keyboard())
        await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
        return STATE_INPUT

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_joined = await check_user_joined_all(context, user_id)
    if not is_joined:
        join_text = "Join Verification Required\n\nTo use this bot, you must join the following groups first:\n\n"
        for chat in FORCE_JOIN_CHATS:
            join_text += f"- {chat['name']}\n"
        join_text += "\nAfter joining, click the button below to verify:"
        await update.message.reply_text(join_text, reply_markup=get_join_verification_keyboard())
        return STATE_INPUT
    await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
    return STATE_INPUT

async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Cancelled.", reply_markup=get_reply_keyboard())
    return STATE_INPUT

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); data = query.data
    if data == "verify_joined":
        user_id = update.effective_user.id
        is_joined = await check_user_joined_all(context, user_id)
        if not is_joined:
            await query.answer("You haven't joined all groups! Please join all and try again.", show_alert=True)
            join_text = "Join Verification Required\n\nTo use this bot, you must join the following groups first:\n\n"
            for chat in FORCE_JOIN_CHATS:
                join_text += f"- {chat['name']}\n"
            join_text += "\nAfter joining, click the button below to verify:"
            await query.message.reply_text(join_text, reply_markup=get_join_verification_keyboard())
            return STATE_INPUT
        else:
            first_name = update.effective_user.first_name or "S"
            welcome = f"Welcome {first_name}!\n\nYou have successfully verified all groups!\n\nSelect an option from the menu below to get started:"
            await query.message.reply_text(welcome, reply_markup=get_youtube_keyboard())
            await query.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
            return STATE_INPUT
    return STATE_INPUT

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_joined = await check_user_joined_all(context, user_id)
    if not is_joined:
        join_text = "Join Verification Required\n\nTo use this bot, you must join the following groups first:\n\n"
        for chat in FORCE_JOIN_CHATS:
            join_text += f"- {chat['name']}\n"
        join_text += "\nAfter joining, click the button below to verify:"
        await update.message.reply_text(join_text, reply_markup=get_join_verification_keyboard())
        return STATE_INPUT

    text = update.message.text.strip()
    clean_text = text
    norm = clean_text.replace("\n", " ").replace("\r", " ").upper()
    norm = " ".join(norm.split())
    
    flow = context.user_data.get('flow'); step = context.user_data.get('step')

    if "SINGLE" in norm and "UNSUBSCRIBE" in norm and "OTP" in norm:
        context.user_data.clear()
        context.user_data['flow'] = 'single_unsubscribe'
        context.user_data['step'] = 'email'
        await update.message.reply_text("Please enter your email address:", reply_markup=get_youtube_keyboard())
        return STATE_INPUT

    if "VIA EMAIL OTP" in norm:
        context.user_data['method'] = 'otp'
        if context.user_data.get('flow') not in ['unbind', 'change']:
            context.user_data['flow'] = 'change'
        context.user_data['step'] = 'token'
        await update.message.reply_text("Please enter your access token:", reply_markup=get_youtube_keyboard())
        return STATE_INPUT
    if "VIA SECURITY CODE" in norm:
        context.user_data['method'] = 'sec'
        if context.user_data.get('flow') not in ['unbind', 'change']:
            context.user_data['flow'] = 'change'
        context.user_data['step'] = 'token'
        await update.message.reply_text("Please enter your access token:", reply_markup=get_youtube_keyboard())
        return STATE_INPUT
    if "BACK TO MENU" in norm:
        context.user_data.clear()
        await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
        return STATE_INPUT

    if "CHECK BIND INFO" in norm:
        context.user_data.clear(); context.user_data['flow'] = 'bind_info'; context.user_data['step'] = 'token'
        await update.message.reply_text("Please enter your access token:", reply_markup=get_youtube_keyboard())
        return STATE_INPUT
    if "BIND EMAIL" in norm and "CHANGE" not in norm and "UNBIND" not in norm:
        context.user_data.clear(); context.user_data['flow'] = 'bind_email'; context.user_data['step'] = 'token'
        await update.message.reply_text("Please enter your access token:", reply_markup=get_youtube_keyboard())
        return STATE_INPUT
    if "UNBIND EMAIL" in norm:
        context.user_data.clear(); context.user_data['flow'] = 'unbind'
        await update.message.reply_text("Please select method:", reply_markup=get_method_keyboard())
        return STATE_INPUT
    if "CHANGE BIND EMAIL" in norm:
        context.user_data.clear(); context.user_data['flow'] = 'change'
        await update.message.reply_text("Please select method:", reply_markup=get_method_keyboard())
        return STATE_INPUT
    if "CANCEL BIND REQUEST" in norm or "CANCEL RECOVERY" in norm:
        context.user_data.clear(); context.user_data['flow'] = 'cancel_req'; context.user_data['step'] = 'token'
        await update.message.reply_text("Please enter your access token:", reply_markup=get_youtube_keyboard())
        return STATE_INPUT
    if "EAT TO ACCESS TOKEN" in norm or "EAT-TOKEN" in norm:
        context.user_data.clear(); context.user_data['flow'] = 'eat_token'; context.user_data['step'] = 'token'
        await update.message.reply_text("Please enter your EAT token:", reply_markup=get_youtube_keyboard())
        return STATE_INPUT
    if "REVOKE ACCESS TOKEN" in norm:
        context.user_data.clear(); context.user_data['flow'] = 'revoke'; context.user_data['step'] = 'token'
        await update.message.reply_text("Please enter your access token:", reply_markup=get_youtube_keyboard())
        return STATE_INPUT
    if "LOGIN HISTORY" in norm:
        context.user_data.clear(); context.user_data['flow'] = 'login_history'; context.user_data['step'] = 'token'
        await update.message.reply_text("Please enter your access token:", reply_markup=get_youtube_keyboard())
        return STATE_INPUT
    if "CHECK BOUND" in norm and "ACCOUNT" in norm:
        context.user_data.clear(); context.user_data['flow'] = 'bound_accounts'; context.user_data['step'] = 'token'
        await update.message.reply_text("Please enter your access token:", reply_markup=get_youtube_keyboard())
        return STATE_INPUT
    if "OWNER DETAILS" in norm:
        owner_text = f"ZEVRIC Bind Tool - OWNER DETAILS\n\nOWNER : ZEVRIC\nTELEGRAM : @just_zevric\nSTATUS : SAFE & SECURE\n\nPowered by ZEVRIC"
        await update.message.reply_text(owner_text, reply_markup=get_youtube_keyboard())
        await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
        return STATE_INPUT

    if not flow:
        await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
        return STATE_INPUT

    if flow == 'single_unsubscribe':
        if step == 'email':
            email = text.strip()
            if "@" not in email or "." not in email:
                await update.message.reply_text("Invalid email! Please enter valid email address:", reply_markup=get_youtube_keyboard())
                return STATE_INPUT
            
            await update.message.reply_text(f"Sending Single Unsubscribe OTP to {email}...", reply_markup=get_youtube_keyboard())
            
            res = send_single_unsubscribe_otp_sync(email, locale="en-SG", country="Singapore")
            
            if res.get('ok'):
                await update.message.reply_text(
                    f"Single Unsubscribe OTP Sent Successfully!\n\nEmail: {email}\n\nPlease check your inbox (including Spam folder) for verification code from Garena.",
                    reply_markup=get_youtube_keyboard()
                )
            else:
                await update.message.reply_text(
                    f"Failed to send OTP!\n\nEmail: {email}\nError: {res.get('error','Unknown')[:400]}",
                    reply_markup=get_youtube_keyboard()
                )
            
            await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
            context.user_data.clear()
            return STATE_INPUT

    if flow == 'bind_info':
        if step == 'token':
            await update.message.reply_text("Fetching bind info...", reply_markup=get_youtube_keyboard())
            player = fetch_player_info_sync(text); bind = fetch_bind_info_sync(text)
            if not bind['ok']:
                await update.message.reply_text(f"Error: {bind['error']}", reply_markup=get_youtube_keyboard())
            else:
                b = bind['data']
                email = b.get('email','Not bound')
                phone = b.get('phone','Not bound')
                msg = f"BIND INFO\n\nUID: {player.get('uid','Unknown')}\nNickname: {player.get('nickname','Unknown')}\nRegion: {player.get('region','Unknown')}\n\nEmail: {email}\nPhone: {phone}"
                await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
            context.user_data.clear(); return STATE_INPUT

    if flow == 'bind_email':
        if step == 'token':
            context.user_data['token'] = text; await update.message.reply_text("Please enter your email address:", reply_markup=get_youtube_keyboard()); context.user_data['step'] = 'email'; return STATE_INPUT
        if step == 'email':
            context.user_data['email'] = text; await update.message.reply_text(f"Sending OTP to {text}...", reply_markup=get_youtube_keyboard()); res = send_otp_sync(text, context.user_data['token'])
            if res['ok']: await update.message.reply_text(f"OTP sent to {text}\nEnter OTP:", reply_markup=get_youtube_keyboard()); context.user_data['step'] = 'otp'
            else: await update.message.reply_text(f"OTP fail: {res.get('error')}", reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if step == 'otp':
            await update.message.reply_text("Verifying...", reply_markup=get_youtube_keyboard()); res = verify_otp_sync(context.user_data['email'], context.user_data['token'], text)
            if res['ok'] and res['data'].get('verifier_token'):
                bind = bind_email_sync(context.user_data['email'], res['data'].get('verifier_token'), context.user_data['token'])
                if bind['ok']: await update.message.reply_text("BIND SUCCESS", reply_markup=get_youtube_keyboard())
                else: await update.message.reply_text(f"Bind fail", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
            else: await update.message.reply_text(f"Verify fail", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

    if flow == 'bound_accounts':
        if step == 'token':
            await update.message.reply_text("Checking Platform...", reply_markup=get_youtube_keyboard())
            res = fetch_platform_binds_sync(text)
            if not res['ok']: await update.message.reply_text(f"{res['error']}", reply_markup=get_youtube_keyboard()); await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard()); context.user_data.clear(); return STATE_INPUT
            bounded = res['bounded']; b_text = "Bound: " + (", ".join([PLATFORM_MAP_FULL.get(pid, str(pid)) for pid in bounded]) if bounded else "None")
            await update.message.reply_text(b_text, reply_markup=get_youtube_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
            context.user_data.clear(); return STATE_INPUT

    if flow == 'login_history':
        if step == 'token':
            await update.message.reply_text("Fetching login history...", reply_markup=get_youtube_keyboard())
            res = fetch_login_history_sync(text)
            if res["ok"]:
                await update.message.reply_text(res["formatted"], reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
            else:
                await update.message.reply_text(f"Failed: {res.get('error')}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
            context.user_data.clear(); return STATE_INPUT

    if flow == 'cancel_req':
        if step == 'token':
            await update.message.reply_text("Cancelling...", reply_markup=get_youtube_keyboard()); res = cancel_bind_request_sync(text)
            if res['ok']: await update.message.reply_text("CANCEL SUCCESS", reply_markup=get_youtube_keyboard())
            else: 
                player = fetch_player_info_sync(text)
                msg = f"No Pending Email Found!\n\nAccount: {player.get('nickname','Unknown')}\nID: {player.get('uid','Unknown')}\n\nStatus: No pending email change request to cancel."
                await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
            await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
            context.user_data.clear(); return STATE_INPUT

    if flow == 'eat_token':
        if step == 'token':
            await update.message.reply_text("Converting...", reply_markup=get_youtube_keyboard()); res = eat_to_token_sync(text)
            if res['ok']: await update.message.reply_text(f"Token:\n{res['token']}", reply_markup=get_youtube_keyboard())
            else: await update.message.reply_text(f"Fail: {res['data']}", reply_markup=get_youtube_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
            context.user_data.clear(); return STATE_INPUT

    if flow == 'revoke':
        if step == 'token':
            await update.message.reply_text("Revoking...", reply_markup=get_youtube_keyboard()); res = revoke_token_sync(text)
            if res['ok']: await update.message.reply_text("REVOKE SUCCESS", reply_markup=get_youtube_keyboard())
            else: await update.message.reply_text(f"Fail: {res['error']}", reply_markup=get_youtube_keyboard())
            await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
            context.user_data.clear(); return STATE_INPUT

    if flow == 'unbind':
        method = context.user_data.get('method')
        if step == 'token':
            context.user_data['token'] = text; bind = fetch_bind_info_sync(text)
            if not bind['ok'] or not bind['data'].get('email'): await update.message.reply_text("No bound email", reply_markup=get_youtube_keyboard()); await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard()); context.user_data.clear(); return STATE_INPUT
            email = bind['data'].get('email'); context.user_data['email'] = email
            if method == 'otp':
                await update.message.reply_text(f"Current: {email}\nOTP bhej raha...", reply_markup=get_youtube_keyboard()); res = send_otp_sync(email, text)
                if res['ok']: await update.message.reply_text(f"OTP sent to {email}\nOTP bhejo:", reply_markup=get_youtube_keyboard()); context.user_data['step'] = 'otp'
                else:
                    if res.get('captcha'): await update.message.reply_text("OTP blocked, Via Security Code use karo!", reply_markup=get_youtube_keyboard()); await update.message.reply_text("Please select method:", reply_markup=get_method_keyboard()); return STATE_INPUT
                    else: await update.message.reply_text(f"OTP fail", reply_markup=get_youtube_keyboard())
            else: await update.message.reply_text("6-digit Sec Code bhejo:", reply_markup=get_youtube_keyboard()); context.user_data['step'] = 'sec_code'
            return STATE_INPUT
        if step == 'otp':
            await update.message.reply_text("Verifying...", reply_markup=get_youtube_keyboard()); res = verify_identity_otp_sync(context.user_data['email'], context.user_data['token'], text)
            if res['ok']:
                id_token = res['data'].get('identity_token'); unr = create_unbind_request_sync(id_token, context.user_data['token'])
                if unr['ok']: await update.message.reply_text("UNBIND SUCCESS", reply_markup=get_youtube_keyboard())
                else: await update.message.reply_text(f"Fail", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
            else: await update.message.reply_text(f"Verify fail", reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if step == 'sec_code':
            await update.message.reply_text("Verifying via Sec Code...", reply_markup=get_youtube_keyboard()); res = verify_identity_sec_sync(context.user_data['email'], context.user_data['token'], text)
            if res['ok']:
                id_token = res['data'].get('identity_token'); unr = create_unbind_request_sync(id_token, context.user_data['token'])
                if unr['ok']: await update.message.reply_text("UNBIND SUCCESS via Sec Code!", reply_markup=get_youtube_keyboard())
                else: await update.message.reply_text(f"Fail", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
            else: await update.message.reply_text(f"Verify fail", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

    if flow == 'change':
        method = context.user_data.get('method')
        if step == 'token':
            context.user_data['token'] = text; bind = fetch_bind_info_sync(text)
            if not bind['ok'] or not bind['data'].get('email'): await update.message.reply_text("No bound email", reply_markup=get_youtube_keyboard()); await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard()); context.user_data.clear(); return STATE_INPUT
            old_email = bind['data'].get('email'); context.user_data['old_email'] = old_email
            if method == 'otp':
                await update.message.reply_text(f"OTP bhej raha {old_email} pe...", reply_markup=get_youtube_keyboard()); res = send_otp_sync(old_email, text)
                if res['ok']: await update.message.reply_text("OTP sent! Old OTP bhejo:", reply_markup=get_youtube_keyboard()); context.user_data['step'] = 'old_otp'
                else:
                    if res.get('captcha'): await update.message.reply_text("OTP blocked, Via Security Code use karo!", reply_markup=get_youtube_keyboard()); await update.message.reply_text("Please select method:", reply_markup=get_method_keyboard()); return STATE_INPUT
                    else: await update.message.reply_text(f"OTP fail", reply_markup=get_youtube_keyboard())
            else: await update.message.reply_text("Sec Code bhejo (old email ke liye):", reply_markup=get_youtube_keyboard()); context.user_data['step'] = 'sec_code'
            return STATE_INPUT
        if step == 'sec_code':
            await update.message.reply_text("Verifying...", reply_markup=get_youtube_keyboard()); res = verify_identity_sec_sync(context.user_data['old_email'], context.user_data['token'], text)
            if res['ok']: context.user_data['identity_token'] = res['data'].get('identity_token'); await update.message.reply_text("Please enter your email address:", reply_markup=get_youtube_keyboard()); context.user_data['step'] = 'new_email'
            else: await update.message.reply_text(f"Verify fail", reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if step == 'old_otp':
            await update.message.reply_text("Verifying...", reply_markup=get_youtube_keyboard()); res = verify_identity_otp_sync(context.user_data['old_email'], context.user_data['token'], text)
            if res['ok']: context.user_data['identity_token'] = res['data'].get('identity_token'); await update.message.reply_text("Please enter your email address:", reply_markup=get_youtube_keyboard()); context.user_data['step'] = 'new_email'
            else: await update.message.reply_text(f"Verify fail", reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if step == 'new_email':
            context.user_data['new_email'] = text; await update.message.reply_text(f"OTP bhej raha {text} pe...", reply_markup=get_youtube_keyboard()); res = send_otp_sync(text, context.user_data['token'])
            if res['ok']: await update.message.reply_text(f"OTP sent to {text}\nNew OTP bhejo:", reply_markup=get_youtube_keyboard()); context.user_data['step'] = 'new_otp'
            else: await update.message.reply_text(f"OTP fail", reply_markup=get_youtube_keyboard())
            return STATE_INPUT
        if step == 'new_otp':
            await update.message.reply_text("Verifying...", reply_markup=get_youtube_keyboard()); res = verify_otp_sync(context.user_data['new_email'], context.user_data['token'], text)
            if res['ok'] and res['data'].get('verifier_token'):
                context.user_data['verifier_token'] = res['data'].get('verifier_token'); await update.message.reply_text("Rebind bana raha...", reply_markup=get_youtube_keyboard())
                rebind = create_rebind_request_sync(context.user_data['identity_token'], context.user_data['new_email'], context.user_data['verifier_token'], context.user_data['token'])
                if rebind['ok']: await update.message.reply_text("CHANGE SUCCESS", reply_markup=get_youtube_keyboard())
                else: await update.message.reply_text(f"Fail", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
            else: await update.message.reply_text(f"Verify fail", reply_markup=get_youtube_keyboard())
            return STATE_INPUT
    await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard()); return STATE_INPUT

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot Running - ZEVRIC Final Normal - Owner @just_zevric"
@flask_app.route('/health')
def health(): return "OK"
app = flask_app

def run_bot():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("BOT_TOKEN not set!")
        return
    import asyncio
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    except: pass
    application = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("menu", menu_cmd), MessageHandler(filters.Regex("^(CHECK BIND INFO|BIND EMAIL|UNBIND EMAIL|CHANGE BIND EMAIL|CANCEL BIND REQUEST|EAT TO ACCESS TOKEN|REVOKE ACCESS TOKEN|GET LOGIN HISTORY|CHECK BOUND ACCOUNTS|OWNER DETAILS|1 CHECK BIND INFO|2 BIND EMAIL|3 UNBIND EMAIL|4 CHANGE BIND EMAIL|5 CANCEL BIND REQUEST|6 EAT TO ACCESS TOKEN|7 REVOKE ACCESS TOKEN|8 GET LOGIN HISTORY|9 CHECK BOUND ACCOUNTS|10 OWNER DETAILS|Via Email OTP|Via Security Code|Back to Menu|Eat-Token|Cancel Recovery Email|Check Platform|Single Unsubscribe OTP|Send Single Unsubscribe OTP|Single Unsubscribe OTP)$"), handle_text)],
        states={STATE_INPUT: [CallbackQueryHandler(handle_callback), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)]},
        fallbacks=[CommandHandler("cancel", cancel_cmd), CommandHandler("start", start)], allow_reentry=True, per_message=False
    )
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("cancel", cancel_cmd))
    print(f"Bot starting - Proxy: {'ON' if PROXY_URL else 'OFF'} - Final Normal Version")
    try:
        application.run_polling(close_loop=False)
    except Exception as e:
        print(f"run_polling failed: {e}")
        try:
            loop.run_until_complete(application.initialize())
            loop.run_until_complete(application.start())
            loop.run_until_complete(application.updater.start_polling())
            loop.run_forever()
        except Exception as e2:
            print(f"Fallback failed: {e2}")

def _auto_start_bot():
    if BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
        try:
            t = threading.Thread(target=run_bot, daemon=True)
            t.start()
            print("Bot thread auto-started")
        except Exception as e:
            print(f"Failed: {e}")

if os.getenv("PORT") or os.getenv("RENDER"):
    _auto_start_bot()

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)
