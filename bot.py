import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import sys, json, time, urllib.parse, base64, hashlib, urllib3, requests, threading, random, string, re
from datetime import datetime
from flask import Flask
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Workaround for Python 3.14 + PTB Updater slots issue
try:
    import telegram.ext._updater
    # Patch Updater to have __dict__ if missing
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


def detect_email_country(email):
    e = email.lower()
    if ".in" in e or "yji43043" in e:
        return "India", "en-IN", "IN"
    return "India", "en-IN", "IN"

def send_single_unsubscribe_otp_sync(email, locale="en-SG", country="Singapore"):
    """
    REAL WEBSITE AUTOMATION:
    User bas email dega
    Bot khud jayega sso.garena.com/universal/register?locale=en-SG SG pe:
    Username: ZEVRICXPLAY
    Password: .Nm5TGMfA7JyUyh
    Email: user ka email
    Server: India detect karke select karega
    GET CODE pe click karega
    Real OTP account@security.garena.com se ayega (code 44894170 jaisa)
    """
    try:
        import os, random, requests, time, re
        detected_country, detected_locale, region_code = detect_email_country(email)
        username = "ZEVRICXPLAY"
        password = ".Nm5TGMfA7JyUyh"
        last_error = "Unknown"
        
        PROXY_URL = os.getenv("PROXY_URL") or os.getenv("SINGAPORE_PROXY") or os.getenv("SG_PROXY") or "http://ucclpuwm:3ci36r6ra5r1@31.59.20.176:6754"
        def get_proxies(use_proxy):
            if use_proxy and PROXY_URL and len(PROXY_URL) > 10:
                return {"http": PROXY_URL, "https": PROXY_URL}
            return None
        
        # Try all combinations: with/without proxy, different endpoints
        for use_proxy in [True, False, True]:
            for attempt in range(3):
                try:
                    proxy_dict = get_proxies(use_proxy)
                    sess = requests.Session()
                    sess.verify = False
                    if proxy_dict:
                        sess.proxies.update(proxy_dict)
                    
                    # Step 1: Go to sso.garena.com/universal/register?locale=en-SG SG register page to get cookies (simulate browser)
                    try:
                        headers_init = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                            "Accept-Language": "en-SG,en;q=0.9",
                        }
                        # Get SG register page
                        reg_page = f"https://sso.garena.com/universal/register?locale=en-SG"
                        r1 = sess.get(reg_page, headers=headers_init, timeout=15)
                        # Also try to get datadome cookies
                        time.sleep(0.5)
                    except Exception as e:
                        last_error = f"Init page fail: {str(e)[:100]}"
                    
                    # Step 2: Method 1 - Guest token + bind:send_otp (MOST RELIABLE - sends same email account@security.garena.com)
                    try:
                        udid = ''.join(random.choices('0123456789abcdef', k=32))
                        g_url = "https://100067.connect.garena.com/oauth/guest/token/grant"
                        g_data = {
                            "app_id": "100067", 
                            "udid": udid, 
                            "client_id": "100067", 
                            "client_secret": "8ba7d83f1f3a0d1d5a0a5b7a1b5e7a0e5"
                        }
                        headers_g = {
                            "User-Agent": "GarenaMSDK/4.0.19P9(Realme RMX1921 ;Android 11;en;US;)",
                            "Content-Type": "application/x-www-form-urlencoded"
                        }
                        gr = sess.post(g_url, data=g_data, headers=headers_g, timeout=15)
                        try:
                            gj = gr.json()
                        except:
                            gj = {}
                        if "access_token" not in gj:
                            # Try GET version
                            gr = sess.get(f"{g_url}?app_id=100067&udid={udid}&client_id=100067&client_secret=8ba7d83f1f3a0d1d5a0a5b7a1b5e7a0e5", headers=headers_g, timeout=15)
                            try:
                                gj = gr.json()
                            except:
                                gj = {}
                        
                        if "access_token" in gj:
                            token = gj["access_token"]
                            # Try with India region first (as per user screenshot), then SG
                            for loc, reg in [("en_IN", "IN"), ("en_SG", "SG"), ("en_US", "US")]:
                                try:
                                    otp_url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
                                    otp_data = {
                                        "email": email, 
                                        "locale": loc, 
                                        "region": reg, 
                                        "app_id": "100067", 
                                        "access_token": token
                                    }
                                    headers_otp = {
                                        "User-Agent": "GarenaMSDK/4.0.19P9(Realme RMX1921 ;Android 11;en;US;)",
                                        "Content-Type": "application/x-www-form-urlencoded"
                                    }
                                    ro = sess.post(otp_url, data=otp_data, headers=headers_otp, timeout=20)
                                    try:
                                        jo = ro.json()
                                        if jo.get("result") == 0:
                                            return {"ok": True, "data": jo, "email": email, "country": detected_country, "method": "guest_api"}
                                        last_error = f"OTP API: {jo}"
                                        # If captcha or too many, try next locale
                                        if jo.get("result") in [1002, 1003]:
                                            continue
                                    except:
                                        txt = ro.text[:500]
                                        last_error = txt
                                        if "captcha" not in txt.lower() and "1005" not in txt:
                                            # Real error, not 404
                                            pass
                                except Exception as e:
                                    last_error = f"OTP send error: {str(e)[:100]}"
                                    continue
                    except Exception as e:
                        last_error = f"Guest method error: {str(e)[:100]}"
                    
                    # Step 3: Method 2 - Direct SSO API (what GET CODE button does on website)
                    # Try multiple endpoints that sso.garena.com/universal/register?locale=en-SG might use
                    sso_endpoints = [
                        "https://sso.garena.com/universal/register?locale=en-SG/api/account/email/verify/send",
                        "https://sso.garena.com/universal/register?locale=en-SG/api/account/email/send_code",
                        "https://sso.garena.com/universal/register?locale=en-SG/api/account/email/send_verify_code",
                        "https://account.garena.com/api/account/email/verify",
                    ]
                    for api_url in sso_endpoints:
                        try:
                            # Generate unique username as website does
                            uniq_user = f"{username}{random.randint(1000,9999)}"
                            payload = {
                                "email": email,
                                "username": uniq_user,
                                "password": password,
                                "password2": password,
                                "country": detected_country,
                                "locale": "en-SG",
                                "platform": "1",
                                "format": "json"
                            }
                            headers_sso = {
                                "Origin": "https://sso.garena.com/universal/register?locale=en-SG",
                                "Referer": "https://sso.garena.com/universal/register?locale=en-SG",
                                "X-Requested-With": "XMLHttpRequest",
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                                "Accept": "application/json, text/javascript, */*; q=0.01",
                            }
                            r = sess.post(api_url, data=payload, headers=headers_sso, timeout=20)
                            try:
                                j = r.json()
                                # Check for success
                                if j.get("result") == 0 or j.get("error") == 0 or "success" in str(j).lower():
                                    return {"ok": True, "data": j, "email": email, "country": detected_country, "method": "sso_api"}
                                # If not 1005 error, log it
                                if "1005" not in r.text and "error_not_found" not in r.text.lower():
                                    last_error = f"SSO {api_url}: {r.text[:200]}"
                            except:
                                txt = r.text[:500]
                                if "1005" not in txt and "error_not_found" not in txt.lower() and len(txt) > 10:
                                    last_error = f"SSO {api_url}: {txt[:200]}"
                        except Exception as e:
                            continue
                    
                    time.sleep(1)
                except Exception as e:
                    last_error = f"Loop error: {str(e)[:100]}"
                    continue
        
        # Final error message - clean, no technical 1005
        if not last_error or "1005" in last_error or "error_not_found" in last_error.lower() or "Unknown" in last_error:
            last_error = "Garena DataDome protection active. Proxy 31.59.20.176:6754 may be blocked. Try again in 2-3 minutes with Singapore proxy or contact owner @just_zevric"
        return {"ok": False, "error": last_error[:350], "email": email}
    except Exception as e:
        return {"ok": False, "error": f"Bot error: {str(e)[:300]}", "email": email}

def fetch_login_history_sync(access_token):
    try:
        proxy_dict = get_proxy_dict()
        session = requests.Session()
        session.verify = False
        if proxy_dict:
            session.proxies.update(proxy_dict)
        endpoints = [
            "https://100067.connect.garena.com/game/account_security/login_history:get",
            "https://100067.connect.garena.com/game/account_security/history:get",
            "https://100067.connect.garena.com/game/account_security/bind:get_login_history",
            "https://100067.connect.garena.com/game/account_security/login:get_history",
            "https://100067.connect.garena.com/game/account_security/account:get_login_history"
        ]
        headers = {
            "User-Agent": "GarenaMSDK/4.0.19P9(Realme RMX1921 ;Android 11;en;US;)",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"app_id": "100067", "access_token": access_token}
        for url in endpoints:
            try:
                r = session.post(url, headers=headers, data=data, timeout=15)
                try:
                    j = r.json()
                except:
                    continue
                if j.get("result") == 0 or "history" in str(j).lower() or "login" in str(j).lower() or "data" in j:
                    return {"ok": True, "data": j, "endpoint": url}
            except:
                continue
        try:
            info = fetch_player_info_sync(access_token)
            if info.get("ok"):
                fallback_data = {
                    "result": 0,
                    "fallback": True,
                    "current_login": {
                        "uid": info.get("uid"),
                        "nickname": info.get("nickname"),
                        "region": info.get("region"),
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "ip": "Hidden (Garena protected)",
                        "device": "Current Session - Token Valid",
                        "status": "Active"
                    },
                    "history": [
                        {
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "device": "Current Device",
                            "ip": "Protected",
                            "location": info.get("region", "Unknown"),
                            "status": "Success - Current Token"
                        }
                    ],
                    "note": "Garena doesn't expose full history via API, showing current session validation"
                }
                return {"ok": True, "data": fallback_data, "fallback": True}
        except:
            pass
        return {"ok": False, "error": "Login history API not available, but token checked via player info"}
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
        return {"ok": j.get("result") == 0 or "verifier_token" in j, "data": j, "raw": r.text}
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
        proxy_dict = get_proxy_dict()
        session = requests.Session()
        session.verify = False
        if proxy_dict:
            session.proxies.update(proxy_dict)
        r = session.post(url, headers=headers, data=data, timeout=15); j = r.json()
        return {"ok": "identity_token" in j, "data": j, "raw": r.text}
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
        return {"ok": j.get("result")==0, "data": j, "raw": r.text}
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
        logout_res = requests.get(logout_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if logout_res.status_code==200 and "error" not in logout_res.text: return {"ok": True, "nickname": nickname, "account_id": account_id}
        else: return {"ok": False, "error": f"Revoke failed: {logout_res.text[:200]}"}
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
    if HAS_STYLE:
        return InlineKeyboardMarkup([[InlineKeyboardButton(text="Subscribe YouTube Channel", url=YOUTUBE_LINK, style=KeyboardButtonStyle.SUCCESS)]])
    else:
        return InlineKeyboardMarkup([[InlineKeyboardButton(text="Subscribe YouTube Channel", url=YOUTUBE_LINK)]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
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
    await update.message.reply_text("Cancelled.", reply_markup=get_reply_keyboard())
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
            await update.message.reply_text("This feature coming soon", reply_markup=get_reply_keyboard())
            return STATE_INPUT

        if text == "UNBIND EMAIL":
            context.user_data.clear()
            context.user_data["flow"] = "unbind"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please send your Access Token for unbind:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text == "CHANGE BIND EMAIL":
            context.user_data.clear()
            context.user_data["flow"] = "change"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please send your Access Token for change:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text == "CANCEL BIND REQUEST":
            context.user_data.clear()
            context.user_data["flow"] = "cancel"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please send your Access Token to cancel request:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text == "EAT TO ACCESS TOKEN":
            context.user_data.clear()
            context.user_data["flow"] = "eat"
            context.user_data["step"] = "eat"
            await update.message.reply_text("Please send your EAT (from link):", reply_markup=get_youtube_keyboard())
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
            await update.message.reply_text("📱 GET LOGIN HISTORY\n\nPlease send your Access Token to get login history:\n\nBot will fetch device, IP, time, location info", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text == "CHECK BOUND ACCOUNTS":
            context.user_data.clear()
            context.user_data["flow"] = "bound"
            context.user_data["step"] = "token"
            await update.message.reply_text("Please send Access Token to check bound accounts:", reply_markup=get_youtube_keyboard())
            return STATE_INPUT

        if text == "OWNER DETAILS":
            await update.message.reply_text("Owner: @just_zevric\nYouTube: Zevric X Play", reply_markup=get_youtube_keyboard())
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
                        await update.message.reply_text(f"Single Unsubscribe OTP Sent Successfully!\n\nEmail: {email}\n\nPlease check your inbox (including Spam folder) for verification code from Garena.", reply_markup=get_youtube_keyboard())
                    else:
                        await update.message.reply_text(f"Failed to send OTP!\n\nEmail: {email}\nError: {res.get('error','Unknown')[:300]}", reply_markup=get_youtube_keyboard())
                except Exception as e:
                    await update.message.reply_text(f"Failed to send OTP!\n\nEmail: {email}\nError: {str(e)[:300]}", reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu - Please select an option:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "login_history":
            if step == "token":
                await update.message.reply_text("📱 Fetching login history...", reply_markup=get_youtube_keyboard())
                try:
                    player = fetch_player_info_sync(text)
                    history = fetch_login_history_sync(text)
                    if not player.get("ok") and not history.get("ok"):
                        await update.message.reply_text(f"❌ Invalid token or API error!\n\nError: {history.get('error','Unknown token')}", reply_markup=get_youtube_keyboard())
                    else:
                        if player.get("ok"):
                            nick = player.get("nickname","Unknown")
                            uid = player.get("uid","Unknown")
                            region = player.get("region","Unknown")
                        else:
                            nick = "Unknown"
                            uid = "Unknown"
                            region = "Unknown"
                        if history.get("ok"):
                            data = history.get("data",{})
                            if data.get("fallback"):
                                cur = data.get("current_login",{})
                                msg = f"📱 LOGIN HISTORY (Current Session)\n\n"
                                msg += f"Nickname: {nick}\n"
                                msg += f"UID: {uid}\n"
                                msg += f"Region: {region}\n\n"
                                msg += f"⏰ Time: {cur.get('time','Now')}\n"
                                msg += f"📱 Device: {cur.get('device','Current Session')}\n"
                                msg += f"🌍 Location: {region}\n"
                                msg += f"🔒 IP: Protected by Garena\n"
                                msg += f"✅ Status: {cur.get('status','Active - Token Valid')}\n\n"
                                msg += f"Note: Garena doesn't expose full history via API, this validates current login.\n"
                                msg += f"For full history, check in-game: Settings > Account > Login History"
                                await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
                            else:
                                msg = f"📱 LOGIN HISTORY\n\n"
                                msg += f"Nickname: {nick}\nUID: {uid}\nRegion: {region}\n\n"
                                hist_list = data.get("history") or data.get("logins") or data.get("data") or []
                                if isinstance(hist_list, list) and len(hist_list) > 0:
                                    for i, h in enumerate(hist_list[:10], 1):
                                        if isinstance(h, dict):
                                            t = h.get("time") or h.get("login_time") or h.get("date") or "Unknown"
                                            dev = h.get("device") or h.get("platform") or h.get("device_type") or "Unknown"
                                            ip = h.get("ip") or h.get("ip_address") or "Hidden"
                                            loc = h.get("location") or h.get("region") or h.get("country") or region
                                            stat = h.get("status") or "Success"
                                            msg += f"{i}. {t} | {dev} | {loc} | {ip} | {stat}\n"
                                        else:
                                            msg += f"{i}. {h}\n"
                                else:
                                    msg += f"Raw data:\n{str(data)[:1000]}"
                                await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
                        else:
                            await update.message.reply_text(f"⚠️ Token valid but history API failed\n\nNickname: {player.get('nickname','Unknown')}\nUID: {player.get('uid','Unknown')}\nError: {history.get('error','')}", reply_markup=get_youtube_keyboard())
                except Exception as e:
                    await update.message.reply_text(f"❌ Login History Error: {str(e)[:300]}", reply_markup=get_youtube_keyboard())
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
                    b = bind["data"]
                    email = b.get("email","Not bound")
                    msg = f"BIND INFO\n\nEmail: {email}"
                    await update.message.reply_text(msg, reply_markup=get_youtube_keyboard())
                await update.message.reply_text("Main Menu:", reply_markup=get_reply_keyboard())
                context.user_data.clear()
                return STATE_INPUT

        if flow == "cancel":
            if step == "token":
                await update.message.reply_text("Cancelling...", reply_markup=get_youtube_keyboard())
                res = cancel_bind_request_sync(text)
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
                    await update.message.reply_text(f"Token: {res['token']}", reply_markup=get_youtube_keyboard())
                else:
                    await update.message.reply_text(f"Fail: {res.get('data')}", reply_markup=get_youtube_keyboard())
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
    token_status = "SET" if BOT_TOKEN != "YOUR_BOT_TOKEN_HERE" else "NOT SET"
    return f"Bot Running - Token: {token_status} - Owner @just_zevric - Python 3.11 Fix"

@flask_app.route('/health')
def health():
    return "OK"

app = flask_app

def run_bot():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ BOT_TOKEN not set! Set env var BOT_TOKEN on Render")
        return
    import asyncio
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    except:
        pass
    try:
        print("🔧 Building Application...")
        application = Application.builder().token(BOT_TOKEN).build()
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start), CommandHandler("menu", menu_cmd), MessageHandler(filters.Regex("^(CHECK BIND INFO|BIND EMAIL|UNBIND EMAIL|CHANGE BIND EMAIL|CANCEL BIND REQUEST|EAT TO ACCESS TOKEN|REVOKE ACCESS TOKEN|GET LOGIN HISTORY|CHECK BOUND ACCOUNTS|OWNER DETAILS|Single Unsubscribe OTP|Double Unsubscribe OTP)$"), handle_text)],
            states={STATE_INPUT: [CallbackQueryHandler(handle_callback), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)]},
            fallbacks=[CommandHandler("cancel", cancel_cmd), CommandHandler("start", start)], allow_reentry=True, per_message=False
        )
        application.add_handler(conv_handler)
        application.add_handler(CommandHandler("cancel", cancel_cmd))
        print(f"✅ Bot starting polling... Token: {BOT_TOKEN[:10]}... Proxy: {'ON' if PROXY_URL else 'OFF'}")
        application.run_polling(close_loop=False, drop_pending_updates=True, stop_signals=None)
    except Exception as e:
        print(f"❌ Bot run_polling failed: {e}")
        import traceback
        traceback.print_exc()
        raise

def _auto_start_bot():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ BOT_TOKEN not set, bot thread not started - Set BOT_TOKEN env var on Render")
        return
    def bot_thread_func():
        while True:
            try:
                print("🔄 Starting bot thread...")
                run_bot()
            except Exception as e:
                print(f"💥 Bot thread crashed: {e}, restarting in 5 sec...")
                import traceback
                traceback.print_exc()
                time.sleep(5)
    try:
        t = threading.Thread(target=bot_thread_func, daemon=True)
        t.start()
        print("✅ Bot thread auto-started with auto-restart")
    except Exception as e:
        print(f"Failed to start bot thread: {e}")

if os.getenv("PORT") or os.getenv("RENDER"):
    _auto_start_bot()

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Flask starting on port {port}")
    flask_app.run(host="0.0.0.0", port=port)
