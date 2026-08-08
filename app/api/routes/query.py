from fastapi import APIRouter, Depends, status
from app.schemas.request import QueryRequest
from app.schemas.response import QueryResponse
from app.services.rag_service import rag_service
from app.core.auth import verify_api_key

router = APIRouter()


@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_api_key)],
    summary="Query Threat Intelligence RAG",
)
async def process_query(payload: QueryRequest):
    return await rag_service.execute_query(payload)
