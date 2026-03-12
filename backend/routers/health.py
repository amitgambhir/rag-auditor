from fastapi import APIRouter
import os

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "anthropic_key_set": bool(os.environ.get("ANTHROPIC_API_KEY")),
    }
