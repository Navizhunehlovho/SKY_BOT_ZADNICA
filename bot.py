
# =========================================================
# TELEGRAM BOT ДЛЯ МАСТЕРА МАНИКЮРА
# ВСЁ В ОДНОМ ФАЙЛЕ
#
# Python 3.11+
# aiogram 3.x
# SQLite
# FSM
# APScheduler
#
# =========================================================
# УСТАНОВКА:
#
# pip install aiogram aiosqlite APScheduler
#
# =========================================================
# ЗАПУСК:
#
# python bot.py
#
# =========================================================
# ВАЖНО:
#
# 1. Создай бота через @BotFather
# 2. Вставь BOT_TOKEN
# 3. Добавь бота в канал админом
# 4. Вставь CHANNEL_ID
#
# =========================================================

import asyncio
import aiosqlite

from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from apscheduler.schedulers.asyncio import AsyncIOScheduler

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

from aiogram.client.default import DefaultBotProperties

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

scheduler = AsyncIOScheduler()

# =========================================================
# FSM
# =========================================================

class BookingState(StatesGroup):
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
            date TEXT,
            time TEXT,
            is_booked INTEGER DEFAULT 0
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
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

async def add_slot(date, time):

    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        INSERT INTO slots (date, time)
        VALUES (?, ?)
        """, (date, time))

        await db.commit()


async def get_dates():

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute("""
        SELECT DISTINCT date
        FROM slots
        WHERE is_booked = 0
        ORDER BY date
        """)

        return await cursor.fetchall()


async def get_times(date):

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute("""
        SELECT time
        FROM slots
        WHERE date = ? AND is_booked = 0
        ORDER BY time
        """, (date,))

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
    name,
    phone,
    date,
    time,
    reminder_job_id=None
):

    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        UPDATE slots
        SET is_booked = 1
        WHERE date = ? AND time = ?
        """, (date, time))

        await db.execute("""
        INSERT INTO bookings
        (user_id, name, phone, date, time, reminder_job_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
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
        SELECT date, time, reminder_job_id
        FROM bookings
        WHERE user_id = ?
        """, (user_id,))

        booking = await cursor.fetchone()

        if booking:

            date, time, reminder_job_id = booking

            await db.execute("""
            UPDATE slots
            SET is_booked = 0
            WHERE date = ? AND time = ?
            """, (date, time))

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


async def get_all_future_bookings():

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute("""
        SELECT user_id, date, time, reminder_job_id
        FROM bookings
        """)

        return await cursor.fetchall()

# =========================================================
# SUBSCRIPTION CHECK
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
            f"⏰ Напоминаем, что вы записаны "
            f"на наращивание ресниц завтра "
            f"в {time}. Ждём вас ❤️"
        )

    except:
        pass


def schedule_reminder(
    user_id,
    date,
    time
):

    booking_datetime = datetime.strptime(
        f"{date} {time}",
        "%Y-%m-%d %H:%M"
    )

    reminder_time = booking_datetime - timedelta(hours=24)

    now = datetime.now()

    if reminder_time <= now:
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


async def restore_reminders():

    bookings = await get_all_future_bookings()

    for booking in bookings:

        user_id, date, time, reminder_job_id = booking

        booking_datetime = datetime.strptime(
            f"{date} {time}",
            "%Y-%m-%d %H:%M"
        )

        reminder_time = booking_datetime - timedelta(hours=24)

        if reminder_time > datetime.now():

            try:

                scheduler.add_job(
                    send_reminder,
                    trigger="date",
                    run_date=reminder_time,
                    args=[user_id, time],
                    id=reminder_job_id
                )

            except:
                pass

# =========================================================
# KEYBOARDS
# =========================================================

def main_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="📅 Записаться",
                    callback_data="booking"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💅 Прайсы",
                    callback_data="prices"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🖼 Портфолио",
                    callback_data="portfolio"
                )
            ],

            [
                InlineKeyboardButton(
                    text="❌ Отменить запись",
                    callback_data="cancel"
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
        "Выберите действие:",
        reply_markup=main_menu()
    )

# =========================================================
# PRICES
# =========================================================

@dp.callback_query(F.data == "prices")
async def prices(call: CallbackQuery):

    await call.message.answer(
        "<b>💅 Прайс</b>\n\n"
        "Френч — 1000₽\n"
        "Квадрат — 500₽"
    )

# =========================================================
# PORTFOLIO
# =========================================================

@dp.callback_query(F.data == "portfolio")
async def portfolio(call: CallbackQuery):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Смотреть портфолио",
                    url="https://ru.pinterest.com/crystalwithluv/_created/"
                )
            ]
        ]
    )

    await call.message.answer(
        "🖼 Портфолио мастера:",
        reply_markup=keyboard
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
            "✅ Подписка подтверждена.\n"
            "Теперь можете записаться."
        )

    else:

        await call.message.answer(
            "❌ Вы не подписаны на канал."
        )

# =========================================================
# BOOKING
# =========================================================

@dp.callback_query(F.data == "booking")
async def booking(call: CallbackQuery):

    is_sub = await check_subscription(
        call.from_user.id
    )

    if not is_sub:

        await call.message.answer(
            "Для записи необходимо подписаться на канал",
            reply_markup=sub_keyboard()
        )

        return

    existing = await get_user_booking(
        call.from_user.id
    )

    if existing:

        await call.message.answer(
            "❌ У вас уже есть запись."
        )

        return

    dates = await get_dates()

    if not dates:

        await call.message.answer(
            "Свободных дат пока нет."
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
# CHOOSE TIME
# =========================================================

@dp.callback_query(F.data.startswith("date_"))
async def choose_time(call: CallbackQuery):

    date = call.data.replace("date_", "")

    times = await get_times(date)

    keyboard = []

    row = []

    for i, t in enumerate(times, start=1):

        row.append(
            InlineKeyboardButton(
                text=t[0],
                callback_data=f"time_{date}_{t[0]}"
            )
        )

        if i % 3 == 0:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    await call.message.answer(
        f"📅 <b>{date}</b>\n"
        f"Выберите время:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )

# =========================================================
# TIME
# =========================================================

@dp.callback_query(F.data.startswith("time_"))
async def choose_slot(
    call: CallbackQuery,
    state: FSMContext
):

    data = call.data.split("_")

    date = data[1]
    time = data[2]

    await state.update_data(
        date=date,
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

    data = await state.get_data()

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
        name=name,
        phone=message.text,
        date=date,
        time=time,
        reminder_job_id=reminder_job_id
    )

    # ADMIN NOTIFY

    admin_text = (
        f"🆕 <b>Новая запись</b>\n\n"
        f"👤 Имя: {name}\n"
        f"📱 Телефон: {message.text}\n"
        f"📅 Дата: {date}\n"
        f"⏰ Время: {time}"
    )

    await bot.send_message(
        ADMIN_ID,
        admin_text
    )

    # CHANNEL NOTIFY

    await bot.send_message(
        CHANNEL_ID,
        f"📅 Новая запись:\n"
        f"{date} {time}"
    )

    await message.answer(
        "✅ Вы успешно записаны!"
    )

    await state.clear()

# =========================================================
# CANCEL
# =========================================================

@dp.callback_query(F.data == "cancel")
async def cancel(call: CallbackQuery):

    booking = await get_user_booking(
        call.from_user.id
    )

    if not booking:

        await call.message.answer(
            "❌ У вас нет активной записи."
        )

        return

    reminder_job_id = await cancel_booking_db(
        call.from_user.id
    )

    if reminder_job_id:

        try:
            scheduler.remove_job(reminder_job_id)
        except:
            pass

    await call.message.answer(
        "✅ Запись отменена."
    )

# =========================================================
# ADMIN
# =========================================================

@dp.message(Command("addslot"))
async def addslot(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    # /addslot 2026-05-10 14:00

    try:

        data = message.text.split()

        date = data[1]
        time = data[2]

        await add_slot(date, time)

        await message.answer(
            f"✅ Слот добавлен:\n"
            f"{date} {time}"
        )

    except:

        await message.answer(
            "Пример:\n"
            "/addslot 2026-05-10 14:00"
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
            "Записей пока нет."
        )

        return

    text = "<b>📅 Все записи:</b>\n\n"

    for b in bookings:

        text += (
            f"👤 {b[2]}\n"
            f"📱 {b[3]}\n"
            f"📅 {b[4]}\n"
            f"⏰ {b[5]}\n\n"
        )

    await message.answer(text)

# =========================================================
# MAIN
# =========================================================

async def main():

    await init_db()

    scheduler.start()

    await restore_reminders()

    print("BOT STARTED")

    await dp.start_polling(bot)

# =========================================================

if __name__ == "__main__":
    asyncio.run(main())

# =========================================================
# ГОТОВО
# =========================================================
#
# РЕАЛИЗОВАНО:
#
# ✅ SQLite
# ✅ FSM
# ✅ Inline кнопки
# ✅ Проверка подписки
# ✅ APScheduler
# ✅ Напоминания
# ✅ Восстановление задач
# ✅ Прайсы
# ✅ Портфолио
# ✅ Админ-панель
# ✅ Отмена записи
# ✅ Один слот на пользователя
# ✅ HTML форматирование
# ✅ Всё в одном файле
#
# =========================================================

