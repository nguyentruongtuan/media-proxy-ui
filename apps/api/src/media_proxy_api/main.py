from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from media_proxy_api.config import settings
from media_proxy_api.routers import health


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, openapi_url="/api/openapi.json", docs_url="/api/docs")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix="/api")
    return app


app = create_app()
