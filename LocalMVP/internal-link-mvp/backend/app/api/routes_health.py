from fastapi import APIRouter

router = APIRouter(tags=["健康检查"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
