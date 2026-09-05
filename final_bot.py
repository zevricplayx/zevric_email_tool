import os, threading, requests, urllib.parse, re, telebot
from telebot import types
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
PORT = int(os.getenv("PORT", 10000))
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)

user_states = {}
user_tokens = {}
HEADERS = {
    "User-Agent": "GarenaMSDK/4.0.30",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json"
}

def is_garena_token(text):
    return len(text.strip())>80

def get_player_info(access_token):
    try:
        url=f"https://api-otrss.garena.com/support/callback/?access_token={access_token}"
        res=requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=15, allow_redirects=True)
        parsed=urllib.parse.urlparse(res.url)
        params=urllib.parse.parse_qs(parsed.query)
        uid=params.get("account_id",["Unknown"])[0]
        nick=urllib.parse.unquote(params.get("nickname",["Unknown"])[0])
        region=params.get("region",["Unknown"])[0]
        return uid,nick,region
    except:
        return "Unknown","Unknown","Unknown"

def get_bind_info_api(access_token):
    url="https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
    try:
        r=requests.get(url, params={'app_id':"100067",'access_token':access_token}, headers={'User-Agent':"GarenaMSDK/4.0.19P9"}, timeout=15)
        return r.json()
    except Exception as e:
        return {"email":"","email_to_be":"","error":str(e)}

def convert_seconds(s):
    try:
        s=int(s)
        d,h=divmod(s,86400)
        h,m=divmod(h,3600)
        m,s=divmod(m,60)
        return f"{d}ᴅ {h}ʜ {m}ᴍ {s}s"
    except:
        return str(s)

def main_menu():
    markup=types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
    markup.add(types.KeyboardButton("➕ Add Recovery Email"),types.KeyboardButton("🔍 Check Recovery Email"))
    markup.add(types.KeyboardButton("🌐 Check Platform"),types.KeyboardButton("🚫 Cancel Recovery Email"))
    markup.add(types.KeyboardButton("❌ Unbind Email"),types.KeyboardButton("🔄 Change Bind Email"))
    markup.add(types.KeyboardButton("📝 Update Bio"),types.KeyboardButton("🎫 Get Token Details"))
    markup.add(types.KeyboardButton("🌍 Eat Token Website"),types.KeyboardButton("🔒 Revoke Access Token"))
    markup.add(types.KeyboardButton("📩 Send Single Unsubscribe OTP"))
    markup.add(types.KeyboardButton("📖 How To Use @GarenaEmailBot"))
    markup.add(types.KeyboardButton("🎯 Eat-Token"))
    return markup

def stylish_start_text():
    return """
╭━━━━━━━━━━━━━━━━━━━━╮
   🔥 <b>𝗭𝗘𝗩𝗥𝗜𝗖 𝗢𝗡 𝗧𝗢𝗣</b> 🔥
╰━━━━━━━━━━━━━━━━━━━━╯

⚡️ <b>𝗭𝗘𝗩𝗥𝗜𝗖 𝗕𝗜𝗡𝗗 𝗕𝗢𝗧</b> ⚡️
▰▱▰▱▰▱▰▱▰▱▰▱▰▱▰▱

👑 <b>𝐃𝐞𝐯𝐞𝐥𝐨𝐩𝐞𝐫 :</b> <code>@just_zevric</code>
📢 <b>𝐂𝐡𝐚𝐧𝐧𝐞𝐥 :</b> <code>@just_zevric</code>
🎥 <b>𝐘𝐨𝐮𝐓𝐮𝐛𝐞 :</b> <code>@zevricxplay</code>
💎 <b>𝐕𝐞𝐫𝐬𝐢𝐨𝐧 :</b> <code>𝘃𝟮.𝟬 𝗣𝗿𝗲𝗺𝗶𝘂𝗺</code>
🛡️ <b>𝐒𝐭𝐚𝐭𝐮𝐬 :</b> <code>𝐒𝐀𝐅𝐄 & 𝐒𝐄𝐂𝐔𝐑𝐄</code>

▰▱▰▱▰▱▰▱▰▱▰▱▰▱▰▱
🚀 <b>𝗔𝗨𝗧𝗢 𝗖𝗛𝗘𝗖𝗞 :</b> <i>Token direct bhejo, bot auto check karega!</i>

<b>💬 𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒 𝐋𝐈𝐒𝐓 :</b>
├ 🔍 <code>/check</code> - 𝗕𝗶𝗻𝗱 𝗜𝗻𝗳𝗼 𝗖𝗵𝗲𝗰𝗸
├ ➕ <code>/bind</code> - 𝗔𝗱𝗱 𝗥𝗲𝗰𝗼𝘃𝗲𝗿𝘆 𝗘𝗺𝗮𝗶𝗹
├ ❌ <code>/unbind</code> - 𝗘𝗺𝗮𝗶𝗹 𝗛𝗮𝘁𝗮𝗼
├ 🔄 <code>/change</code> - 𝗘𝗺𝗮𝗶𝗹 𝗖𝗵𝗮𝗻𝗴𝗲
├ 🚫 <code>/cancel</code> - 𝗣𝗲𝗻𝗱𝗶𝗻𝗴 𝗖𝗮𝗻𝗰𝗲𝗹
├ 🌍 <code>/eat</code> - 𝗘𝗔𝗧 𝘁𝗼 𝗧𝗼𝗸𝗲𝗻
├ 🔒 <code>/revoke</code> - 𝗧𝗼𝗸𝗲𝗻 𝗟𝗼𝗴𝗼𝘂𝘁
├ 📝 <code>/bio</code> - 𝗕𝗶𝗼 𝗨𝗽𝗱𝗮𝘁𝗲
└ 🌐 <code>/platform</code> - 𝗣𝗹𝗮𝘁𝗳𝗼𝗿𝗺 𝗜𝗻𝗳𝗼

👇 <b>Neeche button se bhi use kar sakte ho</b> 👇
"""

def stylish_status(uid,nick,region,email,email_to_be,countdown):
    confirmed = email if email else "❌ 𝗡𝗼 𝗘𝗺𝗮𝗶𝗹 𝗕𝗼𝘂𝗻𝗱"
    if email and not email_to_be:
        status = f"✅ 𝗖𝗼𝗻𝗳𝗶𝗿𝗺𝗲𝗱 : {email}"
        status_icon = "🟢"
    elif email_to_be:
        status = f"⏳ 𝗣𝗲𝗻𝗱𝗶𝗻𝗴 : {email_to_be}\n⏰ 𝗧𝗶𝗺𝗲 : {convert_seconds(countdown)}"
        status_icon = "🟡"
    else:
        status = "❌ 𝗡𝗼 𝗘𝗺𝗮𝗶𝗹 𝗦𝗲𝘁"
        status_icon = "🔴"

    return f"""
╭━━━ <b>🎮 𝗣𝗟𝗔𝗬𝗘𝗥 𝗜𝗡𝗙𝗢</b> ━━━╮
┃
┣ 🆔 <b>𝗨𝗜𝗗 :</b> <code>{uid}</code>
┣ 👤 <b>𝗡𝗶𝗰𝗸 :</b> <code>{nick}</code>
┣ 🌍 <b>𝗥𝗲𝗴𝗶𝗼𝗻 :</b> <code>{region}</code>
┃
╰━━━━━━━━━━━━━━━━━━╯

╭━━━ {status_icon} <b>📧 𝗕𝗜𝗡𝗗 𝗜𝗡𝗙𝗢</b> ━━━╮
┃
┣ 📬 <b>𝗖𝘂𝗿𝗿𝗲𝗻𝘁 :</b> <code>{confirmed}</code>
┣ {status}
┃
╰━━━━━━━━━━━━━━━━━━╯
"""

def send_status(chat_id,access_token):
    uid,nick,region=get_player_info(access_token)
    bind=get_bind_info_api(access_token)
    email=bind.get("email","")
    email_to_be=bind.get("email_to_be","")
    countdown=bind.get("request_exec_countdown",0)
    user_tokens[chat_id]=access_token
    msg = stylish_status(uid,nick,region,email,email_to_be,countdown)
    bot.send_message(chat_id,msg)
    inline=types.InlineKeyboardMarkup()
    inline.add(
        types.InlineKeyboardButton("📢 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 𝗝𝗼𝗶𝗻 ↗", url="https://t.me/just_zevric"),
        types.InlineKeyboardButton("🎥 𝗬𝗼𝘂𝗧𝘂𝗯𝗲 ↗", url="https://youtube.com/@zevricxplay")
    )
    bot.send_message(chat_id,"⚡️ <b>𝗠𝗔𝗜𝗡 𝗠𝗘𝗡𝗨</b> - 𝗢𝗽𝘁𝗶𝗼𝗻 𝗰𝗵𝘂𝗻𝗼 👇",reply_markup=main_menu())
    bot.send_message(chat_id,"🔥 <b>𝗭𝗘𝗩𝗥𝗜𝗖 𝗢𝗡 𝗧𝗢𝗣</b> - 𝗨𝗽𝗱𝗮𝘁𝗲𝘀 𝗸𝗲 𝗹𝗶𝘆𝗲 𝗝𝗼𝗶𝗻 𝗸𝗮𝗿𝗼 👇",reply_markup=inline)

@bot.message_handler(commands=['start','help'])
def cmd_start(message):
    bot.send_message(message.chat.id,stylish_start_text(),reply_markup=main_menu())

@bot.message_handler(commands=['check'])
def cmd_check(message):
    parts=message.text.split(maxsplit=1)
    token=parts[1].strip() if len(parts)>1 else user_tokens.get(message.chat.id)
    if not token:
        bot.reply_to(message,"❌ <b>Usage:</b> <code>/check YOUR_TOKEN</code>\n\n💡 <i>Pehle token bhejo fir /check likho</i>")
        return
    send_status(message.chat.id,token)

@bot.message_handler(commands=['cancel'])
def cmd_cancel(message):
    parts=message.text.split(maxsplit=1)
    token=parts[1].strip() if len(parts)>1 else user_tokens.get(message.chat.id)
    if not token:
        bot.reply_to(message,"❌ <b>Usage:</b> <code>/cancel YOUR_TOKEN</code>")
        return
    try:
        url="https://100067.connect.garena.com/game/account_security/bind:cancel_request"
        data={"app_id":"100067","access_token":token}
        r=requests.post(url,headers=HEADERS,data=data,timeout=15)
        if r.json().get("result")==0:
            bot.reply_to(message,"✅ <b>𝗖𝗔𝗡𝗖𝗘𝗟 𝗦𝗨𝗖𝗖𝗘𝗦𝗦</b> 🎉\n\n🚫 𝗣𝗲𝗻𝗱𝗶𝗻𝗴 𝗿𝗲𝗾𝘂𝗲𝘀𝘁 𝗵𝗮𝘁 𝗴𝗮𝘆𝗮!")
        else:
            bot.reply_to(message,f"❌ <b>Failed:</b> {r.text[:800]}")
    except Exception as e:
        bot.reply_to(message,f"❌ <b>Error:</b> {e}")

@bot.message_handler(commands=['revoke'])
def cmd_revoke(message):
    parts=message.text.split(maxsplit=1)
    token=parts[1].strip() if len(parts)>1 else user_tokens.get(message.chat.id)
    if not token:
        bot.reply_to(message,"❌ <b>Usage:</b> <code>/revoke YOUR_TOKEN</code>")
        return
    try:
        refresh="1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
        url=f"https://100067.connect.garena.com/oauth/logout?access_token={token}&refresh_token={refresh}"
        r=requests.get(url,headers={"User-Agent":"Mozilla/5.0"},timeout=15)
        if r.status_code==200 and "error" not in r.text:
            bot.reply_to(message,"🔒 <b>𝗧𝗢𝗞𝗘𝗡 𝗥𝗘𝗩𝗢𝗞𝗘𝗗</b> ✅\n\n👋 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 𝗟𝗼𝗴𝗴𝗲𝗱 𝗢𝘂𝘁!")
        else:
            bot.reply_to(message,f"❌ <b>Failed:</b> {r.text[:500]}")
    except Exception as e:
        bot.reply_to(message,f"❌ {e}")

@bot.message_handler(commands=['eat'])
def cmd_eat(message):
    parts=message.text.split(maxsplit=1)
    if len(parts)<2:
        bot.reply_to(message,"❌ <b>Usage:</b> <code>/eat EAT_TOKEN</code>\n\n🌍 <i>EAT token localconfig method se milta hai</i>")
        return
    user_input=parts[1].strip()
    eat_token=None
    if "http" in user_input or "eat=" in user_input:
        parsed=urllib.parse.urlparse(user_input)
        qs=urllib.parse.parse_qs(parsed.query)
        if 'eat' in qs:
            eat_token=qs['eat'][0]
    else:
        eat_token=user_input
    try:
        api_url=f"https://api-otrss.garena.com/support/callback/?access_token={eat_token}"
        r=requests.get(api_url,headers={"User-Agent":"Mozilla/5.0"},allow_redirects=True,timeout=15)
        parsed_final=urllib.parse.urlparse(r.url)
        final_params=urllib.parse.parse_qs(parsed_final.query)
        if 'access_token' in final_params:
            access_token=final_params['access_token'][0]
            account_id=final_params.get('account_id',['Unknown'])[0]
            nickname=urllib.parse.unquote(final_params.get('nickname',['Unknown'])[0])
            region=final_params.get('region',['Unknown'])[0]
            bot.reply_to(message,f"""
╭━━━ ✅ <b>𝗘𝗔𝗧 𝗖𝗢𝗡𝗩𝗘𝗥𝗧𝗘𝗗</b> ━━━╮
┃
┣ 👤 <b>𝗡𝗶𝗰𝗸 :</b> {nickname}
┣ 🆔 <b>𝗨𝗜𝗗 :</b> <code>{account_id}</code>
┣ 🌍 <b>𝗥𝗲𝗴𝗶𝗼𝗻 :</b> {region}
┃
┣ 🔑 <b>𝗔𝗰𝗰𝗲𝘀𝘀 𝗧𝗼𝗸𝗲𝗻 :</b>
┃ <code>{access_token}</code>
╰━━━━━━━━━━━━━━━━━━╯
""")
            user_tokens[message.chat.id]=access_token
        else:
            bot.reply_to(message,"❌ <b>EAT invalid / expired</b> 😔\n\n💡 Naya EAT nikalo!")
    except Exception as e:
        bot.reply_to(message,f"❌ <b>Error:</b> {e}")

@bot.message_handler(commands=['bind'])
def cmd_bind(message):
    bot.reply_to(message,"➕ <b>𝗔𝗗𝗗 𝗥𝗘𝗖𝗢𝗩𝗘𝗥𝗬 𝗘𝗠𝗔𝗜𝗟</b>\n\n🔑 <i>Access Token bhejo pehle:</i>")
    user_states[message.chat.id]={"action":"bind","step":"token"}

@bot.message_handler(func=lambda m: m.text in ["➕ Add Recovery Email","Add Recovery Email"])
def btn_add(m): cmd_bind(m)

@bot.message_handler(func=lambda m: m.text in ["🔍 Check Recovery Email","Check Recovery Email"])
def btn_check(m): 
    token=user_tokens.get(m.chat.id)
    if token: send_status(m.chat.id,token)
    else: bot.send_message(m.chat.id,"❌ <b>Pehle token bhejo!</b> 🔑")

@bot.message_handler(func=lambda m: True)
def all_text(message):
    chat_id=message.chat.id
    text=message.text.strip()
    if is_garena_token(text) and chat_id not in user_states:
        send_status(chat_id,text)
        return
    if chat_id not in user_states:
        return
    state=user_states[chat_id]
    if state.get("action")=="bind":
        if state["step"]=="token":
            state["token"]=text
            user_tokens[chat_id]=text
            uid,nick,region=get_player_info(text)
            bot.send_message(chat_id,f"✅ <b>𝗧𝗼𝗸𝗲𝗻 𝗢𝗞</b> - {nick} ({uid})\n\n📧 <b>Ab email bhejo jo bind karni hai:</b>")
            state["step"]="email"
        elif state["step"]=="email":
            state["email"]=text
            try:
                url="https://100067.connect.garena.com/game/account_security/bind:send_otp"
                data={"email":text,"locale":"en_PK","region":"PK","app_id":"100067","access_token":state["token"]}
                r=requests.post(url,headers=HEADERS,data=data,timeout=15)
                if r.json().get("result")==0:
                    bot.send_message(chat_id,f"📩 <b>𝗢𝗧𝗣 𝗦𝗘𝗡𝗧</b> ✅\n\n✉️ <b>{text}</b> pe OTP bhej diya!\n🔢 <b>OTP yaha bhejo:</b>")
                    state["step"]="otp"
                else:
                    bot.send_message(chat_id,f"❌ <b>OTP Fail:</b> {r.text[:600]}")
            except Exception as e:
                bot.send_message(chat_id,f"❌ {e}")
        elif state["step"]=="otp":
            state["otp"]=text
            try:
                url="https://100067.connect.garena.com/game/account_security/bind:verify_otp"
                data={"app_id":"100067","access_token":state["token"],"email":state["email"],"code":text,"otp":text,"type":"1"}
                r=requests.post(url,headers=HEADERS,data=data,timeout=15)
                verifier=r.json().get("verifier_token")
                if verifier:
                    state["verifier_token"]=verifier
                    bot.send_message(chat_id,"✅ <b>𝗢𝗧𝗣 𝗩𝗲𝗿𝗶𝗳𝗶𝗲𝗱!</b> 🎉\n\n🔒 <b>Ab 6-digit security code bhejo</b> (ex: 123456):")
                    state["step"]="sec_code"
                else:
                    bot.send_message(chat_id,f"❌ <b>Verify Fail:</b> {r.text[:600]}")
            except Exception as e:
                bot.send_message(chat_id,f"❌ {e}")
        elif state["step"]=="sec_code":
            try:
                url="https://100067.connect.garena.com/game/account_security/bind:create_bind_request"
                data={"email":state["email"],"app_id":"100067","access_token":state["token"],"verifier_token":state["verifier_token"],"secondary_password":text}
                r=requests.post(url,headers=HEADERS,data=data,timeout=15)
                if r.json().get("result")==0:
                    bot.send_message(chat_id,f"""
🎉 <b>𝗕𝗜𝗡𝗗 𝗦𝗨𝗖𝗖𝗘𝗦𝗦!</b> ✅

📧 <b>𝗘𝗺𝗮𝗶𝗹 :</b> {state['email']}
⏳ <b>𝗦𝘁𝗮𝘁𝘂𝘀 :</b> 𝗣𝗲𝗻𝗱𝗶𝗻𝗴 (1-2 din me confirm hoga)

🔥 <b>𝗭𝗘𝗩𝗥𝗜𝗖 𝗢𝗡 𝗧𝗢𝗣</b> 🔥
""")
                else:
                    bot.send_message(chat_id,f"❌ <b>Bind Fail:</b> {r.text[:800]}")
            except Exception as e:
                bot.send_message(chat_id,f"❌ {e}")
            del user_states[chat_id]

@app.route('/')
def home(): return "🔥 ZEVRIC BOT IS RUNNING - PREMIUM STYLE 🔥"

def run_bot(): bot.infinity_polling()

if __name__=="__main__":
    threading.Thread(target=run_bot,daemon=True).start()
    app.run(host='0.0.0.0',port=PORT)
