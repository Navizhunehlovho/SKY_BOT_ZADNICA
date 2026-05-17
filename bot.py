# =========================================================
# SKYES STUDIO BOT
# PREMIUM DIGITAL STUDIO BOT
# bot.py
# =========================================================

import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command

from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    CallbackQuery
)

from aiogram.client.default import DefaultBotProperties

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = "8796918085:AAF9iveq6vX-Bx50eh2SHK5GkvfgPmdr-0E"

# =========================================================
# ADMINS
# =========================================================

ADMIN_IDS = [
    1350783137,
    1130643805
]

# =========================================================
# BRAND
# =========================================================

BRAND_NAME = "SKIES STUDIO"

PORTFOLIO = "https://t.me/wnenzskyyy"

MANAGER_USERNAME = "stpphout"

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO
)

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

# =========================================================
# SERVICES
# =========================================================

SERVICES = {

    "bot": {
        "name": "🤖 Telegram Bot",
        "price": "2000₽",
        "manager_link":
        "https://t.me/stpphout?text=Здравствуйте%20хочу%20заказать%20Telegram%20Bot"
    },

    "site": {
        "name": "🌐 Website",
        "price": "3000₽",
        "manager_link":
        "https://t.me/stpphout?text=Здравствуйте%20хочу%20заказать%20Website"
    },

    "design": {
        "name": "🎨 Social Media Design",
        "price": "1000₽",
        "manager_link":
        "https://t.me/stpphout?text=Здравствуйте%20хочу%20заказать%20Social%20Media%20Design"
    },

    "install": {
        "name": "🛠 Установка",
        "price": "500₽",
        "manager_link":
        "https://t.me/stpphout?text=Здравствуйте%20хочу%20заказать%20Установку"
    },

    "image": {
        "name": "🖼 Одно изображение",
        "price": "250₽",
        "manager_link":
        "https://t.me/stpphout?text=Здравствуйте%20хочу%20заказать%20Изображение"
    },

    "complex_image": {
        "name": "🎨 Сложное изображение",
        "price": "300₽",
        "manager_link":
        "https://t.me/stpphout?text=Здравствуйте%20хочу%20заказать%20Сложное%20изображение"
    }
}

# =========================================================
# KEYBOARDS
# =========================================================

def main_menu():

    return ReplyKeyboardMarkup(

        keyboard=[

            [
                KeyboardButton(text="💼 Услуги"),
                KeyboardButton(text="💰 Прайс")
            ],

            [
                KeyboardButton(text="🖼 Портфолио"),
                KeyboardButton(text="📞 Контакты")
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
                    text="🤖 Telegram Bot — 2000₽",
                    callback_data="service_bot"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🌐 Website — 3000₽",
                    callback_data="service_site"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🎨 Social Design — 1000₽",
                    callback_data="service_design"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🛠 Установка — 500₽",
                    callback_data="service_install"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🖼 Одно изображение — 250₽",
                    callback_data="service_image"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🎨 Сложное изображение — 300₽",
                    callback_data="service_complex_image"
                )
            ]
        ]
    )

# =========================================================

def payment_keyboard(service_key):

    service = SERVICES[service_key]

    return InlineKeyboardMarkup(

        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="💳 Оплатить",
                    url=service["manager_link"]
                )
            ],

            [
                InlineKeyboardButton(
                    text="✅ Я оплатил",
                    callback_data=f"paid_{service_key}"
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

        f"🚀 <b>{BRAND_NAME}</b>\n\n"

        "Premium digital studio.\n\n"

        "Мы создаём:\n"
        "• Telegram-ботов\n"
        "• сайты\n"
        "• дизайн соцсетей\n"
        "• установку\n"
        "• изображения\n\n"

        "Выберите действие ниже 👇"
    )

    await message.answer(
        text,
        reply_markup=main_menu()
    )

# =========================================================
# SERVICES
# =========================================================

@dp.message(F.text == "💼 Услуги")
async def services(message: Message):

    text = (

        "💼 <b>Наши услуги</b>\n\n"

        "🤖 Telegram Bots\n"
        "🌐 Websites\n"
        "🎨 Social Media Design\n"
        "🛠 Установка\n"
        "🖼 Одно изображение\n"
        "🎨 Сложное изображение\n\n"

        "Выберите услугу ниже 👇"
    )

    await message.answer(
        text,
        reply_markup=services_keyboard()
    )

# =========================================================
# PRICE
# =========================================================

@dp.message(F.text == "💰 Прайс")
async def prices(message: Message):

    text = (

        "💰 <b>Прайс-лист</b>\n\n"

        "🤖 Telegram Bot — 2000₽\n"
        "🌐 Website — 3000₽\n"
        "🎨 Social Media Design — 1000₽\n"
        "🛠 Установка — 500₽\n"
        "🖼 Одно изображение — 250₽\n"
        "🎨 Сложное изображение — 300₽"
    )

    await message.answer(text)

# =========================================================
# PORTFOLIO
# =========================================================

@dp.message(F.text == "🖼 Портфолио")
async def portfolio(message: Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Смотреть работы",
                    url=PORTFOLIO
                )
            ]
        ]
    )

    await message.answer(
        "🖼 <b>Портфолио студии</b>",
        reply_markup=keyboard
    )

# =========================================================
# CONTACTS
# =========================================================

@dp.message(F.text == "📞 Контакты")
async def contacts(message: Message):

    text = (

        "📞 <b>Контакты</b>\n\n"

        f"Менеджер:\n@{MANAGER_USERNAME}"
    )

    await message.answer(text)

# =========================================================
# SERVICE SELECT
# =========================================================

@dp.callback_query(F.data.startswith("service_"))
async def choose_service(call: CallbackQuery):

    service_key = call.data.replace(
        "service_",
        ""
    )

    service = SERVICES[service_key]

    text = (

        f"💎 <b>{service['name']}</b>\n\n"

        f"💰 Стоимость: {service['price']}\n\n"

        "Для оплаты и обсуждения проекта "
        "нажмите кнопку ниже 👇"
    )

    await call.message.answer(
        text,
        reply_markup=payment_keyboard(
            service_key
        )
    )

    await call.answer()

# =========================================================
# PAYMENT CONFIRM
# =========================================================

@dp.callback_query(F.data.startswith("paid_"))
async def payment_confirm(call: CallbackQuery):

    service_key = call.data.replace(
        "paid_",
        ""
    )

    service = SERVICES[service_key]

    admin_text = (

        "🆕 <b>НОВАЯ ЗАЯВКА</b>\n\n"

        f"👤 USER ID: {call.from_user.id}\n"

        f"📨 USERNAME: "
        f"@{call.from_user.username}\n\n"

        f"💼 Услуга:\n"
        f"{service['name']}\n\n"

        f"💰 Цена:\n"
        f"{service['price']}"
    )

    for admin_id in ADMIN_IDS:

        try:

            await bot.send_message(
                admin_id,
                admin_text
            )

        except Exception as e:
            print(e)

    success_text = (

        "✅ <b>Заявка отправлена!</b>\n\n"

        "Менеджер уже получил "
        "информацию ❤️\n\n"

        "Ожидайте ответ в Telegram."
    )

    await call.message.answer(
        success_text
    )

    await call.answer()

# =========================================================
# MAIN
# =========================================================

async def main():

    print("SKYES STUDIO BOT STARTED")

    await dp.start_polling(bot)

# =========================================================

if __name__ == "__main__":
    asyncio.run(main())
