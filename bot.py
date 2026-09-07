
import os
import sys
import json
import time
import re
import base64
import hashlib
import logging
import urllib.parse
import urllib3
import requests
from datetime import datetime

# Telegram imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters, ConversationHandler
from telegram.constants import ParseMode

# Crypto
try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    HAS_CRYPTO = True
except:
    HAS_CRYPTO = False

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Protobuf optional (for EAT & History)
try:
    import MajoRLogin_pb2 as mLpB
    import MajorLoginRes_pb2 as mLrPb
    HAS_PROTOBUF = True
except ImportError:
    HAS_PROTOBUF = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "")  # set via env or replace here
# If you want hardcode: BOT_TOKEN = "123456:ABC..."
OWNER_ID = os.getenv("OWNER_ID", "")

# Conversation states
ASK_TOKEN, ASK_EMAIL, ASK_OTP, ASK_EAT, ASK_NEW_EMAIL, ASK_OLD_EMAIL, ASK_GENERIC = range(7)

# Helper functions
def convert_seconds(s):
    try:
        s = int(s)
        d, h = divmod(s, 86400)
        h, m = divmod(h, 3600)
        m, s = divmod(m, 60)
        return f"{d} Day {h} Hour {m} Min {s} Sec"
    except:
        return str(s)

def get_player_info(access_token):
    try:
        player_url = f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        r = requests.get(player_url, headers=headers, timeout=15, allow_redirects=True)
        parsed = urllib.parse.urlparse(r.url)
        qs = urllib.parse.parse_qs(parsed.query)
        uid = qs.get("account_id", ["Unknown"])[0]
        nickname = qs.get("nickname", ["Unknown"])[0]
        region = qs.get("region", ["Unknown"])[0]
        return uid, nickname, region
    except Exception as e:
        return "Unknown", "Unknown", "Unknown"

def api_bind_info(access_token):
    uid, nick, region = get_player_info(access_token)
    url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
    params = {'app_id': "100067", 'access_token': access_token}
    headers = {
        'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip"
    }
    r = requests.get(url, params=params, headers=headers, timeout=15)
    data = r.json() if r.status_code==200 else {}
    
    email = data.get("email", "")
    email_to_be = data.get("email_to_be", "")
    countdown = data.get("request_exec_countdown", 0)
    result = data.get("result", -1)

    msg = f"🎮 *Player Info*\n"
    msg += f"• UID: `{uid}`\n• Nick: {nick}\n• Region: {region}\n\n"
    msg += f"🔗 *Bind Info*\n"
    msg += f"• Current Email: `{email if email else 'None'}`\n"
    msg += f"• Pending Email: `{email_to_be if email_to_be else 'None'}`\n"
    if email_to_be:
        msg += f"• Countdown: {convert_seconds(countdown)}\n"
    msg += f"• Result Code: {result}\n"
    msg += f"\nRaw: `{json.dumps(data)[:800]}`"
    return msg

def api_bound_accounts(access_token):
    url = "https://100067.connect.garena.com/bind/app/platform/info/get"
    params = {"access_token": access_token}
    headers = {
        "User-Agent": "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    }
    r = requests.get(url, params=params, headers=headers, timeout=10)
    if r.status_code != 200:
        return f"❌ HTTP {r.status_code}: {r.text[:500]}"
    d = r.json()
    bounded = d.get("bounded_accounts", [])
    available = d.get("available_platforms", [])
    PLATFORM_MAP = {
        1: "Garena", 3: "Facebook", 4: "Guest", 5: "VK", 
        6: "Huawei", 7: "Apple", 8: "Google", 10: "GameCenter/Line", 
        11: "X (Twitter)", 13: "Apple ID", 28: "Line", 35: "TikTok"
    }
    msg = "🔗 *Bound Accounts*\n"
    if not bounded:
        msg += "• No platforms bound\n"
    else:
        for pid in bounded:
            msg += f"• {PLATFORM_MAP.get(pid, f'Unknown ({pid})')}\n"
    msg += "\n📋 *Available*\n"
    for pid in available:
        msg += f"• {PLATFORM_MAP.get(pid, f'Unknown ({pid})')}\n"
    return msg

def api_bind_email(access_token, email):
    # Step 1: request bind
    url = "https://100067.connect.garena.com/game/account_security/bind:request_bind"
    # Many tools use this endpoint; fallback logic
    headers = {
        'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)",
        'Content-Type': "application/json"
    }
    payload = {
        "app_id": "100067",
        "access_token": access_token,
        "email": email
    }
    # Try GET style first
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        return f"📧 Bind Request Sent\nEmail: {email}\nResponse: `{r.text[:1000]}`"
    except Exception as e:
        return f"❌ Error: {e}"

def api_unbind_email(access_token):
    url = "https://100067.connect.garena.com/game/account_security/bind:unbind"
    headers = {'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"}
    params = {"app_id": "100067", "access_token": access_token}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        return f"🗑️ Unbind Response:\n`{r.text[:1000]}`"
    except Exception as e:
        return f"❌ {e}"

def api_change_email(access_token, old_email, new_email):
    url = "https://100067.connect.garena.com/game/account_security/bind:change_bind"
    headers = {'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"}
    payload = {"app_id":"100067","access_token":access_token,"old_email":old_email,"new_email":new_email}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        return f"🔄 Change Email\nOld: {old_email}\nNew: {new_email}\nRes: `{r.text[:1000]}`"
    except Exception as e:
        return f"❌ {e}"

def api_cancel_bind(access_token):
    url = "https://100067.connect.garena.com/game/account_security/bind:cancel_request"
    params = {"app_id":"100067","access_token":access_token}
    headers = {'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        return f"🚫 Cancel Request:\n`{r.text[:1000]}`"
    except Exception as e:
        return f"❌ {e}"

def api_revoke_token(access_token):
    url = "https://100067.connect.garena.com/oauth/guest/revoke"
    # alternative endpoint used in many tools
    params = {"access_token": access_token, "app_id":"100067"}
    headers = {'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        # fallback
        if r.status_code!=200:
            url2 = "https://100067.connect.garena.com/game/account_security/bind:revoke"
            r = requests.get(url2, params=params, headers=headers, timeout=15)
        return f"🔒 Revoke Token:\n`{r.text[:1000]}`"
    except Exception as e:
        return f"❌ {e}"

# --- EAT to Access Token (protobuf) ---
def eat_to_token(eat_token):
    if not HAS_PROTOBUF:
        return "❌ Protobuf files missing! Add MajoRLogin_pb2.py and MajorLoginRes_pb2.py in same folder."
    try:
        # This logic is from original app.py - simplified
        # eat format: usually base64 json
        # We decode and build MajorLogin request
        # Placeholder implementation based on common pattern
        req = mLpB.MajorLogin()
        req.app_id = 100067
        req.token = eat_token
        # ... other fields may be needed
        data = req.SerializeToString()
        
        # AES encrypt? Original used AES key
        # For brevity, try direct request to login endpoint
        url = "https://100067.connect.garena.com/oauth/guest/token_grant"
        headers = {'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"}
        payload = {"app_id":"100067","udid":"", "eat": eat_token}
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        # Try to parse response protobuf
        try:
            res_pb = mLrPb.MajorLoginRes()
            res_pb.ParseFromString(r.content)
            access = getattr(res_pb, 'access_token', 'Not found')
            return f"✅ EAT Converted\nAccess Token: `{access}`\nRaw len: {len(r.content)}"
        except:
            return f"📥 Response:\n`{r.text[:1500]}`"
    except Exception as e:
        return f"❌ EAT Error: {e}"

# --- Login History (AES + Protobuf) ---
def get_login_history(access_token):
    if not HAS_CRYPTO:
        return "❌ pycryptodome missing. pip install pycryptodome"
    # This is simplified but keeps structure from original
    # Original used AES key derivation and protobuf parse
    try:
        url = "https://100067.connect.garena.com/game/account_security/history:get_history"
        params = {"app_id":"100067","access_token":access_token}
        headers = {'User-Agent': "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"}
        r = requests.get(url, params=params, headers=headers, timeout=15)
        if r.status_code!=200:
            return f"❌ History HTTP {r.status_code}"
        # Attempt decrypt if encrypted
        content = r.content
        # Placeholder AES decrypt (key from original app if known)
        # Many tools use key: 0x... We'll just try to show raw
        # Real decrypt logic needs key - keep as is
        msg = "📜 *Login History*\n"
        msg += f"Raw size: {len(content)} bytes\n"
        # Try parse as json
        try:
            j = json.loads(content)
            msg += f"```{json.dumps(j, indent=2)[:3000]}```"
        except:
            msg += f"Hex preview: `{content[:100].hex()}`\n"
            msg += "Note: Full decrypt needs AES key from original tool. Add your key logic in function `get_login_history`."
        return msg
    except Exception as e:
        return f"❌ History error: {e}"

def owner_details_text():
    return (
        "👑 *Spidey Bind Tool*\n\n"
        "⊛ Developer: @spideyabd & @INDRAJIT_1M\n"
        "⊛ Status: SAFE & SECURE\n"
        "⊛ Telegram Bot Version\n"
        "⊛ Features: 10 Options\n\n"
        "Support: DM @spideyabd"
    )

# --- Telegram UI ---
def main_menu_keyboard():
    buttons = [
        [InlineKeyboardButton("🔍 Check Bind Info", callback_data="1"),
         InlineKeyboardButton("📧 Bind Email", callback_data="2")],
        [InlineKeyboardButton("🗑️ Unbind Email", callback_data="3"),
         InlineKeyboardButton("🔄 Change Email", callback_data="4")],
        [InlineKeyboardButton("🚫 Cancel Request", callback_data="5"),
         InlineKeyboardButton("🔑 EAT → Token", callback_data="6")],
        [InlineKeyboardButton("🔒 Revoke Token", callback_data="7"),
         InlineKeyboardButton("📜 Login History", callback_data="8")],
        [InlineKeyboardButton("🔗 Bound Accounts", callback_data="9"),
         InlineKeyboardButton("👑 Owner Details", callback_data="10")],
    ]
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🕷️ *Spidey Bind Tool - Telegram Edition*\n\n"
        "Welcome! Select an option below:",
        reply_markup=main_menu_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == "1":
        await query.message.reply_text("🔑 *Access Token bhejo:*\nUse /cancel to abort", parse_mode=ParseMode.MARKDOWN)
        context.user_data['action'] = 'bind_info'
        return ASK_TOKEN
    elif choice == "2":
        await query.message.reply_text("🔑 Pehle *Access Token* bhejo, fir email puchhunga.", parse_mode=ParseMode.MARKDOWN)
        context.user_data['action'] = 'bind_email_step1'
        return ASK_TOKEN
    elif choice == "3":
        await query.message.reply_text("🔑 *Access Token* bhejo for Unbind:", parse_mode=ParseMode.MARKDOWN)
        context.user_data['action'] = 'unbind'
        return ASK_TOKEN
    elif choice == "4":
        await query.message.reply_text("🔑 *Access Token* bhejo for Change Email:", parse_mode=ParseMode.MARKDOWN)
        context.user_data['action'] = 'change_step1'
        return ASK_TOKEN
    elif choice == "5":
        await query.message.reply_text("🔑 *Access Token* bhejo for Cancel:", parse_mode=ParseMode.MARKDOWN)
        context.user_data['action'] = 'cancel'
        return ASK_TOKEN
    elif choice == "6":
        await query.message.reply_text("🍪 *EAT Token bhejo* (guest token):", parse_mode=ParseMode.MARKDOWN)
        context.user_data['action'] = 'eat'
        return ASK_EAT
    elif choice == "7":
        await query.message.reply_text("🔑 *Access Token* bhejo for Revoke:", parse_mode=ParseMode.MARKDOWN)
        context.user_data['action'] = 'revoke'
        return ASK_TOKEN
    elif choice == "8":
        await query.message.reply_text("🔑 *Access Token* bhejo for Login History:", parse_mode=ParseMode.MARKDOWN)
        context.user_data['action'] = 'history'
        return ASK_TOKEN
    elif choice == "9":
        await query.message.reply_text("🔑 *Access Token* bhejo for Bound Accounts:", parse_mode=ParseMode.MARKDOWN)
        context.user_data['action'] = 'platform'
        return ASK_TOKEN
    elif choice == "10":
        await query.message.reply_text(owner_details_text(), parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard())

# Token handler
async def handle_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip()
    action = context.user_data.get('action')
    if not token:
        await update.message.reply_text("❌ Token khali hai!")
        return

    await update.message.reply_text("⏳ Processing...")

    if action == 'bind_info':
        result = api_bind_info(token)
        await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard())
        return ConversationHandler.END

    elif action == 'bind_email_step1':
        context.user_data['access_token'] = token
        await update.message.reply_text("📧 Ab *Email* bhejo jise bind karna hai:", parse_mode=ParseMode.MARKDOWN)
        context.user_data['action'] = 'bind_email_step2'
        return ASK_EMAIL

    elif action == 'unbind':
        result = api_unbind_email(token)
        await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard())
        return ConversationHandler.END

    elif action == 'change_step1':
        context.user_data['access_token'] = token
        await update.message.reply_text("📧 Old Email bhejo:")
        context.user_data['action'] = 'change_step2'
        return ASK_OLD_EMAIL

    elif action == 'cancel':
        result = api_cancel_bind(token)
        await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard())
        return ConversationHandler.END

    elif action == 'revoke':
        result = api_revoke_token(token)
        await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard())
        return ConversationHandler.END

    elif action == 'history':
        result = get_login_history(token)
        await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard())
        return ConversationHandler.END

    elif action == 'platform':
        result = api_bound_accounts(token)
        await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard())
        return ConversationHandler.END

async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    action = context.user_data.get('action')
    token = context.user_data.get('access_token')

    if action == 'bind_email_step2':
        result = api_bind_email(token, email)
        await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard())
        return ConversationHandler.END

    elif action == 'change_step2':
        context.user_data['old_email'] = email
        await update.message.reply_text("📧 Ab New Email bhejo:")
        context.user_data['action'] = 'change_step3'
        return ASK_NEW_EMAIL

async def handle_new_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_email = update.message.text.strip()
    old_email = context.user_data.get('old_email')
    token = context.user_data.get('access_token')
    result = api_change_email(token, old_email, new_email)
    await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard())
    return ConversationHandler.END

async def handle_old_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Actually old email asked, we already handle in handle_email, but this is extra
    await handle_email(update, context)
    return ASK_NEW_EMAIL

async def handle_eat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    eat = update.message.text.strip()
    await update.message.reply_text("⏳ Converting EAT...")
    result = eat_to_token(eat)
    await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled", reply_markup=main_menu_keyboard())
    return ConversationHandler.END

def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not set! Set env variable or edit file.")
        print("Example: export BOT_TOKEN='123456:ABC-YourToken'")
        sys.exit(1)
    
    print("🕷️ Spidey Bind Bot Starting...")
    print(f"Protobuf available: {HAS_PROTOBUF}, Crypto: {HAS_CRYPTO}")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_callback)],
        states={
            ASK_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_token)],
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email)],
            ASK_NEW_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_email)],
            ASK_OLD_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_old_email)],
            ASK_EAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_eat)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    # Also allow /menu
    app.add_handler(CommandHandler("menu", start))
    app.add_handler(CommandHandler("cancel", cancel))

    print("✅ Bot running... Press Ctrl+C to stop")
    app.run_polling()

if __name__ == "__main__":
    main()
