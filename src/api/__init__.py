from fastapi import APIRouter

from api.routers import health

router = APIRouter()
router.include_router(health.router)
