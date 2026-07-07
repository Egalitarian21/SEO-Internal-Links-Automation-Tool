from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_articles import router as articles_router
from app.api.routes_health import router as health_router
from app.api.routes_internal_linking import router as internal_linking_router
from app.api.routes_pages import dashboard_router, router as pages_router
from app.api.routes_snapshots import router as snapshots_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="SEO 内链 MVP API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/api")
    app.include_router(dashboard_router, prefix="/api")
    app.include_router(pages_router, prefix="/api")
    app.include_router(articles_router, prefix="/api")
    app.include_router(internal_linking_router, prefix="/api")
    app.include_router(snapshots_router, prefix="/api")
    return app


app = create_app()
