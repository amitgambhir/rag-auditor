"""Evaluation endpoints — single, batch, streaming SSE, and compare."""
from __future__ import annotations
import asyncio
import json
import logging
import os
import time
from collections import OrderedDict
from typing import AsyncGenerator
from uuid import uuid4

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from models.evaluation import (
    BatchEvaluationRequest,
    CompareRequest,
    CompareResponse,
    EvaluationRequest,
    EvaluationResponse,
    ScoreDelta,
    Scores,
)
from services.llm_judge import detect_hallucination, generate_explanation
from services.ragas_evaluator import stream_ragas_evaluation
from services.trace_analyzer import analyze_trace, generate_recommendations
from utils.formatters import clamp_score, compute_overall_score, score_to_verdict

router = APIRouter(prefix="/evaluate", tags=["evaluate"])
logger = logging.getLogger(__name__)

HISTORY_MAX_SIZE = int(os.environ.get("EVALUATION_HISTORY_MAX_SIZE", "200"))
HISTORY_TTL_SECONDS = int(os.environ.get("EVALUATION_HISTORY_TTL_SECONDS", "3600"))

# In-memory evaluation history for the session, bounded by max size + TTL.
_history: OrderedDict[str, tuple[float, EvaluationResponse]] = OrderedDict()


def _prune_history(now: float | None = None) -> None:
    ts = now if now is not None else time.time()

    expired_keys = [
        key for key, (created_at, _) in _history.items()
        if ts - created_at > HISTORY_TTL_SECONDS
    ]
    for key in expired_keys:
        _history.pop(key, None)

    while len(_history) > HISTORY_MAX_SIZE:
        _history.popitem(last=False)


def _store_history(result: EvaluationResponse) -> None:
    _prune_history()
    _history[uuid4().hex] = (time.time(), result)
    _prune_history()


async def _run_full_evaluation(req: EvaluationRequest) -> tuple[dict, dict]:
    """Run RAGAS metrics and hallucination check in parallel."""
    start = time.perf_counter()
    ragas_task = asyncio.create_task(_collect_ragas_scores(req))
    hallucination_task = asyncio.create_task(
        detect_hallucination(req.question, req.answer, req.contexts)
    )
    scores_raw, hallucination = await asyncio.gather(ragas_task, hallucination_task)
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    logger.info(
        "event=evaluation_finished route=evaluate elapsed_ms=%s mode=%s contexts=%s",
        elapsed_ms,
        req.mode,
        len(req.contexts),
    )
    return scores_raw, hallucination


async def _collect_ragas_scores(req: EvaluationRequest) -> dict:
    scores: dict = {}
    async for event in stream_ragas_evaluation(
        req.question, req.answer, req.contexts, req.ground_truth, req.mode
    ):
        if event.get("type") == "scores":
            scores = event.get("scores", {})
    return scores


def _build_response(
    req: EvaluationRequest,
    raw_scores: dict,
    hallucination: dict,
    explanation: str,
) -> EvaluationResponse:
    scores_clean = {k: clamp_score(v) for k, v in raw_scores.items()}
    overall = compute_overall_score(scores_clean)
    risk = hallucination.get("risk_level", "medium")
    verdict = score_to_verdict(overall, risk)

    trace = analyze_trace(scores_clean, req.contexts, req.question, req.answer)
    recs_raw = generate_recommendations(scores_clean)

    from models.evaluation import Recommendation
    recs = [Recommendation(**r) for r in recs_raw]

    return EvaluationResponse(
        overall_score=overall,
        scores=Scores(
            faithfulness=scores_clean.get("faithfulness"),
            answer_relevancy=scores_clean.get("answer_relevancy"),
            context_precision=scores_clean.get("context_precision"),
            context_recall=scores_clean.get("context_recall"),
            hallucination_risk=risk,
        ),
        trace=trace,
        recommendations=recs,
        verdict=verdict,
        explanation=explanation,
    )


@router.post("", response_model=EvaluationResponse)
async def evaluate(req: EvaluationRequest) -> EvaluationResponse:
    """Run a full RAG evaluation. Returns when all metrics are complete."""
    raw_scores, hallucination = await _run_full_evaluation(req)
    scores_clean = {k: clamp_score(v) for k, v in raw_scores.items()}
    recs_raw = generate_recommendations(scores_clean)
    explanation = await generate_explanation(
        {**scores_clean, "hallucination_risk": hallucination.get("risk_level")},
        recs_raw,
    )
    result = _build_response(req, raw_scores, hallucination, explanation)
    _store_history(result)
    return result


@router.post("/stream")
async def evaluate_stream(req: EvaluationRequest):
    """SSE endpoint — streams progress events then a final result event."""

    async def event_generator() -> AsyncGenerator[dict, None]:
        scores: dict = {}
        hallucination: dict = {}

        # Start hallucination check in parallel with RAGAS
        hallucination_task = asyncio.create_task(
            detect_hallucination(req.question, req.answer, req.contexts)
        )

        # Stream RAGAS metric progress
        async for event in stream_ragas_evaluation(
            req.question, req.answer, req.contexts, req.ground_truth, req.mode
        ):
            if event.get("type") == "scores":
                scores = event.get("scores", {})
            yield {"data": json.dumps(event)}

        # Get hallucination result
        yield {
            "data": json.dumps(
                {"type": "progress", "message": "Running hallucination check..."}
            )
        }
        try:
            hallucination = await hallucination_task
        except Exception as exc:
            logger.warning(
                "event=hallucination_fallback route=evaluate_stream fallback=default_medium error=%s",
                exc,
            )
            hallucination = {"risk_level": "medium"}

        # Generate explanation
        yield {
            "data": json.dumps(
                {"type": "progress", "message": "Generating explanation..."}
            )
        }
        scores_clean = {k: clamp_score(v) for k, v in scores.items()}
        recs_raw = generate_recommendations(scores_clean)
        explanation = await generate_explanation(
            {**scores_clean, "hallucination_risk": hallucination.get("risk_level")},
            recs_raw,
        )

        result = _build_response(req, scores, hallucination, explanation)
        _store_history(result)
        yield {"data": json.dumps({"type": "result", "data": result.model_dump()})}
        yield {"data": "[DONE]"}

    return EventSourceResponse(event_generator())


@router.post("/batch")
async def evaluate_batch(req: BatchEvaluationRequest):
    """Evaluate multiple RAG samples and return aggregate + per-sample results."""
    results = []
    errors = []

    async def eval_one(sample: EvaluationRequest, idx: int):
        try:
            raw_scores, hallucination = await _run_full_evaluation(sample)
            scores_clean = {k: clamp_score(v) for k, v in raw_scores.items()}
            recs_raw = generate_recommendations(scores_clean)
            explanation = await generate_explanation(
                {**scores_clean, "hallucination_risk": hallucination.get("risk_level")},
                recs_raw,
            )
            result = _build_response(sample, raw_scores, hallucination, explanation)
            _store_history(result)
            return idx, result, None
        except Exception as exc:
            logger.exception("event=batch_eval_error sample_index=%s", idx)
            return idx, None, str(exc)

    tasks = [eval_one(sample, i) for i, sample in enumerate(req.samples)]
    task_results = await asyncio.gather(*tasks)

    ordered_results = [None] * len(req.samples)
    for idx, result, error in task_results:
        if error:
            errors.append({"index": idx, "error": error})
        else:
            ordered_results[idx] = result
            results.append(result)

    if not results:
        return {"error": "All evaluations failed", "details": errors}

    # Aggregate scores
    agg: dict = {}
    metric_keys = [
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
        "overall_score",
    ]
    for key in metric_keys:
        vals = []
        for r in results:
            if r is None:
                continue
            val = r.overall_score if key == "overall_score" else getattr(r.scores, key, None)
            if val is not None:
                vals.append(val)
        agg[key] = round(sum(vals) / len(vals), 4) if vals else None

    verdicts = [r.verdict for r in results if r]
    verdict_counts = {v: verdicts.count(v) for v in set(verdicts)}

    return {
        "aggregate": agg,
        "verdict_distribution": verdict_counts,
        "total_samples": len(req.samples),
        "successful": len(results),
        "failed": len(errors),
        "results": [r.model_dump() if r else None for r in ordered_results],
        "errors": errors,
    }


@router.post("/compare", response_model=CompareResponse)
async def compare(req: CompareRequest) -> CompareResponse:
    """Compare two evaluation results and return metric deltas."""
    baseline = req.baseline
    candidate = req.candidate

    metric_keys = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    deltas: list[ScoreDelta] = []

    for key in metric_keys:
        b_val = getattr(baseline.scores, key, None)
        c_val = getattr(candidate.scores, key, None)

        if b_val is None and c_val is None:
            direction = "na"
            delta = None
        elif b_val is None or c_val is None:
            direction = "na"
            delta = None
        else:
            delta = round(c_val - b_val, 4)
            if abs(delta) < 0.01:
                direction = "unchanged"
            elif delta > 0:
                direction = "improved"
            else:
                direction = "regressed"

        deltas.append(
            ScoreDelta(
                metric=key,
                baseline=b_val,
                candidate=c_val,
                delta=delta,
                direction=direction,
            )
        )

    # Overall delta
    overall_delta = round(candidate.overall_score - baseline.overall_score, 4)
    deltas.append(
        ScoreDelta(
            metric="overall_score",
            baseline=baseline.overall_score,
            candidate=candidate.overall_score,
            delta=overall_delta,
            direction=(
                "improved"
                if overall_delta > 0.01
                else "regressed" if overall_delta < -0.01 else "unchanged"
            ),
        )
    )

    improved = [d for d in deltas if d.direction == "improved"]
    regressed = [d for d in deltas if d.direction == "regressed"]

    if len(improved) > len(regressed):
        overall_direction = "improved"
    elif len(regressed) > len(improved):
        overall_direction = "regressed"
    elif improved and regressed:
        overall_direction = "mixed"
    else:
        overall_direction = "unchanged"

    pct = abs(overall_delta) * 100
    if overall_direction == "improved":
        summary = f"Your changes improved overall RAG quality by {pct:.1f}%. "
    elif overall_direction == "regressed":
        summary = f"Your changes reduced overall RAG quality by {pct:.1f}%. "
    elif overall_direction == "mixed":
        best = max(improved, key=lambda d: d.delta or 0)
        worst = min(regressed, key=lambda d: d.delta or 0)
        summary = (
            f"Mixed results: {best.metric} improved by {(best.delta or 0) * 100:.1f}% "
            f"but {worst.metric} regressed by {abs(worst.delta or 0) * 100:.1f}%. "
        )
    else:
        summary = "No significant change in RAG quality. "

    if improved:
        summary += f"Improved: {', '.join(d.metric for d in improved)}."
    if regressed:
        summary += f" Regressed: {', '.join(d.metric for d in regressed)}."

    return CompareResponse(
        deltas=deltas,
        summary=summary.strip(),
        overall_direction=overall_direction,
    )
