"""Centralized configuration loaded from environment variables."""
from __future__ import annotations
import os

# LLM model
ANTHROPIC_MODEL: str = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# Token budgets per call type
MAX_TOKENS_HALLUCINATION: int = int(os.environ.get("MAX_TOKENS_HALLUCINATION", "1024"))
MAX_TOKENS_EXPLANATION: int = int(os.environ.get("MAX_TOKENS_EXPLANATION", "256"))
MAX_TOKENS_GENERATION: int = int(os.environ.get("MAX_TOKENS_GENERATION", "4096"))

# Retry and timeout
LLM_MAX_RETRIES: int = int(os.environ.get("LLM_MAX_RETRIES", "2"))
LLM_TIMEOUT: float = float(os.environ.get("LLM_TIMEOUT", "60.0"))
