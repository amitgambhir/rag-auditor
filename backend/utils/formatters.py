from __future__ import annotations
from typing import Optional


def clamp_score(score: Optional[float]) -> Optional[float]:
    if score is None:
        return None
    return round(max(0.0, min(1.0, float(score))), 4)


def compute_overall_score(scores: dict[str, Optional[float]]) -> float:
    """Weighted average of numeric RAG metrics."""
    weights = {
        "faithfulness": 0.35,
        "answer_relevancy": 0.30,
        "context_precision": 0.20,
        "context_recall": 0.15,
    }
    total_weight = 0.0
    weighted_sum = 0.0
    for key, weight in weights.items():
        val = scores.get(key)
        if val is not None:
            weighted_sum += val * weight
            total_weight += weight
    if total_weight == 0:
        return 0.0
    return round(weighted_sum / total_weight, 4)


def score_to_verdict(overall_score: float, hallucination_risk: Optional[str]) -> str:
    if hallucination_risk == "high":
        return "NOT_READY"
    if overall_score >= 0.80:
        return "READY"
    if overall_score >= 0.60:
        return "NEEDS_WORK"
    return "NOT_READY"


def score_to_color(score: float) -> str:
    """Return a semantic color label for a score."""
    if score >= 0.80:
        return "green"
    if score >= 0.60:
        return "amber"
    return "red"


def format_score_pct(score: Optional[float]) -> str:
    if score is None:
        return "N/A"
    return f"{score * 100:.1f}%"
