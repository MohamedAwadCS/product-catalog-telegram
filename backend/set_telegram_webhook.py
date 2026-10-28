import asyncio
import os
from aiogram import Bot

async def set_webhook():
    bot = Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])
    await bot.set_webhook(url=os.environ["WEBHOOK_URL"] + "/webhook", secret_token=os.environ["WEBHOOK_SECRET"])
    await bot.session.close()


asyncio.run(set_webhook())