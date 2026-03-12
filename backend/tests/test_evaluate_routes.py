"""API contract tests for evaluate routes."""
import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app  # noqa: E402
import routers.evaluate as evaluate_router  # noqa: E402


client = TestClient(app)


def _sample_payload() -> dict:
    return {
        "question": "What is the refund policy?",
        "answer": "Refunds are available within 30 days.",
        "contexts": ["Refunds are available within 30 days for digital products."],
        "ground_truth": "Refunds are available within 30 days.",
        "mode": "full",
    }


async def _fake_full_eval(_req):
    return (
        {
            "faithfulness": 0.9,
            "answer_relevancy": 0.85,
            "context_precision": 0.8,
            "context_recall": 0.75,
        },
        {"risk_level": "low"},
    )


async def _fake_explanation(_scores, _recs):
    return "Strong grounding with minor retrieval tuning opportunities."


async def _fake_hallucination(*_args, **_kwargs):
    return {"risk_level": "low"}


async def _fake_stream(*_args, **_kwargs):
    yield {"type": "progress", "message": "step"}
    yield {
        "type": "scores",
        "scores": {
            "faithfulness": 0.91,
            "answer_relevancy": 0.87,
            "context_precision": 0.8,
        },
    }


def test_evaluate_endpoint_contract(monkeypatch):
    monkeypatch.setattr(evaluate_router, "_run_full_evaluation", _fake_full_eval)
    monkeypatch.setattr(evaluate_router, "generate_explanation", _fake_explanation)

    response = client.post("/evaluate", json=_sample_payload())

    assert response.status_code == 200
    body = response.json()
    assert "overall_score" in body
    assert body["scores"]["faithfulness"] == 0.9
    assert body["scores"]["hallucination_risk"] == "low"
    assert body["verdict"] in {"READY", "NEEDS_WORK", "NOT_READY"}


def test_batch_endpoint_contract(monkeypatch):
    monkeypatch.setattr(evaluate_router, "_run_full_evaluation", _fake_full_eval)
    monkeypatch.setattr(evaluate_router, "generate_explanation", _fake_explanation)

    response = client.post("/evaluate/batch", json={"samples": [_sample_payload(), _sample_payload()]})

    assert response.status_code == 200
    body = response.json()
    assert body["total_samples"] == 2
    assert body["successful"] == 2
    assert body["failed"] == 0
    assert body["aggregate"]["overall_score"] is not None


def test_compare_endpoint_contract():
    payload = {
        "baseline": {
            "overall_score": 0.7,
            "scores": {
                "faithfulness": 0.7,
                "answer_relevancy": 0.7,
                "context_precision": 0.7,
                "context_recall": 0.7,
                "hallucination_risk": "low",
            },
            "trace": {
                "retrieval_stage": {"score": 0.7, "issues": []},
                "generation_stage": {"score": 0.7, "issues": []},
            },
            "recommendations": [],
            "verdict": "NEEDS_WORK",
            "explanation": "base",
        },
        "candidate": {
            "overall_score": 0.8,
            "scores": {
                "faithfulness": 0.8,
                "answer_relevancy": 0.8,
                "context_precision": 0.8,
                "context_recall": 0.8,
                "hallucination_risk": "low",
            },
            "trace": {
                "retrieval_stage": {"score": 0.8, "issues": []},
                "generation_stage": {"score": 0.8, "issues": []},
            },
            "recommendations": [],
            "verdict": "READY",
            "explanation": "cand",
        },
    }

    response = client.post("/evaluate/compare", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["overall_direction"] == "improved"
    assert len(body["deltas"]) == 5


def test_stream_endpoint_returns_result(monkeypatch):
    monkeypatch.setattr(evaluate_router, "stream_ragas_evaluation", _fake_stream)
    monkeypatch.setattr(
        evaluate_router,
        "detect_hallucination",
        _fake_hallucination,
    )
    monkeypatch.setattr(evaluate_router, "generate_explanation", _fake_explanation)

    with client.stream("POST", "/evaluate/stream", json=_sample_payload()) as response:
        assert response.status_code == 200
        raw = "".join([line for line in response.iter_text() if line])

    assert "[DONE]" in raw
    assert '"type": "result"' in raw


def test_history_pruning_by_size():
    evaluate_router._history.clear()
    original_max = evaluate_router.HISTORY_MAX_SIZE

    try:
        evaluate_router.HISTORY_MAX_SIZE = 2
        for i in range(4):
            payload = _sample_payload()
            payload["question"] = f"Q{i}"
            evaluate_router._history[str(i)] = (0.0, None)
        evaluate_router._prune_history(now=0.0)
        assert len(evaluate_router._history) == 2
    finally:
        evaluate_router.HISTORY_MAX_SIZE = original_max
        evaluate_router._history.clear()
