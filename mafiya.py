import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

# TOKEN va ADMIN ID ni shu yerga kiritasiz
TOKEN = "8957940963:AAHujPxVzajKM4BAJGeBLfDKURuALPMqSzg"
ADMIN_ID = 8797252107

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- BAZA BILAN ISHLASH ---
def db_start():
    conn = sqlite3.connect("mafia_ultimate_all.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            fullname TEXT,
            dollars INTEGER DEFAULT 1000,
            diamonds INTEGER DEFAULT 0,
            artifacts INTEGER DEFAULT 0,
            shield INTEGER DEFAULT 0,
            potion INTEGER DEFAULT 0,
            games_played INTEGER DEFAULT 0,
            games_won INTEGER DEFAULT 0,
            house_level TEXT DEFAULT 'Oddiy uy',
            pet TEXT DEFAULT 'Yo''q',
            title TEXT DEFAULT 'Host'
        )
    """)
    conn.commit()
    conn.close()

db_start()

def get_user(user_id):
    conn = sqlite3.connect("mafia_ultimate_all.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def register_user(message: types.Message):
    conn = sqlite3.connect("mafia_ultimate_all.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (message.from_user.id,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (user_id, username, fullname) VALUES (?, ?, ?)",
            (message.from_user.id, message.from_user.username, message.from_user.full_name)
        )
        conn.commit()
    conn.close()

# --- ASOSIY MENYU TUGMALARI ---
def main_menu_kb(user_id):
    kb = [
        [KeyboardButton(text="👤 Profil"), KeyboardButton(text="🛒 Do'kon")],
        [KeyboardButton(text="❤️ Juftni topish"), KeyboardButton(text="🐾 Uy hayvonlari")],
        [KeyboardButton(text="🎭 Rollar va Vazifalar"), KeyboardButton(text="🏆 Reyting va Unvonlar")],
        [KeyboardButton(text="📜 Mavsum haqida")]
    ]
    if user_id == ADMIN_ID:
        kb.append([KeyboardButton(text="👑 Admin Panel")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- START ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    register_user(message)
    await message.answer(
        "✨ **Mafiya olamiga xush kelibsiz!**\n\n"
        "Barcha bo'limlardan pastdagi tugmalar orqali foydalanishingiz mumkin.",
        reply_markup=main_menu_kb(message.from_user.id),
        parse_mode="Markdown"
    )

# --- PROFIL TUGMASI ---
@dp.message(F.text == "👤 Profil")
async def profile_handler(message: types.Message):
    user = get_user(message.from_user.id)
    if not user:
        register_user(message)
        user = get_user(message.from_user.id)
    
    wins = user[9]
    title = "Host"
    if 50 <= wins < 300:
        title = "Veteran"
    elif 300 <= wins < 1000:
        title = "Master"
    elif wins >= 1000:
        title = "Legend"

    text = (
        f"👤 **Sizning profilingiz:**\n\n"
        f"🆔 ID: `{user[0]}`\n"
        f"📛 Ism: {user[2]}\n"
        f"🏅 Unvon: ⭐ {title}\n"
        f"💵 Dollar ($): `{user[3]}`\n"
        f"💎 Olmos: `{user[4]}`\n"
        f"🔮 Artefakt: `{user[5]}`\n"
        f"🛡 Himoya: `{user[6]}` ta | 🧪 Dori: `{user[7]}` ta\n"
        f"🏠 Uy darajasi: {user[10]}\n"
        f"🐾 Uy hayvoni: {user[11]}\n"
        f"🎮 O'yinlar: {user[8]} | 🏆 G'alaba: {user[9]}"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Yangilash", callback_data="refresh_profile")]
    ])
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "refresh_profile")
async def refresh_profile_cb(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    text = (
        f"👤 **Sizning profilingiz:**\n\n"
        f"🆔 ID: `{user[0]}`\n"
        f"📛 Ism: {user[2]}\n"
        f"💵 Dollar ($): `{user[3]}` | 💎 Olmos: `{user[4]}`\n"
        f"🏠 Uy: {user[10]} | 🐾 Hayvon: {user[11]}\n"
        f"🎮 O'yinlar: {user[8]} | 🏆 G'alaba: {user[9]}"
    )
    await call.message.edit_text(text, reply_markup=call.message.reply_markup, parse_mode="Markdown")
    await call.answer("Profil yangilandi!")

# --- DO'KON TUGMASI ---
@dp.message(F.text == "🛒 Do'kon")
async def shop_handler(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛡 Himoya (50,000$)", callback_data="buy_shield")],
        [InlineKeyboardButton(text="🧪 Dori (30,000$)", callback_data="buy_potion")],
        [InlineKeyboardButton(text="💎 Olmos (100,000$ = 1 Olmos)", callback_data="buy_diamond")],
        [InlineKeyboardButton(text="🔮 Artefakt (10 Olmos)", callback_data="buy_artifact")]
    ])
    await message.answer("🛒 **Do'konga xush kelibsiz!** Kerakli buyumni tanlang:", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_"))
async def shop_buy_cb(call: types.CallbackQuery):
    user_id = call.from_user.id
    user = get_user(user_id)
    action = call.data
    
    conn = sqlite3.connect("mafia_ultimate_all.db")
    cursor = conn.cursor()
    
    if action == "buy_shield":
        if user[3] >= 50000:
            cursor.execute("UPDATE users SET dollars = dollars - 50000, shield = shield + 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            await call.answer("Himoya sotib olindi! 🛡", show_alert=True)
        else:
            await call.answer("Mablag'ingiz yetarli emas! ($)", show_alert=True)
            
    elif action == "buy_potion":
        if user[3] >= 30000:
            cursor.execute("UPDATE users SET dollars = dollars - 30000, potion = potion + 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            await call.answer("Dori sotib olindi! 🧪", show_alert=True)
        else:
            await call.answer("Mablag'ingiz yetarli emas! ($)", show_alert=True)
            
    elif action == "buy_diamond":
        if user[3] >= 100000:
            cursor.execute("UPDATE users SET dollars = dollars - 100000, diamonds = diamonds + 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            await call.answer("1 ta Olmos sotib olindi! 💎", show_alert=True)
        else:
            await call.answer("100,000$ kerak!", show_alert=True)
            
    elif action == "buy_artifact":
        if user[4] >= 10:
            cursor.execute("UPDATE users SET diamonds = diamonds - 10, artifacts = artifacts + 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            await call.answer("Eng qimmat Artefakt xarid qilindi! 🔮", show_alert=True)
        else:
            await call.answer("10 ta Olmos kerak!", show_alert=True)
            
    conn.close()

# --- UY HAYVONLARI ---
@dp.message(F.text == "🐾 Uy hayvonlari")
async def pets_handler(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🐕 It (Kechasi kim kelganini biladi)", callback_data="pet_dog")],
        [InlineKeyboardButton(text="🦅 Burgut (Tasodifiy o'yinchini kuzatadi)", callback_data="pet_eagle")],
        [InlineKeyboardButton(text="🦉 Boyqush (Xabar olib keladi va sehrni sezadi)", callback_data="pet_owl")]
    ])
    await message.answer("🐾 **Uy hayvonlari do'koni:**\nHayvonlar 2 ta oyinga xizmat qiladi.", reply_markup=kb)

@dp.callback_query(F.data.startswith("pet_"))
async def pet_buy_cb(call: types.CallbackQuery):
    pet_name = "It" if call.data == "pet_dog" else ("Burgut" if call.data == "pet_eagle" else "Boyqush")
    conn = sqlite3.connect("mafia_ultimate_all.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET pet = ? WHERE user_id = ?", (pet_name, call.from_user.id))
    conn.commit()
    conn.close()
    await call.answer(f"Tabriklaymiz! Siz {pet_name} sotib oldingiz!", show_alert=True)

# --- JUFTNI TOPISH ---
@dp.message(F.text == "❤️ Juftni topish")
async def find_pair(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Tasodifiy juft topish", callback_data="search_pair")]
    ])
    await message.answer("❤️ O'yin yoki suhbat uchun juft topish bo'limi.", reply_markup=kb)

@dp.callback_query(F.data == "search_pair")
async def search_pair_cb(call: types.CallbackQuery):
    conn = sqlite3.connect("mafia_ultimate_all.db")
    cursor = conn.cursor()
    cursor.execute("SELECT fullname FROM users WHERE user_id != ? ORDER BY RANDOM() LIMIT 1", (call.from_user.id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        await call.message.edit_text(f"✨ Tabriklaymiz! Sizga mos juft topildi:\n\n❤️ **{result[0]}** bilan mos keldingiz!")
    else:
        await call.answer("Hozircha boshqa o'yinchilar yo'q.", show_alert=True)

# --- ROLLAR VA VAZIFALAR (TO'LIQ ROLLAR RO'YHATI) ---
@dp.message(F.text == "🎭 Rollar va Vazifalar")
async def roles_info(message: types.Message):
    text = (
        "🎭 **O'YIN ROLLARI VA ULarning VAZIFALARI:**\n\n"
        "🔪 **Qotil** – Tunda o'z qurbonini yo'q qiladi.\n"
        "👮 **Serjant** – Komissarga yordam beradi.\n"
        "🎖 **Janob** – Maxsus imtiyozli shahar fuqarosi.\n"
        "🦹 **Daydi** – Tunda ko'chalarni kezib yuradi.\n"
        "👸 **Malika** – O'z jozibasi bilan tunda kimnidir band qiladi.\n"
        "⚖️ **Advokat** – Mafiyani suddan himoya qiladi.\n"
        "🕳 **Suidsid** – O'yinni o'ziga xos tarzda tark etadi.\n"
        "🤞 **Omadli** – Ba'zida o'limdan qutulib qoladi.\n"
        "🥷 **Yollanma qotil** – Buyurtma asosida ishlaydi.\n"
        "💣 **Afsungar** – Tungi tilsimlar ishlatadi.\n"
        "🃏 **Aferist** – O'yinchilarni chalg'itadi.\n"
        "👺 **G'azabkor** – Kuchli hissiyotlar bilan harakat qiladi.\n"
        "🧙 **Sehrgar** – Sirli kuchlarga ega.\n"
        "💻 **Jurnalist** – Ma'lumot toplash uchun surishtiruv o'tkazadi.\n"
        "🤓 **Sotqin** – O'z jamoasiga xiyonat qilishi mumkin.\n"
        "🤡 **Joker** – Kutilmagan harakatlar qiladi.\n"
        "👨‍✈️ **Admiral** – Shahar flotini boshqaradi.\n"
        "🧪 **Kimyogar** – Turli dorilar va zaharlar tayyorlaydi.\n"
        "💰 **Rais** – Shahar kengashida ovozi muhim.\n"
        "☠️ **Minior** – Portlovchi moddalar bilan ishlaydi.\n"
        "🏹 **Robin Gud** – Kambag'allarga yordam beradi.\n"
        "🦇 **Ayg'oqchi** – Sirlarni poylaydi.\n"
        "👷 **Konchi** – Yer osti sirlarini biladi.\n"
        "📸 **Fotoparatchi** – Tungi voqealarni suratga oladi.\n"
        "⚔️ **Qaroqchi** – Boyliklarni o'g'irlaydi.\n"
        "👩‍⚕️ **Labarant / Hamshira** – Ilmiy tajribalar o'tkazadi va davolaydi.\n"
        "⚡ **Koldun** – Qora afsungarlik qiladi.\n"
        "🎅 **Qorbobo** – Yangi yil muhitini yaratadi.\n"
        "🏬 **Savdodar** – Savdo-sotiq bilan shug'ullanadi.\n"
        "🕊 **Diplomat** – Muzokaralar olib boradi.\n"
        "👩‍💻 **Xakker** – Tizimlarni buzib kiradi.\n"
        "🐉 **Gidra** – Boshini yo'qotmaydigan sirli mavjudot.\n"
        "🤖 **Bosh Don / Transformer** – Mafiyani boshqaradi yoki rolini o'zgartiradi."
    )
    await message.answer(text, parse_mode="Markdown")

# --- MAVSUM HAQIDA ---
@dp.message(F.text == "📜 Mavsum haqida")
async def season_info(message: types.Message):
    text = (
        "🌟 **MAVSUMLAR TIZIMI (Har 3 oyda almashadi)**\n\n"
        "🏆 **1-mavsum:** Qorong'u qishloq\n"
        "🏆 **2-mavsum:** Vampirlar hujumi\n"
        "🏆 **3-mavsum:** Kosmik mafiya\n\n"
        "Uzoq muddatli va qiziqarli o'yinlar davomiyligi ta'minlanadi!"
    )
    await message.answer(text, parse_mode="Markdown")

# --- REYTING VA UNVONLAR ---
@dp.message(F.text == "🏆 Reyting va Unvonlar")
async def rankings_info(message: types.Message):
    text = (
        "🏆 **O'yin unvonlari (G'alabalar soniga qarab):**\n\n"
        "⭐ 10 ta g'alaba — **Host**\n"
        "⭐ 50 ta g'alaba — **Veteran**\n"
        "⭐ 300 ta g'alaba — **Master**\n"
        "⭐ 1000 ta g'alaba — **Legend**"
    )
    await message.answer(text, parse_mode="Markdown")

# --- GURUHDA O'YINNI BOSHLASH (/mafiya) ---
@dp.message(Command("mafiya"))
async def start_mafia_game(message: types.Message):
    if message.chat.type in ["group", "supergroup"]:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎮 O'yinga qo'shilish", callback_data="join_mafia")]
        ])
        await message.answer(
            "🐺 **Yangi Mafiya o'yini boshlanmoqda!**\n\n"
            "O'yinga qo'shilish uchun pastdagi tugmani bosing:",
            reply_markup=kb,
            parse_mode="Markdown"
        )
    else:
        await message.answer("Bu buyruq faqat guruhlarda ishlaydi!")

@dp.callback_query(F.data == "join_mafia")
async def join_mafia_cb(call: types.CallbackQuery):
    await call.answer("Siz o'yinga muvaffaqiyatli qo'shildingiz! 🎮", show_alert=True)

# --- ADMIN PANEL ---
@dp.message(F.text == "👑 Admin Panel")
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🎁 Bonus berish", callback_data="admin_bonus")]
    ])
    await message.answer("👑 **Admin boshqaruv paneli:**", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "admin_stats")
async def admin_stats_cb(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    conn = sqlite3.connect("mafia_ultimate_all.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    
    await call.message.edit_text(f"📊 **Bot statistikasi:**\n\n👥 Jami foydalanuvchilar: `{count}` ta", reply_markup=call.message.reply_markup, parse_mode="Markdown")

# Botni ishga tushirish
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

