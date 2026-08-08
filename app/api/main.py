# app/api/main.py
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.logger import logger  # Using your existing app/core/logger.py
from app.core.exceptions import RAGPipelineException, rag_exception_handler
from app.api.routes import query, health, stats

app = FastAPI(
    title=settings.APP_NAME,
    description="Cybersecurity Threat Intelligence RAG Backend Engine",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Exception Handler Registration
app.add_exception_handler(RAGPipelineException, rag_exception_handler)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Timing & Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time

    # Log execution stats
    logger.info(
        f"Method: {request.method} | Path: {request.url.path} | "
        f"Status: {response.status_code} | Duration: {duration:.4f}s"
    )
    response.headers["X-Process-Time"] = str(duration)
    return response


# Register Routes
app.include_router(health.router, tags=["Health"])
app.include_router(query.router, tags=["RAG Services"])
app.include_router(stats.router, tags=["Analytics"])
