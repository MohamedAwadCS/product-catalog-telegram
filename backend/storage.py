from psycopg_pool import ConnectionPool
import os
from minio import Minio

url = os.environ["DATABASE_URL"]

pool = ConnectionPool(url, open=False, check=ConnectionPool.check_connection)

client = Minio(
    endpoint=os.environ["MINIO_ENDPOINT"],
    access_key=os.environ["MINIO_ROOT_USER"],
    secret_key=os.environ["MINIO_ROOT_PASSWORD"],
    secure=False
)

BUCKET = os.environ["MINIO_BUCKET"]

def save_product(name, image_unique_id, file, size):
    key = f"products/{image_unique_id}.jpg"
    client.put_object(BUCKET, key, file, length=size, content_type="image/jpeg")
    with pool.connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO products (name, image_unique_id, minio_image_key) VALUES (%s, %s, %s) ON CONFLICT (image_unique_id) DO NOTHING", (name, image_unique_id, key))