# ─── backend/api/schemas.py ───────────────────────────────────────────────────
from typing import Optional
from pydantic import BaseModel, field_validator


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


class AnalyzeRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def strip_url(cls, v: str) -> str:
        """Trim whitespace; detailed validation happens in github.reader."""
        s = v.strip()
        if not s:
            raise ValueError("Please enter a repository link or owner/repo.")
        if len(s) > 2048:
            raise ValueError("URL is too long.")
        return s


class AnalyzeResponse(BaseModel):
    success: bool
    data: Optional[AnalysisResult] = None
    error: Optional[str] = None
