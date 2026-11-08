
from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.database import engine

app = FastAPI(
    title="Crop Analytics API",
    description="Backend API for crop analytics",
    version="1.0.0"
)


@app.get("/")
def root():
    return {"message": "Welcome to Crop Analytics API"}


@app.get("/health")
def health_check():

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected"
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "disconnected"
            }
        )
