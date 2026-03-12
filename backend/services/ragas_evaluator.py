"""RAGAS-based evaluation of RAG pipeline metrics."""
from __future__ import annotations
import asyncio
import os
from typing import Optional, AsyncGenerator
from functools import partial

import config


async def _run_in_executor(fn, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(fn, *args))


def _build_judge_llm():
    from ragas.llms import LangchainLLMWrapper
    from langchain_anthropic import ChatAnthropic
    return LangchainLLMWrapper(
        ChatAnthropic(
            model=config.ANTHROPIC_MODEL,
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        )
    )


def _run_ragas_sync(
    question: str,
    answer: str,
    contexts: list[str],
    ground_truth: Optional[str],
    mode: str,
) -> dict:
    """Run RAGAS evaluation synchronously (called in executor)."""
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    )

    judge_llm = _build_judge_llm()
    faithfulness.llm = judge_llm
    answer_relevancy.llm = judge_llm
    context_precision.llm = judge_llm
    context_recall.llm = judge_llm

    data: dict = {
        "question": [question],
        "answer": [answer],
        "contexts": [contexts],
    }
    metrics_to_run = [faithfulness, answer_relevancy, context_precision]

    if ground_truth:
        data["ground_truth"] = [ground_truth]
        metrics_to_run.append(context_recall)

    dataset = Dataset.from_dict(data)
    result = evaluate(dataset, metrics=metrics_to_run, raise_exceptions=False)
    scores_df = result.to_pandas()

    out: dict = {}
    score_map = {
        "faithfulness": "faithfulness",
        "answer_relevancy": "answer_relevancy",
        "context_precision": "context_precision",
        "context_recall": "context_recall",
    }
    for col, key in score_map.items():
        if col in scores_df.columns:
            val = scores_df[col].iloc[0]
            if val is not None and not (isinstance(val, float) and val != val):
                out[key] = float(val)

    return out


async def run_ragas_evaluation(
    question: str,
    answer: str,
    contexts: list[str],
    ground_truth: Optional[str],
    mode: str = "full",
) -> dict:
    """Async wrapper around RAGAS evaluation."""
    try:
        scores = await _run_in_executor(
            _run_ragas_sync, question, answer, contexts, ground_truth, mode
        )
        return {"scores": scores, "error": None}
    except Exception as exc:
        return {"scores": {}, "error": str(exc)}


async def stream_ragas_evaluation(
    question: str,
    answer: str,
    contexts: list[str],
    ground_truth: Optional[str],
    mode: str = "full",
) -> AsyncGenerator[dict, None]:
    """
    Yield progress SSE events, then yield final scores.
    Runs metrics sequentially to stream individual updates.
    """
    metrics_config = [
        ("faithfulness", "Checking answer faithfulness..."),
        ("answer_relevancy", "Measuring answer relevancy..."),
        ("context_precision", "Evaluating context precision..."),
    ]
    if ground_truth:
        metrics_config.append(("context_recall", "Computing context recall..."))

    yield {"type": "progress", "message": "Initializing evaluation engine...", "step": 0, "total": len(metrics_config) + 1}

    scores: dict = {}

    for idx, (metric_name, message) in enumerate(metrics_config):
        yield {"type": "progress", "message": message, "step": idx + 1, "total": len(metrics_config) + 1}
        try:
            result = await _run_in_executor(
                _run_single_metric, metric_name, question, answer, contexts, ground_truth
            )
            scores[metric_name] = result
        except Exception:
            scores[metric_name] = None

    yield {"type": "progress", "message": "Finalizing scores...", "step": len(metrics_config) + 1, "total": len(metrics_config) + 1}
    yield {"type": "scores", "scores": scores}


def _run_single_metric(
    metric_name: str,
    question: str,
    answer: str,
    contexts: list[str],
    ground_truth: Optional[str],
) -> Optional[float]:
    """Run a single RAGAS metric synchronously."""
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    )

    metric_map = {
        "faithfulness": faithfulness,
        "answer_relevancy": answer_relevancy,
        "context_precision": context_precision,
        "context_recall": context_recall,
    }
    metric = metric_map.get(metric_name)
    if metric is None:
        return None

    judge_llm = _build_judge_llm()
    metric.llm = judge_llm

    data: dict = {
        "question": [question],
        "answer": [answer],
        "contexts": [contexts],
    }
    if ground_truth:
        data["ground_truth"] = [ground_truth]

    dataset = Dataset.from_dict(data)
    result = evaluate(dataset, metrics=[metric], raise_exceptions=False)
    df = result.to_pandas()

    if metric_name in df.columns:
        val = df[metric_name].iloc[0]
        if val is not None and not (isinstance(val, float) and val != val):
            return float(val)
    return None
