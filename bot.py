"""
Spidey Bind Tool - Telegram Bot Edition
========================================
Converts the CLI `app.py` into a fully interactive Telegram bot.

Requirements (requirements.txt):
    python-telegram-bot==21.6
    requests
    pycryptodome
    protobuf

Files required in the SAME folder as this bot.py:
    - MajoRLogin_pb2.py
    - MajorLoginRes_pb2.py

Run:
    export BOT_TOKEN="123456:ABC..."      # your @BotFather token
    python bot.py

Owner: @spideyabd & @INDRAJIT_1M
"""

import os
import sys
import json
import base64
import hashlib
import logging
import urllib.parse
from datetime import datetime

import requests
import urllib3
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("spidey-bot")

try:
    import MajoRLogin_pb2 as mLpB
    import MajorLoginRes_pb2 as mLrPb
except ImportError:
    print("[!] Protobuf files (MajoRLogin_pb2.py, MajorLoginRes_pb2.py) missing next to bot.py")
    sys.exit(1)

# ----------------------------------------------------------------------------
# Crypto & helpers (verbatim from app.py)
# ----------------------------------------------------------------------------
AeSkEy = b'Yg&tc%DEuh6%Zc^8'
AeSiV  = b'6oyZDr22E3ychjM%'

PLATFORM_MAP = {
    3: "Facebook", 4: "Guest", 5: "VK",
    6: "Huawei", 8: "Google", 11: "X (Twitter)", 13: "AppleId",
}

def enc(d): return AES.new(AeSkEy, AES.MODE_CBC, AeSiV).encrypt(pad(d, 16))
def dec(d): return unpad(AES.new(AeSkEy, AES.MODE_CBC, AeSiV).decrypt(d), 16)

def convert_seconds(s):
    d, h = divmod(s, 86400)
    h, m = divmod(h, 3600)
    m, s = divmod(m, 60)
    return f"{d}d {h}h {m}m {s}s"

def fmt_result(text, title="API Response"):
    try:
        p = json.loads(text)
        rc = p.get("result")
        if rc == 0:
            return f"✅ <b>{title}</b>: SUCCESS"
        if rc is not None:
            return f"❌ <b>{title}</b>: FAILED (code {rc} | {p.get('error','')})"
        return f"ℹ️ <b>{title}</b>: {text[:200]}"
    except Exception:
        return f"ℹ️ <b>{title}</b>: {text[:200]}"

def html_escape(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

BASE = "https://100067.connect.garena.com/game/account_security"
GARENA_HEADERS = {
    "User-Agent": "GarenaMSDK/4.0.30",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json",
}

# ----------------------------------------------------------------------------
# Core Garena API functions (returning strings for Telegram)
# ----------------------------------------------------------------------------
def api_bind_info(access_token: str) -> str:
    out = ["<b>≡ Bind Info</b>"]
    try:
        p_res = requests.get(
            f"https://api-otrss.garena.com/support/callback/?access_token={access_token}",
            headers={"User-Agent": "Mozilla/5.0"}, timeout=15, allow_redirects=True,
        )
        q = urllib.parse.parse_qs(urllib.parse.urlparse(p_res.url).query)
        out += [
            f"• UID: <code>{html_escape(q.get('account_id',['?'])[0])}</code>",
            f"• Nickname: <code>{html_escape(urllib.parse.unquote(q.get('nickname',['?'])[0]))}</code>",
            f"• Region: <code>{html_escape(q.get('region',['?'])[0])}</code>",
        ]
    except Exception as e:
        out.append(f"⚠️ Player fetch failed: {html_escape(e)}")

    try:
        r = requests.get(f"{BASE}/bind:get_bind_info",
                         params={"app_id": "100067", "access_token": access_token},
                         headers={"User-Agent": "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"},
                         timeout=15)
        d = r.json()
        email = d.get("email", "")
        email_to_be = d.get("email_to_be", "")
        cd = d.get("request_exec_countdown", 0)
        out += [
            f"• Current Email: <code>{html_escape(email or 'None')}</code>",
            f"• Pending Email: <code>{html_escape(email_to_be or 'None')}</code>",
        ]
        if email_to_be:
            out.append(f"• Countdown: <code>{convert_seconds(cd)}</code>")
        rc = d.get("result", -1)
        out.append(f"• Result: {'✅ SUCCESS' if rc == 0 else f'❌ FAILED ({rc})'}")
    except Exception as e:
        out.append(f"❌ Bind info error: {html_escape(e)}")
    return "\n".join(out)

def api_send_otp(access_token, email):
    r = requests.post(f"{BASE}/bind:send_otp", headers=GARENA_HEADERS, data={
        "email": email, "locale": "en_PK", "region": "PK",
        "app_id": "100067", "access_token": access_token,
    })
    return r.text

def api_verify_otp_bind(access_token, email, otp):
    r = requests.post(f"{BASE}/bind:verify_otp", headers=GARENA_HEADERS, data={
        "app_id": "100067", "access_token": access_token,
        "email": email, "code": otp, "otp": otp, "type": "1",
    })
    return r.text, (r.json().get("verifier_token", "") if r.text else "")

def api_create_bind(access_token, email, verifier_token, sec_code):
    r = requests.post(f"{BASE}/bind:create_bind_request", headers=GARENA_HEADERS, data={
        "email": email, "app_id": "100067", "access_token": access_token,
        "verifier_token": verifier_token, "secondary_password": sec_code,
    })
    return r.text

def api_verify_identity_otp(access_token, email, otp):
    r = requests.post(f"{BASE}/bind:verify_identity", headers=GARENA_HEADERS, data={
        "email": email, "app_id": "100067", "access_token": access_token, "otp": otp,
    })
    try: it = r.json().get("identity_token")
    except: it = None
    return r.text, it

def api_verify_identity_sec(access_token, email, sec_code):
    hashed = hashlib.sha256(sec_code.encode()).hexdigest()
    r = requests.post(f"{BASE}/bind:verify_identity", headers=GARENA_HEADERS, data={
        "email": email, "app_id": "100067", "access_token": access_token,
        "secondary_password": hashed,
    })
    try: it = r.json().get("identity_token")
    except: it = None
    return r.text, it

def api_create_change_bind(access_token, new_email, identity_token, sec_code):
    r = requests.post(f"{BASE}/bind:create_change_bind_request", headers=GARENA_HEADERS, data={
        "app_id": "100067", "access_token": access_token,
        "email": new_email, "identity_token": identity_token,
        "secondary_password": sec_code,
    })
    return r.text

def api_create_unbind(access_token, identity_token):
    r = requests.post(f"{BASE}/bind:create_unbind_request", headers=GARENA_HEADERS, data={
        "app_id": "100067", "access_token": access_token, "identity_token": identity_token,
    })
    return r.text

def api_cancel(access_token):
    r = requests.post(f"{BASE}/bind:cancel_request", headers=GARENA_HEADERS, data={
        "app_id": "100067", "access_token": access_token,
    })
    return r.text

def api_current_email(access_token):
    try:
        r = requests.get(f"{BASE}/bind:get_bind_info",
                         params={"app_id": "100067", "access_token": access_token},
                         headers={"User-Agent": "GarenaMSDK/4.0.30"}, timeout=10)
        return r.json().get("email", "")
    except: return ""

def api_eat_to_token(user_input: str) -> str:
    eat = None
    if "http" in user_input or "?" in user_input:
        q = urllib.parse.parse_qs(urllib.parse.urlparse(user_input).query)
        if "eat" in q: eat = q["eat"][0]
    else:
        eat = user_input.strip()
    if not eat:
        return "❌ No EAT token found in input."
    try:
        r = requests.get(f"https://api-otrss.garena.com/support/callback/?access_token={eat}",
                         headers={"User-Agent": "Mozilla/5.0 (Linux; Android 13)"},
                         allow_redirects=True, timeout=15)
        q = urllib.parse.parse_qs(urllib.parse.urlparse(r.url).query)
        if "access_token" not in q:
            return "❌ Access token not found — EAT expired/invalid."
        return (
            "✅ <b>EAT → Access Token</b>\n"
            f"• Nickname: <code>{html_escape(urllib.parse.unquote(q.get('nickname',['?'])[0]))}</code>\n"
            f"• Account ID: <code>{html_escape(q.get('account_id',['?'])[0])}</code>\n"
            f"• Region: <code>{html_escape(q.get('region',['?'])[0])}</code>\n"
            f"• Access Token:\n<code>{html_escape(q['access_token'][0])}</code>"
        )
    except Exception as e:
        return f"❌ Failed: {html_escape(e)}"

def api_revoke(access_token: str) -> str:
    hdr = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(f"https://api-otrss.garena.com/support/callback/?access_token={access_token}",
                           headers=hdr, allow_redirects=True, timeout=15)
        q = urllib.parse.parse_qs(urllib.parse.urlparse(res.url).query)
        if "access_token" not in q:
            return "❌ Token already invalid/expired/revoked."
        nick = urllib.parse.unquote(q.get("nickname", ["?"])[0])
        aid = q.get("account_id", ["?"])[0]
        reg = q.get("region", ["?"])[0]
    except Exception as e:
        return f"❌ Check failed: {html_escape(e)}"
    refresh = "1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
    try:
        lr = requests.get(
            f"https://100067.connect.garena.com/oauth/logout?access_token={access_token}&refresh_token={refresh}",
            headers=hdr, timeout=15)
        if lr.status_code == 200 and "error" not in lr.text:
            return (f"✅ <b>REVOKED</b>\n• Nickname: <code>{html_escape(nick)}</code>\n"
                    f"• Account ID: <code>{aid}</code>\n• Region: <code>{reg}</code>")
        return f"❌ Revoke failed: {html_escape(lr.text[:150])}"
    except Exception as e:
        return f"❌ Revoke error: {html_escape(e)}"

# --- Login history (protobuf) ---
def build_majorlogin(tok, open_id, p_type):
    m = mLpB.MajorLogin()
    m.event_time = str(datetime.now())[:-7]
    m.game_name = "free fire"; m.platform_id = p_type
    m.client_version = "1.120.1"; m.system_software = "Android OS 9 / API-28"
    m.system_hardware = "Handheld"; m.telecom_operator = "Verizon"
    m.network_type = "WIFI"; m.screen_width = 1920; m.screen_height = 1080
    m.screen_dpi = "280"; m.processor_details = "ARM64 FP ASIMD AES VMH | 2865 | 4"
    m.memory = 3003; m.gpu_renderer = "Adreno (TM) 640"
    m.gpu_version = "OpenGL ES 3.1 v1.46"
    m.unique_device_id = "Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57"
    m.client_ip = "223.191.51.89"; m.language = "en"
    m.open_id = open_id; m.open_id_type = str(p_type)
    m.device_type = "Handheld"; m.access_token = tok
    m.platform_sdk_id = 1
    m.client_using_version = "7428b253defc164018c604a1ebbfebdf"
    m.login_by = 3; m.channel_type = 3; m.cpu_type = 2; m.cpu_architecture = "64"
    m.client_version_code = "2019118695"
    m.login_open_id_type = p_type
    m.origin_platform_type = str(p_type); m.primary_platform_type = str(p_type)
    return enc(m.SerializeToString())

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
        tag, offset = read_varint(data, offset); wt, f = tag & 7, tag >> 3
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
    recs = []; offset = 0
    while offset < len(data):
        tag, offset = read_varint(data, offset); wt, f = tag & 7, tag >> 3
        if wt == 0: _, offset = read_varint(data, offset)
        elif wt == 2:
            length, offset = read_varint(data, offset)
            val = data[offset:offset+length]; offset += length
            if f == 1: recs.append(parse_record(val))
        else: break
    return recs

def api_login_history(token: str) -> str:
    jwt_token = None
    if token.startswith("ey") and "." in token:
        jwt_token = token
    else:
        oId = None
        try:
            r = requests.get(f"https://100067.connect.garena.com/oauth/token/inspect?token={token}",
                             headers={"User-Agent": "Mozilla/5.0"}, timeout=5).json()
            oId = r.get("open_id")
        except: pass
        if not oId:
            try:
                ur = requests.get("https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/",
                                  headers={"access-token": token, "user-agent": "Mozilla/5.0"},
                                  verify=False, timeout=5).json()
                uid = ur.get("uid")
                if uid:
                    orr = requests.post("https://topup.pk/api/auth/player_id_login",
                                        json={"app_id": 100067, "login_id": str(uid)},
                                        verify=False, timeout=5).json()
                    oId = orr.get("open_id")
            except: pass
        if not oId:
            return "❌ Failed to extract Open ID — token invalid/expired."
        for p_type in [8, 3, 4, 6]:
            try:
                x = requests.post("https://loginbp.ggpolarbear.com/MajorLogin",
                    headers={
                        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-S908E Build/TP1A.220624.014)",
                        "Connection": "Keep-Alive", "Accept-Encoding": "gzip",
                        "Content-Type": "application/octet-stream", "Expect": "100-continue",
                        "X-GA": "v1 1", "X-Unity-Version": "2018.4.11f1", "ReleaseVersion": "OB52",
                    },
                    data=build_majorlogin(token, oId, p_type), timeout=10, verify=False)
                if x.status_code == 200:
                    res = mLrPb.MajorLoginRes()
                    try: res.ParseFromString(dec(x.content))
                    except: res.ParseFromString(x.content)
                    if res.token:
                        jwt_token = res.token; break
            except: continue
        if not jwt_token:
            return "❌ MajorLogin failed across all platforms."

    lines = []
    try:
        pb = jwt_token.split('.')[1]; pb += "=" * ((4 - len(pb) % 4) % 4)
        dec_j = json.loads(base64.urlsafe_b64decode(pb).decode())
        lines += [
            "<b>≡ Player Info</b>",
            f"• Name: <code>{html_escape(urllib.parse.unquote(dec_j.get('nickname','?')))}</code>",
            f"• UID: <code>{dec_j.get('account_id','?')}</code>",
            f"• Platform: <code>{PLATFORM_MAP.get(dec_j.get('external_type',0), dec_j.get('external_type',0))}</code>",
            f"• Region: <code>{dec_j.get('lock_region','?')}</code>", "",
        ]
    except: pass

    try:
        r = requests.post("https://client.ind.freefiremobile.com/GetLoginHistory",
            headers={
                "Expect": "100-continue", "Authorization": f"Bearer {jwt_token}",
                "X-Unity-Version": "2018.4.11f1", "X-GA": "v1 1", "ReleaseVersion": "OB52",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; G011A Build/PI)",
                "Host": "client.ind.freefiremobile.com", "Connection": "close",
            },
            data=enc(b""), timeout=15, verify=False)
        if r.status_code != 200:
            return "\n".join(lines) + f"\n❌ History HTTP {r.status_code}"
        try: d = dec(r.content)
        except: d = r.content
        recs = parse_history_protobuf(d)
        lines.append("<b>≡ Login History</b>")
        if not recs:
            lines.append("• No records.")
        else:
            for i, rc in enumerate(recs, 1):
                ts = rc.get("ts", 0)
                try: ds = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                except: ds = "?"
                lines += [
                    f"\n<b>#{i}</b>",
                    f"• Time: <code>{ds}</code>",
                    f"• Device: <code>{html_escape(rc.get('dev','?'))}</code>",
                    f"• Arch: <code>{html_escape(rc.get('arch','?'))}</code>",
                    f"• RAM: <code>{rc.get('ram',0)} MB</code>",
                ]
        return "\n".join(lines)
    except Exception as e:
        return "\n".join(lines) + f"\n❌ {html_escape(e)}"

# ============================================================================
# TELEGRAM BOT
# ============================================================================
(MENU,
 BIND_TOKEN, BIND_EMAIL, BIND_OTP, BIND_SEC,
 CHG_METHOD, CHG_TOKEN, CHG_OTP_OLD, CHG_SEC_OLD, CHG_NEW_EMAIL, CHG_NEW_OTP, CHG_NEW_SEC,
 UNB_METHOD, UNB_TOKEN, UNB_OTP, UNB_SEC,
 CANCEL_TOKEN, INFO_TOKEN, EAT_INPUT, REVOKE_TOKEN, HIST_TOKEN,
) = range(21)

def main_menu_kb():
    rows = [
        [InlineKeyboardButton("🔗 Bind Email", callback_data="m:bind"),
         InlineKeyboardButton("♻️ Change Bind", callback_data="m:change")],
        [InlineKeyboardButton("🔓 Unbind Email", callback_data="m:unbind"),
         InlineKeyboardButton("🚫 Cancel Bind", callback_data="m:cancel")],
        [InlineKeyboardButton("ℹ️ Bind Info", callback_data="m:info"),
         InlineKeyboardButton("🎟 EAT → Token", callback_data="m:eat")],
        [InlineKeyboardButton("🗝 Revoke Token", callback_data="m:revoke"),
         InlineKeyboardButton("📜 Login History", callback_data="m:hist")],
        [InlineKeyboardButton("👑 Owner", callback_data="m:owner"),
         InlineKeyboardButton("❌ Close", callback_data="m:close")],
    ]
    return InlineKeyboardMarkup(rows)

WELCOME = (
    "<b>🕷 Spidey Bind Tool — Telegram Edition</b>\n"
    "Developer: @spideyabd &amp; @INDRAJIT_1M\n\n"
    "Choose an option below. Use /cancel any time to abort a flow."
)

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_html(WELCOME, reply_markup=main_menu_kb())
    return MENU

async def cancel_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.effective_message.reply_html("Cancelled.", reply_markup=main_menu_kb())
    return MENU

async def menu_router(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    action = q.data.split(":", 1)[1]
    ctx.user_data.clear()

    if action == "close":
        await q.edit_message_text("Bye 👋")
        return ConversationHandler.END
    if action == "owner":
        txt = (
            "<b>👑 Owner Info</b>\n"
            "• Developer: SPIDEY\n"
            "• Telegram: @spideyabd &amp; @INDRAJIT_1M\n"
            "• Channels: t.me/SPIDEYFREEFILES · t.me/INDRAJITFREEAPI\n"
            "• Version: v2.0 (Premium / Secure)"
        )
        await q.message.reply_html(txt, reply_markup=main_menu_kb())
        return MENU

    prompts = {
        "bind":   ("🔗 <b>Bind Email</b>\nSend the <b>Access Token</b>.", BIND_TOKEN),
        "change": ("♻️ <b>Change Bind Email</b>\nSelect verification method:", CHG_METHOD),
        "unbind": ("🔓 <b>Unbind Email</b>\nSelect verification method:", UNB_METHOD),
        "cancel": ("🚫 <b>Cancel Bind Request</b>\nSend the <b>Access Token</b>.", CANCEL_TOKEN),
        "info":   ("ℹ️ <b>Bind Info</b>\nSend the <b>Access Token</b>.", INFO_TOKEN),
        "eat":    ("🎟 <b>EAT → Access Token</b>\nSend the EAT token or full EAT URL.", EAT_INPUT),
        "revoke": ("🗝 <b>Revoke Access Token</b>\nSend the <b>Access Token</b> to revoke.", REVOKE_TOKEN),
        "hist":   ("📜 <b>Login History</b>\nSend <b>Access Token</b> or Game <b>JWT</b>.", HIST_TOKEN),
    }
    if action in ("change", "unbind"):
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📧 Via OTP", callback_data=f"method:{action}:1"),
             InlineKeyboardButton("🔐 Via Security Code", callback_data=f"method:{action}:2")],
            [InlineKeyboardButton("« Back", callback_data="m:back")],
        ])
        await q.message.reply_html(prompts[action][0], reply_markup=kb)
        return prompts[action][1]

    if action == "back":
        await q.message.reply_html(WELCOME, reply_markup=main_menu_kb())
        return MENU

    text, state = prompts[action]
    await q.message.reply_html(text)
    return state

# ---- Bind flow ----
async def bind_token(u, c):
    c.user_data["token"] = u.message.text.strip()
    await u.message.reply_html("Fetching current bind info...")
    await u.message.reply_html(api_bind_info(c.user_data["token"]))
    await u.message.reply_html("Now send the <b>email</b> to bind.")
    return BIND_EMAIL

async def bind_email(u, c):
    c.user_data["email"] = u.message.text.strip()
    r = api_send_otp(c.user_data["token"], c.user_data["email"])
    await u.message.reply_html(fmt_result(r, "Send OTP") + "\n\nEnter the <b>OTP</b> received.")
    return BIND_OTP

async def bind_otp(u, c):
    otp = u.message.text.strip()
    txt, vt = api_verify_otp_bind(c.user_data["token"], c.user_data["email"], otp)
    await u.message.reply_html(fmt_result(txt, "Verify OTP"))
    if not vt:
        await u.message.reply_html("❌ verifier_token missing — send it manually or /cancel.")
        c.user_data["awaiting_vt"] = True
        return BIND_SEC
    c.user_data["vt"] = vt
    await u.message.reply_html("✅ Verifier token captured. Now set a <b>6-digit security code</b>.")
    return BIND_SEC

async def bind_sec(u, c):
    text = u.message.text.strip()
    if c.user_data.get("awaiting_vt"):
        c.user_data["vt"] = text
        c.user_data["awaiting_vt"] = False
        await u.message.reply_html("Now send 6-digit security code.")
        return BIND_SEC
    r = api_create_bind(c.user_data["token"], c.user_data["email"], c.user_data["vt"], text)
    await u.message.reply_html(fmt_result(r, "Bind Request"), reply_markup=main_menu_kb())
    return MENU

# ---- Method picker ----
async def method_pick(u, c):
    q = u.callback_query; await q.answer()
    _, action, ch = q.data.split(":")
    c.user_data["method"] = ch
    if action == "change":
        await q.message.reply_html("Send the <b>Access Token</b>.")
        return CHG_TOKEN
    else:
        await q.message.reply_html("Send the <b>Access Token</b>.")
        return UNB_TOKEN

# ---- Change bind ----
async def chg_token(u, c):
    c.user_data["token"] = u.message.text.strip()
    old = api_current_email(c.user_data["token"])
    if not old:
        await u.message.reply_html("❌ No bound email found — cannot change.", reply_markup=main_menu_kb())
        return MENU
    c.user_data["old_email"] = old
    await u.message.reply_html(api_bind_info(c.user_data["token"]))
    if c.user_data["method"] == "1":
        r = api_send_otp(c.user_data["token"], old)
        await u.message.reply_html(fmt_result(r, "Send OTP to old email") +
                                   f"\n\nEnter OTP received on <code>{html_escape(old)}</code>.")
        return CHG_OTP_OLD
    else:
        await u.message.reply_html(f"Enter existing 6-digit <b>Security Code</b>.")
        return CHG_SEC_OLD

async def chg_otp_old(u, c):
    otp = u.message.text.strip()
    txt, it = api_verify_identity_otp(c.user_data["token"], c.user_data["old_email"], otp)
    await u.message.reply_html(fmt_result(txt, "Verify Identity"))
    if not it:
        await u.message.reply_html("❌ Identity failed.", reply_markup=main_menu_kb()); return MENU
    c.user_data["it"] = it
    await u.message.reply_html("Send the <b>new email</b> to bind.")
    return CHG_NEW_EMAIL

async def chg_sec_old(u, c):
    sec = u.message.text.strip()
    txt, it = api_verify_identity_sec(c.user_data["token"], c.user_data["old_email"], sec)
    await u.message.reply_html(fmt_result(txt, "Verify Identity"))
    if not it:
        await u.message.reply_html("❌ Identity failed.", reply_markup=main_menu_kb()); return MENU
    c.user_data["it"] = it
    await u.message.reply_html("Send the <b>new email</b> to bind.")
    return CHG_NEW_EMAIL

async def chg_new_email(u, c):
    ne = u.message.text.strip()
    c.user_data["new_email"] = ne
    r = api_send_otp(c.user_data["token"], ne)
    await u.message.reply_html(fmt_result(r, "Send OTP to new email") +
                               f"\n\nEnter OTP received on <code>{html_escape(ne)}</code>.")
    return CHG_NEW_OTP

async def chg_new_otp(u, c):
    otp = u.message.text.strip()
    txt, vt = api_verify_otp_bind(c.user_data["token"], c.user_data["new_email"], otp)
    await u.message.reply_html(fmt_result(txt, "Verify New OTP"))
    # For change_bind we use identity_token; verifier from new email not always needed,
    # but Garena expects secondary_password on final call.
    await u.message.reply_html("Enter a <b>6-digit security code</b> to finalize change.")
    return CHG_NEW_SEC

async def chg_new_sec(u, c):
    sec = u.message.text.strip()
    r = api_create_change_bind(c.user_data["token"], c.user_data["new_email"],
                               c.user_data["it"], sec)
    await u.message.reply_html(fmt_result(r, "Change Bind Request"), reply_markup=main_menu_kb())
    return MENU

# ---- Unbind ----
async def unb_token(u, c):
    c.user_data["token"] = u.message.text.strip()
    email = api_current_email(c.user_data["token"])
    if not email:
        await u.message.reply_html("❌ No bound email — cannot unbind.", reply_markup=main_menu_kb()); return MENU
    c.user_data["email"] = email
    await u.message.reply_html(api_bind_info(c.user_data["token"]))
    if c.user_data["method"] == "1":
        r = api_send_otp(c.user_data["token"], email)
        await u.message.reply_html(fmt_result(r, "Send OTP") +
                                   f"\n\nEnter OTP from <code>{html_escape(email)}</code>.")
        return UNB_OTP
    else:
        await u.message.reply_html("Enter 6-digit <b>Security Code</b>.")
        return UNB_SEC

async def unb_otp(u, c):
    otp = u.message.text.strip()
    txt, it = api_verify_identity_otp(c.user_data["token"], c.user_data["email"], otp)
    await u.message.reply_html(fmt_result(txt, "Verify Identity"))
    if not it:
        await u.message.reply_html("❌ Identity failed.", reply_markup=main_menu_kb()); return MENU
    r = api_create_unbind(c.user_data["token"], it)
    await u.message.reply_html(fmt_result(r, "Unbind Request"), reply_markup=main_menu_kb())
    return MENU

async def unb_sec(u, c):
    sec = u.message.text.strip()
    txt, it = api_verify_identity_sec(c.user_data["token"], c.user_data["email"], sec)
    await u.message.reply_html(fmt_result(txt, "Verify Identity"))
    if not it:
        await u.message.reply_html("❌ Identity failed.", reply_markup=main_menu_kb()); return MENU
    r = api_create_unbind(c.user_data["token"], it)
    await u.message.reply_html(fmt_result(r, "Unbind Request"), reply_markup=main_menu_kb())
    return MENU

# ---- Cancel / Info / EAT / Revoke / Hist ----
async def cancel_token(u, c):
    r = api_cancel(u.message.text.strip())
    await u.message.reply_html(fmt_result(r, "Cancel Request"), reply_markup=main_menu_kb())
    return MENU

async def info_token(u, c):
    await u.message.reply_html(api_bind_info(u.message.text.strip()), reply_markup=main_menu_kb())
    return MENU

async def eat_input(u, c):
    await u.message.reply_html(api_eat_to_token(u.message.text.strip()), reply_markup=main_menu_kb())
    return MENU

async def revoke_token(u, c):
    await u.message.reply_html(api_revoke(u.message.text.strip()), reply_markup=main_menu_kb())
    return MENU

async def hist_token(u, c):
    await u.message.reply_html("⏳ Running MajorLogin & fetching history...")
    await u.message.reply_html(api_login_history(u.message.text.strip()), reply_markup=main_menu_kb())
    return MENU

# ---- App ----
def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("Set BOT_TOKEN env var to your @BotFather token."); sys.exit(1)

    app = Application.builder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [CallbackQueryHandler(menu_router, pattern=r"^m:")],
            BIND_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, bind_token)],
            BIND_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, bind_email)],
            BIND_OTP:   [MessageHandler(filters.TEXT & ~filters.COMMAND, bind_otp)],
            BIND_SEC:   [MessageHandler(filters.TEXT & ~filters.COMMAND, bind_sec)],
            CHG_METHOD: [CallbackQueryHandler(method_pick, pattern=r"^method:change:"),
                         CallbackQueryHandler(menu_router, pattern=r"^m:")],
            CHG_TOKEN:  [MessageHandler(filters.TEXT & ~filters.COMMAND, chg_token)],
            CHG_OTP_OLD:[MessageHandler(filters.TEXT & ~filters.COMMAND, chg_otp_old)],
            CHG_SEC_OLD:[MessageHandler(filters.TEXT & ~filters.COMMAND, chg_sec_old)],
            CHG_NEW_EMAIL:[MessageHandler(filters.TEXT & ~filters.COMMAND, chg_new_email)],
            CHG_NEW_OTP:[MessageHandler(filters.TEXT & ~filters.COMMAND, chg_new_otp)],
            CHG_NEW_SEC:[MessageHandler(filters.TEXT & ~filters.COMMAND, chg_new_sec)],
            UNB_METHOD: [CallbackQueryHandler(method_pick, pattern=r"^method:unbind:"),
                         CallbackQueryHandler(menu_router, pattern=r"^m:")],
            UNB_TOKEN:  [MessageHandler(filters.TEXT & ~filters.COMMAND, unb_token)],
            UNB_OTP:    [MessageHandler(filters.TEXT & ~filters.COMMAND, unb_otp)],
            UNB_SEC:    [MessageHandler(filters.TEXT & ~filters.COMMAND, unb_sec)],
            CANCEL_TOKEN:[MessageHandler(filters.TEXT & ~filters.COMMAND, cancel_token)],
            INFO_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, info_token)],
            EAT_INPUT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, eat_input)],
            REVOKE_TOKEN:[MessageHandler(filters.TEXT & ~filters.COMMAND, revoke_token)],
            HIST_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, hist_token)],
        },
        fallbacks=[CommandHandler("cancel", cancel_cmd), CommandHandler("start", start)],
        allow_reentry=True,
    )
    app.add_handler(conv)
    log.info("Spidey Bind Bot started.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
