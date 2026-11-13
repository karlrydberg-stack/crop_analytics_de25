
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Keep Docker/OS environment variables authoritative.
load_dotenv(PROJECT_ROOT / ".env")

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    host=os.getenv("POSTGRES_HOST"),
    port=int(os.getenv("POSTGRES_PORT", "5432")),
    database=os.getenv("POSTGRES_DB"),
    query={
        "sslmode": os.getenv("POSTGRES_SSLMODE", "prefer"),
    },
)

engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
)
