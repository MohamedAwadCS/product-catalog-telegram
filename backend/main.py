from fastapi import FastAPI, Request, Form, UploadFile, File
from contextlib import asynccontextmanager
from psycopg_pool import ConnectionPool
import os
from minio import Minio

url = os.environ["DATABASE_URL"]

pool = ConnectionPool(url, open=False) 

client = Minio(
    endpoint=os.environ["MINIO_ENDPOINT"],
    access_key=os.environ["MINIO_ROOT_USER"],
    secret_key=os.environ["MINIO_ROOT_PASSWORD"],
    secure=False
)

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
    request.app.state.minio.put_object(request.app.state.bucket, key, photo.file, length=photo.size, content_type=photo.content_type)
    with request.app.state.pool.connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO products (name, image_unique_id, minio_image_key) VALUES (%s, %s, %s) ON CONFLICT (image_unique_id) DO NOTHING", (name, image_unique_id, key))
    return {"status": "done"}



