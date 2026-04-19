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

## RAG Ecosystem

This repo is part of a broader RAG toolkit:

| Repo | What it covers |
| --- | --- |
| [rag-auditor](https://github.com/amitgambhir/rag-auditor) ← you are here | Evaluate your RAG pipeline |
| [multi-llm-rag-agent-chat](https://github.com/amitgambhir/multi-llm-rag-agent-chat) | Build a production RAG chatbot with multi-LLM routing |
| [rag-system-design-guide](https://github.com/amitgambhir/rag-system-design-guide) | Design reference — architecture patterns and trade-offs |

Start with the design guide, build with the chatbot, evaluate with this.

---

## Table of Contents

1. [RAG Ecosystem](#rag-ecosystem)
2. [The Problem](#the-problem)
3. [What It Does](#what-it-does)
4. [Demo](#demo)
5. [Key Features](#key-features)
6. [Built On](#built-on)
7. [Quickstart](#quickstart)
8. [Architecture](#architecture)
9. [Step-by-Step Testing Guide](#step-by-step-testing-guide)
   - [Step 1 — Set Up Your Environment](#step-1--set-up-your-environment)
   - [Step 2 — Start the Backend](#step-2--start-the-backend)
   - [Step 3 — Generate a Synthetic Golden Dataset](#step-3--generate-a-synthetic-golden-dataset)
   - [Step 4 — Evaluate a Single RAG Response](#step-4--evaluate-a-single-rag-response)
   - [Step 5 — Evaluate a Batch](#step-5--evaluate-a-batch)
   - [Step 6 — Compare Two Evaluations](#step-6--compare-two-evaluations)
   - [Step 7 — Run the Automated Test Suite](#step-7--run-the-automated-test-suite)
10. [Understanding Verdicts](#understanding-verdicts)
11. [RAGAS Metrics Explained](#ragas-metrics-explained)
12. [Interpreting Recommendations](#interpreting-recommendations)
13. [How LLM-as-Judge Works](#how-llm-as-judge-works)
14. [Integration: Evaluating multi-llm-rag-agent-chat](#integration-evaluating-multi-llm-rag-agent-chat)
15. [Key Design Decisions](#key-design-decisions)
16. [Extending the System](#extending-the-system)
17. [API Reference](#api-reference)
18. [Key Files](#key-files)
19. [Configuration](#configuration)
20. [Contributing](#contributing)

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
- **Evaluation history** — save results in the current browser session and restore them
  into the evaluator to compare runs or keep iterating
- **RAG trace visualization** — see scores annotated at each stage:
  Query → Retrieval → Prompt Construction → Generation → Answer
- **LLM-as-judge** — Claude evaluates hallucination risk with reasoning, not just a number
- **Fix recommendations** — every low score maps to a specific, actionable suggestion

---

## Built On

RAG Auditor is a product layer built on top of battle-tested open source infrastructure:

- **[RAGAS](https://docs.ragas.io)** — the leading RAG evaluation framework, providing
  the core faithfulness, relevancy, precision, and recall metrics
- **[Claude](https://anthropic.com)** (`claude-sonnet-4-6`) — LLM-as-judge for
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

CSV exports store `contexts` as a JSON array string so they round-trip cleanly into the Batch Evaluator.
The Batch Evaluator also accepts the older pipe-delimited `contexts` format for compatibility.

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
3. Choose mode: **Full** (all metrics) or **Quick** (skips context recall even if Ground Truth is provided, faster)
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

In the UI, batch upload accepts JSON files directly and CSV files with `contexts` stored either as a JSON array string or as a legacy pipe-delimited field.

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

RAG Auditor uses Claude (`claude-sonnet-4-6`) for three purposes:

1. **RAGAS metrics** — Claude is the judge LLM for all RAGAS computations (faithfulness, answer relevancy, context precision, context recall)
2. **Hallucination detection** — A custom Claude prompt analyzes whether the answer introduces unsupported claims, returning `risk_level`, `confidence`, `unsupported_claims`, and `rationale`
3. **Plain-English explanation** — Claude synthesizes scores into a 2–3 sentence summary of what to fix

---

## Integration: Evaluating multi-llm-rag-agent-chat

[multi-llm-rag-agent-chat](https://github.com/amitgambhir/multi-llm-rag-agent-chat) is a production RAG chatbot with dual-LLM routing (GPT-4o / Gemini Flash), ChromaDB vector storage, HuggingFace embeddings (`all-MiniLM-L6-v2`), and an RLHF feedback loop. RAG Auditor is the ideal complement — it gives you objective metric scores for every dimension of that pipeline.

```
multi-llm-rag-agent-chat          RAG Auditor
─────────────────────────         ─────────────────────────────────
Upload documents          ──►     Generate golden dataset from same docs
Ask question              ──►     Capture question + answer + contexts
ChromaDB retrieval (top 6)──►     Evaluate context_precision / context_recall
GPT-4o or Gemini answer   ──►     Evaluate faithfulness / answer_relevancy
RLHF re-ranking active    ──►     Re-run batch eval, compare delta scores
```

### Step 1 — Generate a Golden Dataset from Your Documents

Use the same documents you uploaded to the chatbot to generate ground-truth Q&A pairs:

```bash
curl -X POST http://localhost:8000/generate-dataset \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      "paste the text content of one of your uploaded PDFs or web pages here",
      "paste a second document here"
    ],
    "num_questions": 20
  }' \
  -o golden_dataset.json
```

These Q&A pairs become your evaluation harness. The `ground_truth` field is what you use to score context recall.

### Step 2 — Capture Live Responses from the Chatbot

For each question in your golden dataset, query the chatbot and capture the full response including the retrieved source chunks. The chatbot's chat endpoint accepts `{ "query": "...", "session_id": "..." }` and returns `answer` + `sources`.

> **Note on content truncation:** The chatbot's `sources[].content` field is currently truncated to 300 characters (`doc.page_content[:300]` in `chat.py`). This is fine for UI display but too short for RAGAS to compute accurate faithfulness and recall scores. See [Changes needed to multi-llm-rag-agent-chat](#changes-needed-to-multi-llm-rag-agent-chat) below for the one-line fix.

```python
import httpx, json, uuid

golden = json.load(open("golden_dataset.json"))
samples = []
session_id = str(uuid.uuid4())

for pair in golden["pairs"]:
    # Query the chatbot backend — field is "query", not "message"
    resp = httpx.post(
        "http://localhost:8001/chat",
        json={"query": pair["question"], "session_id": session_id},
        timeout=60,
    )
    data = resp.json()

    samples.append({
        "question": pair["question"],
        "answer": data["answer"],
        # sources[].content is truncated to 300 chars by default — apply the
        # full_content fix (see below) to get meaningful RAGAS scores
        "contexts": [s["content"] for s in data["sources"]],
        "ground_truth": pair["ground_truth"],
        "mode": "full",
    })

json.dump({"samples": samples}, open("batch_input.json", "w"))
```

#### Changes needed to multi-llm-rag-agent-chat

Only one change is required in the chatbot to make it fully compatible with RAG Auditor evaluation.

**Problem:** `backend/routers/chat.py` truncates source content to 300 chars:
```python
# current — too short for RAGAS
Source(content=doc.page_content[:300], ...)
```

**Fix:** Return the full chunk content (or add a `full_content` field alongside the truncated preview):
```python
# option A — return full content (evaluation-friendly, slightly larger payload)
Source(content=doc.page_content, ...)

# option B — keep the 300-char preview for UI, add full content for eval
Source(
    content=doc.page_content[:300],   # UI display
    full_content=doc.page_content,    # evaluation use
    ...
)
```

If you go with option B, update the integration script to use `s["full_content"]` instead of `s["content"]`.

No other changes are required — the chatbot's API shape (`query`, `answer`, `sources`, `chunk_ids`, `llm_used`, `complexity_score`) maps cleanly to RAG Auditor's evaluation input.

### Step 3 — Run Batch Evaluation

```bash
curl -X POST http://localhost:8000/evaluate/batch \
  -H "Content-Type: application/json" \
  -d @batch_input.json \
  -o batch_results.json

# Quick summary
cat batch_results.json | jq '.aggregate'
```

This gives you aggregate scores across your whole document corpus — exactly what you need to decide if the pipeline is production-ready.

### Step 4 — Compare GPT-4o vs Gemini Routing

The chatbot routes queries above complexity threshold 0.4 to GPT-4o and below to Gemini Flash. Use RAG Auditor's compare mode to measure whether the routing decision actually improves quality:

```python
import httpx, json

question = "What are the key architectural trade-offs in microservices?"  # high complexity
contexts = ["...retrieved chunks..."]
ground_truth = "..."

# Force GPT-4o answer (or capture from a high-complexity query)
gpt4o_eval = httpx.post("http://localhost:8000/evaluate", json={
    "question": question,
    "answer": "GPT-4o generated answer here",
    "contexts": contexts,
    "ground_truth": ground_truth,
    "mode": "full"
}).json()

# Capture Gemini answer (low-complexity routing)
gemini_eval = httpx.post("http://localhost:8000/evaluate", json={
    "question": question,
    "answer": "Gemini Flash generated answer here",
    "contexts": contexts,
    "ground_truth": ground_truth,
    "mode": "full"
}).json()

# Compare
compare = httpx.post("http://localhost:8000/evaluate/compare", json={
    "baseline": gemini_eval,
    "candidate": gpt4o_eval
}).json()

print(compare["summary"])
# e.g. "GPT-4o improved faithfulness by 12.0% and answer_relevancy by 8.0%."
```

This tells you whether the routing threshold (0.4) is correctly placed — if GPT-4o isn't consistently outscoring Gemini on hard questions, you may need to adjust the threshold.

### Step 5 — Measure RLHF Improvement Over Time

The chatbot's RLHF loop re-ranks ChromaDB results based on user thumbs up/down. To measure whether feedback is actually improving retrieval quality:

```bash
# Baseline: evaluate before users have given feedback
curl -X POST http://localhost:8000/evaluate/batch \
  -H "Content-Type: application/json" \
  -d @batch_input.json \
  -o before_rlhf.json

# ... let users interact with the chatbot and submit feedback ...

# Re-run: same questions, same contexts, re-capture from chatbot
curl -X POST http://localhost:8000/evaluate/batch \
  -H "Content-Type: application/json" \
  -d @batch_input_after.json \
  -o after_rlhf.json

# Compare aggregate context_precision scores
cat before_rlhf.json | jq '.aggregate.context_precision'
cat after_rlhf.json  | jq '.aggregate.context_precision'
```

An increase in `context_precision` after RLHF feedback confirms that re-ranking is surfacing higher-signal chunks. An increase in `context_recall` confirms fewer relevant chunks are being missed.

### What to Watch For

| Metric | What it reveals about the chatbot |
|---|---|
| **context_precision** | Whether ChromaDB's cosine similarity retrieval (top 6 → top 3) is pulling in noise |
| **context_recall** | Whether `all-MiniLM-L6-v2` embeddings capture the semantic meaning of your domain |
| **faithfulness** | Whether GPT-4o / Gemini is staying grounded or hallucinating beyond retrieved chunks |
| **answer_relevancy** | Whether the complexity router is selecting the right LLM for each query type |
| **hallucination_risk** | Claude's independent assessment — useful as a cross-check on the routing decision |

> **Expected baseline:** `all-MiniLM-L6-v2` is a lightweight embedding model optimized for speed, not domain accuracy. If `context_recall` scores below 0.70 consistently, consider upgrading to a larger embedding model (e.g. `BAAI/bge-large-en-v1.5`) and re-running the batch eval to measure the improvement.

---

## Key Design Decisions

### 1. RAGAS + Claude in combination, not either/or
RAGAS provides statistically rigorous, reproducible metrics based on dataset science. Claude provides contextual reasoning that RAGAS cannot — specifically hallucination detection and plain-English explanations. Running both in parallel via `asyncio.gather()` means neither adds latency to the other.

### 2. Weighted overall score, not a simple average
Faithfulness (35%) is weighted highest because hallucinating content is the most damaging RAG failure mode. Answer relevancy (30%) is second because an off-topic answer is equally useless regardless of how well it's grounded. Context metrics are weighted lower (20%/15%) because they diagnose the retriever, which is fixable without touching the LLM.

### 3. SSE streaming over polling
The `/evaluate/stream` endpoint emits progress events per metric so the UI can update in real time as each RAGAS metric completes. This avoids a blank "loading" state during what can be a 10–30 second evaluation.

### 4. Three-tier verdict, not a score
`READY` / `NEEDS_WORK` / `NOT_READY` gives developers and stakeholders a clear go/no-go signal without needing to interpret a float. Hallucination risk overrides the score: even a 0.95 overall score is `NOT_READY` if Claude classifies hallucination as `high`.

### 5. RAGAS → Claude fallback for dataset generation
The dataset generator first attempts RAGAS `TestsetGenerator` (which produces richer, more diverse question types using multi-hop reasoning). If RAGAS is unavailable or fails, it falls back to a direct Claude prompt that produces the same JSON schema. The caller never needs to know which path ran.

### 6. Recommendations sorted by severity, not metric
Critical issues (`score < 0.50`) surface first regardless of which metric produced them. This matches how a developer would triage — fix the worst thing first, then warnings, then informational.

---

## Extending the System

### Swap the LLM Judge

All Claude calls are isolated in `backend/services/llm_judge.py`. To use a different model, change the `model` parameter:

```python
# llm_judge.py
response = await client.messages.create(
    model="claude-sonnet-4-6",   # change this
    ...
)
```

To use a different provider entirely, replace the `anthropic.AsyncAnthropic` client with any async client that accepts the same prompt structure.

### Add a New RAGAS Metric

In `backend/services/ragas_evaluator.py`, add your metric to `metrics_config` in `stream_ragas_evaluation()` and to `_run_ragas_sync()`:

```python
from ragas.metrics import answer_correctness   # example new metric

metrics_config = [
    ...
    ("answer_correctness", "Checking answer correctness..."),
]
```

Then add it to the `Scores` model in `backend/models/evaluation.py` and the weighting dict in `backend/utils/formatters.py`.

### Change the Verdict Thresholds

Edit `score_to_verdict()` in `backend/utils/formatters.py`:

```python
def score_to_verdict(overall_score: float, hallucination_risk) -> str:
    if hallucination_risk == "high":
        return "NOT_READY"
    if overall_score >= 0.85:   # raise the bar
        return "READY"
    if overall_score >= 0.65:
        return "NEEDS_WORK"
    return "NOT_READY"
```

### Change the Score Weights

Edit the `weights` dict in `compute_overall_score()` in `backend/utils/formatters.py`. Weights are automatically re-normalized if a metric is absent, so you can adjust without breaking missing-metric cases.

### Add a New Evaluation Endpoint

Add a router file in `backend/routers/` and register it in `backend/main.py`:

```python
from routers.my_endpoint import router as my_router
app.include_router(my_router)
```

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

## Project Structure

```
rag-auditor/
│
├── .env.example                          # Template — copy to .env and add ANTHROPIC_API_KEY
├── docker-compose.yml                    # Orchestrates backend + frontend
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt                  # ragas==0.1.21, anthropic, langchain-anthropic, fastapi
│   ├── main.py                           # FastAPI app, CORS middleware, router registration
│   │
│   ├── models/
│   │   ├── evaluation.py                 # EvaluationRequest/Response, Scores, Trace, Recommendations
│   │   └── dataset.py                    # GenerateDatasetRequest/Response, QAPair
│   │
│   ├── routers/
│   │   ├── evaluate.py                   # POST /evaluate, /evaluate/stream, /evaluate/batch, /evaluate/compare
│   │   ├── generate_dataset.py           # POST /generate-dataset
│   │   └── health.py                     # GET /health
│   │
│   ├── services/
│   │   ├── ragas_evaluator.py            # RAGAS metric runner — sync executor + async SSE streaming
│   │   ├── llm_judge.py                  # Claude hallucination detector + plain-English explanation
│   │   ├── trace_analyzer.py             # Maps scores → retrieval/generation stage issues + recommendations
│   │   └── dataset_generator.py          # RAGAS TestsetGenerator with Claude fallback
│   │
│   ├── utils/
│   │   └── formatters.py                 # clamp_score(), compute_overall_score(), score_to_verdict()
│   │
│   └── tests/
│       └── test_evaluate.py              # Unit tests for formatters, trace, recommendations (no API key)
│
└── frontend/
    ├── Dockerfile
    ├── vite.config.js                    # Dev proxy → localhost:8000
    ├── src/
    │   ├── App.jsx                       # Top-level layout + tab routing
    │   ├── components/
    │   │   ├── EvaluatorForm.jsx         # Single-sample input form
    │   │   ├── ResultsDashboard.jsx      # Score cards, verdict, explanation
    │   │   ├── TraceVisualizer.jsx       # Retrieval + generation stage breakdown
    │   │   ├── HallucinationBadge.jsx    # LOW / MEDIUM / HIGH risk badge
    │   │   ├── RecommendationsPanel.jsx  # Sorted fix recommendations
    │   │   ├── BatchEvaluator.jsx        # CSV/JSON upload + aggregate results
    │   │   ├── DatasetGenerator.jsx      # Doc input + dataset download
    │   │   ├── CompareMode.jsx           # Baseline vs candidate delta view
    │   │   ├── HistoryPanel.jsx          # In-memory session history + restore
    │   │   └── ScoreCard.jsx             # Reusable per-metric score component
    │   ├── hooks/
    │   │   ├── useEvaluate.js            # SSE streaming hook for /evaluate/stream
    │   │   └── useHistory.js             # In-memory session history state
    │   ├── api/
    │   │   └── client.js                 # Axios wrappers for all backend endpoints
    │   └── utils/
    │       └── scoreHelpers.js           # Color/label helpers for score display
    └── src/utils/
        └── scoreHelpers.test.js          # Frontend unit tests
```

---

## Configuration

All settings are loaded from `.env` (copy from `.env.example`):

| Variable | Default | Required | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | — | Yes | Anthropic API key — used for RAGAS judge LLM, hallucination detection, and explanations |
| `RAGAS_APP_TOKEN` | — | No | RAGAS Cloud token for dashboard and experiment tracking |
| `CORS_ORIGINS` | `http://localhost:3000` | No | Comma-separated list of allowed frontend origins |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to submit issues, PRs, and run tests.

## License

MIT — see [LICENSE](LICENSE)
