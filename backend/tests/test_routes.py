"""FastAPI route tests for /evaluate endpoints."""
from __future__ import annotations
import json
import sys
import os
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

SAMPLE_REQUEST = {
    "question": "What is RAG?",
    "answer": "RAG stands for Retrieval-Augmented Generation.",
    "contexts": ["RAG is a technique that combines retrieval with generation."],
    "ground_truth": "Retrieval-Augmented Generation",
    "mode": "full",
}

MOCK_SCORES = {
    "faithfulness": 0.9,
    "answer_relevancy": 0.85,
    "context_precision": 0.8,
    "context_recall": 0.75,
}

MOCK_HALLUCINATION = {
    "risk_level": "low",
    "confidence": 0.95,
    "unsupported_claims": [],
    "rationale": "Answer is well-grounded.",
}

MOCK_EXPLANATION = "The RAG pipeline performs well overall with high faithfulness."


async def _mock_ragas_stream(*args, **kwargs):
    yield {"type": "progress", "message": "Initializing...", "step": 0, "total": 4}
    yield {"type": "scores", "scores": MOCK_SCORES}


def _make_eval_response(overall: float, faithfulness: float, hallucination: str = "low") -> dict:
    return {
        "overall_score": overall,
        "scores": {
            "faithfulness": faithfulness,
            "answer_relevancy": 0.8,
            "context_precision": 0.75,
            "context_recall": 0.7,
            "hallucination_risk": hallucination,
        },
        "trace": {
            "retrieval_stage": {"score": 0.75, "issues": []},
            "generation_stage": {"score": 0.8, "issues": []},
        },
        "recommendations": [],
        "verdict": "READY",
        "explanation": "Good performance.",
    }


# ---------------------------------------------------------------------------
# /evaluate
# ---------------------------------------------------------------------------

class TestEvaluateRoute:
    def test_evaluate_success(self):
        with (
            patch("routers.evaluate._run_full_evaluation", new=AsyncMock(return_value=(MOCK_SCORES, MOCK_HALLUCINATION))),
            patch("routers.evaluate.generate_explanation", new=AsyncMock(return_value=MOCK_EXPLANATION)),
        ):
            resp = client.post("/evaluate", json=SAMPLE_REQUEST)
        assert resp.status_code == 200
        body = resp.json()
        assert "overall_score" in body
        assert body["verdict"] in ("READY", "NEEDS_WORK", "NOT_READY")
        assert body["explanation"] == MOCK_EXPLANATION
        assert body["scores"]["faithfulness"] == pytest.approx(0.9)

    def test_evaluate_missing_required_fields(self):
        resp = client.post("/evaluate", json={"question": "What is RAG?"})
        assert resp.status_code == 422

    def test_evaluate_without_ground_truth(self):
        req = {k: v for k, v in SAMPLE_REQUEST.items() if k != "ground_truth"}
        with (
            patch("routers.evaluate._run_full_evaluation", new=AsyncMock(return_value=(MOCK_SCORES, MOCK_HALLUCINATION))),
            patch("routers.evaluate.generate_explanation", new=AsyncMock(return_value=MOCK_EXPLANATION)),
        ):
            resp = client.post("/evaluate", json=req)
        assert resp.status_code == 200

    def test_evaluate_high_hallucination_forces_not_ready(self):
        high_risk = {**MOCK_HALLUCINATION, "risk_level": "high"}
        with (
            patch("routers.evaluate._run_full_evaluation", new=AsyncMock(return_value=(MOCK_SCORES, high_risk))),
            patch("routers.evaluate.generate_explanation", new=AsyncMock(return_value=MOCK_EXPLANATION)),
        ):
            resp = client.post("/evaluate", json=SAMPLE_REQUEST)
        assert resp.status_code == 200
        assert resp.json()["verdict"] == "NOT_READY"

    def test_evaluate_response_shape(self):
        with (
            patch("routers.evaluate._run_full_evaluation", new=AsyncMock(return_value=(MOCK_SCORES, MOCK_HALLUCINATION))),
            patch("routers.evaluate.generate_explanation", new=AsyncMock(return_value=MOCK_EXPLANATION)),
        ):
            body = client.post("/evaluate", json=SAMPLE_REQUEST).json()
        for field in ("overall_score", "scores", "trace", "recommendations", "verdict", "explanation"):
            assert field in body


# ---------------------------------------------------------------------------
# /evaluate/stream
# ---------------------------------------------------------------------------

class TestEvaluateStreamRoute:
    def test_stream_returns_sse_content_type(self):
        with (
            patch("routers.evaluate.ensure_provider_ready", new=AsyncMock(return_value=None)),
            patch("routers.evaluate.stream_ragas_evaluation", _mock_ragas_stream),
            patch("routers.evaluate.detect_hallucination", new=AsyncMock(return_value=MOCK_HALLUCINATION)),
            patch("routers.evaluate.generate_explanation", new=AsyncMock(return_value=MOCK_EXPLANATION)),
        ):
            resp = client.post("/evaluate/stream", json=SAMPLE_REQUEST)
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

    def test_stream_contains_data_lines(self):
        with (
            patch("routers.evaluate.ensure_provider_ready", new=AsyncMock(return_value=None)),
            patch("routers.evaluate.stream_ragas_evaluation", _mock_ragas_stream),
            patch("routers.evaluate.detect_hallucination", new=AsyncMock(return_value=MOCK_HALLUCINATION)),
            patch("routers.evaluate.generate_explanation", new=AsyncMock(return_value=MOCK_EXPLANATION)),
        ):
            resp = client.post("/evaluate/stream", json=SAMPLE_REQUEST)
        assert "data:" in resp.text

    def test_stream_final_result_event(self):
        with (
            patch("routers.evaluate.ensure_provider_ready", new=AsyncMock(return_value=None)),
            patch("routers.evaluate.stream_ragas_evaluation", _mock_ragas_stream),
            patch("routers.evaluate.detect_hallucination", new=AsyncMock(return_value=MOCK_HALLUCINATION)),
            patch("routers.evaluate.generate_explanation", new=AsyncMock(return_value=MOCK_EXPLANATION)),
        ):
            raw = client.post("/evaluate/stream", json=SAMPLE_REQUEST).text

        data_lines = [
            line[len("data: "):].strip()
            for line in raw.splitlines()
            if line.startswith("data: ") and line[len("data: "):].strip() not in ("[DONE]", "")
        ]
        events = [json.loads(line) for line in data_lines]
        result_events = [e for e in events if e.get("type") == "result"]
        assert len(result_events) == 1
        result = result_events[0]["data"]
        assert "overall_score" in result
        assert "verdict" in result

    def test_stream_ends_with_done(self):
        with (
            patch("routers.evaluate.ensure_provider_ready", new=AsyncMock(return_value=None)),
            patch("routers.evaluate.stream_ragas_evaluation", _mock_ragas_stream),
            patch("routers.evaluate.detect_hallucination", new=AsyncMock(return_value=MOCK_HALLUCINATION)),
            patch("routers.evaluate.generate_explanation", new=AsyncMock(return_value=MOCK_EXPLANATION)),
        ):
            raw = client.post("/evaluate/stream", json=SAMPLE_REQUEST).text
        assert "[DONE]" in raw

    def test_stream_preflight_failure_returns_error_event(self):
        with patch(
            "routers.evaluate.ensure_provider_ready",
            new=AsyncMock(side_effect=RuntimeError("Provider unavailable")),
        ):
            raw = client.post("/evaluate/stream", json=SAMPLE_REQUEST).text

        data_lines = [
            line[len("data: "):].strip()
            for line in raw.splitlines()
            if line.startswith("data: ") and line[len("data: "):].strip() not in ("[DONE]", "")
        ]
        events = [json.loads(line) for line in data_lines]
        assert any(e.get("type") == "error" for e in events)


# ---------------------------------------------------------------------------
# /evaluate/batch
# ---------------------------------------------------------------------------

class TestEvaluateBatchRoute:
    def test_batch_single_sample(self):
        with (
            patch("routers.evaluate._run_full_evaluation", new=AsyncMock(return_value=(MOCK_SCORES, MOCK_HALLUCINATION))),
            patch("routers.evaluate.generate_explanation", new=AsyncMock(return_value=MOCK_EXPLANATION)),
        ):
            resp = client.post("/evaluate/batch", json={"samples": [SAMPLE_REQUEST]})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_samples"] == 1
        assert body["successful"] == 1
        assert body["failed"] == 0
        assert len(body["results"]) == 1

    def test_batch_multiple_samples(self):
        with (
            patch("routers.evaluate._run_full_evaluation", new=AsyncMock(return_value=(MOCK_SCORES, MOCK_HALLUCINATION))),
            patch("routers.evaluate.generate_explanation", new=AsyncMock(return_value=MOCK_EXPLANATION)),
        ):
            resp = client.post("/evaluate/batch", json={"samples": [SAMPLE_REQUEST, SAMPLE_REQUEST]})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_samples"] == 2
        assert body["successful"] == 2
        assert body["failed"] == 0

    def test_batch_aggregate_contains_metrics(self):
        with (
            patch("routers.evaluate._run_full_evaluation", new=AsyncMock(return_value=(MOCK_SCORES, MOCK_HALLUCINATION))),
            patch("routers.evaluate.generate_explanation", new=AsyncMock(return_value=MOCK_EXPLANATION)),
        ):
            body = client.post("/evaluate/batch", json={"samples": [SAMPLE_REQUEST]}).json()
        agg = body["aggregate"]
        assert agg["faithfulness"] == pytest.approx(0.9, abs=0.01)
        assert agg["overall_score"] is not None

    def test_batch_verdict_distribution(self):
        with (
            patch("routers.evaluate._run_full_evaluation", new=AsyncMock(return_value=(MOCK_SCORES, MOCK_HALLUCINATION))),
            patch("routers.evaluate.generate_explanation", new=AsyncMock(return_value=MOCK_EXPLANATION)),
        ):
            body = client.post("/evaluate/batch", json={"samples": [SAMPLE_REQUEST]}).json()
        assert "verdict_distribution" in body
        assert isinstance(body["verdict_distribution"], dict)

    def test_batch_missing_samples_field(self):
        resp = client.post("/evaluate/batch", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# /evaluate/compare
# ---------------------------------------------------------------------------

class TestEvaluateCompareRoute:
    def test_compare_improved(self):
        payload = {
            "baseline": _make_eval_response(0.70, 0.70),
            "candidate": _make_eval_response(0.85, 0.90),
        }
        resp = client.post("/evaluate/compare", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["overall_direction"] == "improved"
        overall = next(d for d in body["deltas"] if d["metric"] == "overall_score")
        assert overall["direction"] == "improved"
        assert overall["delta"] == pytest.approx(0.15, abs=0.001)

    def test_compare_regressed(self):
        payload = {
            "baseline": _make_eval_response(0.85, 0.90),
            "candidate": _make_eval_response(0.70, 0.70),
        }
        resp = client.post("/evaluate/compare", json=payload)
        assert resp.status_code == 200
        assert resp.json()["overall_direction"] == "regressed"

    def test_compare_unchanged(self):
        ev = _make_eval_response(0.80, 0.80)
        resp = client.post("/evaluate/compare", json={"baseline": ev, "candidate": ev})
        assert resp.status_code == 200
        assert resp.json()["overall_direction"] == "unchanged"

    def test_compare_delta_count(self):
        payload = {
            "baseline": _make_eval_response(0.70, 0.70),
            "candidate": _make_eval_response(0.85, 0.90),
        }
        body = client.post("/evaluate/compare", json=payload).json()
        # 4 per-metric deltas + 1 overall_score delta
        assert len(body["deltas"]) == 5

    def test_compare_summary_not_empty(self):
        payload = {
            "baseline": _make_eval_response(0.70, 0.70),
            "candidate": _make_eval_response(0.85, 0.90),
        }
        body = client.post("/evaluate/compare", json=payload).json()
        assert body["summary"] != ""

    def test_compare_missing_fields_fails_validation(self):
        resp = client.post("/evaluate/compare", json={"baseline": {}})
        assert resp.status_code == 422
