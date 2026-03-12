"""Tests for evaluation endpoints and logic."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.formatters import compute_overall_score, score_to_verdict, clamp_score
from services.trace_analyzer import generate_recommendations, analyze_trace


class TestFormatters:
    def test_clamp_score_valid(self):
        assert clamp_score(0.75) == 0.75
        assert clamp_score(1.5) == 1.0
        assert clamp_score(-0.1) == 0.0
        assert clamp_score(None) is None

    def test_compute_overall_score_all_metrics(self):
        scores = {
            "faithfulness": 0.9,
            "answer_relevancy": 0.8,
            "context_precision": 0.7,
            "context_recall": 0.6,
        }
        overall = compute_overall_score(scores)
        assert 0.0 <= overall <= 1.0
        # Weighted: 0.9*0.35 + 0.8*0.30 + 0.7*0.20 + 0.6*0.15 = 0.315+0.24+0.14+0.09 = 0.785
        assert abs(overall - 0.785) < 0.01

    def test_compute_overall_score_missing_recall(self):
        scores = {
            "faithfulness": 0.9,
            "answer_relevancy": 0.8,
            "context_precision": 0.7,
        }
        overall = compute_overall_score(scores)
        assert 0.0 <= overall <= 1.0

    def test_compute_overall_score_empty(self):
        assert compute_overall_score({}) == 0.0

    def test_verdict_ready(self):
        assert score_to_verdict(0.85, "low") == "READY"
        assert score_to_verdict(0.80, None) == "READY"

    def test_verdict_needs_work(self):
        assert score_to_verdict(0.75, "low") == "NEEDS_WORK"
        assert score_to_verdict(0.60, None) == "NEEDS_WORK"

    def test_verdict_not_ready_low_score(self):
        assert score_to_verdict(0.55, "low") == "NOT_READY"

    def test_verdict_not_ready_high_hallucination(self):
        assert score_to_verdict(0.90, "high") == "NOT_READY"


class TestRecommendations:
    def test_no_recommendations_when_all_good(self):
        scores = {
            "faithfulness": 0.95,
            "answer_relevancy": 0.90,
            "context_precision": 0.85,
            "context_recall": 0.88,
        }
        recs = generate_recommendations(scores)
        assert all(r["severity"] in ("info",) for r in recs)

    def test_critical_faithfulness(self):
        scores = {"faithfulness": 0.3}
        recs = generate_recommendations(scores)
        faith_rec = next((r for r in recs if r["dimension"] == "faithfulness"), None)
        assert faith_rec is not None
        assert faith_rec["severity"] == "critical"

    def test_warning_context_precision(self):
        scores = {"context_precision": 0.65}
        recs = generate_recommendations(scores)
        cp_rec = next((r for r in recs if r["dimension"] == "context_precision"), None)
        assert cp_rec is not None
        assert cp_rec["severity"] == "warning"

    def test_recommendations_sorted_by_severity(self):
        scores = {
            "faithfulness": 0.3,
            "answer_relevancy": 0.65,
            "context_precision": 0.4,
        }
        recs = generate_recommendations(scores)
        severities = [r["severity"] for r in recs]
        order = {"critical": 0, "warning": 1, "info": 2}
        assert severities == sorted(severities, key=lambda s: order[s])


class TestTraceAnalyzer:
    def test_analyze_trace_with_all_scores(self):
        scores = {
            "faithfulness": 0.85,
            "answer_relevancy": 0.80,
            "context_precision": 0.75,
            "context_recall": 0.70,
        }
        trace = analyze_trace(scores, ["context1", "context2"], "question", "answer")
        assert 0.0 <= trace.retrieval_stage.score <= 1.0
        assert 0.0 <= trace.generation_stage.score <= 1.0

    def test_analyze_trace_low_precision_adds_issue(self):
        scores = {"context_precision": 0.3}
        trace = analyze_trace(scores, ["context1"], "q", "a")
        assert len(trace.retrieval_stage.issues) > 0

    def test_analyze_trace_no_contexts(self):
        scores = {}
        trace = analyze_trace(scores, [], "q", "a")
        assert any("No contexts" in issue for issue in trace.retrieval_stage.issues)
