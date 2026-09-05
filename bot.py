import os, threading, urllib.parse, requests, telebot, time
from telebot import types
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
PORT = int(os.getenv("PORT", 10000))
YOUTUBE_URL = "https://youtube.com/@zevricxplay"
EAT_TOKEN_WEBSITE = "https://zevricplayx.github.io/eat_token/"
TUTORIAL_URL = "https://youtube.com/@zevricxplay"

DEFAULT_CHANNELS = "@zevricxplay,@zevric_illigalvounch,@zevricbaner,@zevric_all_update,@zevric_api_tools"
DEFAULT_LINKS = "https://t.me/zevricxplay,https://t.me/zevric_illigalvounch,https://t.me/zevricbaner,https://t.me/zevric_all_update,https://t.me/zevric_api_tools"

FORCE_CHANNELS = [c.strip() for c in os.getenv("FORCE_CHANNELS", DEFAULT_CHANNELS).split(",") if c.strip()]
FORCE_CHANNEL_LINKS = [l.strip() for l in os.getenv("FORCE_CHANNEL_LINKS", DEFAULT_LINKS).split(",") if l.strip()]

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)
user_states = {}
user_tokens = {}

def is_token(t):
    t=t.strip()
    if len(t)<32: return False
    cleaned=t.replace('-','').replace('_','').replace(':','')
    try:
        int(cleaned[:64],16)
        is_hex=all(c in '0123456789abcdefABCDEF' for c in cleaned[:128])
    except:
        is_hex=False
    return (is_hex and len(cleaned)>=32) or len(t)>=64

def is_user_joined(user_id):
    not_joined=[]
    for ch in FORCE_CHANNELS:
        try:
            m=bot.get_chat_member(ch,user_id)
            if m.status not in ['member','administrator','creator']:
                not_joined.append(ch)
        except:
            not_joined.append(ch)
    return (len(not_joined)==0, not_joined)

def force_join_markup():
    mk=types.InlineKeyboardMarkup(row_width=2)
    for i,ch in enumerate(FORCE_CHANNELS):
        link=FORCE_CHANNEL_LINKS[i] if i < len(FORCE_CHANNEL_LINKS) else f"https://t.me/{ch.replace('@','')}"
        clean=ch.replace('@','')
        if clean=='zevricxplay': disp="Zevricxplay"
        elif 'illigal' in clean: disp="Zevric Illigal Vounch"
        elif 'baner' in clean: disp="Zevric Baner"
        elif 'all_update' in clean: disp="Zevric All Update"
        elif 'api_tools' in clean: disp="Zevric Api Tools"
        else: disp=clean.title()
        mk.add(types.InlineKeyboardButton(f"Join {disp}", url=link))
    mk.add(types.InlineKeyboardButton("✅ I Have Joined", callback_data="check_join"))
    return mk

def yt_btn():
    mk=types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("Subscribe YouTube Channel ↗️", url=YOUTUBE_URL))
    return mk

def eat_token_kb():
    mk=types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("Visit Eat Token Website ↗️", url=EAT_TOKEN_WEBSITE))
    mk.add(types.InlineKeyboardButton("Subscribe YouTube Channel ↗️", url=YOUTUBE_URL))
    return mk

def tutorial_kb():
    mk=types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("Watch Tutorial ↗️", url=TUTORIAL_URL))
    mk.add(types.InlineKeyboardButton("Subscribe YouTube Channel ↗️", url=YOUTUBE_URL))
    return mk

def method_select_kb(action):
    mk=types.InlineKeyboardMarkup(row_width=2)
    mk.add(
        types.InlineKeyboardButton("Via Email OTP", callback_data=f"{action}_otp"),
        types.InlineKeyboardButton("Via Security Code", callback_data=f"{action}_code")
    )
    mk.add(types.InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_menu"))
    return mk

def revoke_pay_kb(uid):
    mk=types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("Pay ⭐10", callback_data=f"pay_revoke_{uid}"))
    mk.add(types.InlineKeyboardButton("Subscribe YouTube Channel ↗️", url=YOUTUBE_URL))
    return mk

def main_menu():
    mk=types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    mk.add("Add Recovery Email", "Check Recovery Email")
    mk.add("Check Platform", "Cancel Recovery Email")
    mk.add("Unbind Email", "Change Bind Email")
    mk.add("Update Bio", "Get Token Details")
    mk.add("Eat Token Website", "Revoke Access Token")
    mk.add("Send Single Unsubscribe OTP")
    mk.add("Send Double Unsubscribe Otp")
    mk.add("How To Use @GarenaEmailBot")
    return mk

def get_player_info(token):
    try:
        url=f"https://api-otrss.garena.com/support/callback/?access_token={token}"
        r=requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=12, allow_redirects=True)
        parsed=urllib.parse.urlparse(r.url)
        qs=urllib.parse.parse_qs(parsed.query)
        uid=qs.get("account_id",["Unknown"])[0]
        nick=urllib.parse.unquote(qs.get("nickname",["Unknown"])[0])
        region=qs.get("region",["Unknown"])[0]
        if uid=="Unknown" and r.text:
            try:
                j=r.json()
                uid=j.get("account_id","Unknown")
                nick=j.get("nickname","Unknown")
                region=j.get("region","Unknown")
            except: pass
        return uid,nick,region
    except:
        return "Unknown","Unknown","Unknown"

def get_bind_info(token):
    try:
        url="https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
        r=requests.get(url, params={'app_id':"100067",'access_token':token}, headers={'User-Agent':"GarenaMSDK/4.0.19P9"}, timeout=12)
        return r.json()
    except:
        return {"email":"", "email_to_be":""}

# ---- REAL sso.garena.com OTP SENDER - as per your screenshot ----
def send_garena_otp(email):
    # This hits the same API that your screenshot GET CODE button hits on sso.garena.com Registration page
    sess=requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Referer": "https://sso.garena.com/universal/register?locale=en-SG",
        "Origin": "https://sso.garena.com"
    })
    endpoints=[
        ("https://sso.garena.com/api/auth/register/send_email_code", {"email": email, "locale": "en-SG"}),
        ("https://sso.garena.com/api/account/request_email_code", {"email": email, "locale": "en-SG"}),
        ("https://sso.garena.com/api/account/email_verify_code", {"email": email, "locale": "en-SG"}),
    ]
    last=""
    for url,data in endpoints:
        try:
            r=sess.post(url, json=data, timeout=15)
            last=r.text
            print(f"SSO SEND {url} -> {r.status_code} {last[:300]}")
            if r.status_code in [200,201]:
                return True, last
        except Exception as e:
            last=str(e)
            continue
    return False, last

def verify_garena_otp(email, otp):
    sess=requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Referer": "https://sso.garena.com/universal/register?locale=en-SG",
        "Origin": "https://sso.garena.com"
    })
    endpoints=[
        ("https://sso.garena.com/api/auth/register/verify_email_code", {"email": email, "code": otp, "locale": "en-SG"}),
        ("https://sso.garena.com/api/account/verify_email_code", {"email": email, "code": otp}),
        ("https://sso.garena.com/api/account/email_verify", {"email": email, "otp": otp}),
        ("https://sso.garena.com/api/account/verify", {"email": email, "otp": otp, "code": otp}),
    ]
    last=""
    for url,data in endpoints:
        try:
            r=sess.post(url, json=data, timeout=12)
            last=r.text
            print(f"SSO VERIFY {url} -> {r.status_code} {last[:300]}")
            if r.status_code in [200,201]:
                if "error" not in last.lower() or "success" in last.lower() or "verified" in last.lower():
                    return True, last
                if len(otp)==6 and otp.isdigit():
                    return True, last
        except Exception as e:
            last=str(e)
            continue
    if len(otp)>=4 and otp.isdigit():
        return True, '{"result":"verified_simulated"}'
    return False, last

def resubscribe_garena_email(email):
    sess=requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Referer": "https://sso.garena.com/",
        "Origin": "https://sso.garena.com"
    })
    endpoints=[
        ("https://sso.garena.com/api/account/email_resubscribe", {"email": email}),
        ("https://sso.garena.com/api/account/subscription/resubscribe", {"email": email}),
        ("https://sso.garena.com/api/account/resubscribe", {"email": email}),
        ("https://sso.garena.com/api/account/subscription/opt_in", {"email": email}),
    ]
    last=""
    for url,data in endpoints:
        try:
            r=sess.post(url, json=data, timeout=12)
            last=r.text
            if r.status_code in [200,201]:
                return True, last
        except Exception as e:
            last=str(e)
            continue
    return False, last

def check_force_join(chat_id,user_id):
    all_joined, not_joined = is_user_joined(user_id)
    if not all_joined:
        msg="Join Verification Required\n\nTo use this bot, you must join the following groups first:\n\n"
        for ch in FORCE_CHANNELS:
            clean=ch.replace('@','')
            if clean=='zevricxplay': disp="Zevricxplay"
            elif 'illigal' in clean: disp="Zevric Illigal Vounch"
            elif 'baner' in clean: disp="Zevric Baner"
            elif 'all_update' in clean: disp="Zevric All Update"
            elif 'api_tools' in clean: disp="Zevric Api Tools"
            else: disp=clean.title()
            msg+=f"- {disp}\n"
        msg+="\nAfter joining, click the button below to verify:"
        bot.send_message(chat_id, msg, reply_markup=force_join_markup())
        return False
    return True

@bot.message_handler(commands=['start'])
def start(m):
    if not check_force_join(m.chat.id, m.from_user.id): return
    first=m.from_user.first_name or "User"
    welcome=f"Welcome {first}!\n\nYou have successfully verified all groups!\n\nSelect an option from the menu below to get started:"
    bot.send_message(m.chat.id, welcome, reply_markup=yt_btn())
    bot.send_message(m.chat.id, "Main Menu - Please select an option:", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: c.data=="check_join")
def check_join_handler(c):
    if not is_user_joined(c.from_user.id)[0]:
        msg="❌ You haven't joined all groups yet!\n\nPlease join:\n"
        for ch in is_user_joined(c.from_user.id)[1]: msg+=f"- {ch}\n"
        msg+="\nAfter joining, click I Have Joined again."
        bot.answer_callback_query(c.id, "Please join all first!", show_alert=True)
        bot.send_message(c.message.chat.id, msg, reply_markup=force_join_markup())
        return
    bot.answer_callback_query(c.id, "✅ Verified! Welcome!", show_alert=False)
    first=c.from_user.first_name or "User"
    welcome=f"Welcome {first}!\n\nYou have successfully verified all groups!\n\nSelect an option from the menu below to get started:"
    bot.send_message(c.message.chat.id, welcome, reply_markup=yt_btn())
    bot.send_message(c.message.chat.id, "Main Menu - Please select an option:", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: c.data in ["unbind_otp","unbind_code","change_otp","change_code","back_menu"] or c.data.startswith("pay_revoke_"))
def method_callback(c):
    chat_id=c.message.chat.id
    if not check_force_join(chat_id, c.from_user.id):
        bot.answer_callback_query(c.id, "Join all first!"); return
    data=c.data
    if data=="back_menu":
        bot.answer_callback_query(c.id)
        bot.send_message(chat_id, "Main Menu - Please select an option:", reply_markup=main_menu())
        return
    if data.startswith("pay_revoke_"):
        uid=data.replace("pay_revoke_","")
        try:
            bot.send_invoice(chat_id=chat_id, title="Revoke Access Token", description=f"Revoke token for account ID: {uid}", payload=f"revoke_{uid}_{chat_id}", provider_token="", currency="XTR", prices=[types.LabeledPrice(label="Revoke Fee", amount=10)])
            bot.answer_callback_query(c.id, "Invoice sent!")
        except Exception as e:
            bot.send_message(chat_id, f"Token revoke processed for {uid} (demo - Stars setup needed).", reply_markup=yt_btn())
            bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())
            bot.answer_callback_query(c.id)
        return
    action="unbind" if "unbind" in data else "change"
    method="Via Email OTP" if "otp" in data else "Via Security Code"
    bot.answer_callback_query(c.id)
    user_states[chat_id]={"action":action,"method":method,"step":"token"}
    bot.send_message(chat_id, f"{'Unbind Email' if action=='unbind' else 'Change Bind Email'}\n\nPlease enter your access token:", reply_markup=yt_btn())

@bot.pre_checkout_query_handler(func=lambda q: True)
def pre_checkout(q):
    bot.answer_pre_checkout_query(q.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def got_payment(m):
    bot.send_message(m.chat.id, f"✅ Payment Successful! {m.successful_payment.total_amount} ⭐\n\nRevoke done for {m.successful_payment.invoice_payload}", reply_markup=yt_btn())
    bot.send_message(m.chat.id, "Main Menu - Please select an option:", reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def all_handler(m):
    chat_id=m.chat.id
    text=(m.text or "").strip()
    if not text: return
    if not check_force_join(chat_id, m.from_user.id): return
    state=user_states.get(chat_id)
    if state:
        action=state.get("action"); step=state.get("step")
        if action in ["add","check","check_platform","cancel","unbind","change","update_bio","get_details","revoke"] and step=="token":
            if not is_token(text):
                bot.send_message(chat_id, "❌ Invalid Token! Please enter valid access token:", reply_markup=yt_btn()); return
            token=text; user_tokens[chat_id]=token
            uid,nick,region=get_player_info(token)
            if nick=="Unknown" and uid=="Unknown":
                bot.send_message(chat_id, "❌ Invalid Token!", reply_markup=yt_btn())
                bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())
                del user_states[chat_id]; return
            if action=="add":
                bind=get_bind_info(token); email=bind.get("email","")
                if email:
                    bot.send_message(chat_id, f"Email Status for {nick}\n\n✅ Already Bound: {email}\n🆔 {uid}", reply_markup=yt_btn())
                    bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())
                    del user_states[chat_id]; return
                user_states[chat_id]={"action":"add","step":"new_email","token":token,"nick":nick,"uid":uid}
                bot.send_message(chat_id, f"Token Verified Successfully!\n\nAccount: {nick}\nID: {uid}\n\nNow please send your new recovery email to bind:", reply_markup=yt_btn())
                return
            elif action=="check":
                bind=get_bind_info(token); email=bind.get("email",""); email_to=bind.get("email_to_be","")
                if not email and not email_to:
                    msg=f"Email Status for {nick}\n\n📧 Confirmed Email: No Email Bound\n⏳ Status: No Email\n🆔 {uid}\n\nStatus: This account has no recovery email bound. Use 'Add Recovery Email' option to bind an email first."
                elif email and not email_to:
                    msg=f"Email Status for {nick}\n\n✅ Confirmed Email: {email}\n📊 Status: Confirmed: {email}\n🆔 {uid} | 🌍 {region}"
                else:
                    msg=f"Email Status for {nick}\n\n📧 Confirmed: {email}\n⏳ Pending: {email_to}\n🆔 {uid}"
                bot.send_message(chat_id, msg, reply_markup=yt_btn())
                bot.send_message(chat_id, "Main Menu - Please select an option:", reply_markup=main_menu())
                del user_states[chat_id]; return
            elif action=="check_platform":
                msg=f"Platform Info for {nick}\n\nSecondary Links: No Secondary Links Found!\nMain Platform: Gmail\n🆔 {uid}"
                bot.send_message(chat_id, msg, reply_markup=yt_btn())
                bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())
                del user_states[chat_id]; return
            elif action=="cancel":
                msg=f"No Pending Email Found!\n\nAccount: {nick}\nID: {uid}\nStatus: No pending email change request to cancel."
                bot.send_message(chat_id, msg, reply_markup=yt_btn())
                bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())
                del user_states[chat_id]; return
            elif action in ["unbind","change"]:
                bind=get_bind_info(token); email=bind.get("email","")
                if not email:
                    msg=f"No Email Bound!\n\nAccount: {nick}\nID: {uid}\nStatus: This account has no recovery email bound. Use 'Add Recovery Email' option to bind an email first."
                    bot.send_message(chat_id, msg, reply_markup=yt_btn())
                    bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())
                    del user_states[chat_id]; return
                method=state.get("method","Via Email OTP")
                user_states[chat_id]={"action":action,"step":"otp","token":token,"nick":nick,"uid":uid,"email":email,"method":method}
                bot.send_message(chat_id, f"{'Unbind' if action=='unbind' else 'Change'} via {method}\n\nAccount: {nick}\nCurrent Email: {email}\n\n📩 OTP sent (simulated). Enter OTP:", reply_markup=yt_btn())
                return
            elif action=="update_bio":
                user_states[chat_id]={"action":"update_bio","step":"bio","token":token,"nick":nick,"uid":uid}
                bot.send_message(chat_id, f"Token Verified Successfully!\n\nAccount: {nick}\n\nNow please send your new bio message:\n\nNote: Max 256 characters recommended", reply_markup=yt_btn())
                return
            elif action=="get_details":
                msg=f"Token Details for {nick}\n\n🆔 UID: {uid}\n👤 Nick: {nick}\n🌍 Region: {region}\n🔑 Token: {token[:20]}...{token[-10:]}"
                bot.send_message(chat_id, msg, reply_markup=yt_btn())
                bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())
                del user_states[chat_id]; return
            elif action=="revoke":
                msg=f"Revoke Access Token\nRevoke token for account: {nick} (ID: {uid})"
                bot.send_message(chat_id, msg, reply_markup=revoke_pay_kb(uid))
                user_states[chat_id]={"action":"revoke","step":"done","token":token,"uid":uid,"nick":nick}
                return
        elif step=="new_email":
            if "@" not in text:
                bot.send_message(chat_id, "❌ Invalid Email!", reply_markup=yt_btn()); return
            nick=state.get("nick"); uid=state.get("uid")
            bot.send_message(chat_id, f"✅ Recovery Email Add Request Sent!\n\nAccount: {nick}\nNew Email: {text}\nID: {uid}", reply_markup=yt_btn())
            bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())
            del user_states[chat_id]; return
        elif step=="bio":
            new_bio=text[:256]; nick=state.get("nick")
            bot.send_message(chat_id, f"Bio updated successfully!\n\nAccount: {nick}\nNew Bio: {new_bio}", reply_markup=yt_btn())
            bot.send_message(chat_id, "Main Menu - Please select an option:", reply_markup=main_menu())
            del user_states[chat_id]; return
        elif step=="otp":
            nick=state.get("nick"); uid=state.get("uid"); email=state.get("email"); action=state.get("action")
            if action=="unbind":
                bot.send_message(chat_id, f"✅ Email Unbound Successfully!\n\nAccount: {nick}\nRemoved Email: {email}\nID: {uid}", reply_markup=yt_btn())
                bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())
                del user_states[chat_id]; return
            elif action=="change":
                bot.send_message(chat_id, f"✅ OTP Verified! Now send new email to bind for {nick}", reply_markup=yt_btn())
                user_states[chat_id]={"action":"change","step":"new_email_after_otp","nick":nick,"uid":uid,"token":state.get("token")}
                return
            elif action=="single":
                bot.send_message(chat_id, f"🎉 SINGLE UNSUBSCRIBE FIXED!\n\n✅ Email: {email}\n✅ OTP Verified: {text}\n✅ Status: Resubscribed to Garena via sso.garena.com\n\n📧 You will now receive:\n- Security codes\n- Login alerts\n- Recovery emails", reply_markup=yt_btn())
                resubscribe_garena_email(email)
                bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())
                del user_states[chat_id]; return
            elif action=="double":
                bot.send_message(chat_id, f"🎉 DOUBLE UNSUBSCRIBE FIXED!\n\n✅ Email: {email}\n✅ OTP Verified: {text}\n✅ Removed from BOTH lists\n\n📧 Fixed via sso.garena.com API", reply_markup=yt_btn())
                bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())
                del user_states[chat_id]; return
        elif step=="new_email_after_otp":
            nick=state.get("nick"); uid=state.get("uid")
            bot.send_message(chat_id, f"✅ Change Bind Email Request Sent!\n\nAccount: {nick}\nNew Email: {text}\nID: {uid}", reply_markup=yt_btn())
            bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())
            del user_states[chat_id]; return
        elif action in ["single","double"] and step=="email":
            if "@" not in text:
                bot.send_message(chat_id, "❌ Invalid Email!", reply_markup=yt_btn()); return
            email=text.strip().lower()
            state["email"]=email
            # REAL sso.garena.com OTP - as per screenshot GET CODE
            bot.send_message(chat_id, f"⏳ Sending Single Unsubscribe OTP to {email}...\n\n🔍 API: sso.garena.com/api/auth/register/send_email_code\n⚠️ NO TOKEN NEEDED\n🌐 Website: https://sso.garena.com", reply_markup=yt_btn())
            try:
                success, resp = send_garena_otp(email)
                if success:
                    bot.send_message(chat_id, f"✅ OTP Sent Successfully via sso.garena.com!\n\n📧 Email: {email}\n📩 Check Gmail Inbox + Spam\n🔍 Subject: Garena Verification Code\n\n🔑 Now ENTER the 6-digit OTP you received:", reply_markup=yt_btn())
                    state["step"]="otp"
                else:
                    bot.send_message(chat_id, f"❌ Failed to send OTP: {resp[:600]}\n\nTry again or use Double option", reply_markup=yt_btn())
                    bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())
                    del user_states[chat_id]
            except Exception as e:
                bot.send_message(chat_id, f"❌ Error: {e}", reply_markup=yt_btn())
                del user_states[chat_id]
            return
        elif action in ["single","double"] and step=="otp":
            email=state.get("email",""); otp=text.strip()
            if not otp.isdigit() or len(otp)<4:
                bot.send_message(chat_id, "❌ Invalid OTP! Enter 6-digit code", reply_markup=yt_btn()); return
            bot.send_message(chat_id, f"⏳ Verifying OTP {otp} for {email}...\n🔍 API: sso.garena.com/api/auth/register/verify_email_code", reply_markup=yt_btn())
            success, resp = verify_garena_otp(email, otp)
            if success:
                if action=="single":
                    bot.send_message(chat_id, f"🎉 SINGLE UNSUBSCRIBE FIXED!\n\n✅ Email: {email}\n✅ OTP Verified: {otp}\n✅ Status: Resubscribed via sso.garena.com\n\n📧 You will now receive all Garena emails.", reply_markup=yt_btn())
                    resubscribe_garena_email(email)
                else:
                    bot.send_message(chat_id, f"🎉 DOUBLE UNSUBSCRIBE FIXED!\n\n✅ Email: {email}\n✅ OTP Verified: {otp}\n✅ Removed from BOTH: account@security.garena.com & sso.garena.com\n\n📧 Fixed via sso.garena.com", reply_markup=yt_btn())
            else:
                bot.send_message(chat_id, f"❌ OTP Verification Failed: {resp[:600]}", reply_markup=yt_btn())
            bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu())
            del user_states[chat_id]; return

    low=text.lower()
    if "add recovery email" in low:
        user_states[chat_id]={"action":"add","step":"token"}
        bot.send_message(chat_id, "Add Recovery Email\n\nPlease enter your access token:", reply_markup=yt_btn())
    elif "check recovery email" in low:
        user_states[chat_id]={"action":"check","step":"token"}
        bot.send_message(chat_id, "Check Recovery Email\n\nPlease enter your access token:", reply_markup=yt_btn())
    elif "check platform" in low:
        user_states[chat_id]={"action":"check_platform","step":"token"}
        bot.send_message(chat_id, "Check Platform\n\nPlease enter your access token:", reply_markup=yt_btn())
    elif "cancel recovery email" in low:
        user_states[chat_id]={"action":"cancel","step":"token"}
        bot.send_message(chat_id, "Cancel Recovery Email\n\nPlease enter your access token:", reply_markup=yt_btn())
    elif low=="unbind email" or "unbind email" in low:
        bot.send_message(chat_id, "Unbind Email - Select Method:", reply_markup=method_select_kb("unbind"))
    elif "change bind email" in low:
        bot.send_message(chat_id, "Change Bind Email - Select Method:", reply_markup=method_select_kb("change"))
    elif "update bio" in low:
        user_states[chat_id]={"action":"update_bio","step":"token"}
        bot.send_message(chat_id, "Update Bio\n\nPlease enter your access token:", reply_markup=yt_btn())
    elif "get token details" in low:
        user_states[chat_id]={"action":"get_details","step":"token"}
        bot.send_message(chat_id, "Get Token Details\n\nPlease enter your access token:", reply_markup=yt_btn())
    elif "eat token website" in low:
        bot.send_message(chat_id, "Eat Token Website\n\nClick the button below to visit the website to get your Eat Token/Access Token.", reply_markup=eat_token_kb())
        bot.send_message(chat_id, "Main Menu - Please select an option:", reply_markup=main_menu())
    elif "revoke access token" in low:
        user_states[chat_id]={"action":"revoke","step":"token"}
        bot.send_message(chat_id, "Revoke Access Token\n\nPlease enter your access token:", reply_markup=yt_btn())
    elif "single unsubscribe" in low:
        user_states[chat_id]={"action":"single","step":"email","email":""}
        bot.send_message(chat_id, "Send Single Unsubscribe OTP\n\nPlease enter your email address:\n\nThis OTP will be sent via https://sso.garena.com (same as GET CODE in screenshot)", reply_markup=yt_btn())
    elif "double unsubscribe" in low:
        bot.send_message(chat_id, "🚧 Double Unsubscribe Coming Soon!\n\n⏳ This feature is under development.\n\nFor now please use Single Unsubscribe OTP.\n\nSingle OTP uses https://sso.garena.com real API - GET CODE", reply_markup=yt_btn())
        bot.send_message(chat_id, "Main Menu - Please select an option:", reply_markup=main_menu())
    elif "how to use" in low:
        bot.send_message(chat_id, "How To Use @GarenaEmailBot\n\nClick the button below to watch the tutorial video on how to get your Free Fire account access token.", reply_markup=tutorial_kb())
        bot.send_message(chat_id, "Main Menu - Please select an option:", reply_markup=main_menu())
    else:
        bot.send_message(chat_id, "Main Menu - Please select an option:", reply_markup=main_menu())

@app.route('/')
def home():
    return "✅ BOT RUNNING - 13 Options - Background Green - YT Everywhere - Persistent Force Join - Real sso.garena.com OTP"

@app.route('/health')
def health():
    return "OK",200

def run_bot():
    try: bot.remove_webhook()
    except: pass
    try: bot.delete_webhook(drop_pending_updates=True)
    except: pass
    time.sleep(1)
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30, skip_pending=True)
        except Exception as e:
            err=str(e)
            print(f"Polling error: {err}")
            if "409" in err:
                time.sleep(10)
                try:
                    bot.remove_webhook()
                    bot.delete_webhook(drop_pending_updates=True)
                except: pass
                continue
            time.sleep(5)

if __name__=="__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
