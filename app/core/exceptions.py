# app/core/exceptions.py
from fastapi import Request, status
from fastapi.responses import JSONResponse


class RAGPipelineException(Exception):
    """Base exception for RAG processing errors."""

    def __init__(
        self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class VectorStoreNotFoundError(RAGPipelineException):
    """Raised when FAISS or SQLite database is missing."""

    def __init__(
        self, message: str = "Vector store index not found. Please run indexing first."
    ):
        super().__init__(
            message=message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class ModelInferenceError(RAGPipelineException):
    """Raised when NVIDIA NIM or LLM invocation fails."""

    def __init__(self, message: str = "LLM service unavailable or API key invalid."):
        super().__init__(message=message, status_code=status.HTTP_502_BAD_GATEWAY)


async def rag_exception_handler(request: Request, exc: RAGPipelineException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "path": str(request.url.path),
        },
    )
