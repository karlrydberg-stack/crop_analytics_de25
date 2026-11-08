
from sqlalchemy import text
from backend.database import engine

def test_connection():
    try:
        with engine.connect() as connection:

            result = connection.execute(
                text("SELECT version();")
            )

            print("Connection successful!")
            print(result.scalar())

            result = connection.execute(
                text("SELECT current_database(), current_user;")
            )

            database, user = result.fetchone()

            print(f"Database: {database}")
            print(f"User: {user}")

    except Exception as e:
        print(f"Connection failed: {e}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    test_connection()

