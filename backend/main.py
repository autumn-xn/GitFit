# ─── backend/main.py ──────────────────────────────────────────────────────────
# Step 2 — Real GitHub data replaces the hardcoded stub.
# The /analyze endpoint now calls github/reader.py and returns live repo data.
#
# Run with:  uvicorn main:app --reload
# Or:        python main.py
#
# Create backend/.env (or project-root .env) with:
#   GITHUB_TOKEN=ghp_your_token_here
#
# Without a token you still work, but GitHub limits you to 60 req/hr.
# With a token you get 5 000 req/hr — enough for heavy development use.

import re
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from github.reader import fetch_repo, RepoFetchResult

# Must be called before any os.getenv() reads happen
load_dotenv()

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s %(name)s  %(message)s",
)
log = logging.getLogger("github_analyzer")

# ─── Pydantic Models ──────────────────────────────────────────────────────────
# These mirror frontend/src/types/index.ts exactly — same field names,
# same nesting. In Step 3 they move to backend/api/schemas.py and are
# imported here; for now keeping everything in one file is simpler.

class RepoMeta(BaseModel):
    owner: str
    name: str
    full_name: str
    description: Optional[str] = None
    url: str
    stars: int
    forks: int
    open_issues: int
    watchers: int
    default_branch: str
    created_at: str       # ISO 8601
    updated_at: str       # ISO 8601
    license: Optional[str] = None
    is_private: bool
    topics: list[str]


class LanguageBreakdown(BaseModel):
    language: str
    bytes: int
    percentage: float     # 0–100, one decimal place


class Contributor(BaseModel):
    login: str
    avatar_url: str
    profile_url: str
    contributions: int    # commit count


class WeeklyActivity(BaseModel):
    week: str             # ISO date string, start of week
    commits: int
    additions: int
    deletions: int


class ArchitectureInsight(BaseModel):
    summary: str          # 2–3 sentence overview
    patterns: list[str]   # e.g. ["MVC", "Monorepo"]
    entry_points: list[str]
    key_directories: list[str]


class CodeQuality(BaseModel):
    score: int            # 0–100
    has_tests: bool
    has_ci: bool
    has_docs: bool
    has_linter: bool
    has_docker: bool
    notes: list[str]


class SecurityFlags(BaseModel):
    has_env_example: bool
    exposes_secrets: bool
    dependency_audit: str  # "clean" | "outdated" | "vulnerable" | "unknown"
    notes: list[str]


class AnalysisResult(BaseModel):
    meta: RepoMeta
    languages: list[LanguageBreakdown]
    contributors: list[Contributor]
    activity: list[WeeklyActivity]
    architecture: ArchitectureInsight
    code_quality: CodeQuality
    security: SecurityFlags
    analyzed_at: str      # ISO 8601 timestamp


# ─── Request / Response wrappers ──────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def must_be_github_repo(cls, v: str) -> str:
        """Reject anything that isn't a github.com/owner/repo URL."""
        pattern = r"^https?://(www\.)?github\.com/[\w.\-]+/[\w.\-]+"
        if not re.match(pattern, v.strip()):
            raise ValueError("Must be a valid github.com repository URL")
        return v.strip()


class AnalyzeResponse(BaseModel):
    success: bool
    data: Optional[AnalysisResult] = None
    error: Optional[str] = None


# ─── FastAPI app ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="GitHub Analyzer API",
    version="0.2.0",
    description="AI-powered GitHub repository analysis — Step 2: real GitHub data",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Heuristic helpers (will be replaced by LLM calls in Step 4) ─────────────

def _heuristic_summary(fetch: RepoFetchResult) -> str:
    """
    Build a plain-English summary from fetched data.
    Step 4 replaces this with a genuine LLM-generated architectural overview.
    """
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
    """
    Score 0–100 from detected quality signals.
      50 base + up to 50 for good practices.
    """
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


def _build_result(fetch: RepoFetchResult) -> AnalysisResult:
    """
    Convert a RepoFetchResult (from github/reader.py) into a fully
    typed AnalysisResult that the frontend expects.
    """
    flags   = fetch.quality_flags
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

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
            summary         = _heuristic_summary(fetch),
            patterns        = fetch.arch_patterns,
            entry_points    = fetch.entry_points,
            key_directories = fetch.key_directories,
        ),
        code_quality=CodeQuality(
            score      = _compute_quality_score(flags),
            has_tests  = flags["has_tests"],
            has_ci     = flags["has_ci"],
            has_docs   = flags["has_docs"],
            has_linter = flags["has_linter"],
            has_docker = flags["has_docker"],
            notes      = _quality_notes(flags),
        ),
        security=SecurityFlags(
            has_env_example  = flags["has_env_example"],
            exposes_secrets  = flags["exposes_secrets"],
            dependency_audit = "unknown",   # Step 4: LLM / runtime audit
            notes            = _security_notes(flags),
        ),
        analyzed_at=now_str,
    )


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health", tags=["meta"])
async def health() -> dict:
    """Liveness check called by the frontend on startup."""
    return {"status": "ok", "version": "0.2.0"}


@app.post("/analyze", response_model=AnalyzeResponse, tags=["analysis"])
async def analyze(body: AnalyzeRequest) -> AnalyzeResponse:
    """
    Step 2 — Live GitHub data.

    Fetches real repository data from the GitHub REST API.
    Architecture summary and quality notes are heuristic for now;
    Step 4 (LLM integration) will replace them with AI-generated content.
    """
    log.info("analyze  url=%s", body.url)

    try:
        fetch = await fetch_repo(body.url)
        return AnalyzeResponse(success=True, data=_build_result(fetch))

    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status == 404:
            msg = (
                "Repository not found. "
                "Check the URL and make sure the repo is public."
            )
        elif status in (403, 429):
            msg = (
                "GitHub API rate limit reached. "
                "Add GITHUB_TOKEN=ghp_... to your backend/.env file "
                "for 5 000 requests/hour."
            )
        else:
            msg = f"GitHub API returned an unexpected error (HTTP {status})."
        log.warning("GitHub API error  url=%s  status=%d", body.url, status)
        return AnalyzeResponse(success=False, error=msg)

    except ValueError as exc:
        # parse_github_url raised — shouldn't normally reach here because
        # the Pydantic validator on AnalyzeRequest already checks the URL,
        # but keep it as a safety net.
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


# ─── Dev entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)