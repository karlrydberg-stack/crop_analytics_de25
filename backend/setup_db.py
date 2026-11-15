# --- Database setup --- 
""" Creates:
- schemas staging, cleaned, warehouse and chatbot
- and read-only users (streamlit_reader and chatbot_reader)
- runs as the admin user (cropadmin), as the first step of the pipeline.
"""

import os

import psycopg
from dotenv import load_dotenv
from pathlib import Path
from psycopg import sql

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

# --- User name with env variables --- 
READ_ONLY_USERS = {
    "streamlit_reader": ("STREAMLIT_READER_PASSWORD", "warehouse"),
    "chatbot_reader": ("CHATBOT_READER_PASSWORD", "chatbot"),
}

# --- Connect as the admin user (same settings as before, plus sslmode for Azure) --- 
def connect():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        sslmode=os.getenv("POSTGRES_SSLMODE", "prefer"),
        autocommit=True,
    )

def create_schemas(conn):
    conn.execute("""
        CREATE SCHEMA IF NOT EXISTS staging;
        CREATE SCHEMA IF NOT EXISTS cleaned;
        CREATE SCHEMA IF NOT EXISTS warehouse;
        CREATE SCHEMA IF NOT EXISTS chatbot;
    """)
    print("Database schemas created successfully!")


# --- 2 users (streamlit_reader and chabot_reader) that can only read ---
# --- Help from LLM ---
def create_read_only_users(conn):

# --- Loop through the users to read their password  ---
    for user, (password_variable, schema) in READ_ONLY_USERS.items():
        password = os.environ[password_variable]

# --- Here sql.Identifier() tells psycopg: “this is a name” and psycopg can write it correctly as a "name" ---
        user_id, schema_id = sql.Identifier(user), sql.Identifier(schema)

# --- Checking in Postgres if user already exists, if so no error (using update instead of CREATE) ---
        exists = conn.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (user,)).fetchone()
        action = "ALTER" if exists else "CREATE"
# --- Create/update the user: allowed to log in, with password ---
        conn.execute(sql.SQL(action + " ROLE {} LOGIN PASSWORD {}").format(user_id, sql.Literal(password)))

# --- Every session of this user is read-only ---
        conn.execute(sql.SQL("ALTER ROLE {} SET default_transaction_read_only = on").format(user_id))
# --- Let the user enter its schema, othewrwise cannot read anything ---
        conn.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(schema_id, user_id))
# --- Can read ALL tables, existing and futures eventually ---
        conn.execute(sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA {} TO {}").format(schema_id, user_id))
        conn.execute(sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA {} GRANT SELECT ON TABLES TO {}").format(schema_id, user_id))

# --- Safety: Chatbot's query can run max 5 sec ---
    conn.execute("ALTER ROLE chatbot_reader SET statement_timeout = '5s'")
    print("Read-only users created successfully!")

# --- Run schemas first, then the users
def setup_db():
    with connect() as conn:
        create_schemas(conn)
        create_read_only_users(conn)


if __name__ == "__main__":
    setup_db()