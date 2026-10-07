from fastapi import FastAPI

from backend.app.database import test_database_connection


app = FastAPI(
    title="Surakshit Basti API",
    description="Proactive Relocation Intelligence for Disaster-Prone Habitations",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "project": "Surakshit Basti",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/health/db")
def database_health():
    postgis_version = test_database_connection()

    return {
        "database": "connected",
        "postgis_version": postgis_version,
    }