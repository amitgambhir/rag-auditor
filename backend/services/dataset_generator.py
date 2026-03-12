"""Synthetic golden dataset generation using RAGAS and Claude."""
from __future__ import annotations
import asyncio
import json
import os
from functools import partial
from typing import Optional
import anthropic

_client: Optional[anthropic.AsyncAnthropic] = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _client


async def _run_in_executor(fn, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(fn, *args))


def _generate_with_ragas(documents: list[str], num_questions: int) -> list[dict]:
    """Try RAGAS TestsetGenerator — falls back to Claude if unavailable."""
    from ragas.testset.generator import TestsetGenerator
    from ragas.testset.evolutions import simple, reasoning, multi_context
    from langchain_anthropic import ChatAnthropic
    from langchain.schema import Document

    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from langchain_community.embeddings import FakeEmbeddings

    judge_llm = LangchainLLMWrapper(
        ChatAnthropic(
            model="claude-sonnet-4-6",
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        )
    )
    embeddings = LangchainEmbeddingsWrapper(FakeEmbeddings(size=768))

    generator = TestsetGenerator.from_langchain(
        generator_llm=judge_llm,
        critic_llm=judge_llm,
        embeddings=embeddings,
    )
    docs = [Document(page_content=doc, metadata={"source": f"doc_{i}"}) for i, doc in enumerate(documents)]

    testset = generator.generate_with_langchain_docs(
        docs,
        test_size=num_questions,
        distributions={simple: 0.5, reasoning: 0.3, multi_context: 0.2},
    )
    df = testset.to_pandas()
    pairs = []
    for _, row in df.iterrows():
        pairs.append({
            "question": str(row.get("question", "")),
            "answer": str(row.get("answer", "")),
            "ground_truth": str(row.get("ground_truth", row.get("answer", ""))),
            "contexts": list(row.get("contexts", [])) if row.get("contexts") is not None else [],
            "evolution_type": str(row.get("evolution_type", "simple")),
        })
    return pairs


GENERATION_SYSTEM = """You are an expert dataset creator for RAG system evaluation.
Given source documents, generate realistic question-answer pairs that test different
aspects of a RAG system. Create diverse questions: factual, inferential, multi-hop.

For each Q&A pair, provide:
- A realistic user question
- A comprehensive answer grounded in the documents
- The exact ground truth (correct answer)
- The relevant context passages (verbatim excerpts)
- An evolution type: "simple", "reasoning", or "multi_context"

Return a JSON array. Each element:
{
  "question": "...",
  "answer": "...",
  "ground_truth": "...",
  "contexts": ["passage1", "passage2"],
  "evolution_type": "simple" | "reasoning" | "multi_context"
}"""


async def generate_with_claude(documents: list[str], num_questions: int) -> list[dict]:
    """Generate Q&A pairs using Claude directly when RAGAS is unavailable."""
    client = _get_client()
    doc_text = "\n\n===\n\n".join(
        f"Document {i+1}:\n{doc[:3000]}" for i, doc in enumerate(documents[:5])
    )
    prompt = f"""Source documents:

{doc_text}

Generate exactly {num_questions} diverse Q&A pairs for RAG evaluation.
Include a mix of simple, reasoning-based, and multi-context questions.
Return only valid JSON — no explanation."""

    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=GENERATION_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    pairs = json.loads(text)
    return pairs[:num_questions]


async def generate_dataset(documents: list[str], num_questions: int) -> list[dict]:
    """Generate a synthetic golden dataset. Tries RAGAS first, falls back to Claude."""
    try:
        pairs = await _run_in_executor(_generate_with_ragas, documents, num_questions)
        return pairs
    except Exception:
        # Fall back to Claude-based generation
        return await generate_with_claude(documents, num_questions)
