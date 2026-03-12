"""RAG Auditor — FastAPI backend entry point."""
from __future__ import annotations
import os
import time
import uuid
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from logger import configure_logging, get_logger, request_id_var  # noqa: E402
from routers.health import router as health_router  # noqa: E402
from routers.evaluate import router as evaluate_router  # noqa: E402
from routers.generate_dataset import router as dataset_router  # noqa: E402

configure_logging(os.environ.get("LOG_LEVEL", "INFO"))
_log = get_logger("rag_auditor.http")

app = FastAPI(
    title="RAG Auditor API",
    description="Production-grade RAG evaluation engine powered by RAGAS and Claude",
    version="1.0.0",
)

cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def _observability(request: Request, call_next):
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    token = request_id_var.set(rid)
    t0 = time.perf_counter()
    try:
        response = await call_next(request)
        _log.info(
            "http_request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
            },
        )
        response.headers["X-Request-ID"] = rid
        return response
    finally:
        request_id_var.reset(token)


app.include_router(health_router)
app.include_router(evaluate_router)
app.include_router(dataset_router)


@app.get("/")
async def root():
    return {
        "name": "RAG Auditor API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
