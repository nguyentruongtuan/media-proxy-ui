from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from media_proxy_api.config import settings
from media_proxy_api.db import get_database
from media_proxy_api.repositories.urls import MongoUrlRepository
from media_proxy_api.routers import health, urls


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await MongoUrlRepository(get_database()).ensure_indexes()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix="/api")
    app.include_router(urls.router, prefix="/api")
    return app


app = create_app()
