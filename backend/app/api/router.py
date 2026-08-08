from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.readiness import router as readiness_router
from app.api.routes.repositories import router as repositories_router
from app.api.routes.scans import router as scans_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(readiness_router)
api_router.include_router(repositories_router)
api_router.include_router(scans_router)
