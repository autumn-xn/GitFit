# ─── backend/github/reader.py ────────────────────────────────────────────────
# Step 2 — GitHub REST API reader.
#
# Public entry-point:
#   from github.reader import fetch_repo, RepoFetchResult
#
#   result = await fetch_repo(
#       "https://github.com/vercel/next.js",
#       token="ghp_..."    # optional; falls back to GITHUB_TOKEN env var
#   )
#
# All API calls are fired concurrently via asyncio.gather to minimise
# wall-clock time.  The returned RepoFetchResult contains both raw API
# data and pre-computed heuristics (quality flags, arch patterns, etc.)
# so main.py only has to assemble Pydantic models, not crunch data.
#
# GitHub API docs used:
#   GET /repos/{owner}/{repo}
#   GET /repos/{owner}/{repo}/languages
#   GET /repos/{owner}/{repo}/contributors
#   GET /repos/{owner}/{repo}/stats/commit_activity   (52-week commit counts)
#   GET /repos/{owner}/{repo}/stats/code_frequency    (52-week add/del counts)
#   GET /repos/{owner}/{repo}/readme
#   GET /repos/{owner}/{repo}/git/trees/{branch}?recursive=1
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import asyncio
import base64
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import httpx

# ─── Constants ────────────────────────────────────────────────────────────────

_API_BASE = "https://api.github.com"

_GITHUB_URL_RE = re.compile(
    r"^https?://(www\.)?github\.com/"
    r"(?P<owner>[\w.\-]+)/(?P<repo>[\w.\-]+)"
)

# ─── URL parser ───────────────────────────────────────────────────────────────


def parse_github_url(url: str) -> tuple[str, str]:
    """
    Extract (owner, repo) from a GitHub URL.

    Raises
    ------
    ValueError
        URL is not a recognisable github.com repository link.
    """
    m = _GITHUB_URL_RE.match(url.strip())
    if not m:
        raise ValueError(f"Not a valid GitHub repository URL: {url!r}")
    return m.group("owner"), m.group("repo")


# ─── Data containers ──────────────────────────────────────────────────────────


@dataclass
class RawRepoInfo:
    """Selected fields from GET /repos/{owner}/{repo}."""
    owner:          str
    name:           str
    full_name:      str
    description:    Optional[str]
    html_url:       str
    stars:          int
    forks:          int
    open_issues:    int
    watchers:       int
    default_branch: str
    created_at:     str           # ISO 8601 from GitHub
    updated_at:     str           # ISO 8601 from GitHub
    license_name:   Optional[str]
    is_private:     bool
    topics:         list[str]


@dataclass
class WeekData:
    """One weekly activity bucket, ISO-formatted and ready for AnalysisResult."""
    week_iso:  str    # "2025-01-05T00:00:00Z"
    commits:   int
    additions: int
    deletions: int


@dataclass
class ContributorData:
    login:         str
    avatar_url:    str
    profile_url:   str
    contributions: int


@dataclass
class RepoFetchResult:
    """
    Everything fetched and pre-processed from GitHub.
    Feed this into main.py's _build_result() to produce an AnalysisResult.
    """
    # ── Raw GitHub data ──────────────────────────────────────────────────────
    info:            RawRepoInfo
    languages:       dict[str, int]        # e.g. {"Python": 80_000, "JS": 30_000}
    contributors:    list[ContributorData]
    weekly_activity: list[WeekData]        # last 12 weeks, oldest first
    readme:          Optional[str]         # decoded UTF-8 text, or None
    tree_paths:      list[str]             # every path in the repo
    # ── Pre-computed from tree_paths ─────────────────────────────────────────
    lang_breakdown:  list[dict]            # [{language, bytes, percentage}, ...]
    quality_flags:   dict[str, bool]       # has_tests, has_ci, has_docker, …
    entry_points:    list[str]             # likely app entry files
    key_directories: list[str]             # top dirs by file count, e.g. "src/"
    arch_patterns:   list[str]             # e.g. ["Monorepo", "REST API"]


# ─── HTTP helpers ─────────────────────────────────────────────────────────────


def _headers(token: Optional[str]) -> dict[str, str]:
    h = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


async def _get(client: httpx.AsyncClient, path: str) -> dict | list:
    """GET {_API_BASE}{path} → parsed JSON.  Raises httpx.HTTPStatusError on non-2xx."""
    r = await client.get(f"{_API_BASE}{path}")
    r.raise_for_status()
    return r.json()


async def _get_stats(
    client: httpx.AsyncClient, path: str, *, retries: int = 3
) -> list:
    """
    GET a stats endpoint with back-off retry on HTTP 202.

    GitHub returns 202 while it computes weekly stats for the first time.
    We retry up to `retries` times with exponential back-off (1 s, 2 s, 4 s).
    Returns [] if all retries are exhausted (graceful degradation).
    """
    for attempt in range(retries):
        r = await client.get(f"{_API_BASE}{path}")
        if r.status_code == 200:
            return r.json() or []
        if r.status_code == 202:
            await asyncio.sleep(2 ** attempt)   # 1 s → 2 s → 4 s
            continue
        r.raise_for_status()
    return []   # stats not ready after all retries — return empty gracefully


# ─── Individual API fetchers ──────────────────────────────────────────────────


async def _fetch_repo_info(
    client: httpx.AsyncClient, owner: str, repo: str
) -> RawRepoInfo:
    d = await _get(client, f"/repos/{owner}/{repo}")
    return RawRepoInfo(
        owner          = d["owner"]["login"],
        name           = d["name"],
        full_name      = d["full_name"],
        description    = d.get("description"),
        html_url       = d["html_url"],
        stars          = d.get("stargazers_count", 0),
        forks          = d.get("forks_count", 0),
        open_issues    = d.get("open_issues_count", 0),
        watchers       = d.get("watchers_count", 0),
        default_branch = d.get("default_branch", "main"),
        created_at     = d["created_at"],
        updated_at     = d["updated_at"],
        license_name   = (d.get("license") or {}).get("name"),
        is_private     = bool(d.get("private", False)),
        topics         = d.get("topics", []),
    )


async def _fetch_languages(
    client: httpx.AsyncClient, owner: str, repo: str
) -> dict[str, int]:
    return dict(await _get(client, f"/repos/{owner}/{repo}/languages"))


async def _fetch_contributors(
    client: httpx.AsyncClient,
    owner:  str,
    repo:   str,
    limit:  int = 10,
) -> list[ContributorData]:
    """Returns at most `limit` top contributors (by commit count)."""
    data = await _get(
        client,
        f"/repos/{owner}/{repo}/contributors?per_page={limit}&anon=false",
    )
    if not isinstance(data, list):
        return []
    return [
        ContributorData(
            login        = c["login"],
            avatar_url   = c.get("avatar_url", ""),
            profile_url  = c.get("html_url", f"https://github.com/{c['login']}"),
            contributions= c.get("contributions", 0),
        )
        for c in data
    ]


async def _fetch_readme(
    client: httpx.AsyncClient, owner: str, repo: str
) -> Optional[str]:
    """
    Return the default README as plain UTF-8 text.
    Returns None (not an error) when no README is found (404).
    """
    try:
        d       = await _get(client, f"/repos/{owner}/{repo}/readme")
        encoded = d.get("content", "")
        # GitHub wraps base64 content with newlines — strip them first.
        return base64.b64decode(
            encoded.replace("\n", "")
        ).decode("utf-8", errors="replace")
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return None
        raise


async def _fetch_tree(
    client: httpx.AsyncClient, owner: str, repo: str, branch: str
) -> list[str]:
    """
    Return all file/directory paths via the Git Trees API (recursive=1).

    Returns [] on:
      - 404  (branch not found)
      - 409  (empty repository)

    Note: GitHub sets truncated=true for repos with > 100 000 files.
    We still return whatever was provided — partial data is better than none.
    """
    try:
        d = await _get(
            client,
            f"/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
        )
        return [item["path"] for item in d.get("tree", [])]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in (404, 409):
            return []
        raise


# ─── Activity data processing ─────────────────────────────────────────────────


def _unix_to_iso(ts: int) -> str:
    """Convert a Unix timestamp (GitHub week start) to ISO 8601 UTC string."""
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT00:00:00Z")


def _merge_weekly_activity(
    commit_buckets: list[dict],
    code_freq:      list[list[int]],
    n_weeks:        int = 12,
) -> list[WeekData]:
    """
    Combine two GitHub stats endpoints into WeekData objects.

    commit_buckets  /stats/commit_activity — 52 items like:
        {"week": 1700000000, "total": 34, "days": [0,3,7,...]}

    code_freq       /stats/code_frequency  — 52 items like:
        [week_unix, additions, -deletions]

    Returns the most recent `n_weeks`, sorted oldest → newest.
    """
    # Build lookup: week_unix → (additions, abs_deletions)
    freq_map: dict[int, tuple[int, int]] = {}
    for row in code_freq:
        if len(row) >= 3:
            freq_map[int(row[0])] = (max(0, int(row[1])), abs(int(row[2])))

    rows: list[WeekData] = []
    for b in commit_buckets:
        ts      = int(b.get("week", 0))
        commits = int(b.get("total", 0))
        adds, dels = freq_map.get(ts, (0, 0))
        rows.append(WeekData(
            week_iso  = _unix_to_iso(ts),
            commits   = commits,
            additions = adds,
            deletions = dels,
        ))

    # Trim to the most recent n_weeks, then sort chronologically
    return sorted(rows, key=lambda w: w.week_iso)[-n_weeks:]


# ─── Language breakdown ───────────────────────────────────────────────────────


def compute_language_breakdown(lang_bytes: dict[str, int]) -> list[dict]:
    """
    Sort languages by byte count, compute percentages, cap at top 9.
    Everything beyond rank 9 is merged into an "Other" bucket.

    Returns a list of dicts with keys: language, bytes, percentage.
    """
    total = sum(lang_bytes.values()) or 1
    items = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)

    breakdown: list[dict] = []
    other_bytes = 0

    for i, (lang, b) in enumerate(items):
        if i < 9:
            breakdown.append({
                "language":   lang,
                "bytes":      b,
                "percentage": round(b / total * 100, 1),
            })
        else:
            other_bytes += b

    if other_bytes:
        breakdown.append({
            "language":   "Other",
            "bytes":      other_bytes,
            "percentage": round(other_bytes / total * 100, 1),
        })

    return breakdown


# ─── File-tree heuristics ─────────────────────────────────────────────────────
# These detect common project signals from path names alone — no file reading.
# Step 4 (LLM integration) will enrich these with actual content analysis.


def detect_quality_flags(tree_paths: list[str]) -> dict[str, bool]:
    """
    Detect code-quality and security signals purely from the file/dir tree.

    Returns a dict of bool flags:
        has_tests, has_ci, has_docs, has_linter, has_docker,
        has_env_example, exposes_secrets
    """
    paths    = [p.lower() for p in tree_paths]
    # Flat set of every individual path segment for exact-name matching
    segments = {seg for p in paths for seg in p.split("/") if seg}

    def sub(*snippets: str) -> bool:
        """True if ANY snippet appears as a substring of ANY path."""
        return any(s in p for p in paths for s in snippets)

    def seg_match(*names: str) -> bool:
        """True if ANY name matches an exact path segment."""
        return bool(segments.intersection(names))

    return {
        "has_tests": (
            seg_match("test", "tests", "spec", "specs", "__tests__")
            or sub("test_", "_test.", "pytest.ini", "jest.config",
                   "vitest.config", "karma.conf", ".spec.")
        ),
        "has_ci": sub(
            ".github/workflows", ".circleci", ".travis.yml",
            "jenkinsfile", ".gitlab-ci.yml", "azure-pipelines.yml",
            "bitbucket-pipelines.yml",
        ),
        "has_docs": (
            seg_match("docs", "doc", "documentation")
            or sub("mkdocs.yml", "readthedocs.yml", ".readthedocs.yaml")
        ),
        "has_linter": sub(
            ".eslintrc", ".flake8", ".pylintrc", ".rubocop",
            "tslint.json", ".prettierrc", "pyproject.toml",
        ),
        "has_docker": sub("dockerfile", "docker-compose"),
        "has_env_example": sub(".env.example", ".env.sample", ".env.template"),
        # Only flag *exact* filenames at any depth — avoid false positives
        "exposes_secrets": any(
            p.split("/")[-1] in {".env", "secrets.json", "credentials.json", "id_rsa"}
            for p in paths
        ),
    }


def detect_entry_points(tree_paths: list[str]) -> list[str]:
    """
    Return likely application entry-point files from the tree.
    Common names are checked first; top-level source files are the fallback.
    """
    _CANDIDATES = [
        "main.py", "app.py", "server.py", "run.py", "manage.py",
        "wsgi.py", "asgi.py", "index.py",
        "main.ts", "index.ts", "server.ts", "app.ts",
        "main.js", "index.js", "server.js", "app.js",
        "src/main.py", "src/app.py",
        "src/index.ts", "src/main.ts",
        "src/index.js", "src/main.js",
    ]
    found = [c for c in _CANDIDATES if c in tree_paths]

    if not found:
        # Fallback: top-level source files that aren't config files
        for p in tree_paths:
            if (
                "/" not in p
                and p.endswith((".py", ".ts", ".js", ".go", ".rs", ".rb", ".java"))
                and not p.startswith(".")
            ):
                found.append(p)

    return found[:6]   # cap at 6 entries


def detect_key_directories(tree_paths: list[str]) -> list[str]:
    """
    Return the most prominent top-level directories, ranked by child-file count.
    Only directories (not top-level files) are included.
    """
    dir_count: dict[str, int] = {}
    for p in tree_paths:
        parts = p.split("/")
        if len(parts) > 1:
            top = parts[0]
            dir_count[top] = dir_count.get(top, 0) + 1

    return [
        f"{d}/"
        for d, _ in sorted(dir_count.items(), key=lambda x: x[1], reverse=True)
    ][:8]


# Architecture pattern signals: (display_name, list_of_path_snippets)
_ARCH_SIGNALS: list[tuple[str, list[str]]] = [
    ("Monorepo",       ["packages/", "apps/", "lerna.json",
                        "pnpm-workspace.yaml", "nx.json", "turborepo.json"]),
    ("REST API",       ["routes/", "controllers/", "routers/", "endpoints/"]),
    ("MVC",            ["controllers/", "models/", "views/"]),
    ("GraphQL",        [".graphql", "schema.graphql", "resolvers/", "graphql/"]),
    ("Microservices",  ["services/", "microservices/"]),
    ("Plugin system",  ["plugins/", "extensions/"]),
    ("CLI tool",       ["bin/", "cmd/", "commands/", "cli/"]),
    ("Frontend SPA",   ["src/components/", "src/pages/",
                        "src/views/", "src/app/"]),
    ("Serverless",     ["serverless.yml", "functions/",
                        "lambda/", "netlify.toml"]),
]


def detect_architecture_patterns(tree_paths: list[str]) -> list[str]:
    """
    Return high-level architecture pattern labels detected from the file tree.
    Returns ["Standard layout"] when no known patterns are detected.
    """
    paths_lower = [p.lower() for p in tree_paths]
    found = [
        name
        for name, signals in _ARCH_SIGNALS
        if any(any(sig in path for path in paths_lower) for sig in signals)
    ]
    return found if found else ["Standard layout"]


# ─── Public entry-point ──────────────────────────────────────────────────────


async def fetch_repo(
    url:   str,
    token: Optional[str] = None,
) -> RepoFetchResult:
    """
    Fetch and pre-process all GitHub data required to analyse a repository.

    Parameters
    ----------
    url :
        Full GitHub URL — e.g. ``"https://github.com/vercel/next.js"``.
    token :
        GitHub personal-access token.  Falls back to the ``GITHUB_TOKEN``
        environment variable.  Without a token, GitHub limits you to
        **60 unauthenticated requests per hour**.  A token raises this to
        **5 000 requests per hour**.

    Returns
    -------
    RepoFetchResult
        Raw API data **plus** pre-computed heuristics (language breakdown,
        quality flags, architecture patterns, entry points, key dirs).
        Pass this directly to ``_build_result()`` in ``main.py``.

    Raises
    ------
    ValueError
        ``url`` is not a valid ``github.com`` repository link.
    httpx.HTTPStatusError
        GitHub returned a 4xx / 5xx response.
        Common cases — 404: repo not found or private without auth;
        403 / 429: rate-limited.
    httpx.TimeoutException
        Network or connect timeout exceeded.
    """
    token = token or os.getenv("GITHUB_TOKEN")
    owner, repo = parse_github_url(url)

    async with httpx.AsyncClient(
        headers          = _headers(token),
        timeout          = httpx.Timeout(20.0, connect=5.0),
        follow_redirects = True,
    ) as client:

        # ── Fire all independent requests concurrently ────────────────────
        (
            info,
            lang_bytes,
            contributors,
            commit_weeks,
            code_freq,
            readme,
        ) = await asyncio.gather(
            _fetch_repo_info(client, owner, repo),
            _fetch_languages(client, owner, repo),
            _fetch_contributors(client, owner, repo),
            _get_stats(client, f"/repos/{owner}/{repo}/stats/commit_activity"),
            _get_stats(client, f"/repos/{owner}/{repo}/stats/code_frequency"),
            _fetch_readme(client, owner, repo),
        )

        # Tree requires the default_branch from info, so it runs after gather
        tree_paths = await _fetch_tree(client, owner, repo, info.default_branch)

    # ── Post-process (CPU-only, no more network I/O) ──────────────────────
    lang_bd = compute_language_breakdown(lang_bytes)
    flags   = detect_quality_flags(tree_paths)

    return RepoFetchResult(
        info            = info,
        languages       = lang_bytes,
        contributors    = contributors,
        weekly_activity = _merge_weekly_activity(commit_weeks, code_freq),
        readme          = readme,
        tree_paths      = tree_paths,
        lang_breakdown  = lang_bd,
        quality_flags   = flags,
        entry_points    = detect_entry_points(tree_paths),
        key_directories = detect_key_directories(tree_paths),
        arch_patterns   = detect_architecture_patterns(tree_paths),
    )