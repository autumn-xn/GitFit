# ─── backend/agent/tools.py ──────────────────────────────────────────────────
# LLM interaction layer for repository analysis.
#
# Uses Google Gemini via LangChain.  Falls back gracefully when
# GOOGLE_API_KEY is not set — the caller receives a RuntimeError
# which the workflow translates into a None result (heuristic fallback).
#
# Override the model with the LLM_MODEL env var (default: gemini-2.0-flash).
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import json
import logging
import os
import re
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

log = logging.getLogger("github_analyzer.agent")

# ─── Defaults ─────────────────────────────────────────────────────────────────

_DEFAULT_MODEL = "gemini-2.0-flash"


# ─── Model factory ────────────────────────────────────────────────────────────


def _get_model() -> Optional[ChatGoogleGenerativeAI]:
    """
    Create the LLM client.

    Returns None if no API key is configured, letting the caller
    decide whether to raise or fall back.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        log.warning(
            "GOOGLE_API_KEY not set — LLM analysis disabled, "
            "using heuristic fallback"
        )
        return None

    model_name = os.getenv("LLM_MODEL", _DEFAULT_MODEL)
    log.info("Using LLM model: %s", model_name)

    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=0.2,
        max_output_tokens=2048,
        timeout=30,
    )


# ─── Response parsing ─────────────────────────────────────────────────────────


def _extract_json(text: str) -> dict:
    """
    Extract JSON from the LLM response.

    Handles the common case where the model wraps its output in
    ```json ... ``` fences despite being told not to.
    """
    # Strip markdown code fences if present
    fenced = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)

    return json.loads(text.strip())


# ─── Public API ───────────────────────────────────────────────────────────────


async def call_llm_analysis(system_prompt: str, user_prompt: str) -> dict:
    """
    Call the LLM with the analysis prompts and return parsed JSON.

    Raises
    ------
    RuntimeError
        If no API key is configured.
    ValueError
        If the LLM response cannot be parsed as valid JSON or
        is missing required top-level keys.
    """
    model = _get_model()
    if model is None:
        raise RuntimeError("No LLM API key configured")

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    log.info("Calling LLM for repository analysis...")
    response = await model.ainvoke(messages)

    raw_text = response.content
    log.info("LLM response received (%d chars)", len(raw_text))

    # ── Parse JSON ────────────────────────────────────────────────────────
    try:
        result = _extract_json(raw_text)
    except json.JSONDecodeError as exc:
        log.warning(
            "Failed to parse LLM JSON: %s\nRaw response (first 500 chars): %s",
            exc,
            raw_text[:500],
        )
        raise ValueError(f"LLM returned invalid JSON: {exc}") from exc

    # ── Validate required keys ────────────────────────────────────────────
    for key in ("architecture", "code_quality", "security"):
        if key not in result:
            raise ValueError(f"LLM response missing required key: '{key}'")

    return result
