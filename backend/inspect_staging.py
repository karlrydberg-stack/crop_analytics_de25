import psycopg
import os

from dotenv import load_dotenv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def inspect_data():

    with psycopg.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    ) as conn:

        with conn.cursor() as cur:

            # 1. Count rows
            cur.execute("""
                SELECT COUNT(*)
                FROM staging.crops;
            """)

            print("\n--- ROW COUNT ---")
            print("Rows loaded:", cur.fetchone()[0])

            # 2. Inspect column names and data types
            cur.execute("""
                SELECT
                    ordinal_position,
                    column_name,
                    data_type
                FROM information_schema.columns
                WHERE table_schema = 'staging'
                  AND table_name = 'crops'
                ORDER BY ordinal_position;
            """)

            print("\n--- TABLE STRUCTURE ---")
            for row in cur.fetchall():
                print(row)

            # 3. Inspect sample records
            cur.execute("""
                SELECT *
                FROM staging.crops
                LIMIT 5;
            """)

            print("\n--- SAMPLE RECORDS ---")
            for row in cur.fetchall():
                print(row)


if __name__ == "__main__":
    inspect_data()
