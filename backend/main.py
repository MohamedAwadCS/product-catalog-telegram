from fastapi import FastAPI
from contextlib import asynccontextmanager

from storage import pool, client, BUCKET
from routes import health, products, webhook

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = pool
    app.state.minio = client
    app.state.bucket = BUCKET
    pool.open()
    yield
    pool.close()

app = FastAPI(lifespan=lifespan)

app.include_router(health.router)
app.include_router(products.router)
app.include_router(webhook.router)