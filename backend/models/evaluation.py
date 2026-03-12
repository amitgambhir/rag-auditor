from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field


class EvaluationRequest(BaseModel):
    question: str = Field(..., description="The user query")
    answer: str = Field(..., description="The generated answer")
    contexts: list[str] = Field(..., description="Retrieved context chunks")
    ground_truth: Optional[str] = Field(None, description="Optional reference answer")
    mode: Literal["quick", "full"] = Field("full", description="Evaluation depth")


class BatchEvaluationRequest(BaseModel):
    samples: list[EvaluationRequest]


class TraceStage(BaseModel):
    score: float
    issues: list[str] = []


class Trace(BaseModel):
    retrieval_stage: TraceStage
    generation_stage: TraceStage


class Recommendation(BaseModel):
    dimension: str
    score: float
    severity: Literal["info", "warning", "critical"]
    issue: str
    fix: str


class Scores(BaseModel):
    faithfulness: Optional[float] = None
    answer_relevancy: Optional[float] = None
    context_precision: Optional[float] = None
    context_recall: Optional[float] = None
    hallucination_risk: Optional[Literal["low", "medium", "high"]] = None


class EvaluationResponse(BaseModel):
    overall_score: float
    scores: Scores
    trace: Trace
    recommendations: list[Recommendation]
    verdict: Literal["READY", "NEEDS_WORK", "NOT_READY"]
    explanation: str


class CompareRequest(BaseModel):
    baseline: EvaluationResponse
    candidate: EvaluationResponse


class ScoreDelta(BaseModel):
    metric: str
    baseline: Optional[float]
    candidate: Optional[float]
    delta: Optional[float]
    direction: Literal["improved", "regressed", "unchanged", "na"]


class CompareResponse(BaseModel):
    deltas: list[ScoreDelta]
    summary: str
    overall_direction: Literal["improved", "regressed", "mixed", "unchanged"]
