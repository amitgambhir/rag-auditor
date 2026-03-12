"""Analyze RAG pipeline trace — per-stage scoring and issue detection."""
from __future__ import annotations
from typing import Optional
from models.evaluation import Trace, TraceStage


def analyze_trace(
    scores: dict,
    contexts: list[str],
    question: str,
    answer: str,
) -> Trace:
    """
    Map RAGAS metric scores onto retrieval and generation stages.

    Retrieval stage = context_precision + context_recall
    Generation stage = faithfulness + answer_relevancy
    """
    retrieval_scores = []
    retrieval_issues = []
    generation_scores = []
    generation_issues = []

    cp = scores.get("context_precision")
    cr = scores.get("context_recall")
    faith = scores.get("faithfulness")
    ar = scores.get("answer_relevancy")

    # Retrieval stage analysis
    if cp is not None:
        retrieval_scores.append(cp)
        if cp < 0.5:
            retrieval_issues.append("High noise in retrieved chunks — many irrelevant passages")
        elif cp < 0.7:
            retrieval_issues.append("Retrieved chunks contain some irrelevant content")

    if cr is not None:
        retrieval_scores.append(cr)
        if cr < 0.5:
            retrieval_issues.append("Critical information is missing from retrieved context")
        elif cr < 0.7:
            retrieval_issues.append("Some relevant information may not be retrieved")

    if not contexts:
        retrieval_issues.append("No contexts provided — retrieval stage cannot be assessed")

    # Generation stage analysis
    if faith is not None:
        generation_scores.append(faith)
        if faith < 0.5:
            generation_issues.append("Answer significantly deviates from context — high hallucination risk")
        elif faith < 0.7:
            generation_issues.append("Answer partially unsupported by context")

    if ar is not None:
        generation_scores.append(ar)
        if ar < 0.5:
            generation_issues.append("Answer does not adequately address the question")
        elif ar < 0.7:
            generation_issues.append("Answer relevance could be improved")

    # Context length check
    avg_context_len = sum(len(c) for c in contexts) / max(len(contexts), 1)
    if avg_context_len > 2000:
        retrieval_issues.append("Context chunks are very long — consider smaller chunk sizes")
    if len(contexts) > 10:
        retrieval_issues.append("Too many retrieved chunks — consider reducing top-k")

    retrieval_score = (
        sum(retrieval_scores) / len(retrieval_scores) if retrieval_scores else 0.5
    )
    generation_score = (
        sum(generation_scores) / len(generation_scores) if generation_scores else 0.5
    )

    return Trace(
        retrieval_stage=TraceStage(score=round(retrieval_score, 4), issues=retrieval_issues),
        generation_stage=TraceStage(score=round(generation_score, 4), issues=generation_issues),
    )


def generate_recommendations(scores: dict) -> list[dict]:
    """Map scores to specific, actionable recommendations."""
    recommendations = []

    faith = scores.get("faithfulness")
    ar = scores.get("answer_relevancy")
    cp = scores.get("context_precision")
    cr = scores.get("context_recall")

    if faith is not None and faith < 0.7:
        severity = "critical" if faith < 0.5 else "warning"
        recommendations.append({
            "dimension": "faithfulness",
            "score": faith,
            "severity": severity,
            "issue": "Answer contains claims not supported by the retrieved context",
            "fix": (
                "Add explicit instructions to your generation prompt: 'Only use information "
                "from the provided context. Do not add external knowledge.' "
                "Consider using structured prompts that reference the context directly."
            ) if faith < 0.5 else (
                "Tighten your generation prompt to emphasize grounding in provided documents. "
                "Consider adding a post-generation fact-checking step."
            ),
        })

    if ar is not None and ar < 0.7:
        severity = "critical" if ar < 0.5 else "warning"
        recommendations.append({
            "dimension": "answer_relevancy",
            "score": ar,
            "severity": severity,
            "issue": "Generated answer does not fully address the user question",
            "fix": (
                "Implement query rewriting or HyDE (Hypothetical Document Embeddings) "
                "to better align retrieval with intent. Ensure your prompt explicitly "
                "instructs the model to answer the specific question asked."
            ) if ar < 0.5 else (
                "Review your prompt template — ensure the question is prominently featured. "
                "Consider query expansion techniques to capture intent better."
            ),
        })

    if cp is not None and cp < 0.7:
        severity = "critical" if cp < 0.5 else "warning"
        recommendations.append({
            "dimension": "context_precision",
            "score": cp,
            "severity": severity,
            "issue": "Retrieved chunks contain significant irrelevant content (low signal-to-noise)",
            "fix": (
                "Reduce your retrieval top-k value (try k=3 instead of k=10). "
                "Upgrade your embedding model — consider text-embedding-3-large or Cohere. "
                "Add a reranking step (cross-encoder) after initial retrieval."
            ) if cp < 0.5 else (
                "Tighten your retrieval top-k or add a reranking step. "
                "Try hybrid search (dense + sparse) to improve precision."
            ),
        })

    if cr is not None and cr < 0.7:
        severity = "critical" if cr < 0.5 else "warning"
        recommendations.append({
            "dimension": "context_recall",
            "score": cr,
            "severity": severity,
            "issue": "Relevant information is not being retrieved from your knowledge base",
            "fix": (
                "Revisit your chunking strategy — try smaller chunks (256-512 tokens) "
                "with overlap. Ensure your embedding model captures the semantic meaning "
                "of your domain. Consider parent-document retrieval or sentence-window retrieval."
            ) if cr < 0.5 else (
                "Increase your retrieval top-k or use a hierarchical chunking strategy. "
                "Multi-query retrieval (generate 3 query variants) can improve recall significantly."
            ),
        })

    if faith is not None and faith >= 0.8 and ar is not None and ar >= 0.8:
        if not recommendations:
            recommendations.append({
                "dimension": "overall",
                "score": (faith + ar) / 2,
                "severity": "info",
                "issue": "Your RAG pipeline is performing well",
                "fix": "Monitor production metrics and consider running the full evaluation suite on a diverse test set.",
            })

    return sorted(
        recommendations,
        key=lambda r: {"critical": 0, "warning": 1, "info": 2}[r["severity"]],
    )
