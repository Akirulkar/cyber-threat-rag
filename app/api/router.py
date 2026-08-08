from fastapi import APIRouter
from app.api.routes import query, health, stats

api_router = APIRouter()

api_router.include_router(query.router, tags=["RAG Interface"])
api_router.include_router(health.router, tags=["Monitoring"])
api_router.include_router(stats.router, tags=["Monitoring"])
