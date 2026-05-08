
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
    KeyboardButton
)

from aiogram.client.default import DefaultBotProperties

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from apscheduler.schedulers.asyncio import AsyncIOScheduler

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(level=logging.INFO)

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = "8796918085:AAHuy3GTUEyP5LEN8fDKxvo6jWZjBMHY9D0"

ADMIN_ID = 1350783137

CHANNEL_ID = -1003931253794
CHANNEL_LINK = "https://t.me/+fIGX41vfUl1lMTY6"

DB_NAME = "beauty.db"

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

        await db.execute("""
        CREATE TABLE IF NOT EXISTS slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT,
            date TEXT,
            time TEXT,
            is_booked INTEGER DEFAULT 0
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service TEXT,
            name TEXT,
            phone TEXT,
            date TEXT,
            time TEXT,
            reminder_job_id TEXT
        )
        """)

        await db.commit()

# =========================================================
# DATABASE FUNCTIONS
# =========================================================

async def add_slot(service, date, time):

    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        INSERT INTO slots (service, date, time)
        VALUES (?, ?, ?)
        """, (service, date, time))

        await db.commit()


async def get_dates(service):

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute("""
        SELECT DISTINCT date
        FROM slots
        WHERE service = ? AND is_booked = 0
        ORDER BY date
        """, (service,))

        return await cursor.fetchall()


async def get_times(service, date):

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute("""
        SELECT time
        FROM slots
        WHERE service = ? AND date = ? AND is_booked = 0
        ORDER BY time
        """, (service, date))

        return await cursor.fetchall()


async def get_user_booking(user_id):

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute("""
        SELECT *
        FROM bookings
        WHERE user_id = ?
        """, (user_id,))

        return await cursor.fetchone()


async def create_booking(
    user_id,
    service,
    name,
    phone,
    date,
    time,
    reminder_job_id
):

    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        UPDATE slots
        SET is_booked = 1
        WHERE service = ? AND date = ? AND time = ?
        """, (service, date, time))

        await db.execute("""
        INSERT INTO bookings
        (
            user_id,
            service,
            name,
            phone,
            date,
            time,
            reminder_job_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            service,
            name,
            phone,
            date,
            time,
            reminder_job_id
        ))

        await db.commit()


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
            WHERE service = ? AND date = ? AND time = ?
            """, (service, date, time))

            await db.execute("""
            DELETE FROM bookings
            WHERE user_id = ?
            """, (user_id,))

            await db.commit()

            return reminder_job_id

        return None


async def get_all_bookings():

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute("""
        SELECT *
        FROM bookings
        ORDER BY date, time
        """)

        return await cursor.fetchall()

# =========================================================
# SUB CHECK
# =========================================================

async def check_subscription(user_id):

    try:

        member = await bot.get_chat_member(
            CHANNEL_ID,
            user_id
        )

        return member.status in [
            "member",
            "administrator",
            "creator"
        ]

    except:
        return False

# =========================================================
# REMINDER
# =========================================================

async def send_reminder(user_id, time):

    try:

        await bot.send_message(
            user_id,
            f"⏰ Напоминание!\n\n"
            f"Вы записаны завтра в {time} ❤️"
        )

    except:
        pass


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
        args=[user_id, time],
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
                KeyboardButton(text="💅 Прайс")
            ],

            [
                KeyboardButton(text="🖼 Портфолио"),
                KeyboardButton(text="❌ Моя запись")
            ],

            [
                KeyboardButton(text="📞 Контакты")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )


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
                    text="👁 Ресницы",
                    callback_data="service_Ресницы"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🪄 Брови",
                    callback_data="service_Брови"
                )
            ]
        ]
    )


def sub_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="Подписаться",
                    url=CHANNEL_LINK
                )
            ],

            [
                InlineKeyboardButton(
                    text="Проверить подписку",
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

    await message.answer(
        "<b>Добро пожаловать ❤️</b>\n\n"
        "Выберите действие ниже 👇",
        reply_markup=main_menu()
    )

# =========================================================
# PRICE
# =========================================================

@dp.message(F.text == "💅 Прайс")
async def prices(message: Message):

    await message.answer(
        "<b>💅 Прайс:</b>\n\n"
        "Маникюр — 2500₽\n"
        "Ресницы — 3000₽\n"
        "Брови — 1500₽"
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
                    text="Смотреть работы",
                    url="https://ru.pinterest.com/crystalwithluv/_created/"
                )
            ]
        ]
    )

    await message.answer(
        "🖼 Портфолио мастера:",
        reply_markup=keyboard
    )

# =========================================================
# CONTACTS
# =========================================================

@dp.message(F.text == "📞 Контакты")
async def contacts(message: Message):

    await message.answer(
        "<b>📞 Контакты:</b>\n\n"
        "Телефон: +7 999 999 99 99\n"
        "Instagram: @beauty_salon\n"
        "Адрес: Москва"
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
            "Для записи подпишитесь на канал 👇",
            reply_markup=sub_keyboard()
        )

        return

    existing = await get_user_booking(
        message.from_user.id
    )

    if existing:

        await message.answer(
            "❌ У вас уже есть запись."
        )

        return

    await message.answer(
        "Выберите услугу:",
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
            "✅ Подписка подтверждена."
        )

    else:

        await call.message.answer(
            "❌ Вы не подписаны."
        )

# =========================================================
# SERVICE
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
            "❌ Свободных дат нет."
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
        "Введите ваше имя:"
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
        "Введите номер телефона:"
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

    await create_booking(
        user_id=message.from_user.id,
        service=service,
        name=name,
        phone=phone,
        date=date,
        time=time,
        reminder_job_id=reminder_job_id
    )

    await bot.send_message(
        ADMIN_ID,
        f"🆕 Новая запись!\n\n"
        f"👤 {name}\n"
        f"📱 {phone}\n"
        f"💅 {service}\n"
        f"📅 {date}\n"
        f"⏰ {time}"
    )

    await message.answer(
        f"✅ Вы успешно записаны!\n\n"
        f"💅 {service}\n"
        f"📅 {date}\n"
        f"⏰ {time}"
    )

    await state.clear()

# =========================================================
# MY BOOKING
# =========================================================

@dp.message(F.text == "❌ Моя запись")
async def my_booking(message: Message):

    booking = await get_user_booking(
        message.from_user.id
    )

    if not booking:

        await message.answer(
            "❌ У вас нет записи."
        )

        return

    text = (
        f"<b>Ваша запись:</b>\n\n"
        f"💅 {booking[2]}\n"
        f"📅 {booking[5]}\n"
        f"⏰ {booking[6]}"
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
# BOOKINGS
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
            f"👤 {b[3]}\n"
            f"📱 {b[4]}\n"
            f"💅 {b[2]}\n"
            f"📅 {b[5]}\n"
            f"⏰ {b[6]}\n\n"
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


