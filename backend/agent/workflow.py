# ─── backend/agent/workflow.py ────────────────────────────────────────────────
# LangGraph workflow for AI-powered repository analysis.
#
# The graph is intentionally simple — two nodes in a linear chain:
#
#   prepare  ──▶  analyze  ──▶  END
#
# If the analyze node fails (no API key, timeout, bad JSON), it records
# the error in state.  The public entry-point analyze_with_llm() checks
# for errors and returns None, letting main.py fall back to heuristics.
#
# Public API
# ----------
#   analyze_with_llm(fetch: RepoFetchResult) -> dict | None
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import logging
from typing import Optional

from langgraph.graph import StateGraph, END

from agent.state import AnalysisState
from agent.tools import call_llm_analysis
from prompts.analysis import SYSTEM_PROMPT, build_analysis_prompt
from github.reader import RepoFetchResult

log = logging.getLogger("github_analyzer.agent")


# ─── Graph nodes ──────────────────────────────────────────────────────────────


def prepare(state: AnalysisState) -> AnalysisState:
    """Node 1: inject the system prompt into the state."""
    return {
        **state,
        "system_prompt": SYSTEM_PROMPT,
    }


async def analyze(state: AnalysisState) -> AnalysisState:
    """Node 2: call the LLM and parse the JSON response."""
    try:
        result = await call_llm_analysis(
            system_prompt=state["system_prompt"],
            user_prompt=state["prompt"],
        )
        return {**state, "llm_output": result, "error": None}
    except Exception as exc:
        log.warning("LLM analysis failed: %s", exc)
        return {**state, "llm_output": None, "error": str(exc)}


# ─── Graph construction ──────────────────────────────────────────────────────


def _build_graph():
    """Compile the analysis StateGraph once at import time."""
    graph = StateGraph(AnalysisState)

    graph.add_node("prepare", prepare)
    graph.add_node("analyze", analyze)

    graph.set_entry_point("prepare")
    graph.add_edge("prepare", "analyze")
    graph.add_edge("analyze", END)

    return graph.compile()


_compiled_graph = _build_graph()


# ─── Public API ───────────────────────────────────────────────────────────────


async def analyze_with_llm(fetch: RepoFetchResult) -> Optional[dict]:
    """
    Run the LLM analysis workflow on fetched repository data.

    Returns
    -------
    dict
        Parsed analysis with keys ``architecture``, ``code_quality``,
        and ``security`` — ready for ``_build_result()`` in ``main.py``.
    None
        If the LLM call failed for any reason (no key, timeout,
        invalid JSON, etc.).  The caller should fall back to
        heuristic analysis.
    """
    # ── Build the user prompt from all available repo data ────────────────
    prompt = build_analysis_prompt(
        repo_full_name  = fetch.info.full_name,
        description     = fetch.info.description,
        readme          = fetch.readme,
        tree_paths      = fetch.tree_paths,
        lang_breakdown  = fetch.lang_breakdown,
        quality_flags   = fetch.quality_flags,
        arch_patterns   = fetch.arch_patterns,
        entry_points    = fetch.entry_points,
        key_directories = fetch.key_directories,
    )

    initial_state: AnalysisState = {
        "prompt":        prompt,
        "system_prompt": "",       # overwritten by the prepare node
        "llm_output":    None,
        "error":         None,
    }

    try:
        final_state = await _compiled_graph.ainvoke(initial_state)

        if final_state.get("error"):
            log.warning(
                "LLM workflow completed with error: %s",
                final_state["error"],
            )
            return None

        output = final_state.get("llm_output")
        if output:
            log.info("LLM analysis completed successfully")
        return output

    except Exception as exc:
        log.exception("LLM workflow crashed unexpectedly: %s", exc)
        return None
