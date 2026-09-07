import telebot
from telebot import types
from telebot import apihelper
apihelper.proxy = {'https': 'http://proxy.server:3128', 'http': 'http://proxy.server:3128'}
import os

BOT_TOKEN = "8847907390:AAFkEtCtZ6qaAVIrXrRfyDdUxqvaGGLHfu0"
ADMIN_ID = 8981733976
UPI_ID = "zervicxplay@okhdfcbank"
SUPPORT_USERNAME = "just_zevric"
SUPPORT_LINK = "https://t.me/just_zevric"
BOT_LINK = "https://t.me/Zervic_Otp_Bazar_bot"

COUNTRIES = {
    "ARGENTINA_SERVER_1": {"flag": "🇦🇷", "sname": "Argentina server 1", "code": "+54", "price": 95, "country": "Argentina"},
    "BANGLADESH_SERVER_1": {"flag": "🇧🇩", "sname": "Bangladesh server 1", "code": "+880", "price": 95, "country": "Bangladesh"},
    "BANGLADESH_SERVER_3": {"flag": "🇧🇩", "sname": "Bangladesh server 3", "code": "+880", "price": 115, "country": "Bangladesh"},
    "BRAZIL": {"flag": "🇧🇷", "sname": "Brazil", "code": "+55", "price": 190, "country": "Brazil"},
    "CANADA_SERVER_14": {"flag": "🇨🇦", "sname": "Canada server 14", "code": "+1", "price": 82, "country": "Canada"},
    "CANADA_SERVER_15": {"flag": "🇨🇦", "sname": "Canada server 15", "code": "+1", "price": 82, "country": "Canada"},
    "CANADA_SERVER_16": {"flag": "🇨🇦", "sname": "Canada server 16", "code": "+1", "price": 90, "country": "Canada"},
    "CANADA_SERVER_18": {"flag": "🇨🇦", "sname": "Canada server 18", "code": "+1", "price": 139, "country": "Canada"},
    "CANADA_SERVER_21": {"flag": "🇨🇦", "sname": "Canada server 21", "code": "+1", "price": 95, "country": "Canada"},
    "CANADA_SERVER_22": {"flag": "🇨🇦", "sname": "Canada server 22", "code": "+1", "price": 93, "country": "Canada"},
    "CANADA_SERVER_3": {"flag": "🇨🇦", "sname": "Canada server 3", "code": "+1", "price": 92, "country": "Canada"},
    "CHILE": {"flag": "🇨🇱", "sname": "Chile", "code": "+56", "price": 75, "country": "Chile"},
    "CHILE_SERVER_1": {"flag": "🇨🇱", "sname": "Chile server 1", "code": "+56", "price": 68, "country": "Chile"},
    "CHILE_SERVER_2": {"flag": "🇨🇱", "sname": "Chile server 2", "code": "+56", "price": 80, "country": "Chile"},
    "COLOMBIA": {"flag": "🇨🇴", "sname": "Colombia", "code": "+57", "price": 75, "country": "Colombia"},
    "COLOMBIA_SERVER_1": {"flag": "🇨🇴", "sname": "Colombia server 1", "code": "+57", "price": 95, "country": "Colombia"},
    "COLOMBIA_SERVER_5": {"flag": "🇨🇴", "sname": "Colombia server 5", "code": "+57", "price": 95, "country": "Colombia"},
    "COLOMBIA_SERVER_8": {"flag": "🇨🇴", "sname": "Colombia server 8", "code": "+57", "price": 82, "country": "Colombia"},
    "INDIA_SERVER_10": {"flag": "🇮🇳", "sname": "India server 10", "code": "+91", "price": 152, "country": "India"},
    "INDIA_SERVER_25": {"flag": "🇮🇳", "sname": "India server 25", "code": "+91", "price": 160, "country": "India"},
    "INDONESIA": {"flag": "🇮🇩", "sname": "Indonesia", "code": "+62", "price": 68, "country": "Indonesia"},
    "INDONESIA_SERVER_12": {"flag": "🇮🇩", "sname": "Indonesia server 12", "code": "+62", "price": 65, "country": "Indonesia"},
    "INDONESIA_SERVER_14": {"flag": "🇮🇩", "sname": "Indonesia server 14", "code": "+62", "price": 65, "country": "Indonesia"},
    "INDONESIA_SERVER_15": {"flag": "🇮🇩", "sname": "Indonesia server 15", "code": "+62", "price": 63, "country": "Indonesia"},
    "INDONESIA_SERVER_16": {"flag": "🇮🇩", "sname": "Indonesia server 16", "code": "+62", "price": 65, "country": "Indonesia"},
    "INDONESIA_SERVER_17": {"flag": "🇮🇩", "sname": "Indonesia server 17", "code": "+62", "price": 65, "country": "Indonesia"},
    "INDONESIA_SERVER_18": {"flag": "🇮🇩", "sname": "Indonesia server 18", "code": "+62", "price": 65, "country": "Indonesia"},
    "INDONESIA_SERVER_2": {"flag": "🇮🇩", "sname": "Indonesia server 2", "code": "+62", "price": 65, "country": "Indonesia"},
    "INDONESIA_SERVER_6": {"flag": "🇮🇩", "sname": "Indonesia server 6", "code": "+62", "price": 73, "country": "Indonesia"},
    "INDONESIA_SERVER_9": {"flag": "🇮🇩", "sname": "Indonesia server 9", "code": "+62", "price": 64, "country": "Indonesia"},
    "IVORY_COAST": {"flag": "🇨🇮", "sname": "Ivory Coast", "code": "+225", "price": 65, "country": "Ivory Coast"},
    "KENYA_SERVER_1": {"flag": "🇰🇪", "sname": "Kenya server 1", "code": "+254", "price": 80, "country": "Kenya"},
    "MALAYSIA_SERVER_1": {"flag": "🇲🇾", "sname": "Malaysia server 1", "code": "+60", "price": 125, "country": "Malaysia"},
    "MALAYSIA_SERVER_2": {"flag": "🇲🇾", "sname": "Malaysia server 2", "code": "+60", "price": 129, "country": "Malaysia"},
    "MAURITANIA_SERVER_1": {"flag": "🇲🇷", "sname": "Mauritania server 1", "code": "+222", "price": 80, "country": "Mauritania"},
    "NEPAL_SERVER_2": {"flag": "🇳🇵", "sname": "Nepal server 2", "code": "+977", "price": 95, "country": "Nepal"},
    "NETHERLANDS": {"flag": "🇳🇱", "sname": "Netherlands", "code": "+31", "price": 195, "country": "Netherlands"},
    "PHILIPPINES": {"flag": "🇵🇭", "sname": "Philippines", "code": "+63", "price": 67, "country": "Philippines"},
    "PHILIPPINES_SERVER_3": {"flag": "🇵🇭", "sname": "Philippines server 3", "code": "+63", "price": 85, "country": "Philippines"},
    "PHILIPPINES_SERVER_5": {"flag": "🇵🇭", "sname": "Philippines server 5", "code": "+63", "price": 90, "country": "Philippines"},
    "POLAND_SERVER_1": {"flag": "🇵🇱", "sname": "Poland server 1", "code": "+48", "price": 130, "country": "Poland"},
    "SAUDI_ARABIA_SERVER_1": {"flag": "🇸🇦", "sname": "Saudi Arabia server 1", "code": "+966", "price": 100, "country": "Saudi Arabia"},
    "SOUTH_AFRICA": {"flag": "🇿🇦", "sname": "South Africa", "code": "+27", "price": 65, "country": "South Africa"},
    "SOUTH_AFRICA_SERVER_3": {"flag": "🇿🇦", "sname": "South Africa server 3", "code": "+27", "price": 63, "country": "South Africa"},
    "SOUTH_AFRICA_SERVER_6": {"flag": "🇿🇦", "sname": "South Africa server 6", "code": "+27", "price": 62, "country": "South Africa"},
    "SOUTH_AFRICA_SERVER_7": {"flag": "🇿🇦", "sname": "South Africa server 7", "code": "+27", "price": 59, "country": "South Africa"},
    "SOUTH_AFRICA_SERVER_8": {"flag": "🇿🇦", "sname": "South Africa server 8", "code": "+27", "price": 60, "country": "South Africa"},
    "THAILAND_SERVER_1": {"flag": "🇹🇭", "sname": "Thailand server 1", "code": "+66", "price": 100, "country": "Thailand"},
    "THAILAND_SERVER_3": {"flag": "🇹🇭", "sname": "Thailand server 3", "code": "+66", "price": 113, "country": "Thailand"},
    "USA": {"flag": "🇺🇸", "sname": "USA", "code": "+1", "price": 155, "country": "USA"},
    "USA_SERVER_0": {"flag": "🇺🇸", "sname": "USA server 0", "code": "+1", "price": 110, "country": "USA"},
    "USA_SERVER_1": {"flag": "🇺🇸", "sname": "USA server 1", "code": "+1", "price": 239, "country": "USA"},
    "USA_SERVER_12": {"flag": "🇺🇸", "sname": "USA server 12", "code": "+1", "price": 68, "country": "USA"},
    "USA_SERVER_17": {"flag": "🇺🇸", "sname": "USA server 17", "code": "+1", "price": 65, "country": "USA"},
    "USA_SERVER_25": {"flag": "🇺🇸", "sname": "USA server 25", "code": "+1", "price": 100, "country": "USA"},
    "USA_SERVER_26": {"flag": "🇺🇸", "sname": "USA server 26", "code": "+1", "price": 80, "country": "USA"},
    "UNITED_KINGDOM": {"flag": "🇬🇧", "sname": "United Kingdom", "code": "+44", "price": 105, "country": "UK"},
    "UNITED_KINGDOM_SERVER_2": {"flag": "🇬🇧", "sname": "UK server 2", "code": "+44", "price": 145, "country": "UK"},
    "UZBEKISTAN_SERVER_1": {"flag": "🇺🇿", "sname": "Uzbekistan server 1", "code": "+998", "price": 130, "country": "Uzbekistan"},
    "VIETNAM_SERVER_1": {"flag": "🇻🇳", "sname": "Vietnam server 1", "code": "+84", "price": 90, "country": "Vietnam"},
    "VIETNAM_SERVER_2": {"flag": "🇻🇳", "sname": "Vietnam server 2", "code": "+84", "price": 75, "country": "Vietnam"},
    "YEMEN_SERVER_1": {"flag": "🇾🇪", "sname": "Yemen server 1", "code": "+967", "price": 62, "country": "Yemen"},
}

bot = telebot.TeleBot(BOT_TOKEN)

try:
    import qrcode
    QR_OK = True
except:
    QR_OK = False

# === CLEAN COMMAND MENU - NO ID - HOWTOBUY FIXED ===
def set_commands():
    try:
        # Delete old first
        bot.delete_my_commands()
        bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())
        bot.delete_my_commands(scope=types.BotCommandScopeAllGroupChats())
    except: pass
    try:
        cmds = [
            types.BotCommand("start", "🔥 ZEVRIC OTP BAZAAR - Main Menu"),
            types.BotCommand("buy", "🛒 Buy Number - 62 Servers"),
            types.BotCommand("pricelist", "💰 Full Pricelist A-Z"),
            types.BotCommand("support", "📞 Support @just_zevric"),
            types.BotCommand("howtobuy", "📜 How To Buy Guide"),
        ]
        bot.set_my_commands(cmds)
        bot.set_my_commands(cmds, scope=types.BotCommandScopeAllPrivateChats())
    except Exception as e:
        print(f"Command set error: {e}")

set_commands()

user_selection = {}
user_numbers = {}

def make_qr(amount):
    if not QR_OK: return None
    try:
        import qrcode
        upi_str = f"upi://pay?pa={UPI_ID}&pn=ZEVRIC OTP BAZAAR&am={amount}&cu=INR"
        qr = qrcode.make(upi_str)
        path = f"/tmp/qr_{amount}.png"
        qr.save(path)
        return path
    except: return None

def country_menu(page=0):
    items = list(COUNTRIES.items())
    per_page = 8
    s = page*per_page
    e = s+per_page
    mk = types.InlineKeyboardMarkup(row_width=1)
    for k, d in items[s:e]:
        mk.add(types.InlineKeyboardButton(f"{d['flag']} {d['sname']} {d['code']} - ₹{d['price']} ✅", callback_data=f"c_{k}"))
    nav = []
    if page>0: nav.append(types.InlineKeyboardButton("⬅️ Prev", callback_data=f"p_{page-1}"))
    if e < len(items): nav.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"p_{page+1}"))
    if nav: mk.row(*nav)
    mk.add(types.InlineKeyboardButton("🔙 Main Menu 🏠", callback_data="main"))
    return mk

def retention_menu():
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.add(
        types.InlineKeyboardButton("🛒 Buy Again 10% OFF 🔥", callback_data="buy"),
        types.InlineKeyboardButton("💰 Pricelist", callback_data="plist"),
    )
    mk.add(
        types.InlineKeyboardButton("📤 Share & Earn ₹20", callback_data="share"),
        types.InlineKeyboardButton("⭐ Rate Us 5 Star", callback_data="rate")
    )
    mk.add(types.InlineKeyboardButton("📞 Support @just_zevric", url=SUPPORT_LINK))
    return mk

def welcome_text():
    return """🔥 <b>ZEVRIC OTP BAZAAR</b> 🔥
━━━━━━━━━━━━━━━━━━━━
💜 <b>Welcome to Premium OTP Store!</b> 💜
━━━━━━━━━━━━━━━━━━━━
🚀 62 Premium Servers Worldwide 🌍
⚡ Instant Delivery | ✅ 100% Working
💎 Trusted by 10K+ Users

🎁 <b>Special Features:</b>
🇮🇳 India | 🇺🇸 USA | 🇬🇧 UK | 🇨🇦 Canada
🇮🇩 Indonesia | 🇵🇭 Philippines & 15+ Countries

💰 <b>Starting @ ₹59 Only!</b>
━━━━━━━━━━━━━━━━━━━━
👇 <b>Select Karo & Start Karo:</b>"""

@bot.message_handler(commands=['start'])
def start_handler(message):
    txt = welcome_text()
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🛒 Buy Number 🔥", callback_data="buy"),
        types.InlineKeyboardButton("💰 Pricelist 💎", callback_data="plist"),
    )
    m.add(
        types.InlineKeyboardButton("📞 Support", url=SUPPORT_LINK),
        types.InlineKeyboardButton("📜 How To Buy", callback_data="how")
    )
    m.add(types.InlineKeyboardButton("🌍 All 62 Servers", callback_data="buy"))
    try:
        # Try to send with logo if exists, else text
        logo_path = "/mnt/data/image_B4075E28-65DF-48F7-90AC-A09C515A1A5D.jpeg"
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                bot.send_photo(message.chat.id, f, caption=txt, parse_mode="HTML", reply_markup=m)
        else:
            bot.send_message(message.chat.id, txt, parse_mode="HTML", reply_markup=m)
    except:
        bot.send_message(message.chat.id, txt, parse_mode="HTML", reply_markup=m)

@bot.message_handler(commands=['buy'])
def buy_handler(message):
    bot.send_message(message.chat.id, "🌍 <b>SELECT SERVER - 62 Options! 🔥</b>\n💜 Premium Quality Numbers 💜\n👇 Select Karo:", parse_mode="HTML", reply_markup=country_menu(0))

@bot.message_handler(commands=['pricelist','price'])
def plist_handler(message):
    text = "💰 <b>ZEVRIC OTP BAZAAR - FULL PRICELIST 🔥</b>\n━━━━━━━━━━━━━━━━━━━━\n"
    for d in COUNTRIES.values():
        text += f"{d['flag']} {d['sname']} {d['code']} = ₹{d['price']} ✅\n"
    text += f"━━━━━━━━━━━━━━━━━━━━\n💳 UPI: <code>{UPI_ID}</code>\n📞 Support: @{SUPPORT_USERNAME}\n⚡ Instant Delivery!"
    for i in range(0, len(text), 4000):
        bot.send_message(message.chat.id, text[i:i+4000], parse_mode="HTML")

@bot.message_handler(commands=['support','help'])
def support_handler(message):
    txt = f"""📞 <b>SUPPORT - ZEVRIC OTP BAZAAR 💜</b>
━━━━━━━━━━━━━━━━━━━━
👤 Admin: @{SUPPORT_USERNAME}
🔗 Link: {SUPPORT_LINK}
⚡ Reply Time: 2-5 Minutes

💬 <b>Kisi bhi issue ke liye direct message karo!</b>
💰 Payment Issue? Number Issue? OTP Issue?
📞 Turant Help Milegi!

━━━━━━━━━━━━━━━━━━━━"""
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("📞 Contact Support @just_zevric", url=SUPPORT_LINK))
    mk.add(types.InlineKeyboardButton("🛒 Buy Number", callback_data="buy"))
    bot.send_message(message.chat.id, txt, parse_mode="HTML", reply_markup=mk)

# === HOWTOBUY FIXED - 100% WORKING ===
@bot.message_handler(commands=['howtobuy','how','guide'])
def howtobuy_handler(message):
    txt = """📜 <b>HOW TO BUY - ZEVRIC OTP BAZAAR 🔥</b>
━━━━━━━━━━━━━━━━━━━━
💜 <b>Step By Step Guide:</b>

1️⃣ /buy command dabao 🛒
2️⃣ Server select karo (62 options) 🌍
   Example: Canada server 16 - ₹90
3️⃣ QR Code ayega - UPI se pay karo 💳
   UPI: <code>zervicxplay@okhdfcbank</code>
4️⃣ Screenshot bhejo 📸
5️⃣ Admin 2 min me Approve karega ✅
6️⃣ Number milega:+1623456783 📱
7️⃣ Whatsapp me login karo 🔑
8️⃣ Niche <b>Get OTP</b> button dabao 👇
9️⃣ OTP milega: 465789 🎉
🔟 Jaldi daalo - OTP expire ho jayega! ⚡

━━━━━━━━━━━━━━━━━━━━
💰 <b>Price:</b> ₹59 se start - ₹239 tak
🌍 <b>62 Servers:</b> India, USA, UK, Canada etc
⚡ <b>Delivery:</b> 2-5 min Instant
✅ <b>100% Working Guarantee</b>

📞 <b>Support:</b> @just_zevric
━━━━━━━━━━━━━━━━━━━━
👇 Ab Buy Karo:"""
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.add(
        types.InlineKeyboardButton("🛒 Buy Now 🔥", callback_data="buy"),
        types.InlineKeyboardButton("💰 Pricelist", callback_data="plist"),
    )
    mk.add(types.InlineKeyboardButton("📞 Support", url=SUPPORT_LINK))
    bot.send_message(message.chat.id, txt, parse_mode="HTML", reply_markup=mk)

@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    try:
        d = call.data
        if d == "main":
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            start_handler(call.message)
        elif d == "buy":
            try:
                bot.edit_message_text("🌍 <b>SELECT SERVER A-Z - 62 Servers 🔥</b>\n💜 Premium Quality 💜", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=country_menu(0))
            except:
                bot.send_message(call.message.chat.id, "🌍 <b>SELECT SERVER - 62 Options! 🔥</b>", parse_mode="HTML", reply_markup=country_menu(0))
        elif d == "plist":
            plist_handler(call.message)
        elif d == "how":
            howtobuy_handler(call.message)
        elif d == "share":
            bot.send_message(call.message.chat.id, f"📤 <b>SHARE & EARN ₹20 🔥</b>\n━━━━━━━━━━━━\n👥 Dost ko bot share karo:\n🔗 <code>{BOT_LINK}</code>\n\n💰 Har referral pe ₹20 discount!\n📞 Support: @{SUPPORT_USERNAME}\n\nShare karo aur kamao! 🚀", parse_mode="HTML")
        elif d == "rate":
            bot.send_message(call.message.chat.id, "⭐ <b>RATE US 5 STAR ⭐</b>\n━━━━━━━━━━━━\n🙏 Agar service pasand aayi ho to\n⭐ 5 Star de do!\n\n📸 Screenshot bhejo support pe @just_zervic\n🎁 Next order pe 10% OFF milega! Code: ZEVRIC10\n\nThank you! 🔥❤️", parse_mode="HTML")
        elif d.startswith("p_"):
            page = int(d.split("_")[1])
            bot.edit_message_text(f"🌍 <b>Page {page+1} - Select Server 🔥</b>\n💜 Premium Quality 💜", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=country_menu(page))
        elif d.startswith("c_"):
            key = d[2:]
            info = COUNTRIES.get(key)
            if not info: return
            user_selection[call.from_user.id] = key
            qr_path = make_qr(info['price'])
            caption = f"💳 <b>{info['flag']} {info['sname']}</b> 💳\n━━━━━━━━━━━━━━━━━━━━\n🌍 Country: {info['country']} {info['code']}\n💰 Price: <b>₹{info['price']}</b> ✅\n💳 UPI: <code>{UPI_ID}</code>\n━━━━━━━━━━━━━━━━━━━━\n💸 Pay <b>₹{info['price']} only</b> and send screenshot 📸\n⚡ Instant Delivery!\n\n<b>UPI ID: {UPI_ID}</b>\nScan QR and Pay 💜"
            mk = types.InlineKeyboardMarkup()
            mk.add(types.InlineKeyboardButton("📞 Support @just_zevric", url=SUPPORT_LINK))
            bot.answer_callback_query(call.id, f"{info['sname']} selected! 💜")
            if qr_path and os.path.exists(qr_path):
                with open(qr_path,'rb') as f:
                    bot.send_photo(call.message.chat.id, f, caption=caption, parse_mode="HTML", reply_markup=mk)
            else:
                bot.send_message(call.message.chat.id, caption, parse_mode="HTML", reply_markup=mk)
        elif d.startswith("ap_"):
            uid = int(d.split("_")[1])
            key = d.split("_",2)[2] if len(d.split("_",2))>2 else ""
            info = COUNTRIES.get(key, {"sname":"Server","flag":"✅","price":0,"country":""})
            bot.send_message(call.message.chat.id, f"✅ <b>Approved User {uid} - {info['flag']} {info['country']}</b>\n\nAb number do:\n<code>/number {uid} +91XXXXXXXXXX</code>", parse_mode="HTML")
            bot.send_message(uid, f"✅ <b>Payment Approved! 🎉</b>\n\n{info['flag']} {info['sname']} Approved ✅\n💰 ₹{info['price']}\n\n📱 Admin number bhej raha hai... ⏳", parse_mode="HTML")
        elif d.startswith("rj_"):
            uid = int(d.split("_")[1])
            bot.send_message(uid, "❌ <b>Payment Rejected! ❌</b>\nSahi amount pay karo aur screenshot bhejo!\n📞 Support: @just_zervic", parse_mode="HTML")
            bot.answer_callback_query(call.id, "Rejected!")
        elif d.startswith("go_"):
            uid = int(d.split("_")[1])
            num = user_numbers.get(uid, "Unknown")
            bot.send_message(ADMIN_ID, f"🔑 <b>OTP REQUEST! 🔥</b>\n\n👤 User: <code>{uid}</code>\n📱 Number: <code>{num}</code>\n\nUser ne Whatsapp me login kiya hai, OTP bhej do:\n<code>/otp {uid} 123456</code>", parse_mode="HTML")
            bot.send_message(uid, "🔑 OTP Request sent to Admin! 1 min wait karo ⏳🚀\nAdmin OTP bhejega jaldi!", parse_mode="HTML")
            bot.answer_callback_query(call.id, "OTP Request Sent! 🚀")
    except Exception as e:
        print(f"CB Error: {e}")

@bot.message_handler(commands=['number','give','num'])
def give_num(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split()
        uid = int(parts[1])
        number = parts[2]
        user_numbers[uid] = number
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("🔑 Get OTP - Click Here 👇", callback_data=f"go_{uid}"))
        txt = f"🎉 <b>NUMBER READY! 🔥</b> 🎉\n━━━━━━━━━━━━\n📱 Number: <code>{number}</code>\n━━━━━━━━━━━━\n📲 <b>Ab Whatsapp me login karo:</b>\n1️⃣ Number daalo\n2️⃣ Niche <b>Get OTP</b> dikhega\n3️⃣ <b>Get OTP button dabao 👇</b>\n4️⃣ OTP mil jayega!\n━━━━━━━━━━━━"
        bot.send_message(uid, txt, parse_mode="HTML", reply_markup=mk)
        bot.send_message(message.chat.id, f"✅ <b>Number {number} sent to {uid}</b> ✅\nUser ko bol Whatsapp me login kare aur Get OTP dabaye!", parse_mode="HTML")
    except Exception as e:
        bot.send_message(message.chat.id, f"Use: /number USERID +91NUMBER\nError: {e}")

@bot.message_handler(commands=['otp'])
def give_otp(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split()
        uid = int(parts[1])
        otp = parts[2]
        num = user_numbers.get(uid, "")
        bot.send_message(uid, f"🔑 <b>OTP READY! 🎉</b> 🔑\n━━━━━━━━━━━━\n📱 Number: <code>{num}</code>\n🔐 OTP: <code>{otp}</code>\n━━━━━━━━━━━━\n⚡ Jaldi daalo! OTP expire ho jayega!", parse_mode="HTML")
        bot.send_message(message.chat.id, f"✅ OTP {otp} sent to {uid} 🔥")

        import time
        time.sleep(1)
        retention_text = f"""🎉 <b>ORDER COMPLETED SUCCESSFULLY! 🔥</b> 🎉
━━━━━━━━━━━━━━━━━━━━
✅ Number: <code>{num}</code>
✅ OTP Delivered
━━━━━━━━━━━━━━━━━━━━

🎁 <b>THANK YOU FOR USING ZEVRIC! ❤️💜</b>

🔥 <b>SPECIAL OFFERS FOR YOU:</b>
💰 Next Order pe <b>10% OFF</b> - Code: <code>ZEVRIC10</code>
👥 Refer karo & <b>₹20 Earn</b> karo
⭐ Review do & Extra Discount pao!

━━━━━━━━━━━━━━━━━━━━
🚀 <b>Dubara Chahiye? 1 Click me Order Karo!</b>
62 Countries Available - Instant Delivery! ⚡

💜 <b>ZEVRIC OTP BAZAAR - Trusted by 10K+ Users</b>
"""
        bot.send_message(uid, retention_text, parse_mode="HTML", reply_markup=retention_menu())

    except Exception as e:
        bot.send_message(message.chat.id, f"Use: /otp USERID OTP\n{e}")

@bot.message_handler(content_types=['photo'])
def photo_handler(message):
    uid = message.from_user.id
    sel = user_selection.get(uid)
    if not sel:
        bot.send_message(message.chat.id, "⚠️ Pehle /buy se server select karo! 🌍", parse_mode="HTML")
        return
    info = COUNTRIES[sel]
    username = f"@{message.from_user.username}" if message.from_user.username else "No username"
    name = message.from_user.first_name or ""
    order_txt = f"💰 <b>NEW ORDER - {info['flag']} {info['sname']} 🔥</b>\n━━━━━━━━━━━━\n💰 Price: ₹{info['price']}\n👤 {username} | {name} 🚀\n🆔 ID: <code>{uid}</code>\n🌍 Server: {info['sname']}"
    bot.send_message(ADMIN_ID, order_txt, parse_mode="HTML")
    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.add(types.InlineKeyboardButton(f"✅ Approve {info['flag']} ₹{info['price']}", callback_data=f"ap_{uid}_{sel}"), types.InlineKeyboardButton("❌ Reject", callback_data=f"rj_{uid}"))
    bot.send_message(ADMIN_ID, "👇 Action Lo:", reply_markup=mk)
    bot.send_message(message.chat.id, f"📸 Screenshot Received for {info['flag']} {info['sname']} ✅\n⏳ Admin 2 min me check karega! 🚀\n\nAfter payment:\n1️⃣ Admin number dega\n2️⃣ Whatsapp me login karo\n3️⃣ Niche <b>Get OTP</b> dabao\n4️⃣ OTP mil jayega! 💜", parse_mode="HTML")

print("FINAL PERFECT - NO ID - HOWTOBUY FIXED - RETENTION - STARTED 🔥🔥🔥")
bot.infinity_polling(skip_pending=True, timeout=10, long_polling_timeout=10, allowed_updates=["message","callback_query"], none_stop=True)
