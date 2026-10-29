import os
from pathlib import Path
import psycopg
from minio import Minio

text = Path(__file__).parent.parent.joinpath("schema.sql").read_text()
db_url = os.environ["DATABASE_URL"]

with psycopg.connect(db_url) as connection:
    connection.execute(text)

client = Minio(
    endpoint=os.environ["MINIO_ENDPOINT"],
    access_key=os.environ["MINIO_ROOT_USER"],
    secret_key=os.environ["MINIO_ROOT_PASSWORD"],
    secure=False
)

bucket_name = os.environ["MINIO_BUCKET"]

if not client.bucket_exists(bucket_name):
    client.make_bucket(bucket_name)