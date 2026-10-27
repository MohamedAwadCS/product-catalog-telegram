from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from psycopg_pool import ConnectionPool
import os

url = os.environ["DATABASE_URL"]

pool = ConnectionPool(url, open=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = pool
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