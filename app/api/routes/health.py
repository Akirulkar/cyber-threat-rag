# app/api/routes/health.py
from fastapi import APIRouter
from app.schemas.response import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Health Check")
async def health_check():
    return HealthResponse(status="healthy")
