"""Unit tests for flexible GitHub URL parsing and resolution."""

import asyncio

import pytest

from github.reader import parse_github_url, canonical_repo_url, resolve_repo_url


@pytest.mark.parametrize(
    "raw, owner, repo",
    [
        ("vercel/next.js", "vercel", "next.js"),
        ("github.com/vercel/next.js", "vercel", "next.js"),
        ("https://github.com/vercel/next.js", "vercel", "next.js"),
        ("http://www.github.com/vercel/next.js", "vercel", "next.js"),
        ("https://github.com/vercel/next.js/tree/main", "vercel", "next.js"),
        ("https://github.com/vercel/next.js.git", "vercel", "next.js"),
        ("  owner/repo-name  ", "owner", "repo-name"),
    ],
)
def test_parse_github_url_direct(raw: str, owner: str, repo: str) -> None:
    assert parse_github_url(raw) == (owner, repo)
    assert canonical_repo_url(owner, repo) == f"https://github.com/{owner}/{repo}"


@pytest.mark.parametrize(
    "raw",
    ["", "https://google.com", "not-a-url", "github.com/onlyowner"],
)
def test_parse_github_url_rejects(raw: str) -> None:
    with pytest.raises(ValueError):
        parse_github_url(raw)


@pytest.mark.asyncio
async def test_resolve_repo_url_direct() -> None:
    owner, repo, canonical = await resolve_repo_url("vercel/next.js")
    assert owner == "vercel"
    assert repo == "next.js"
    assert canonical == "https://github.com/vercel/next.js"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_resolve_linkedin_short_url() -> None:
    """Follows lnkd.in redirect to github.com (requires network)."""
    owner, repo, canonical = await resolve_repo_url("https://lnkd.in/dbwp3hQJ")
    assert owner == "manaspros"
    assert repo == "govrix-scout"
    assert canonical == "https://github.com/manaspros/govrix-scout"
