from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import cards, drafts, imports, projects, publish, review, suggestions, tasks


app = FastAPI(
    title="Internal Linking Tool Demo API",
    version="0.1.0",
    description="A demo backend for the Internal Linking Tool v1 workbench.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(imports.router, prefix="/api", tags=["imports"])
app.include_router(drafts.router, prefix="/api", tags=["drafts"])
app.include_router(cards.router, prefix="/api", tags=["cards"])
app.include_router(suggestions.router, prefix="/api", tags=["suggestions"])
app.include_router(review.router, prefix="/api", tags=["review"])
app.include_router(publish.router, prefix="/api", tags=["publish"])
app.include_router(tasks.router, prefix="/api", tags=["tasks"])


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}

