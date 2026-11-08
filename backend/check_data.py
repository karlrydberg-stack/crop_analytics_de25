from unittest import result

from sqlalchemy import text
from backend.database import engine
from sqlalchemy import text

def main():
    with engine.connect() as connection:

        # Check whether the table exists
        table_exists = connection.execute(text("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'staging'
                  AND table_name = 'crops'
            );
        """)).scalar()

        if not table_exists:
            print("Table staging.crops does not exist.")
            return

        # Count rows
        row_count = connection.execute(text("""
            SELECT COUNT(*)
            FROM staging.crops;
        """)).scalar()

                    # Inspect column names and data types
        result = connection.execute(text("""
            SELECT
                ordinal_position,
                column_name,
                data_type
            FROM information_schema.columns
            WHERE table_schema = 'staging'
            AND table_name = 'crops'
            ORDER BY ordinal_position;
        """))

        print("\n--- TABLE STRUCTURE ---")
        for row in result:
            print(row)

        print(f"Table found: staging.crops")
        print(f"Number of rows: {row_count}")

        # Inspect a few records
        sample = connection.execute(text("""
            SELECT *
            FROM staging.crops
            LIMIT 5;
        """))

        print("\nSample records:")
        for row in sample:
            print(row)

if __name__ == "__main__":
    main()