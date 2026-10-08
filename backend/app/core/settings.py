from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


# Resolve project directories
BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --------------------------------------------------
    # Application & Environment
    # --------------------------------------------------
    APP_NAME: str = "Surakshit Basti API"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    ACTIVE_DISTRICT: str = "wayanad"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # --------------------------------------------------
    # Database Configuration (PostgreSQL 17 + PostGIS 3.6.2)
    # --------------------------------------------------
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "surakshit_basti"
    DB_USER: str = "postgres"
    DB_PASSWORD: Optional[str] = None

    # --------------------------------------------------
    # NASA GPM IMERG NRT / PPS Configuration
    # --------------------------------------------------
    EARTHDATA_TOKEN: Optional[str] = None
    PPS_USERNAME: Optional[str] = None
    PPS_PASSWORD: Optional[str] = None
    NASA_GPM_BASE_URL: str = "https://jsimpsonhttps.pps.eosdis.nasa.gov/text/"

    # --------------------------------------------------
    # OpenStreetMap Configuration
    # --------------------------------------------------
    OSM_OVERPASS_URL: str = "https://overpass-api.de/api/interpreter"

    # --------------------------------------------------
    # AWS S3 Open Data Buckets (Public / Unsigned)
    # --------------------------------------------------
    COPERNICUS_DEM_BUCKET: str = "copernicus-dem-30m"
    ESA_WORLDCOVER_BUCKET: str = "esa-worldcover"

    # --------------------------------------------------
    # Directories
    # --------------------------------------------------
    PROJECT_ROOT_PATH: Path = PROJECT_ROOT
    DATA_PATH: Path = PROJECT_ROOT / "data"
    CONFIG_PATH: Path = PROJECT_ROOT / "config"

    @property
    def database_url(self) -> URL:
        if not self.DB_PASSWORD:
            raise ValueError("DB_PASSWORD is not configured in environment or .env file.")
        return URL.create(
            drivername="postgresql+psycopg2",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
        )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # Presence-only secret checks (no secret values exposed)
    @property
    def has_db_password(self) -> bool:
        return bool(self.DB_PASSWORD)

    @property
    def has_earthdata_token(self) -> bool:
        return bool(self.EARTHDATA_TOKEN)

    @property
    def has_pps_credentials(self) -> bool:
        return bool(self.PPS_USERNAME and self.PPS_PASSWORD)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
