from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes import router as api_router
from src.infrastructure.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="Events Aggregator",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router)
