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

BOT_TOKEN = "8796918085:AAHuy3GTUEyP5LEN8fDKxvo6jWZjBMHY9D0"

ADMIN_ID = 1350783137

# =========================================================
# BRAND
# =========================================================

BRAND_NAME = "SKYES STUDIO"

INSTAGRAM = "https://www.instagram.com/whenzsky?igsh=MXdjdDhsM3JkOTh2NQ%3D%3D&utm_source=qr"

PORTFOLIO = "https://t.me/+fhCkm4prLSRhZTMy"

PAYMENT_LINK = "https://yoomoney.ru/"  # ВСТАВЬ СВОЮ ССЫЛКУ

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
        "price": "2000₽"
    },

    "site": {
        "name": "Website",
        "price": "3000₽"
    },

    "design": {
        "name": "Social Media Design",
        "price": "1000₽"
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
                    text="Website — 3000₽",
                    callback_data="service_site"
                )
            ],

            [
                InlineKeyboardButton(
                    text="Social Design — 1000₽",
                    callback_data="service_design"
                )
            ]
        ]
    )

# =========================================================

def payment_keyboard(service_key):

    return InlineKeyboardMarkup(

        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="💳 Оплатить",
                    url=PAYMENT_LINK
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
        "• дизайн соцсетей\n\n"

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
        "Websites\n"
        "Social Media Design\n\n"

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
        "Website — 3000₽\n"
        "Social Media Design — 1000₽"
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

        f"Instagram:\n{INSTAGRAM}\n\n"

        "Telegram:\n"
        "@skyesstudio"
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

        "После оплаты нажмите кнопку "
        "<b>Я оплатил</b> 👇"
    )

    await call.message.answer(
        text,
        reply_markup=payment_keyboard(
            service_key
        )
    )

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

    # =====================================================
    # ADMIN NOTIFY
    # =====================================================

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

    await bot.send_message(
        ADMIN_ID,
        admin_text
    )

    # =====================================================
    # USER SUCCESS
    # =====================================================

    success_text = (

        "✅ <b>Заявка отправлена!</b>\n\n"

        "Мы получили информацию "
        "об оплате ❤️\n\n"

        "С вами скоро свяжется "
        "менеджер студии."
    )

    await call.message.answer(
        success_text
    )

# =========================================================
# MAIN
# =========================================================

async def main():

    print("SKYES STUDIO BOT STARTED")

    await dp.start_polling(bot)

# =========================================================

if __name__ == "__main__":
    asyncio.run(main())
