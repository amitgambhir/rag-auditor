from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class GenerateDatasetRequest(BaseModel):
    documents: list[str] = Field(..., description="Source documents to generate Q&A from")
    num_questions: int = Field(10, ge=1, le=100, description="Number of Q&A pairs to generate")


class QAPair(BaseModel):
    question: str
    answer: str
    ground_truth: str
    contexts: list[str]
    evolution_type: Optional[str] = None


class GenerateDatasetResponse(BaseModel):
    pairs: list[QAPair]
    total: int
    source_documents: int
