import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.embeddings import load_embedder
from app.core.log import logger
from app.core.rerank import load_reranker

log = logger("http")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    load_embedder()
    load_reranker()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        log.exception("%s %s failed", request.method, request.url.path)
        raise
    ms = (time.perf_counter() - started) * 1000
    log.info("%s %s %s %.0fms", request.method, request.url.path, response.status_code, ms)
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/")
def root():
    return {"name": settings.app_name, "status": "ok"}
