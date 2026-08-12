import asyncio
import logging
import sqlite3
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiohttp import web

TOKEN = "8957940963:AAHujPxVzajKM4BAJGeBLfDKURuALPMqSzg"
ADMIN_ID = 8797252107
CHANNEL_USERNAME = "https://t.me/mafiya_game_team"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Botning username'ini olish uchun o'zgaruvchi (tugmalar uchun)
BOT_USERNAME = "@Mafiya_bottbot" # O'z botingiz username'i bilan almashtiring

# FSM holatlari
class GiftState(StatesGroup):
    waiting_for_target_id = State()
    waiting_for_amount = State()
    waiting_for_item = State()

class LoverState(StatesGroup):
    waiting_for_lover_id = State()

class BonusPostState(StatesGroup):
    waiting_for_bonus_type = State()
    waiting_for_bonus_amount = State()

game_lobbies = {}

def db_start():
    conn = sqlite3.connect("mafia_ultimate_all.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            fullname TEXT,
            dollars INTEGER DEFAULT 100,
            diamonds INTEGER DEFAULT 0,
            artifacts INTEGER DEFAULT 0,
            shield INTEGER DEFAULT 0,
            potion INTEGER DEFAULT 0,
            documents INTEGER DEFAULT 0,
            mask INTEGER DEFAULT 0,
            vote_shield INTEGER DEFAULT 0,
            rifle INTEGER DEFAULT 0,
            mystery_box INTEGER DEFAULT 0,
            games_played INTEGER DEFAULT 0,
            games_won INTEGER DEFAULT 0,
            house_level TEXT DEFAULT '🏚 Oddiy uy',
            pet TEXT DEFAULT 'Yo''q',
            title TEXT DEFAULT 'Rookie',
            role TEXT DEFAULT 'Fuqoro',
            skin TEXT DEFAULT 'Oddiy',
            lover_id INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_skins (
            user_id INTEGER,
            role_name TEXT,
            skin_name TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS claimed_bonuses (
            user_id INTEGER,
            bonus_code TEXT
        )
    """)
    conn.commit()
    conn.close()

db_start()

def update_user_house(user_id):
    conn = sqlite3.connect("mafia_ultimate_all.db")
    cursor = conn.cursor()
    cursor.execute("SELECT games_played FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    if res:
        games = res[0]
        if games >= 1500: house = "🏰 Qasr"
        elif games >= 1200: house = "🕌 Saroy"
        elif games >= 900: house = "🏢 Ko'p qavatli uy"
        elif games >= 600: house = "🏡 Villa"
        elif games >= 300: house = "🏠 Katta uy"
        else: house = "🏚 Oddiy uy"
            
        cursor.execute("UPDATE users SET house_level = ? WHERE user_id = ?", (house, user_id))
        conn.commit()
    conn.close()

def get_user(user_id):
    update_user_house(user_id)
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

async def check_subscription(user_id: int):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
    except Exception:
        pass
    return False

def main_menu_kb(user_id):
    kb = [
        [KeyboardButton(text="👤 Profil"), KeyboardButton(text="🛒 Do'kon")],
        [KeyboardButton(text="❤️ Juftni topish"), KeyboardButton(text="🎁 Sovg'a yuborish")],
        [KeyboardButton(text="🐾 Uy hayvonlari"), KeyboardButton(text="🎭 Rollar va Vazifalar")],
        [KeyboardButton(text="🏆 Reyting va Unvonlar"), KeyboardButton(text="📜 Mavsum haqida")],
        [KeyboardButton(text="🎁 Kunlik Topshiriqlar")]
    ]
    if user_id == ADMIN_ID:
        kb.append([KeyboardButton(text="👑 Admin Panel")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.chat.type != "private":
        return
    if CHANNEL_USERNAME and not await check_subscription(message.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")],
            [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")]
        ])
        await message.answer("⚠️ Botdan foydalanish uchun kanalimizga obuna bo'lishingiz kerak!", reply_markup=kb)
        return

    register_user(message)
    await message.answer(
        "👋 **Xush kelibsiz!** Botdan foydalanish uchun asosiy menyu ochildi.\n"
        "💳 Boshlang'ich mablag'ingiz: **100$**",
        reply_markup=main_menu_kb(message.from_user.id),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "check_sub")
async def check_sub_cb(call: types.CallbackQuery):
    if await check_subscription(call.from_user.id):
        await call.message.delete()
        register_user(call)
        await call.message.answer("✅ Obuna tasdiqlandi! Xush kelibsiz.", reply_markup=main_menu_kb(call.from_user.id))
    else:
        await call.answer("❌ Hali kanalga obuna bo'lmadingiz!", show_alert=True)

@dp.message(F.chat.type == "private", F.text == "👤 Profil")
async def profile_handler(message: types.Message):
    user = get_user(message.from_user.id)
    wins = user[14]
    title = "Rookie"
    if 10 <= wins < 50: title = "Veteran"
    elif 50 <= wins < 300: title = "Master"
    elif wins >= 300: title = "Legend"

    text = (
        f"👤 **Sizning profilingiz:**\n\n"
        f"🆔 ID: `{user[0]}`\n"
        f"📛 Ism: {user[2]}\n"
        f"🏅 Unvon: ⭐ {title}\n"
        f"💵 Dollar ($): `{user[3]}` | 💎 Olmos: `{user[4]}`\n"
        f"🛡 Himoya: `{user[6]}` | 🧪 Dori: `{user[7]}`\n"
        f"📄 Hujjat: `{user[8]}` | 👺 Maska: `{user[9]}`\n"
        f"🛡 Ovoz himoyasi: `{user[10]}` | 🔫 Miltiq: `{user[11]}`\n"
        f"📦 Sirli quti: `{user[12]}`\n"
        f"🏠 Uy: {user[15]} | 🐾 Hayvon: {user[16]}\n"
        f"🎮 O'yinlar: {user[13]} | 🏆 G'alaba: {user[14]}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Yangilash", callback_data="refresh_profile")]])
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "refresh_profile")
async def refresh_profile_cb(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    text = (
        f"👤 **Sizning profilingiz:**\n\n"
        f"🆔 ID: `{user[0]}`\n"
        f"📛 Ism: {user[2]}\n"
        f"💵 Dollar ($): `{user[3]}` | 💎 Olmos: `{user[4]}`\n"
        f"🎮 O'yinlar: {user[13]} | 🏆 G'alaba: {user[14]}"
    )
    await call.message.edit_text(text, reply_markup=call.message.reply_markup, parse_mode="Markdown")
    await call.answer("Profil yangilandi!")

@dp.message(F.chat.type == "private", F.text == "🛒 Do'kon")
async def shop_handler(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛡 Himoya (100$)", callback_data="buy_shield"), InlineKeyboardButton(text="🧪 Dori (100$)", callback_data="buy_potion")],
        [InlineKeyboardButton(text="📄 Yolgon Hujjat (1000$)", callback_data="buy_documents"), InlineKeyboardButton(text="👺 Maska (1000$)", callback_data="buy_mask")],
        [InlineKeyboardButton(text="🛡 Ovozdan himoya (300$)", callback_data="buy_vote_shield"), InlineKeyboardButton(text="🔫 Miltiq (1300$)", callback_data="buy_rifle")],
        [InlineKeyboardButton(text="📦 Sirli quti (500$)", callback_data="buy_mystery_box")],
        [InlineKeyboardButton(text="🐾 Uy hayvonlari do'koni", callback_data="shop_pets"), InlineKeyboardButton(text="🎨 Skinlar do'koni", callback_data="shop_skins")]
    ])
    await message.answer("🛒 **Do'konga xush kelibsiz!** Kerakli buyumni tanlang:", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "shop_skins")
async def shop_skins_cb(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Robot Don (1000$)", callback_data="buy_skin_Robot Don")],
        [InlineKeyboardButton(text="🔥 Olov Don (1000$)", callback_data="buy_skin_Olov Don")],
        [InlineKeyboardButton(text="❄️ Muz Don (1000$)", callback_data="buy_skin_Muz Don")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_shop")]
    ])
    await call.message.edit_text("🎨 **Skinlar do'koniga xush kelibsiz!**", reply_markup=kb)

@dp.callback_query(F.data.startswith("buy_skin_"))
async def buy_skin_callback(call: types.CallbackQuery):
    skin_name = call.data.replace("buy_skin_", "")
    user_id = call.from_user.id
    user = get_user(user_id)
    conn = sqlite3.connect("mafia_ultimate_all.db")
    cursor = conn.cursor()
    if user[3] >= 1000:
        cursor.execute("UPDATE users SET dollars = dollars - 1000 WHERE user_id = ?", (user_id,))
        cursor.execute("INSERT INTO user_skins (user_id, role_name, skin_name) VALUES (?, ?, ?)", (user_id, "Don", skin_name))
        conn.commit()
        await call.answer(f"🎉 Tabriklaymiz! '{skin_name}' skini sotib olindi!", show_alert=True)
    else:
        await call.answer("❌ Mablag'ingiz yetarli emas! (1000$ kerak)", show_alert=True)
    conn.close()

@dp.callback_query(F.data == "shop_pets")
async def shop_pets_cb(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🐕 It - 710$", callback_data="buy_pet_dog")],
        [InlineKeyboardButton(text="🦅 Burgut - 600$", callback_data="buy_pet_eagle")],
        [InlineKeyboardButton(text="🦉 Boyqush - 520$", callback_data="buy_pet_owl")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_shop")]
    ])
    await call.message.edit_text("🐾 **Uy hayvonlari do'koni:**", reply_markup=kb)

@dp.callback_query(F.data == "back_to_shop")
async def back_shop_cb(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛡 Himoya (100$)", callback_data="buy_shield"), InlineKeyboardButton(text="🧪 Dori (100$)", callback_data="buy_potion")],
        [InlineKeyboardButton(text="📄 Yolgon Hujjat (1000$)", callback_data="buy_documents"), InlineKeyboardButton(text="👺 Maska (1000$)", callback_data="buy_mask")],
        [InlineKeyboardButton(text="🛡 Ovozdan himoya (300$)", callback_data="buy_vote_shield"), InlineKeyboardButton(text="🔫 Miltiq (1300$)", callback_data="buy_rifle")],
        [InlineKeyboardButton(text="📦 Sirli quti (500$)", callback_data="buy_mystery_box")],
        [InlineKeyboardButton(text="🐾 Uy hayvonlari do'koni", callback_data="shop_pets"), InlineKeyboardButton(text="🎨 Skinlar do'koni", callback_data="shop_skins")]
    ])
    await call.message.edit_text("🛒 **Do'konga xush kelibsiz!** Kerakli buyumni tanlang:", reply_markup=kb)

@dp.callback_query(F.data.startswith("buy_"))
async def shop_buy_cb(call: types.CallbackQuery):
    if call.data.startswith("buy_skin_") or call.data == "buy_mystery_box":
        if call.data == "buy_mystery_box":
            user_id = call.from_user.id
            user = get_user(user_id)
            conn = sqlite3.connect("mafia_ultimate_all.db")
            cursor = conn.cursor()
            if user[3] >= 500:
                cursor.execute("UPDATE users SET dollars = dollars - 500, mystery_box = mystery_box + 1 WHERE user_id = ?", (user_id,))
                conn.commit()
                await call.answer("📦 Sirli quti sotib olindi!", show_alert=True)
            else:
                await call.answer("❌ Mablag'ingiz yetarli emas! (500$ kerak)", show_alert=True)
            conn.close()
        return

    user_id = call.from_user.id
    user = get_user(user_id)
    action = call.data
    conn = sqlite3.connect("mafia_ultimate_all.db")
    cursor = conn.cursor()

    if action == "buy_shield":
        if user[3] >= 100:
            cursor.execute("UPDATE users SET dollars = dollars - 100, shield = shield + 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            await call.answer("Himoya sotib olindi! 🛡", show_alert=True)
        else:
            await call.answer("Mablag'ingiz yetarli emas! (100$ kerak)", show_alert=True)
    elif action == "buy_potion":
        if user[3] >= 100:
            cursor.execute("UPDATE users SET dollars = dollars - 100, potion = potion + 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            await call.answer("Dori sotib olindi! 🧪", show_alert=True)
        else:
            await call.answer("Mablag'ingiz yetarli emas! (100$ kerak)", show_alert=True)
    elif action == "buy_documents":
        if user[3] >= 1000:
            cursor.execute("UPDATE users SET dollars = dollars - 1000, documents = documents + 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            await call.answer("Yolg'on hujjatlar tayyorlandi! 📄", show_alert=True)
        else:
            await call.answer("Mablag'ingiz yetarli emas! (1000$ kerak)", show_alert=True)
    elif action == "buy_mask":
        if user[3] >= 1000:
            cursor.execute("UPDATE users SET dollars = dollars - 1000, mask = mask + 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            await call.answer("Maska sotib olindi! 👺", show_alert=True)
        else:
            await call.answer("Mablag'ingiz yetarli emas! (1000$ kerak)", show_alert=True)
    elif action == "buy_vote_shield":
        if user[3] >= 300:
            cursor.execute("UPDATE users SET dollars = dollars - 300, vote_shield = vote_shield + 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            await call.answer("Ovoz berishdan himoya sotib olindi! 🛡", show_alert=True)
        else:
            await call.answer("Mablag'ingiz yetarli emas! (300$ kerak)", show_alert=True)
    elif action == "buy_rifle":
        if user[3] >= 1300:
            cursor.execute("UPDATE users SET dollars = dollars - 1300, rifle = rifle + 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            await call.answer("Miltiq sotib olindi! 🔫", show_alert=True)
        else:
            await call.answer("Mablag'ingiz yetarli emas! (1300$ kerak)", show_alert=True)
    elif action.startswith("buy_pet_"):
        ptype = action.split("_")[2]
        price = 710 if ptype == "dog" else (600 if ptype == "eagle" else 520)
        pname = "It" if ptype == "dog" else ("Burgut" if ptype == "eagle" else "Boyqush")
        if user[3] >= price:
            cursor.execute("UPDATE users SET dollars = dollars - ?, pet = ? WHERE user_id = ?", (price, pname, user_id))
            conn.commit()
            await call.answer(f"{pname} sotib olindi! 🐾", show_alert=True)
        else:
            await call.answer(f"Mablag'ingiz yetarli emas! ({price}$ kerak)", show_alert=True)
    conn.close()

# --- SOVG'A YUBORISH TIZIMI ---
@dp.message(F.chat.type == "private", F.text == "🎁 Sovg'a yuborish")
async def gift_start(message: types.Message, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Tanga (Dollar)", callback_data="gift_type_money")],
        [InlineKeyboardButton(text="🎁 Buyum yoki Sirli quti", callback_data="gift_type_item")]
    ])
    await message.answer("🎁 **Sovg'a turini tanlang:**", reply_markup=kb)

@dp.callback_query(F.data.startswith("gift_type_"))
async def gift_type_chosen(call: types.CallbackQuery, state: FSMContext):
    gtype = call.data.replace("gift_type_", "")
    await state.update_data(gift_type=gtype)
    await call.message.edit_text("👤 Sovg'a yubormoqchi bo'lgan o'yinchining **ID raqamini** yuboring:")
    await state.set_state(GiftState.waiting_for_target_id)

@dp.message(GiftState.waiting_for_target_id, F.chat.type == "private")
async def gift_receive_id(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Iltimos, to'g'ri ID raqamini kiriting (faqat raqam):")
        return
    target_id = int(message.text)
    target_user = get_user(target_id)
    if not target_user:
        await message.answer("❌ Bunday ID raqamidagi foydalanuvchi topilmadi! Qaytadan kiriting:")
        return
    if target_id == message.from_user.id:
        await message.answer("❌ O'zingizga sovg'a yubora olmaysiz! Boshqa ID kiriting:")
        return

    await state.update_data(target_id=target_id)
    data = await state.get_data()
    if data["gift_type"] == "money":
        await message.answer("💰 Qancha dollar ($) yubormoqchisiz? Miqdorni raqamda yuboring:")
        await state.set_state(GiftState.waiting_for_amount)
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛡 Himoya", callback_data="gift_item_shield"), InlineKeyboardButton(text="🧪 Dori", callback_data="gift_item_potion")],
            [InlineKeyboardButton(text="📦 Sirli quti", callback_data="gift_item_mystery_box"), InlineKeyboardButton(text="🔫 Miltiq", callback_data="gift_item_rifle")]
        ])
        await message.answer("🎁 Qaysi buyumni yubormoqchisiz?", reply_markup=kb)
        await state.set_state(GiftState.waiting_for_item)

@dp.message(GiftState.waiting_for_amount, F.chat.type == "private")
async def gift_receive_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Iltimos, miqdorni raqamda kiriting:")
        return
    amount = int(message.text)
    sender_id = message.from_user.id
    sender = get_user(sender_id)
    if sender[3] < amount or amount <= 1:
        await message.answer(f"❌ Hisobingizda yetarli mablag' yo'q yoki noto'g'ri miqdor! (Sizda: {sender[3]}$)")
        return
    data = await state.get_data()
    target_id = data["target_id"]
    
    conn = sqlite3.connect("mafia_ultimate_all.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET dollars = dollars - ? WHERE user_id = ?", (amount, sender_id))
    cursor.execute("UPDATE users SET dollars = dollars + ? WHERE user_id = ?", (amount, target_id))
    conn.commit()
    conn.close()
    
    await message.answer(f"✅ Muvaffaqiyatli! {target_id} raqamli o'yinchiga **{amount}$** yuborildi.")
    try:
        await bot.send_message(target_id, f"🎁 Sizga **{sender[2]}**dan **{amount}$** miqdorida sovg'a keldi! 🎉")
    except Exception:
        pass
    await state.clear()

@dp.callback_query(F.data.startswith("gift_item_"), GiftState.waiting_for_item)
async def gift_receive_item(call: types.CallbackQuery, state: FSMContext):
    item_key = call.data.replace("gift_item_", "")
    sender_id = call.from_user.id
    sender = get_user(sender_id)
    item_indices = {
        "shield": (6, "Himoya 🛡"),
        "potion": (7, "Dori 🧪"),
        "mystery_box": (12, "Sirli quti 📦"),
        "rifle": (11, "Miltiq 🔫")
    }
    col_idx, item_name = item_indices[item_key]
    if sender[col_idx] <= 0:
        await call.answer(f"❌ Sizda yuborish uchun {item_name} yo'q!", show_alert=True)
        return
    data = await state.get_data()
    target_id = data["target_id"]
    col_names = {"shield": "shield", "potion": "potion", "mystery_box": "mystery_box", "rifle": "rifle"}
    col_name = col_names[item_key]
    
    conn = sqlite3.connect("mafia_ultimate_all.db")
    cursor = conn.cursor()
    cursor.execute(f"UPDATE users SET {col_name} = {col_name} - 1 WHERE user_id = ?", (sender_id,))
    cursor.execute(f"UPDATE users SET {col_name} = {col_name} + 1 WHERE user_id = ?", (target_id,))
    conn.commit()
    conn.close()
    
    await call.message.edit_text(f"✅ Muvaffaqiyatli! {target_id} raqamli o'yinchiga **{item_name}** sovg'a qilindi!")
    try:
        await bot.send_message(target_id, f"🎁 Sizga **{sender[2]}**dan **{item_name}** sovg'asi keldi! 🎉")
    except Exception:
        pass
    await state.clear()

@dp.message(F.chat.type == "private", F.text == "🐾 Uy hayvonlari")
async def pets_info(message: types.Message):
    await message.answer("🐾 **It (710$), Burgut (600$) va Boyqush (520$)** kechasi qidiruv va xabarlar uchun xizmat qiladi!")

@dp.message(F.chat.type == "private", F.text == "❤️ Juftni topish")
async def find_pair(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔍 Juft topish", callback_data="search_pair")]])
    await message.answer("❤️ Oshiq sifatida sevgilingizni tanlang:", reply_markup=kb)

@dp.callback_query(F.data == "search_pair")
async def search_pair_cb(call: types.CallbackQuery):
    conn = sqlite3.connect("mafia_ultimate_all.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, fullname FROM users WHERE user_id != ? ORDER BY RANDOM() LIMIT 1", (call.from_user.id,))
    res = cursor.fetchone()
    conn.close()
    if res:
        await call.message.edit_text(f"✨ Tabriklaymiz! Siz **{res[1]}** bilan juftlashdingiz ❤️\n*(Eslatma: Agar biri o'lsa, ikkinchisi ham qayg'udan o'ladi!)*")
    else:
        await call.answer("Hozircha boshqalar yo'q.", show_alert=True)

@dp.message(F.chat.type == "private", F.text == "🎭 Rollar va Vazifalar")
async def roles_info(message: types.Message):
    roles_text = (
        "🎭 **O'YIN ROLLARI VA ULarning VAZIFALARI:**\n\n"
        "❤️ **Oshiq** — sevgilisini tanlaydi, ulardan biri o'lsa ikkinchisi ham o'ladi.\n"
        "🛡 **Tansoqchi** — himoya qilgan o'yinchi o'rniga o'zi qurbon bo'ladi.\n"
        "🎭 **Josus** — kechasi bir o'yinchining rolini yashirin bilib oladi.\n"
        "🤡 **Masxaraboz** — ovoz berish orqali chiqarib yuborishsa, g'alaba qozonadi.\n"
        "🧛 **Vampir** — har kecha bitta o'yinchini tishlaydi va maxsus mexanikaga ega.\n"
    )
    await message.answer(roles_text, parse_mode="Markdown")

@dp.message(F.chat.type == "private", F.text == "📜 Mavsum haqida")
async def season_info(message: types.Message):
    await message.answer("🌟 **Mavsum:** Qorong'u qishloq va Vampirlar hujumi!")

@dp.message(F.chat.type == "private", F.text == "🎁 Kunlik Topshiriqlar")
async def quests_handler(message: types.Message):
    await message.answer("🎁 3 ta o'yinda g'alaba qozoning va tangalarga ega bo'ling!")

@dp.message(F.chat.type == "private", F.text == "🏆 Reyting va Unvonlar")
async def rankings_info(message: types.Message):
    await message.answer("🏆 Unvonlar: Rookie, Veteran, Master, Legend!")

# --- ADMIN PANEL VA BONUS POST TIZIMI ---
@dp.message(F.chat.type == "private", F.text == "👑 Admin Panel")
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Kanalga Bonus Post Yuborish", callback_data="admin_send_bonus")]
    ])
    await message.answer("👑 **Admin Paneli:** Kerakli amalni tanlang:", reply_markup=kb)

@dp.callback_query(F.data == "admin_send_bonus")
async def admin_send_bonus_cb(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID: return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Dollar ($)", callback_data="btype_dollars"), InlineKeyboardButton(text="💎 Olmos", callback_data="btype_diamonds")]
    ])
    await call.message.edit_text("🎁 Kanalga qanday turdagi bonus yubormoqchisiz?", reply_markup=kb)
    await state.set_state(BonusPostState.waiting_for_bonus_type)

@dp.callback_query(BonusPostState.waiting_for_bonus_type, F.data.startswith("btype_"))
async def bonus_type_chosen(call: types.CallbackQuery, state: FSMContext):
    btype = call.data.replace("btype_", "")
    await state.update_data(bonus_type=btype)
    unit_name = "Dollar ($)" if btype == "dollars" else "Olmos 💎"
    await call.message.edit_text(f"✍️ Har bir foydalanuvchi oladigan **{unit_name}** miqdorini raqamda yuboring:")
    await state.set_state(BonusPostState.waiting_for_bonus_amount)

@dp.message(BonusPostState.waiting_for_bonus_amount, F.chat.type == "private")
async def bonus_amount_received(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Iltimos, to'g'ri miqdorni raqamda kiriting:")
        return
    amount = int(message.text)
    data = await state.get_data()
    btype = data["bonus_type"]
    unit_symbol = "$" if btype == "dollars" else "💎"
    
    bonus_code = f"bonus_{random.randint(100000, 999999)}"
    await state.update_data(bonus_amount=amount, bonus_code=bonus_code)
    
    post_text = (
        f"🎁 **MAFIYA BOTDAN KUNLIK BONUS!** 🎉\n\n"
        f"Hurmatli o'yinchilar, kanalimiz uchun maxsus bonus ajratildi!\n"
        f"Quyidagi tugmani bosing va **{amount} {unit_symbol}**ga ega bo'ling!\n\n"
        f"*(Tugma faqat 1 marta ishlaydi)*"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🎁 {amount} {unit_symbol} Olish", callback_data=f"claim_{bonus_code}")]
    ])
    
    try:
        await bot.send_message(CHANNEL_USERNAME, post_text, reply_markup=kb, parse_mode="Markdown")
        await message.answer(f"✅ Bonus post muvaffaqiyatli **{CHANNEL_USERNAME}** kanaliga yuborildi!", reply_markup=main_menu_kb(message.from_user.id))
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {e}", reply_markup=main_menu_kb(message.from_user.id))
    
    await state.clear()

@dp.callback_query(F.data.startswith("claim_"))
async def claim_bonus_callback(call: types.CallbackQuery):
    user_id = call.from_user.id
    if CHANNEL_USERNAME and not await check_subscription(user_id):
        await call.answer("⚠️ Bonusni olish uchun avval kanalimizga obuna bo'ling!", show_alert=True)
        return

    bonus_code = call.data
    conn = sqlite3.connect("mafia_ultimate_all.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM claimed_bonuses WHERE user_id = ? AND bonus_code = ?", (user_id, bonus_code))
    if cursor.fetchone():
        conn.close()
        await call.answer("❌ Siz bu bonusni allaqachon olgansiz!", show_alert=True)
        return

    text = call.message.text
    import re
    numbers = re.findall(r'\d+', text)
    amount = int(numbers[0]) if numbers else 100
    
    is_diamond = "💎" in text
    col_name = "diamonds" if is_diamond else "dollars"
    
    cursor.execute(f"UPDATE users SET {col_name} = {col_name} + ? WHERE user_id = ?", (amount, user_id))
    cursor.execute("INSERT INTO claimed_bonuses (user_id, bonus_code) VALUES (?, ?)", (user_id, bonus_code))
    conn.commit()
    conn.close()
    
    unit_name = "💎 Olmos" if is_diamond else "💵 Dollar"
    await call.answer(f"🎉 Tabriklaymiz! Sizning balansingizga {amount} {unit_name} qo'shildi!", show_alert=True)


# =====================================================================
# --- MAFIYA O'YINI MEXANIKASI VA AVTOMATIK JARAYON ---
# =====================================================================

@dp.message(Command("mafiya"))
async def start_mafia_game(message: types.Message):
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("Bu buyruq faqat guruhlarda ishlaydi!")
        return
    chat_id = message.chat.id
    game_lobbies[chat_id] = {"players": {}, "roles": {}, "status": "waiting"}
    
    # Guruhda o'yin ochilganda chiqadigan xabarga botga o'tish tugmasi
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 O'yinga qo'shilish", callback_data="join_mafia")],
        [InlineKeyboardButton(text="🤖 Botga o'tish (Rollarni ko'rish)", url=f"https://t.me/{BOT_USERNAME}?start=game")]
    ])
    await message.answer("🎭 **Yangi MAFIA O'yini ochildi!** Qo'shilish uchun pastdagi tugmani bosing:", reply_markup=kb)

@dp.callback_query(F.data == "join_mafia")
async def join_mafia_cb(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    user_name = call.from_user.full_name
    if chat_id not in game_lobbies or game_lobbies[chat_id]["status"] != "waiting":
        await call.answer("Hozir o'yin ochilmagan!", show_alert=True)
        return
    if user_id in game_lobbies[chat_id]["players"]:
        await call.answer("Siz allaqachon qo'shilgansiz! ✅", show_alert=True)
    else:
        game_lobbies[chat_id]["players"][user_id] = user_name
        count = len(game_lobbies[chat_id]["players"])
        await call.answer(f"Qo'shildingiz! Jami o'yinchilar: {count}", show_alert=True)

@dp.message(Command("boshlash"))
async def start_game_process(message: types.Message):
    if message.chat.type not in ["group", "supergroup"]: return
    chat_id = message.chat.id
    if chat_id not in game_lobbies or len(game_lobbies[chat_id]["players"]) < 3:
        await message.answer("⚠️ O'yinni boshlash uchun kamida 3 ta o'yinchi kerak! Avval `/mafiya` yuboring va o'yinga qo'shiling.")
        return
    
    players = game_lobbies[chat_id]["players"]
    game_lobbies[chat_id]["status"] = "playing"
    user_ids = list(players.keys())
    random.shuffle(user_ids)
    
    roles = {user_ids[0]: "👑 Bosh Don", user_ids[1]: "👩‍⚕️ Doktor", user_ids[2]: "🎭 Josus"}
    for i in range(3, len(user_ids)):
        roles[user_ids[i]] = random.choice(["🔪 Qotil", "🛡 Tansoqchi", "🧛 Vampir", "🤡 Masxaraboz", "❤️ Oshiq", "👨‍💼 Fuqoro"])
    game_lobbies[chat_id]["roles"] = roles

    # Guruhdagi boshlash xabariga botga o'tish tugmasi
    start_group_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Botga o'tish (Rollarni tekshirish)", url=f"https://t.me/{BOT_USERNAME}?start=game")]
    ])
    await message.answer("🚀 **O'yin boshlandi! Barcha o'yinchilarga rollari shaxsiy xabar (lichka) orqali yuborildi.**", reply_markup=start_group_kb)

    # HAR BIR O'YINCHIGA LICHKASIGA ROL, QOBILIYAT VA GURUHGA QAYTISH TUGMASINI YUBORISH
    for uid, rname in roles.items():
        # Rolga mos qobiliyat va guruhga o'tish tugmalarini birlashtirib yaratish
        keyboard_rows = []
        if "Don" in rname or "Qotil" in rname:
            keyboard_rows.append([InlineKeyboardButton(text="🔪 O'ldirish uchun nishon tanlash", callback_data="mafia_kill")])
        elif "Doktor" in rname:
            keyboard_rows.append([InlineKeyboardButton(text="💉 Davolash uchun o'yinchi tanlash", callback_data="doctor_heal")])
        elif "Josus" in rname:
            keyboard_rows.append([InlineKeyboardButton(text="🔍 Rolni tekshirish", callback_data="spy_check")])
        else:
            keyboard_rows.append([InlineKeyboardButton(text="📖 Vazifani o'qish", callback_data="role_info")])
        
        # Lichkadan guruhga o'tish tugmasini qo'shish
        keyboard_rows.append([InlineKeyboardButton(text="💬 Guruhga qaytish", url=f"https://t.me/{message.chat.username}" if message.chat.username else f"https://t.me/c/{str(chat_id)[4:]}/1")])
        
        ability_kb = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

        role_msg = (
            f"🎭 **SIZNING ROLINGIZ TAYINLANDI!**\n\n"
            f"Sizning rolingiz: **{rname}**\n\n"
            f"💡 *Esda tuting:* O'yin davomida o'z rolingizni sir saqlang va kechasi o'z qobiliyatingizdan foydalaning!"
        )
        try:
            await bot.send_message(uid, role_msg, reply_markup=ability_kb, parse_mode="Markdown")
        except Exception:
            pass  # Agar foydalanuvchi botni start qilmagan bo'lsa xatolikni oldini oladi
    
    # Avtomatik jarayonni boshlash uchun fon vazifasi (Task) ochamiz
    asyncio.create_task(run_game_loop(chat_id, message))

# Qobiliyat tugmalari bosilganda ishlaydigan umumiy callback handler
@dp.callback_query(F.data.in_({"mafia_kill", "doctor_heal", "spy_check", "role_info"}))
async def ability_buttons_cb(call: types.CallbackQuery):
    action = call.data
    if action == "mafia_kill":
        await call.answer("🎯 Kechasi qaysi o'yinchining uyiga borasiz? (Guruhda ovoz bering)", show_alert=True)
    elif action == "doctor_heal":
        await call.answer("💉 Kimni davolamoqchisiz? Ehtiyotkor bo'ling!", show_alert=True)
    elif action == "spy_check":
        await call.answer("🔍 Qaysi o'yinchining sirini ochmoqchisiz?", show_alert=True)
    else:
        await call.answer("📜 O'z vazifangizni bajarib, jamoangiz bilan g'alaba qozoning!", show_alert=True)

async def run_game_loop(chat_id: int, message: types.Message):
    try:
        roles = game_lobbies[chat_id]["roles"]

        # Guruhdagi xabarlarga botga o'tish tugmasi
        group_link_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Botga o'tish", url=f"https://t.me/{BOT_USERNAME}?start=game")]
        ])

        # 1. TUN JARAYONI
        night_caption = (
            "📰 **SHOSHILINCH XABAR!**\n\n"
            "🌃 Tun shaharga o'z hukmini o'tkazmoqda...\n\n"
            "🚪 Uylar eshiklari berkitildi.\n"
            "💡 Chiroqlar birin-ketin o'chmoqda.\n"
            "👣 Qorong'ulik orasida sirli soyalar harakatlana boshladi.\n\n"
            "😈 Har bir rol o'z vazifasini bajarishga kirishmoqda...\n\n"
            "⏳ Qaroringizni ehtiyotkorlik bilan qabul qiling."
        )
        await bot.send_animation(chat_id, "https://media.giphy.com/media/26AHONQ79FdWZhAI0/giphy.gif", caption=night_caption, reply_markup=group_link_kb, parse_mode="Markdown")
        
        await asyncio.sleep(10)

        # 2. TONG VA KELISHILGAN VOQEALAR JARAYONI
        morning_caption = (
            "🚨 **SHOSHILINCH XABAR!**\n\n"
            "🌅 Quyosh nurlari shaharga yoyildi...\n\n"
            "😨 Ammo bu tong ham hamma uchun quvonchli emas.\n\n"
            "🏠 Kechasi fuqaroning uyida dahshatli voqea sodir bo'lgan...\n\n"
            "💀 Jabrlanuvchi voqea joyida halok bo'ldi.\n\n"
            "🗣 Endi shahar aholisi jinoyatchini topishga harakat qiladi."
        )
        await bot.send_animation(chat_id, "https://media.giphy.com/media/xT9IgusXg6PLEZ8IGY/giphy.gif", caption=morning_caption, reply_markup=group_link_kb, parse_mode="Markdown")
        
        await asyncio.sleep(6)

        # Doktorni qutqargani yoki qotil o'ldirgani haqida xabar
        saved_text = (
            "📰 **FAVQULODDA XUSHXABAR!**\n\n"
            "🌅 Tong otishi bilan quvonchli xabar tarqaldi.\n\n"
            "💉 Doktorning jasorati va tezkor yordami sababli o'yinchining hayoti saqlab qolindi.\n\n"
            "👏 Butun shahar Doktorni olqishlamoqda!"
        )
        await bot.send_message(chat_id, saved_text, reply_markup=group_link_kb, parse_mode="Markdown")
        
        await asyncio.sleep(6)

        # 3. OVOZ BERISH JARAYONI
        voting_caption = (
            "📺 **JONLI EFIR**\n\n"
            "🎙 Studio ekranidan maxsus reportaj.\n\n"
            "🏛 Shahar maydoniga barcha fuqarolar yig'ildi.\n\n"
            "😠 Har kimning gumoni bor.\n"
            "⚖ Bugun bir insonning taqdiri hal bo'ladi.\n\n"
            "👇 Muhokama qiling va gumondorni aniqlang!"
        )
        await bot.send_animation(chat_id, "https://media.giphy.com/media/3o7TKSjRrfIPjeiVyM/giphy.gif", caption=voting_caption, reply_markup=group_link_kb, parse_mode="Markdown")

        await asyncio.sleep(8)

        # 4. O'YIN TUGASHI, MUKOFOTLASH VA G'OLIBNI E'LON QILISH
        winner_choice = random.choice(["citizen", "mafia"])
        
        conn = sqlite3.connect("mafia_ultimate_all.db")
        cursor = conn.cursor()

        # Barcha ishtirokchilarning o'yinlar sonini (+1) ga oshiramiz
        for uid in roles.keys():
            cursor.execute("UPDATE users SET games_played = games_played + 1 WHERE user_id = ?", (uid,))

        mafia_roles = ["👑 Bosh Don", "🔪 Qotil"]

        if winner_choice == "mafia":
            for uid, rname in roles.items():
                if rname in mafia_roles:
                    cursor.execute("UPDATE users SET dollars = dollars + 100, games_won = games_won + 1 WHERE user_id = ?", (uid,))
            conn.commit()

            win_caption = (
                "🚨 **SHOSHILINCH XABAR!**\n\n"
                "🌑 Zulmat g'alaba qozondi...\n\n"
                "👑 Don boshchiligidagi mafiya butun shaharni o'z nazoratiga oldi.\n\n"
                "🚔 Qonun mag'lub bo'ldi.\n\n"
                "🏆 **G'OLIB:**\n"
                "👑 DON VA MAFIYA\n\n"
                "💰 G'oliblarning har biriga **100$** mukofot berildi! 🎉"
            )
            await bot.send_animation(chat_id, "https://media.giphy.com/media/13HgwGsXF0aiGY/giphy.gif", caption=win_caption, reply_markup=group_link_kb, parse_mode="Markdown")
        else:
            for uid, rname in roles.items():
                if rname not in mafia_roles:
                    cursor.execute("UPDATE users SET dollars = dollars + 100, games_won = games_won + 1 WHERE user_id = ?", (uid,))
            conn.commit()

            win_caption = (
                "🎉 **MAXSUS SON!**\n\n"
                "📣 Butun shahar bo'ylab bayram boshlandi!\n\n"
                "👮‍♂️ Fuqarolar jinoyatchilarni fosh etishga muvaffaq bo'lishdi.\n\n"
                "☀️ Nihoyat shaharda tinchlik hukm surmoqda.\n\n"
                "🏆 **G'OLIB:**\n"
                "👥 FUQAROLAR JAMOASI\n\n"
                "💰 G'oliblarning har biriga **100$** mukofot berildi! 🎉"
            )
            await bot.send_animation(chat_id, "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif", caption=win_caption, reply_markup=group_link_kb, parse_mode="Markdown")

        conn.close()

        if chat_id in game_lobbies:
            del game_lobbies[chat_id]

    except Exception as e:
        logging.error(f"O'yin jarayonida xatolik: {e}")


# --- WEB SERVER ---
async def handle(request):
    return web.Response(text="Mafia Bot Web Server is running successfully!")

async def web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    import os
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    await web_server()
    await dp.start_polling(bot)

if __name__ == "__main__"
    asyncio.run(main())

