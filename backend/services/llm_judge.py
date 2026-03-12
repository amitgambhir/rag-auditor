"""Claude-powered hallucination detector and LLM-as-judge."""
from __future__ import annotations
import json
import os
import time
import anthropic

import config
from logger import get_logger

_log = get_logger("rag_auditor.llm_judge")
_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            max_retries=config.LLM_MAX_RETRIES,
            timeout=config.LLM_TIMEOUT,
        )
    return _client


HALLUCINATION_SYSTEM = """You are an expert RAG quality evaluator specializing in hallucination detection.
Your task is to determine whether a given answer introduces information not present in the provided context chunks.

Evaluate:
1. Factual consistency — does every claim trace back to the context?
2. Unsupported claims — statements that are plausible but not in the context
3. Contradictions — anything that directly conflicts with the context

Respond with a JSON object only — no preamble or explanation outside the JSON:
{
  "risk_level": "low" | "medium" | "high",
  "confidence": 0.0-1.0,
  "unsupported_claims": ["claim1", "claim2"],
  "rationale": "brief explanation"
}

Risk levels:
- low: Answer is well-grounded, any additions are trivially true inferences
- medium: Some claims lack direct support but aren't clearly wrong
- high: Clear hallucinations, fabricated facts, or contradictions present"""


async def detect_hallucination(
    question: str,
    answer: str,
    contexts: list[str],
) -> dict:
    """Use Claude to detect hallucination risk in a RAG answer."""
    client = _get_client()
    context_text = "\n\n---\n\n".join(
        f"[Context {i+1}]:\n{ctx}" for i, ctx in enumerate(contexts)
    )
    user_message = f"""Question: {question}

Retrieved Context:
{context_text}

Generated Answer: {answer}

Analyze whether this answer hallucinate or introduces unsupported information."""

    t0 = time.perf_counter()
    try:
        response = await client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=config.MAX_TOKENS_HALLUCINATION,
            system=HALLUCINATION_SYSTEM,
            messages=[{"role": "user", "content": user_message}],
        )
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        text = response.content[0].text.strip()
        # Strip markdown code blocks if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        result = json.loads(text)
        risk = result.get("risk_level", "medium")
        _log.info(
            "anthropic_call",
            extra={
                "op": "detect_hallucination",
                "model": config.ANTHROPIC_MODEL,
                "latency_ms": latency_ms,
                "risk_level": risk,
            },
        )
        return {
            "risk_level": risk,
            "confidence": float(result.get("confidence", 0.5)),
            "unsupported_claims": result.get("unsupported_claims", []),
            "rationale": result.get("rationale", ""),
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        _log.warning(
            "anthropic_error",
            extra={
                "op": "detect_hallucination",
                "model": config.ANTHROPIC_MODEL,
                "error_class": type(exc).__name__,
                "latency_ms": latency_ms,
            },
        )
        return {
            "risk_level": "medium",
            "confidence": 0.0,
            "unsupported_claims": [],
            "rationale": f"Hallucination check unavailable: {exc}",
        }


EXPLANATION_SYSTEM = """You are an expert in RAG (Retrieval-Augmented Generation) quality.
Given evaluation scores and metrics, produce a concise 2-3 sentence plain-English summary
that tells a developer what the scores mean and what to focus on.
Be direct, specific, and actionable. Do not mention score numbers — describe quality in plain English."""


async def generate_explanation(scores: dict, recommendations: list[dict]) -> str:
    """Generate a plain-English explanation of evaluation results."""
    client = _get_client()
    rec_summary = "; ".join(
        f"{r['dimension']} ({r['severity']}): {r['issue']}"
        for r in recommendations[:3]
    )
    prompt = f"""Evaluation scores: {json.dumps(scores)}
Top issues: {rec_summary if rec_summary else 'None'}
Generate a brief plain-English summary."""

    t0 = time.perf_counter()
    try:
        response = await client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=config.MAX_TOKENS_EXPLANATION,
            system=EXPLANATION_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        _log.info(
            "anthropic_call",
            extra={
                "op": "generate_explanation",
                "model": config.ANTHROPIC_MODEL,
                "latency_ms": latency_ms,
            },
        )
        return response.content[0].text.strip()
    except Exception as exc:
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        _log.warning(
            "anthropic_error",
            extra={
                "op": "generate_explanation",
                "model": config.ANTHROPIC_MODEL,
                "error_class": type(exc).__name__,
                "latency_ms": latency_ms,
            },
        )
        return "Evaluation complete. Review the metric scores and recommendations above for details."
