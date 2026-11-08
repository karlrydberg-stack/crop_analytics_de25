import os
import psycopg
from dotenv import load_dotenv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def create_schemas():

    with psycopg.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    ) as conn:

        with conn.cursor() as cur:

            cur.execute("""
                CREATE SCHEMA IF NOT EXISTS staging;
                CREATE SCHEMA IF NOT EXISTS warehouse;
            """)

        conn.commit()

    print("Database schemas created successfully!")


if __name__ == "__main__":
    create_schemas()