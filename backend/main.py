"""RAG Auditor — FastAPI backend entry point."""
from __future__ import annotations
import logging
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from routers.evaluate import router as evaluate_router  # noqa: E402
from routers.generate_dataset import router as dataset_router  # noqa: E402
from routers.health import router as health_router  # noqa: E402

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

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
