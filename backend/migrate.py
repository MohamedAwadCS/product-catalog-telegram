import os
from pathlib import Path
import psycopg

text = Path(__file__).parent.joinpath("schema.sql").read_text()
db_url = os.environ["DATABASE_URL"]

with psycopg.connect(db_url) as connection:
    connection.execute(text)