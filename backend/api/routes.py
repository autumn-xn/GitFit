# ─── backend/api/routes.py ────────────────────────────────────────────────────
import time
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter

from api.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    AnalysisResult,
    RepoMeta,
    LanguageBreakdown,
    Contributor,
    WeeklyActivity,
    ArchitectureInsight,
    CodeQuality,
    SecurityFlags,
)
from github.reader import fetch_repo, RepoFetchResult
from agent.workflow import analyze_with_llm

log = logging.getLogger("github_analyzer.routes")
router = APIRouter()


# ─── Heuristic helpers ────────────────────────────────────────────────────────

def _heuristic_summary(fetch: RepoFetchResult) -> str:
    top_langs = [
        r["language"] for r in fetch.lang_breakdown[:2]
        if r["language"] != "Other"
    ]
    lang_str = " and ".join(top_langs) if top_langs else "multiple languages"
    pat_str  = ", ".join(fetch.arch_patterns[:2]) if fetch.arch_patterns else "a standard layout"
    n_contrib = len(fetch.contributors)

    return (
        f"{fetch.info.full_name} is a {lang_str} project with "
        f"{fetch.info.stars:,} stars and {n_contrib} tracked contributor"
        f"{'s' if n_contrib != 1 else ''}. "
        f"The codebase follows {pat_str}."
    )


def _compute_quality_score(flags: dict[str, bool]) -> int:
    score = 50
    score += 15 if flags.get("has_tests")  else 0
    score += 15 if flags.get("has_ci")     else 0
    score += 10 if flags.get("has_docs")   else 0
    score += 7  if flags.get("has_linter") else 0
    score += 3  if flags.get("has_docker") else 0
    return min(score, 100)


def _quality_notes(flags: dict[str, bool]) -> list[str]:
    notes = []
    if flags.get("has_tests"):
        notes.append("Test suite detected.")
    else:
        notes.append("No test directory detected — consider adding automated tests.")
    if flags.get("has_ci"):
        notes.append("CI/CD pipeline configuration found.")
    else:
        notes.append("No CI configuration detected.")
    if flags.get("has_docs"):
        notes.append("Documentation folder present.")
    if flags.get("has_linter"):
        notes.append("Linter or formatter configuration found.")
    else:
        notes.append("No linter config detected — code style may be inconsistent.")
    if flags.get("has_docker"):
        notes.append("Docker support configured.")
    return notes


def _security_notes(flags: dict[str, bool]) -> list[str]:
    notes = []
    if flags.get("has_env_example"):
        notes.append(".env.example present — good onboarding practice.")
    else:
        notes.append(
            "No .env.example found; new contributors may miss required env vars."
        )
    if flags.get("exposes_secrets"):
        notes.append("⚠ Possible secret file (.env / credentials) detected in the tree.")
    else:
        notes.append("No obvious secret files detected in the repository tree.")
    notes.append(
        "Dependency vulnerability audit requires runtime tooling (npm audit / pip-audit)."
    )
    return notes


def _build_result(
    fetch: RepoFetchResult,
    llm_analysis: dict | None = None,
) -> AnalysisResult:
    flags   = fetch.quality_flags
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if llm_analysis:
        ai_arch = llm_analysis.get("architecture", {})
        ai_cq   = llm_analysis.get("code_quality", {})
        ai_sec  = llm_analysis.get("security", {})

        summary          = ai_arch.get("summary", _heuristic_summary(fetch))
        patterns         = ai_arch.get("patterns", fetch.arch_patterns)

        base_score       = _compute_quality_score(flags)
        adjustment       = int(ai_cq.get("score_adjustment", 0))
        quality_score    = max(0, min(100, base_score + adjustment))
        quality_notes_ls = ai_cq.get("notes", _quality_notes(flags))

        dep_audit        = ai_sec.get("dependency_audit", "unknown")
        sec_notes_ls     = ai_sec.get("notes", _security_notes(flags))

        log.info("Using AI-generated analysis (score adj: %+d)", adjustment)
    else:
        summary          = _heuristic_summary(fetch)
        patterns         = fetch.arch_patterns
        quality_score    = _compute_quality_score(flags)
        quality_notes_ls = _quality_notes(flags)
        dep_audit        = "unknown"
        sec_notes_ls     = _security_notes(flags)

    return AnalysisResult(
        meta=RepoMeta(
            owner          = fetch.info.owner,
            name           = fetch.info.name,
            full_name      = fetch.info.full_name,
            description    = fetch.info.description,
            url            = fetch.info.html_url,
            stars          = fetch.info.stars,
            forks          = fetch.info.forks,
            open_issues    = fetch.info.open_issues,
            watchers       = fetch.info.watchers,
            default_branch = fetch.info.default_branch,
            created_at     = fetch.info.created_at,
            updated_at     = fetch.info.updated_at,
            license        = fetch.info.license_name,
            is_private     = fetch.info.is_private,
            topics         = fetch.info.topics,
        ),
        languages=[
            LanguageBreakdown(
                language   = row["language"],
                bytes      = row["bytes"],
                percentage = row["percentage"],
            )
            for row in fetch.lang_breakdown
        ],
        contributors=[
            Contributor(
                login        = c.login,
                avatar_url   = c.avatar_url,
                profile_url  = c.profile_url,
                contributions= c.contributions,
            )
            for c in fetch.contributors
        ],
        activity=[
            WeeklyActivity(
                week      = w.week_iso,
                commits   = w.commits,
                additions = w.additions,
                deletions = w.deletions,
            )
            for w in fetch.weekly_activity
        ],
        architecture=ArchitectureInsight(
            summary         = summary,
            patterns        = patterns,
            entry_points    = fetch.entry_points,
            key_directories = fetch.key_directories,
        ),
        code_quality=CodeQuality(
            score      = quality_score,
            has_tests  = flags["has_tests"],
            has_ci     = flags["has_ci"],
            has_docs   = flags["has_docs"],
            has_linter = flags["has_linter"],
            has_docker = flags["has_docker"],
            notes      = quality_notes_ls,
        ),
        security=SecurityFlags(
            has_env_example  = flags["has_env_example"],
            exposes_secrets  = flags["exposes_secrets"],
            dependency_audit = dep_audit,
            notes            = sec_notes_ls,
        ),
        analyzed_at=now_str,
    )


# ─── Cache ────────────────────────────────────────────────────────────────────

class SimpleCache:
    def __init__(self, ttl_seconds: int = 600):
        self.ttl = ttl_seconds
        self.store: dict[str, tuple[AnalysisResult, float]] = {}

    def get(self, key: str) -> Optional[AnalysisResult]:
        if key in self.store:
            val, timestamp = self.store[key]
            if time.time() - timestamp < self.ttl:
                return val
            del self.store[key]
        return None

    def set(self, key: str, value: AnalysisResult) -> None:
        self.store[key] = (value, time.time())


_analyze_cache = SimpleCache(ttl_seconds=600)  # 10 minutes


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/health", tags=["meta"])
async def health() -> dict:
    """Liveness check called by the frontend on startup."""
    return {"status": "ok", "version": "0.2.0"}


@router.post("/analyze", response_model=AnalyzeResponse, tags=["analysis"])
async def analyze(body: AnalyzeRequest) -> AnalyzeResponse:
    """
    Step 2 — Live GitHub data.
    Step 4 — AI-powered analysis with heuristic fallback.
    """
    log.info("analyze  url=%s", body.url)

    try:
        cached_result = _analyze_cache.get(body.url)
        if cached_result:
            log.info("Returning cached analysis for %s", body.url)
            return AnalyzeResponse(success=True, data=cached_result)

        fetch = await fetch_repo(body.url)
        llm_analysis = await analyze_with_llm(fetch)
        
        result = _build_result(fetch, llm_analysis)
        _analyze_cache.set(body.url, result)

        return AnalyzeResponse(success=True, data=result)

    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status == 404:
            msg = "Repository not found. Check the URL and make sure the repo is public."
        elif status in (403, 429):
            msg = "GitHub API rate limit reached. Add GITHUB_TOKEN=ghp_... to your backend/.env file for 5 000 requests/hour."
        else:
            msg = f"GitHub API returned an unexpected error (HTTP {status})."
        log.warning("GitHub API error  url=%s  status=%d", body.url, status)
        return AnalyzeResponse(success=False, error=msg)

    except ValueError as exc:
        return AnalyzeResponse(success=False, error=str(exc))

    except httpx.TimeoutException:
        log.warning("GitHub API timeout  url=%s", body.url)
        return AnalyzeResponse(
            success=False,
            error="GitHub API timed out. Please try again in a moment.",
        )

    except Exception as exc:
        log.exception("Unexpected error  url=%s", body.url)
        return AnalyzeResponse(success=False, error=f"Unexpected error: {exc}")
