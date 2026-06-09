# ─── backend/agent/state.py ──────────────────────────────────────────────────
# LangGraph state schema for the repository analysis workflow.
#
# The state flows through the graph nodes:
#   prepare → analyze → END
#
# If `error` is set after the analyze node, the caller falls back
# to heuristic analysis — the graph itself never crashes.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

from typing import Optional, TypedDict


class AnalysisState(TypedDict, total=False):
    """State dict passed through the LangGraph analysis workflow."""

    # ── Input (set before graph invocation) ───────────────────────────────
    prompt: str                    # Formatted user prompt
    system_prompt: str             # System instructions for the LLM

    # ── Output (set by graph nodes) ───────────────────────────────────────
    llm_output: Optional[dict]     # Parsed JSON from the LLM response
    error: Optional[str]           # Error message — triggers heuristic fallback
