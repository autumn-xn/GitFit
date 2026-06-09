# ─── backend/prompts/analysis.py ─────────────────────────────────────────────
# Prompt templates for LLM-powered repository analysis.
#
# The system prompt instructs the LLM to act as a senior architect.
# build_analysis_prompt() formats all available repo data into a
# structured user prompt that the LLM can reason over.
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations


SYSTEM_PROMPT = """\
You are a senior software architect and code reviewer. You are analyzing a \
GitHub repository based on its README, file tree, language breakdown, and \
detected quality signals.

Your task is to produce a structured JSON analysis with three sections: \
architecture, code_quality, and security.

Rules:
- Be specific and actionable — avoid generic filler statements.
- Reference actual files and directories from the file tree when possible.
- Keep the architecture summary to 2–4 sentences.
- score_adjustment should be between -20 and +20 (relative to the heuristic baseline).
- dependency_audit must be exactly one of: "clean", "outdated", "vulnerable", "unknown".
- Respond with ONLY valid JSON. No markdown fencing, no commentary, no extra text.

Required JSON schema:
{
  "architecture": {
    "summary": "2-4 sentence overview of the project purpose, architecture, and key design decisions",
    "patterns": ["architectural patterns, e.g. MVC, Microservices, Monorepo, REST API"],
    "recommendations": ["1-3 actionable architecture improvement suggestions"]
  },
  "code_quality": {
    "score_adjustment": 0,
    "notes": ["3-5 specific observations about code quality, testing, CI, documentation"]
  },
  "security": {
    "dependency_audit": "unknown",
    "notes": ["2-4 specific security observations and recommendations"]
  }
}
"""


def build_analysis_prompt(
    repo_full_name: str,
    description: str | None,
    readme: str | None,
    tree_paths: list[str],
    lang_breakdown: list[dict],
    quality_flags: dict[str, bool],
    arch_patterns: list[str],
    entry_points: list[str],
    key_directories: list[str],
) -> str:
    """
    Format all available repo data into a structured user prompt.

    Large fields (README, file tree) are truncated to stay within
    reasonable token limits while preserving the most useful context.
    """
    sections: list[str] = [f"# Repository: {repo_full_name}"]

    # ── Description ───────────────────────────────────────────────────────
    if description:
        sections.append(f"\n## Description\n{description}")

    # ── README (truncated to ~4 000 chars) ────────────────────────────────
    if readme:
        truncated = readme[:4000]
        if len(readme) > 4000:
            truncated += "\n\n[... README truncated ...]"
        sections.append(f"\n## README\n{truncated}")
    else:
        sections.append("\n## README\nNo README found.")

    # ── Language breakdown ────────────────────────────────────────────────
    lang_lines = [
        f"- {entry['language']}: {entry['percentage']}% ({entry['bytes']:,} bytes)"
        for entry in lang_breakdown[:10]
    ]
    sections.append("\n## Languages\n" + "\n".join(lang_lines))

    # ── File tree (capped at 500 paths) ──────────────────────────────────
    tree_sample = tree_paths[:500]
    tree_str = "\n".join(tree_sample)
    if len(tree_paths) > 500:
        tree_str += f"\n\n[... {len(tree_paths) - 500} more files ...]"
    sections.append(f"\n## File Tree ({len(tree_paths)} total files)\n{tree_str}")

    # ── Pre-detected signals (from heuristics) ───────────────────────────
    flags_str = "\n".join(
        f"- {key}: {'Yes' if val else 'No'}"
        for key, val in quality_flags.items()
    )
    sections.append(f"\n## Detected Quality Signals\n{flags_str}")

    sections.append(
        "\n## Detected Architecture Patterns (heuristic)\n"
        + ", ".join(arch_patterns)
    )

    if entry_points:
        sections.append(
            "\n## Entry Points\n" + ", ".join(entry_points)
        )

    if key_directories:
        sections.append(
            "\n## Key Directories\n" + ", ".join(key_directories)
        )

    sections.append(
        "\n---\n"
        "Analyze this repository and respond with the JSON analysis."
    )

    return "\n".join(sections)
