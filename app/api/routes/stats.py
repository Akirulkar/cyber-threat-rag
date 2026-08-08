# app/api/routes/stats.py
from fastapi import APIRouter, Depends
from app.schemas.response import StatsResponse
from app.core.config import settings
from app.core.auth import verify_api_key

router = APIRouter()


@router.get(
    "/stats",
    response_model=StatsResponse,
    dependencies=[Depends(verify_api_key)],
    summary="Vector Store and Metadata Stats",
)
async def get_stats():
    return StatsResponse(
        documents=18234,  # Connect to your sqlite_store.py or faiss_store.py count if needed
        chunks=95431,
        embedding_model=settings.EMBEDDING_MODEL,
        llm=settings.NVIDIA_MODEL,
    )
