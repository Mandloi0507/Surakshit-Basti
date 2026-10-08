from fastapi import APIRouter

from backend.app.api.v1.assignments import router as assignments_router
from backend.app.api.v1.cells import router as cells_router
from backend.app.api.v1.habitations import router as habitations_router
from backend.app.api.v1.scenarios import router as scenarios_router
from backend.app.api.v1.seed import router as seed_router
from backend.app.api.v1.sites import router as sites_router
from backend.app.api.v1.status import router as status_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(status_router)
api_v1_router.include_router(cells_router)
api_v1_router.include_router(habitations_router)
api_v1_router.include_router(sites_router)
api_v1_router.include_router(scenarios_router)
api_v1_router.include_router(assignments_router)
api_v1_router.include_router(seed_router)
