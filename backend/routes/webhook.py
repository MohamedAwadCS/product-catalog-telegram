import os
from fastapi import APIRouter, Request, HTTPException
from aiogram.types import Update

from bot import bot, dp

router = APIRouter()

@router.post("/webhook")
async def webhook(request: Request):
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != os.environ["WEBHOOK_SECRET"]:
        raise HTTPException(status_code=403, detail="Invalid")
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}