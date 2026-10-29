from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException, Response
from contextlib import asynccontextmanager
from psycopg_pool import ConnectionPool
import os
from minio import Minio

from aiogram import Bot, Dispatcher, F
from aiogram.types import Update, CallbackQuery

from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

url = os.environ["DATABASE_URL"]

pool = ConnectionPool(url, open=False, check=ConnectionPool.check_connection) 


client = Minio(
    endpoint=os.environ["MINIO_ENDPOINT"],
    access_key=os.environ["MINIO_ROOT_USER"],
    secret_key=os.environ["MINIO_ROOT_PASSWORD"],
    secure=False
)

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

    # i kept the message in russian because it was specified in the task requirements but you can change it to english if you want
    await message.answer("У меня есть товар", reply_markup=keyboard)

    
    

@dp.callback_query(F.data == "create_product")
async def create_product_button(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Access is not allowed")
        return

    await callback.message.answer("Send one image with the product name as its caption")
    await callback.answer()
    


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = pool
    app.state.minio = client        
    app.state.bucket = os.environ["MINIO_BUCKET"]
    pool.open()
    yield
    pool.close()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/ready")
def ready(request: Request):
    with request.app.state.pool.connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            return {"status": "ready"}

        
@app.post("/products")
def create_product(request: Request, name: str = Form(), image_unique_id: str = Form(), photo: UploadFile = File()):
    key = f"products/{image_unique_id}.jpg"

    # Checking and validating inputs
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is needed")

    if not photo.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid image type")

    request.app.state.minio.put_object(request.app.state.bucket, key, photo.file, length=photo.size, content_type=photo.content_type)
    with request.app.state.pool.connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO products (name, image_unique_id, minio_image_key) VALUES (%s, %s, %s) ON CONFLICT (image_unique_id) DO NOTHING", (name, image_unique_id, key))
    return {"status": "done"}

@app.get("/products")
def get_products(request: Request):
    with request.app.state.pool.connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name, created_at FROM products ORDER BY id DESC")
            products = cursor.fetchall()
            return {"products": [{"id": p[0], "name": p[1], "created_at": p[2]} for p in products]}


@app.get("/products/{id}/photo")
def get_product_photo(request: Request, id: int):
    with request.app.state.pool.connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT minio_image_key FROM products WHERE id = %s", (id,))
            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404)

    bucket = request.app.state.bucket
    key = result[0]
    data = request.app.state.minio.get_object(bucket, key).read()
    return Response(content=data, media_type="image/jpeg")

@app.post("/webhook")
async def webhook(request: Request):
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != os.environ["WEBHOOK_SECRET"]:
        raise HTTPException(status_code=403, detail="Invalid")
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot,update)
    return {"ok": True}


