# ─── backend/main.py ──────────────────────────────────────────────────────────
# Step 1 — FastAPI app with stub /analyze endpoint.
# Returns a hardcoded AnalysisResult so the full frontend ↔ backend
# HTTP flow can be tested immediately, with no GitHub API or LLM calls yet.
#
# Run with:  uvicorn main:app --reload
# Or:        python main.py

import re
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

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
    version="0.1.0",
    description="AI-powered GitHub repository analysis — Step 1 stub",
)

# Allow the Vite dev server (port 5173) and a generic port 3000 to call us.
# Expand this list in production or read it from .env.
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

# ─── Stub data ────────────────────────────────────────────────────────────────
# A realistic-looking AnalysisResult for facebook/react.
# Every field matches the TypeScript type so the Results page renders
# as soon as you build it — no waiting on the real API.

def _stub_activity() -> list[WeeklyActivity]:
    """12 weeks of deterministic activity (no randomness → no test flakiness)."""
    commits   = [45, 38, 62, 71, 55, 80, 48, 60, 53, 66, 74, 58]
    additions = [2100, 1800, 3200, 4100, 2700, 5000, 2300, 3600, 2900, 3800, 4400, 3200]
    deletions = [ 800,  600, 1100, 1500,  900, 1900,  700, 1300, 1000, 1400, 1700, 1200]
    now = datetime.now(timezone.utc)
    return [
        WeeklyActivity(
            week=(now - timedelta(weeks=11 - i)).strftime("%Y-%m-%dT00:00:00Z"),
            commits=commits[i],
            additions=additions[i],
            deletions=deletions[i],
        )
        for i in range(12)
    ]


_STUB_DATA = AnalysisResult(
    meta=RepoMeta(
        owner="facebook",
        name="react",
        full_name="facebook/react",
        description="The library for web and native user interfaces.",
        url="https://github.com/facebook/react",
        stars=226_000,
        forks=46_100,
        open_issues=892,
        watchers=6_700,
        default_branch="main",
        created_at="2013-05-24T16:15:54Z",
        updated_at="2024-12-01T10:30:00Z",
        license="MIT",
        is_private=False,
        topics=["javascript", "ui", "frontend", "declarative", "react"],
    ),
    languages=[
        LanguageBreakdown(language="JavaScript", bytes=12_450_000, percentage=68.4),
        LanguageBreakdown(language="TypeScript",  bytes=3_890_000, percentage=21.3),
        LanguageBreakdown(language="HTML",          bytes=540_000, percentage=3.0),
        LanguageBreakdown(language="CSS",           bytes=380_000, percentage=2.1),
        LanguageBreakdown(language="Other",         bytes=960_000, percentage=5.2),
    ],
    contributors=[
        Contributor(
            login="gaearon",
            avatar_url="https://avatars.githubusercontent.com/u/810438",
            profile_url="https://github.com/gaearon",
            contributions=3842,
        ),
        Contributor(
            login="sebmarkbage",
            avatar_url="https://avatars.githubusercontent.com/u/63648",
            profile_url="https://github.com/sebmarkbage",
            contributions=2910,
        ),
        Contributor(
            login="acdlite",
            avatar_url="https://avatars.githubusercontent.com/u/3624098",
            profile_url="https://github.com/acdlite",
            contributions=2104,
        ),
        Contributor(
            login="sophiebits",
            avatar_url="https://avatars.githubusercontent.com/u/6820473",
            profile_url="https://github.com/sophiebits",
            contributions=1876,
        ),
    ],
    activity=_stub_activity(),
    architecture=ArchitectureInsight(
        summary=(
            "React is a monorepo organised around independently publishable packages. "
            "The core reconciler (react-reconciler) is renderer-agnostic; concrete "
            "renderers such as react-dom plug into it via a HostConfig interface."
        ),
        patterns=["Monorepo", "Plugin architecture", "Virtual DOM", "Fiber reconciler"],
        entry_points=["packages/react/index.js", "packages/react-dom/index.js"],
        key_directories=["packages/", "scripts/", "fixtures/", "__tests__/"],
    ),
    code_quality=CodeQuality(
        score=91,
        has_tests=True,
        has_ci=True,
        has_docs=True,
        has_linter=True,
        has_docker=False,
        notes=[
            "Comprehensive Jest test suite with >95% coverage on core packages.",
            "GitHub Actions CI runs tests across multiple Node versions.",
            "ESLint enforced project-wide with custom react-hooks plugin rules.",
            "No Dockerfile — library packages are not typically containerised.",
        ],
    ),
    security=SecurityFlags(
        has_env_example=False,
        exposes_secrets=False,
        dependency_audit="clean",
        notes=[
            "No server-side secrets — pure frontend library.",
            "Dependabot enabled; no high-severity advisories detected.",
        ],
    ),
    # analyzed_at is intentionally blank here; the endpoint fills it fresh
    # on every request so the timestamp in the UI is always accurate.
    analyzed_at="",
)

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health", tags=["meta"])
async def health() -> dict:
    """
    Liveness check.
    The frontend calls this on startup (see api/client.ts → checkHealth).
    """
    return {"status": "ok", "version": "0.1.0"}


@app.post("/analyze", response_model=AnalyzeResponse, tags=["analysis"])
async def analyze(body: AnalyzeRequest) -> AnalyzeResponse:
    """
    STEP 1 — Stub endpoint.

    Accepts any valid github.com URL and returns a hardcoded AnalysisResult
    for facebook/react. The URL is validated but not actually fetched yet.

    Steps 2–4 replace this with:
      • github/reader.py  →  real GitHub API data
      • prompts/analysis.py + LLM call  →  real AI analysis
      • agent/workflow.py  →  multi-step LangGraph agent
    """
    log.info("analyze  url=%s", body.url)

    # Stamp the current time on each response so the UI shows a fresh timestamp
    result = _STUB_DATA.model_copy(
        update={"analyzed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    )

    return AnalyzeResponse(success=True, data=result)


# ─── Dev entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
