from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.app.core.settings import get_settings


settings = get_settings()

# --------------------------------------------------
# Database configuration variables for compatibility
# --------------------------------------------------
DB_HOST = settings.DB_HOST
DB_PORT = str(settings.DB_PORT)
DB_NAME = settings.DB_NAME
DB_USER = settings.DB_USER
DB_PASSWORD = settings.DB_PASSWORD

# Create PostgreSQL connection URL
DATABASE_URL = settings.database_url


# --------------------------------------------------
# SQLAlchemy engine
# --------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


# --------------------------------------------------
# Database session
# --------------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# --------------------------------------------------
# Base class for database models
# --------------------------------------------------
Base = declarative_base()


# --------------------------------------------------
# Database dependency
# --------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------------------------------------------
# Test PostgreSQL + PostGIS connection
# --------------------------------------------------
def test_database_connection():
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT PostGIS_Version();")
        )
        version = result.fetchone()[0]
        return version