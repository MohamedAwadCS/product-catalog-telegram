import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from storage import save_product

# AIOgram bot setup
bot = Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])
dp = Dispatcher()

ADMIN_ID = int(os.environ["ADMIN_ID"])

@dp.message(CommandStart())
async def start_command(message: Message):
    button = InlineKeyboardButton(text="Catalog", web_app=WebAppInfo(url=os.environ["CATALOG_URL"]))
    rows = [[button]]

    if message.from_user.id == ADMIN_ID:
        rows.append([InlineKeyboardButton(text="Create Product", callback_data="create_product")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)

    # the reply text is required word for word by the assignment
    await message.answer("У меня есть товар", reply_markup=keyboard)


@dp.callback_query(F.data == "create_product")
async def create_product_button(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Access is not allowed")
        return

    await callback.message.answer("Send one image with the product name as its caption")
    await callback.answer()