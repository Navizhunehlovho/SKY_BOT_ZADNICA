
# =========================================================
# PREMIUM BEAUTY SALON BOT
# LEVEL: COMMERCIAL / PREMIUM
# AIROGRAM 3.x
# =========================================================

import asyncio
import logging
import re
import aiosqlite

from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    FSInputFile
)

from aiogram.client.default import DefaultBotProperties

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from apscheduler.schedulers.asyncio import AsyncIOScheduler

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = "8796918085:AAHuy3GTUEyP5LEN8fDKxvo6jWZjBMHY9D0"

ADMIN_ID = 1350783137

CHANNEL_ID = -1003931253794
CHANNEL_LINK = "https://t.me/your_channel"

DB_NAME = "beauty.db"

SALON_NAME = "LUXE BEAUTY STUDIO"

INSTAGRAM = "https://instagram.com/your_inst"

ADDRESS = "Москва, Тверская 1"

PHONE = "+7 999 999 99 99"

WORK_TIME = "10:00 - 22:00"

# =========================================================
# BOT
# =========================================================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()

scheduler = AsyncIOScheduler()

# =========================================================
# FSM
# =========================================================

class BookingState(StatesGroup):

    waiting_service = State()
    waiting_date = State()
    waiting_time = State()
    waiting_name = State()
    waiting_phone = State()

# =========================================================
# DATABASE
# =========================================================

async def init_db():

    async with aiosqlite.connect(DB_NAME) as db:

        # SLOTS

        await db.execute("""
        CREATE TABLE IF NOT EXISTS slots (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            service TEXT,
            date TEXT,
            time TEXT,

            is_booked INTEGER DEFAULT 0
        )
        """)

        # BOOKINGS

        await db.execute("""
        CREATE TABLE IF NOT EXISTS bookings (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            username TEXT,

            service TEXT,

            name TEXT,

            phone TEXT,

            date TEXT,

            time TEXT,

            created_at TEXT,

            reminder_job_id TEXT
        )
        """)

        # CLIENTS

        await db.execute("""
        CREATE TABLE IF NOT EXISTS clients (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER UNIQUE,

            visits INTEGER DEFAULT 0
        )
        """)

        await db.commit()

# =========================================================
# DATABASE FUNCTIONS
# =========================================================

async def add_slot(service, date, time):

    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        INSERT INTO slots (
            service,
            date,
            time
        )
        VALUES (?, ?, ?)
        """, (service, date, time))

        await db.commit()

# =========================================================

async def get_dates(service):

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute("""
        SELECT DISTINCT date
        FROM slots
        WHERE service = ?
        AND is_booked = 0
        ORDER BY date
        """, (service,))

        return await cursor.fetchall()

# =========================================================

async def get_times(service, date):

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute("""
        SELECT time
        FROM slots
        WHERE service = ?
        AND date = ?
        AND is_booked = 0
        ORDER BY time
        """, (service, date))

        return await cursor.fetchall()

# =========================================================

async def get_user_booking(user_id):

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute("""
        SELECT *
        FROM bookings
        WHERE user_id = ?
        """, (user_id,))

        return await cursor.fetchone()

# =========================================================

async def increase_visits(user_id):

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute("""
        SELECT visits
        FROM clients
        WHERE user_id = ?
        """, (user_id,))

        client = await cursor.fetchone()

        if client:

            await db.execute("""
            UPDATE clients
            SET visits = visits + 1
            WHERE user_id = ?
            """, (user_id,))

        else:

            await db.execute("""
            INSERT INTO clients (
                user_id,
                visits
            )
            VALUES (?, 1)
            """, (user_id,))

        await db.commit()

# =========================================================

async def create_booking(
    user_id,
    username,
    service,
    name,
    phone,
    date,
    time,
    reminder_job_id
):

    async with aiosqlite.connect(DB_NAME) as db:

        # DOUBLE BOOKING PROTECTION

        cursor = await db.execute("""
        SELECT is_booked
        FROM slots
        WHERE service = ?
        AND date = ?
        AND time = ?
        """, (service, date, time))

        slot = await cursor.fetchone()

        if not slot or slot[0] == 1:
            return False

        await db.execute("""
        UPDATE slots
        SET is_booked = 1
        WHERE service = ?
        AND date = ?
        AND time = ?
        """, (service, date, time))

        await db.execute("""
        INSERT INTO bookings (

            user_id,
            username,
            service,
            name,
            phone,
            date,
            time,
            created_at,
            reminder_job_id

        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (

            user_id,
            username,
            service,
            name,
            phone,
            date,
            time,
            str(datetime.now()),
            reminder_job_id
        ))

        await db.commit()

        await increase_visits(user_id)

        return True

# =========================================================

async def cancel_booking_db(user_id):

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute("""
        SELECT service, date, time, reminder_job_id
        FROM bookings
        WHERE user_id = ?
        """, (user_id,))

        booking = await cursor.fetchone()

        if booking:

            service, date, time, reminder_job_id = booking

            await db.execute("""
            UPDATE slots
            SET is_booked = 0
            WHERE service = ?
            AND date = ?
            AND time = ?
            """, (service, date, time))

            await db.execute("""
            DELETE FROM bookings
            WHERE user_id = ?
            """, (user_id,))

            await db.commit()

            return reminder_job_id

        return None

# =========================================================

async def get_all_bookings():

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute("""
        SELECT *
        FROM bookings
        ORDER BY date, time
        """)

        return await cursor.fetchall()

# =========================================================
# SUBSCRIPTION
# =========================================================

async def check_subscription(user_id):

    try:

        member = await bot.get_chat_member(
            CHANNEL_ID,
            user_id
        )

        print(member.status)

        return member.status in [
            "member",
            "administrator",
            "creator"
        ]

    except Exception as e:

        print("SUB ERROR:", e)

        return False

# =========================================================
# REMINDERS
# =========================================================

async def send_reminder(user_id, date, time):

    try:

        await bot.send_message(
            user_id,
            f"⏰ <b>Напоминание о записи</b>\n\n"
            f"📅 Завтра: {date}\n"
            f"⏰ Время: {time}\n\n"
            f"Ждём вас ❤️"
        )

    except:
        pass

# =========================================================

def schedule_reminder(user_id, date, time):

    booking_datetime = datetime.strptime(
        f"{date} {time}",
        "%Y-%m-%d %H:%M"
    )

    reminder_time = booking_datetime - timedelta(hours=24)

    if reminder_time <= datetime.now():
        return None

    job_id = f"{user_id}_{date}_{time}"

    scheduler.add_job(
        send_reminder,
        trigger="date",
        run_date=reminder_time,
        args=[user_id, date, time],
        id=job_id
    )

    return job_id

# =========================================================
# KEYBOARDS
# =========================================================

def main_menu():

    return ReplyKeyboardMarkup(

        keyboard=[

            [
                KeyboardButton(text="📅 Записаться"),
                KeyboardButton(text="💎 Услуги")
            ],

            [
                KeyboardButton(text="🖼 Портфолио"),
                KeyboardButton(text="💰 Прайс")
            ],

            [
                KeyboardButton(text="👑 Моя запись"),
                KeyboardButton(text="📍 Контакты")
            ]
        ],

        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )

# =========================================================

def services_keyboard():

    return InlineKeyboardMarkup(

        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="💅 Маникюр",
                    callback_data="service_Маникюр"
                )
            ],

            [
                InlineKeyboardButton(
                    text="👁 Наращивание ресниц",
                    callback_data="service_Ресницы"
                )
            ],

            [
                InlineKeyboardButton(
                    text="✨ Брови",
                    callback_data="service_Брови"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💎 VIP Комплекс",
                    callback_data="service_VIP"
                )
            ]
        ]
    )

# =========================================================

def sub_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="📢 Подписаться",
                    url=CHANNEL_LINK
                )
            ],

            [
                InlineKeyboardButton(
                    text="✅ Проверить подписку",
                    callback_data="check_sub"
                )
            ]
        ]
    )

# =========================================================
# START
# =========================================================

@dp.message(Command("start"))
async def start(message: Message):

    text = (
        f"👑 <b>{SALON_NAME}</b>\n\n"

        f"Добро пожаловать в премиальную "
        f"beauty-студию ❤️\n\n"

        f"✨ Онлайн запись\n"
        f"✨ Напоминания\n"
        f"✨ Премиальный сервис\n\n"

        f"Выберите действие ниже 👇"
    )

    await message.answer(
        text,
        reply_markup=main_menu()
    )

# =========================================================
# SERVICES
# =========================================================

@dp.message(F.text == "💎 Услуги")
async def services(message: Message):

    await message.answer(
        "<b>💎 Наши услуги:</b>\n\n"

        "💅 Маникюр\n"
        "👁 Наращивание ресниц\n"
        "✨ Оформление бровей\n"
        "💎 VIP-комплексы"
    )

# =========================================================
# PRICES
# =========================================================

@dp.message(F.text == "💰 Прайс")
async def prices(message: Message):

    await message.answer(
        "<b>💰 Прайс-лист:</b>\n\n"

        "💅 Маникюр — 2500₽\n"
        "👁 Ресницы — 3500₽\n"
        "✨ Брови — 1800₽\n"
        "💎 VIP — 7000₽"
    )

# =========================================================
# CONTACTS
# =========================================================

@dp.message(F.text == "📍 Контакты")
async def contacts(message: Message):

    await message.answer(
        f"<b>📍 Контакты:</b>\n\n"

        f"📍 Адрес: {ADDRESS}\n"
        f"📞 Телефон: {PHONE}\n"
        f"🕒 График: {WORK_TIME}\n\n"

        f"Instagram:\n{INSTAGRAM}"
    )

# =========================================================
# PORTFOLIO
# =========================================================

@dp.message(F.text == "🖼 Портфолио")
async def portfolio(message: Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✨ Смотреть работы",
                    url=INSTAGRAM
                )
            ]
        ]
    )

    await message.answer(
        "🖼 <b>Наше портфолио:</b>",
        reply_markup=keyboard
    )

# =========================================================
# BOOKING
# =========================================================

@dp.message(F.text == "📅 Записаться")
async def booking(message: Message):

    is_sub = await check_subscription(
        message.from_user.id
    )

    if not is_sub:

        await message.answer(
            "📢 Для записи подпишитесь на канал:",
            reply_markup=sub_keyboard()
        )

        return

    existing = await get_user_booking(
        message.from_user.id
    )

    if existing:

        await message.answer(
            "❌ У вас уже есть активная запись."
        )

        return

    await message.answer(
        "💎 Выберите услугу:",
        reply_markup=services_keyboard()
    )

# =========================================================
# CHECK SUB
# =========================================================

@dp.callback_query(F.data == "check_sub")
async def check_sub(call: CallbackQuery):

    is_sub = await check_subscription(
        call.from_user.id
    )

    if is_sub:

        await call.message.answer(
            "✅ Подписка подтверждена.\n\n"
            "Теперь вы можете записаться ❤️"
        )

    else:

        await call.message.answer(
            "❌ Подписка не найдена.\n\n"
            "Проверьте, что:\n"
            "• вы подписаны\n"
            "• канал не замьючен\n"
            "• прошло 5-10 секунд после подписки"
        )

# =========================================================
# SERVICE SELECT
# =========================================================

@dp.callback_query(F.data.startswith("service_"))
async def choose_service(
    call: CallbackQuery,
    state: FSMContext
):

    service = call.data.replace(
        "service_",
        ""
    )

    await state.update_data(
        service=service
    )

    dates = await get_dates(service)

    if not dates:

        await call.message.answer(
            "❌ Свободных дат пока нет."
        )

        return

    keyboard = []

    row = []

    for i, d in enumerate(dates, start=1):

        row.append(
            InlineKeyboardButton(
                text=d[0],
                callback_data=f"date_{d[0]}"
            )
        )

        if i % 2 == 0:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    await call.message.answer(
        "📅 Выберите дату:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )

# =========================================================
# DATE
# =========================================================

@dp.callback_query(F.data.startswith("date_"))
async def choose_date(
    call: CallbackQuery,
    state: FSMContext
):

    date = call.data.replace(
        "date_",
        ""
    )

    data = await state.get_data()

    service = data["service"]

    await state.update_data(
        date=date
    )

    times = await get_times(
        service,
        date
    )

    keyboard = []

    row = []

    for i, t in enumerate(times, start=1):

        row.append(
            InlineKeyboardButton(
                text=t[0],
                callback_data=f"time_{t[0]}"
            )
        )

        if i % 3 == 0:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    await call.message.answer(
        "⏰ Выберите время:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )

# =========================================================
# TIME
# =========================================================

@dp.callback_query(F.data.startswith("time_"))
async def choose_time(
    call: CallbackQuery,
    state: FSMContext
):

    time = call.data.replace(
        "time_",
        ""
    )

    await state.update_data(
        time=time
    )

    await state.set_state(
        BookingState.waiting_name
    )

    await call.message.answer(
        "👤 Введите ваше имя:"
    )

# =========================================================
# NAME
# =========================================================

@dp.message(BookingState.waiting_name)
async def get_name(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        name=message.text
    )

    await state.set_state(
        BookingState.waiting_phone
    )

    await message.answer(
        "📱 Введите номер телефона:"
    )

# =========================================================
# PHONE
# =========================================================

@dp.message(BookingState.waiting_phone)
async def get_phone(
    message: Message,
    state: FSMContext
):

    phone = message.text.strip()

    if not re.match(
        r"^\+?\d{10,15}$",
        phone
    ):

        await message.answer(
            "❌ Неверный формат номера."
        )

        return

    data = await state.get_data()

    service = data["service"]
    date = data["date"]
    time = data["time"]
    name = data["name"]

    reminder_job_id = schedule_reminder(
        message.from_user.id,
        date,
        time
    )

    success = await create_booking(

        user_id=message.from_user.id,

        username=message.from_user.username,

        service=service,

        name=name,

        phone=phone,

        date=date,

        time=time,

        reminder_job_id=reminder_job_id
    )

    if not success:

        await message.answer(
            "❌ Это время уже занято."
        )

        return

    # ADMIN NOTIFY

    admin_text = (

        f"🆕 <b>НОВАЯ ЗАПИСЬ</b>\n\n"

        f"👤 Имя: {name}\n"

        f"📱 Телефон: {phone}\n"

        f"🆔 ID: {message.from_user.id}\n"

        f"👤 Username: @{message.from_user.username}\n\n"

        f"💎 Услуга: {service}\n"

        f"📅 Дата: {date}\n"

        f"⏰ Время: {time}"
    )

    await bot.send_message(
        ADMIN_ID,
        admin_text
    )

    # USER SUCCESS

    await message.answer(

        f"✅ <b>Запись подтверждена!</b>\n\n"

        f"💎 Услуга: {service}\n"

        f"📅 Дата: {date}\n"

        f"⏰ Время: {time}\n\n"

        f"📍 {ADDRESS}\n\n"

        f"⏰ За сутки до записи "
        f"мы отправим напоминание ❤️"
    )

    await state.clear()

# =========================================================
# MY BOOKING
# =========================================================

@dp.message(F.text == "👑 Моя запись")
async def my_booking(message: Message):

    booking = await get_user_booking(
        message.from_user.id
    )

    if not booking:

        await message.answer(
            "❌ У вас нет активной записи."
        )

        return

    text = (

        f"👑 <b>Ваша запись</b>\n\n"

        f"💎 Услуга: {booking[3]}\n"

        f"📅 Дата: {booking[6]}\n"

        f"⏰ Время: {booking[7]}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Отменить запись",
                    callback_data="cancel_booking"
                )
            ]
        ]
    )

    await message.answer(
        text,
        reply_markup=keyboard
    )

# =========================================================
# CANCEL BOOKING
# =========================================================

@dp.callback_query(F.data == "cancel_booking")
async def cancel_booking(call: CallbackQuery):

    reminder_job_id = await cancel_booking_db(
        call.from_user.id
    )

    if reminder_job_id:

        try:
            scheduler.remove_job(
                reminder_job_id
            )
        except:
            pass

    await call.message.answer(
        "✅ Запись отменена."
    )

# =========================================================
# ADMIN ADD SLOT
# =========================================================

@dp.message(Command("addslot"))
async def addslot(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    # /addslot Маникюр 2026-05-10 14:00

    try:

        data = message.text.split()

        service = data[1]
        date = data[2]
        time = data[3]

        await add_slot(
            service,
            date,
            time
        )

        await message.answer(
            f"✅ Слот добавлен:\n\n"
            f"{service}\n"
            f"{date} {time}"
        )

    except:

        await message.answer(
            "Пример:\n"
            "/addslot Маникюр 2026-05-10 14:00"
        )

# =========================================================
# ADMIN BOOKINGS
# =========================================================

@dp.message(Command("bookings"))
async def bookings(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    bookings = await get_all_bookings()

    if not bookings:

        await message.answer(
            "Записей нет."
        )

        return

    text = "<b>📅 Все записи:</b>\n\n"

    for b in bookings:

        text += (

            f"👤 {b[4]}\n"

            f"📱 {b[5]}\n"

            f"💎 {b[3]}\n"

            f"📅 {b[6]}\n"

            f"⏰ {b[7]}\n\n"
        )

    await message.answer(text)

# =========================================================
# MAIN
# =========================================================

async def main():

    await init_db()

    scheduler.start()

    print("BOT STARTED")

    await dp.start_polling(bot)

# =========================================================

if __name__ == "__main__":
    asyncio.run(main())

