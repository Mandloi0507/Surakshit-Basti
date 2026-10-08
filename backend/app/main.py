from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1 import api_v1_router
from backend.app.core.logging import setup_logging
from backend.app.core.settings import get_settings
from backend.app.database import test_database_connection


settings = get_settings()
setup_logging(settings.LOG_LEVEL)

app = FastAPI(
    title=settings.APP_NAME,
    description="Proactive Relocation Intelligence for Disaster-Prone Habitations (SIH26191, MHA/NDRF)",
    version=settings.APP_VERSION,
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include versioned API routers
app.include_router(api_v1_router)


# --------------------------------------------------
# Root & Health Check Endpoints (Preserved)
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "project": "Surakshit Basti",
        "status": "running",
        "version": settings.APP_VERSION,
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