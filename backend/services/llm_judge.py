"""Claude-powered hallucination detector and LLM-as-judge."""
from __future__ import annotations
import json
import os
import anthropic

_client: anthropic.AsyncAnthropic | None = None


def _env_int(name: str, default: int) -> int:
    val = os.environ.get(name)
    if not val:
        return default
    try:
        return int(val)
    except ValueError:
        return default


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            timeout=_env_int("LLM_JUDGE_TIMEOUT_SECONDS", 60),
            max_retries=_env_int("LLM_JUDGE_MAX_RETRIES", 2),
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
    model_name = os.environ.get("LLM_JUDGE_MODEL", "claude-opus-4-6")
    context_text = "\n\n---\n\n".join(
        f"[Context {i+1}]:\n{ctx}" for i, ctx in enumerate(contexts)
    )
    user_message = f"""Question: {question}

Retrieved Context:
{context_text}

Generated Answer: {answer}

Analyze whether this answer hallucinate or introduces unsupported information."""

    try:
        response = await client.messages.create(
            model=model_name,
            max_tokens=1024,
            system=HALLUCINATION_SYSTEM,
            messages=[{"role": "user", "content": user_message}],
        )
        text = response.content[0].text.strip()
        # Strip markdown code blocks if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        result = json.loads(text)
        return {
            "risk_level": result.get("risk_level", "medium"),
            "confidence": float(result.get("confidence", 0.5)),
            "unsupported_claims": result.get("unsupported_claims", []),
            "rationale": result.get("rationale", ""),
        }
    except Exception as exc:
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
    model_name = os.environ.get("LLM_EXPLANATION_MODEL", os.environ.get("LLM_JUDGE_MODEL", "claude-opus-4-6"))
    rec_summary = "; ".join(
        f"{r['dimension']} ({r['severity']}): {r['issue']}"
        for r in recommendations[:3]
    )
    prompt = f"""Evaluation scores: {json.dumps(scores)}
Top issues: {rec_summary if rec_summary else 'None'}
Generate a brief plain-English summary."""

    try:
        response = await client.messages.create(
            model=model_name,
            max_tokens=256,
            system=EXPLANATION_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception:
        return "Evaluation complete. Review the metric scores and recommendations above for details."
