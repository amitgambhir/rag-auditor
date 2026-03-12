<div align="center">

# 🔍 RAG Auditor

**Know if your RAG is production-ready before your users find out it isn't.**

[![MIT License](https://img.shields.io/badge/license-MIT-00d4aa.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com)
[![Powered by RAGAS](https://img.shields.io/badge/eval-RAGAS-7c3aed.svg)](https://docs.ragas.io)
[![Powered by Claude](https://img.shields.io/badge/judge-Claude%20AI-d97706.svg)](https://anthropic.com)

</div>

---

## The Problem

Most RAG systems ship broken.

Not broken in obvious ways — broken in the ways that matter: answers that sound confident
but contradict the source documents, retrieved chunks that miss the point entirely,
prompts that quietly hallucinate under edge cases.

The teams building these systems usually know something's off. They just have no way to
*measure* it systematically — so they eyeball outputs, cross their fingers, and ship.

**RAG Auditor fixes that.**

---

## What It Does

RAG Auditor is an open source evaluation platform that automatically scores your RAG
pipeline across the four dimensions that predict real-world quality — then tells you
exactly what to fix and how.

```
Input:  Your question  +  Retrieved context chunks  +  RAG-generated answer
Output: A production-readiness verdict with scored diagnostics and fix recommendations
```

### Evaluation Dimensions

| Metric | What It Measures | Why It Matters |
|--------|-----------------|----------------|
| **Faithfulness** | Is the answer grounded in the retrieved context? | Catches hallucinations |
| **Answer Relevancy** | Does the answer actually address the question? | Catches non-answers |
| **Context Precision** | Are retrieved chunks signal or noise? | Catches retrieval bloat |
| **Context Recall** | Did retrieval surface the right information? | Catches retrieval gaps |
| **Hallucination Risk** | `LOW` / `MEDIUM` / `HIGH` classification | Human-readable safety check |

Each score comes with a plain-English explanation and a specific, actionable recommendation.

---

## Demo

> ⚡ *Paste a question, context, and answer. Get a verdict in ~10 seconds.*

```
Question:    "What is our refund policy for digital products?"
Context:     [3 retrieved chunks from your knowledge base]
Answer:      "You can get a refund within 30 days, no questions asked."

──────────────────────────────────────────────
  Overall Score      0.84    ● NEEDS WORK
──────────────────────────────────────────────
  Faithfulness       0.91    ✓ Strong
  Answer Relevancy   0.88    ✓ Strong
  Context Precision  0.67    ⚠ Warning
  Context Recall     0.79    ● Review
  Hallucination Risk  LOW    ✓ Safe
──────────────────────────────────────────────
  Top Issue: Context precision is low — your retriever is pulling in
  irrelevant chunks alongside the relevant ones. Try reducing top-k
  from 5 to 3, or add a reranking step before generation.
──────────────────────────────────────────────
```

---

## Key Features

- **Single-sample evaluator** — paste one Q/context/answer, get instant scores
- **Batch evaluation** — upload CSV/JSON for bulk pipeline testing
- **Golden dataset generator** — paste your source docs, auto-generate synthetic Q&A
  test pairs (the #1 reason teams skip evals is they have no dataset — this removes
  that blocker entirely)
- **Compare mode** — run before/after evals when you change chunking, top-k, or prompts;
  see exact delta per metric
- **RAG trace visualization** — see scores annotated at each stage:
  Query → Retrieval → Prompt Construction → Generation → Answer
- **LLM-as-judge** — Claude evaluates hallucination risk with reasoning, not just a number
- **Fix recommendations** — every low score maps to a specific, actionable suggestion

---

## Built On

RAG Auditor is a product layer built on top of battle-tested open source infrastructure:

- **[RAGAS](https://docs.ragas.io)** — the leading RAG evaluation framework, providing
  the core faithfulness, relevancy, precision, and recall metrics
- **[Claude](https://anthropic.com)** (`claude-opus-4.6`) — LLM-as-judge for
  hallucination detection and plain-English explanations
- **[FastAPI](https://fastapi.tiangolo.com)** — async Python backend with SSE streaming
- **[React](https://react.dev) + [Recharts](https://recharts.org)** — dashboard UI

> RAGAS provides the scoring science. Claude provides the reasoning layer.
> RAG Auditor provides the product experience that makes both usable without a PhD.

---

## Quickstart

**Docker (recommended):**
```bash
git clone https://github.com/yourusername/rag-auditor
cd rag-auditor
cp .env.example .env          # Add your ANTHROPIC_API_KEY
docker-compose up
```

Open `http://localhost:3000` — that's it.

**Local development:**
```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend && npm install && npm run dev
```

---

## Architecture

```
┌─────────────────────────────────────────────┐
│                  React UI                   │
│  Evaluator · Batch · Generator · Compare    │
└──────────────────┬──────────────────────────┘
                   │ REST + SSE
┌──────────────────▼──────────────────────────┐
│               FastAPI Backend               │
│                                             │
│  ┌─────────────┐    ┌────────────────────┐  │
│  │    RAGAS    │    │   Claude (Judge)   │  │
│  │  Evaluator  │    │  Hallucination     │  │
│  │             │    │  Detection +       │  │
│  │ Faithfulness│    │  Recommendations   │  │
│  │ Relevancy   │    │  Plain-English     │  │
│  │ Precision   │    │  Explanations      │  │
│  │ Recall      │    └────────────────────┘  │
│  └─────────────┘                            │
│         └──────────── asyncio.gather() ─────┘
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │     Recommendation Engine            │   │
│  │  Score → Root Cause → Specific Fix   │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

---

## Step-by-Step Testing Guide

This section walks you through the full workflow: generating a dataset, evaluating it, and running automated tests.

### Prerequisites

- Python 3.11+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com/)

---

### Step 1 — Set Up Your Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set:
```
ANTHROPIC_API_KEY=sk-ant-...
CORS_ORIGINS=http://localhost:3000
```

---

### Step 2 — Start the Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Verify it's running:
```bash
curl http://localhost:8000/health
# → {"status": "ok"}
```

Interactive API docs are available at http://localhost:8000/docs

---

### Step 3 — Generate a Synthetic Golden Dataset

Before you can evaluate your RAG system, you need Q&A pairs with ground truth. Use the Dataset Generator to create them from your own source documents.

#### Via the UI

1. Open http://localhost:3000
2. Click **Dataset Generator** in the nav
3. Paste 1–5 source documents (e.g., product docs, knowledge-base articles)
4. Set the number of Q&A pairs (1–100)
5. Click **Generate**
6. Download as JSON or CSV

#### Via curl

```bash
curl -X POST http://localhost:8000/generate-dataset \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      "RAG stands for Retrieval-Augmented Generation. It is a technique that combines information retrieval with large language models. The retrieval step fetches relevant documents from a knowledge base. The generation step uses the retrieved documents as context to produce an answer.",
      "Faithfulness measures whether every claim in the generated answer can be traced back to the retrieved context. A faithfulness score of 1.0 means the answer is fully grounded in the provided documents."
    ],
    "num_questions": 5
  }'
```

**Response structure:**
```json
{
  "pairs": [
    {
      "question": "What does RAG stand for?",
      "answer": "RAG stands for Retrieval-Augmented Generation.",
      "ground_truth": "RAG stands for Retrieval-Augmented Generation.",
      "contexts": ["RAG stands for Retrieval-Augmented Generation..."],
      "evolution_type": "simple"
    }
  ],
  "total": 5,
  "source_documents": 2
}
```

The generator first attempts RAGAS `TestsetGenerator` (which creates diverse question types: simple, reasoning, multi-context). If RAGAS is unavailable it falls back to Claude directly. Either path produces the same output format.

#### Save the dataset for reuse

```bash
curl -X POST http://localhost:8000/generate-dataset \
  -H "Content-Type: application/json" \
  -d '{"documents": ["...your text..."], "num_questions": 10}' \
  -o my_dataset.json
```

#### Dataset evolution types

| Type | Description | Distribution |
|---|---|---|
| `simple` | Direct factual questions from one document | 50% |
| `reasoning` | Questions requiring inference or multi-step thinking | 30% |
| `multi_context` | Questions that require combining multiple documents | 20% |

Each pair contains:
- `question` — the user query to pose to your RAG system
- `answer` — a reference answer (useful for comparison)
- `ground_truth` — the canonical correct answer (used for context recall)
- `contexts` — the source passages (use these as your "retrieved chunks" in evaluation)
- `evolution_type` — question category

> **Tip:** To evaluate your own RAG system with the generated dataset, replace `contexts` with the chunks your retriever actually returns, and replace `answer` with what your LLM generates. Keep `ground_truth` as-is.

---

### Step 4 — Evaluate a Single RAG Response

Use a Q&A pair from your dataset (or write one manually) and evaluate it.

#### Via the UI

1. Open http://localhost:3000
2. Fill in **Question**, **Answer**, **Retrieved Contexts** (one per line), and optionally **Ground Truth**
3. Choose mode: **Full** (all metrics) or **Quick** (skips context recall, faster)
4. Click **Evaluate**
5. View per-metric scores, hallucination badge, trace visualization, and recommendations

#### Via curl (non-streaming)

```bash
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is RAG?",
    "answer": "RAG stands for Retrieval-Augmented Generation. It retrieves relevant documents and uses them to generate answers.",
    "contexts": [
      "RAG stands for Retrieval-Augmented Generation. It is a technique that combines information retrieval with large language models.",
      "The retrieval step fetches relevant documents. The generation step uses them as context."
    ],
    "ground_truth": "RAG retrieves relevant documents from a knowledge base and uses them as context to generate accurate answers.",
    "mode": "full"
  }'
```

**Response structure:**
```json
{
  "overall_score": 0.87,
  "scores": {
    "faithfulness": 0.95,
    "answer_relevancy": 0.88,
    "context_precision": 0.80,
    "context_recall": 0.75,
    "hallucination_risk": "low"
  },
  "trace": {
    "retrieval_stage": {"score": 0.775, "issues": []},
    "generation_stage": {"score": 0.915, "issues": []}
  },
  "recommendations": [...],
  "verdict": "READY",
  "explanation": "Your RAG pipeline is well-grounded and relevant..."
}
```

#### Via curl (streaming SSE)

The streaming endpoint yields real-time progress events followed by the final result:

```bash
curl -N -X POST http://localhost:8000/evaluate/stream \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is RAG?",
    "answer": "RAG stands for Retrieval-Augmented Generation.",
    "contexts": ["RAG stands for Retrieval-Augmented Generation..."],
    "ground_truth": "RAG retrieves documents and generates answers.",
    "mode": "full"
  }'
```

Events emitted (one per line, `data: {...}`):
- `{"type": "progress", "message": "Initializing evaluation engine...", "step": 0, "total": 5}`
- `{"type": "progress", "message": "Checking answer faithfulness...", "step": 1, "total": 5}`
- `{"type": "progress", "message": "Running hallucination check..."}`
- `{"type": "scores", "scores": {...}}`
- `{"type": "result", "data": {...full EvaluationResponse...}}`
- `[DONE]`

---

### Step 5 — Evaluate a Batch

Use this when you have a full dataset and want aggregate statistics.

```bash
curl -X POST http://localhost:8000/evaluate/batch \
  -H "Content-Type: application/json" \
  -d '{
    "samples": [
      {
        "question": "What is RAG?",
        "answer": "RAG is Retrieval-Augmented Generation.",
        "contexts": ["RAG combines retrieval with generation."],
        "ground_truth": "RAG retrieves documents to generate answers.",
        "mode": "full"
      },
      {
        "question": "What does faithfulness measure?",
        "answer": "Faithfulness measures if claims trace back to context.",
        "contexts": ["Faithfulness measures whether every claim in the answer can be traced back to context."],
        "ground_truth": "Faithfulness measures grounding of the answer in retrieved context.",
        "mode": "full"
      }
    ]
  }'
```

**Response includes:**
```json
{
  "aggregate": {
    "faithfulness": 0.91,
    "answer_relevancy": 0.85,
    "context_precision": 0.78,
    "context_recall": 0.72,
    "overall_score": 0.85
  },
  "verdict_distribution": {"READY": 2},
  "total_samples": 2,
  "successful": 2,
  "failed": 0,
  "results": [...],
  "errors": []
}
```

#### Using a generated dataset directly

```bash
# Generate
curl -X POST http://localhost:8000/generate-dataset \
  -H "Content-Type: application/json" \
  -d '{"documents": ["..."], "num_questions": 5}' \
  -o dataset.json

# Transform to batch format with jq
cat dataset.json | jq '{samples: [.pairs[] | {question, answer, contexts, ground_truth, mode: "full"}]}' \
  > batch_input.json

# Evaluate
curl -X POST http://localhost:8000/evaluate/batch \
  -H "Content-Type: application/json" \
  -d @batch_input.json
```

---

### Step 6 — Compare Two Evaluations

After changing your RAG pipeline, compare before and after:

```bash
# Save your baseline result
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{"question": "...", "answer": "old answer", "contexts": [...], "mode": "full"}' \
  -o baseline.json

# Save your candidate result
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{"question": "...", "answer": "improved answer", "contexts": [...], "mode": "full"}' \
  -o candidate.json

# Compare
curl -X POST http://localhost:8000/evaluate/compare \
  -H "Content-Type: application/json" \
  -d "{\"baseline\": $(cat baseline.json), \"candidate\": $(cat candidate.json)}"
```

**Response:**
```json
{
  "deltas": [
    {"metric": "faithfulness", "baseline": 0.70, "candidate": 0.90, "delta": 0.20, "direction": "improved"},
    {"metric": "answer_relevancy", "baseline": 0.85, "candidate": 0.82, "delta": -0.03, "direction": "regressed"}
  ],
  "summary": "Mixed results: faithfulness improved by 20.0% but answer_relevancy regressed by 3.0%.",
  "overall_direction": "mixed"
}
```

---

### Step 7 — Run the Automated Test Suite

Unit tests cover formatters, trace analysis, and recommendation logic — no API key required.

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

Expected output:
```
tests/test_evaluate.py::TestFormatters::test_clamp_score_valid PASSED
tests/test_evaluate.py::TestFormatters::test_compute_overall_score_all_metrics PASSED
tests/test_evaluate.py::TestFormatters::test_verdict_ready PASSED
tests/test_evaluate.py::TestFormatters::test_verdict_not_ready_high_hallucination PASSED
tests/test_evaluate.py::TestRecommendations::test_critical_faithfulness PASSED
tests/test_evaluate.py::TestRecommendations::test_recommendations_sorted_by_severity PASSED
tests/test_evaluate.py::TestTraceAnalyzer::test_analyze_trace_with_all_scores PASSED
...
```

Run frontend tests:
```bash
cd frontend
npm test
```

---

## Understanding Verdicts

| Verdict | Condition |
|---|---|
| **READY** | Overall score ≥ 0.80 AND hallucination risk is not `high` |
| **NEEDS_WORK** | Overall score ≥ 0.60 (and hallucination not `high`) |
| **NOT_READY** | Overall score < 0.60, OR hallucination risk is `high` |

The **overall score** is a weighted average:

| Metric | Weight |
|---|---|
| Faithfulness | 35% |
| Answer Relevancy | 30% |
| Context Precision | 20% |
| Context Recall | 15% |

---

## RAGAS Metrics Explained

| Metric | What it measures | Requires ground truth? |
|---|---|---|
| **Faithfulness** | Does every claim in the answer trace back to the retrieved context? A score of 1.0 means the answer is fully grounded. | No |
| **Answer Relevancy** | Does the answer actually address the question asked? Low scores mean the answer is off-topic. | No |
| **Context Precision** | What fraction of the retrieved chunks are actually relevant? Low scores mean your retriever is returning noise. | No |
| **Context Recall** | Was all the relevant information present in the retrieved chunks? Low scores mean your retriever missed important content. | Yes |

**Hallucination Risk** is an additional LLM-as-judge assessment (not from RAGAS) that classifies whether the answer introduces information not in the context: `low`, `medium`, or `high`.

---

## Interpreting Recommendations

Every evaluation returns prioritized recommendations sorted by severity:

| Severity | Score range | Example fix |
|---|---|---|
| **critical** | < 0.50 | Rewrite your generation prompt to forbid external knowledge |
| **warning** | 0.50–0.70 | Tighten top-k, add reranking |
| **info** | ≥ 0.80 | Monitor production metrics |

---

## How LLM-as-Judge Works

RAG Auditor uses Claude (`claude-opus-4.6`) for three purposes:

1. **RAGAS metrics** — Claude is the judge LLM for all RAGAS computations (faithfulness, answer relevancy, context precision, context recall)
2. **Hallucination detection** — A custom Claude prompt analyzes whether the answer introduces unsupported claims, returning `risk_level`, `confidence`, `unsupported_claims`, and `rationale`
3. **Plain-English explanation** — Claude synthesizes scores into a 2–3 sentence summary of what to fix

---

## API Reference

Interactive docs available at http://localhost:8000/docs

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/evaluate` | Single evaluation (blocking) |
| `POST` | `/evaluate/stream` | Single evaluation with SSE progress |
| `POST` | `/evaluate/batch` | Batch evaluation with aggregates |
| `POST` | `/evaluate/compare` | Compare baseline vs candidate |
| `POST` | `/generate-dataset` | Generate synthetic golden dataset |

---

## Key Files

| File | Purpose |
|---|---|
| `backend/main.py` | FastAPI app, CORS, router registration |
| `backend/routers/evaluate.py` | Single, batch, streaming, compare endpoints |
| `backend/routers/generate_dataset.py` | Dataset generation endpoint |
| `backend/services/ragas_evaluator.py` | RAGAS metric runner (async + streaming) |
| `backend/services/llm_judge.py` | Hallucination detection + explanation via Claude |
| `backend/services/trace_analyzer.py` | Maps scores to retrieval/generation stage traces |
| `backend/services/dataset_generator.py` | RAGAS TestsetGenerator + Claude fallback |
| `backend/models/evaluation.py` | Pydantic models for requests and responses |
| `backend/models/dataset.py` | Pydantic models for dataset generation |
| `backend/utils/formatters.py` | Score clamping, weighting, verdict logic |
| `backend/tests/test_evaluate.py` | Unit tests (no API key required) |

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key |
| `RAGAS_APP_TOKEN` | No | RAGAS Cloud token for advanced features |
| `CORS_ORIGINS` | No | Allowed origins (default: `http://localhost:3000`) |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to submit issues, PRs, and run tests.

## License

MIT — see [LICENSE](LICENSE)
