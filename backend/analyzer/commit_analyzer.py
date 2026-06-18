# ─── backend/analyzer/commit_analyzer.py ─────────────────────────────────────
# Analyzer 7: Commit Analyzer
#
# Analyzes git commit history from the cloned repository.
# Extracts patterns, frequency, trends, and contributor activity.
#
# Input:  repo_path (str) - path to cloned repository
# Output: CommitAnalysis dataclass with structured analysis
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import asyncio
import logging
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Optional

log = logging.getLogger("github_analyzer.commit_analyzer")


# ─── Data Models ──────────────────────────────────────────────────────────────


@dataclass
class CommitFrequency:
    """Commit frequency metrics over time periods."""
    commits_total: int              # Total commits in history
    commits_last_30_days: int       # Last 30 days
    commits_last_90_days: int       # Last 90 days
    commits_last_year: int          # Last 365 days
    avg_commits_per_week: float     # Average across entire history
    avg_commits_per_month: float    # Average across entire history


@dataclass
class CommitTrend:
    """Trend analysis of commit activity."""
    trend: str                      # "increasing", "stable", "declining"
    last_30_days_rate: float        # commits/week in last 30 days
    last_90_days_rate: float        # commits/week in last 90 days
    months_since_last_commit: int   # Days since last commit / 30
    is_active: bool                 # True if last commit < 30 days ago


@dataclass
class CommitAuthor:
    """Author information from commits."""
    name: str
    email: str
    commit_count: int
    percentage: float               # % of total commits


@dataclass
class CommitMessage:
    """Patterns detected in commit messages."""
    avg_length: int                 # Average message length in chars
    conventional_commits: int       # Commits following conventional format
    has_issues_refs: int            # Commits referencing issues (#123)
    has_breaking_changes: int       # Commits with BREAKING CHANGE
    message_quality_score: float    # 0-10, based on conventions


@dataclass
class CommitAnalysis:
    """Complete commit analysis result."""
    frequency: CommitFrequency
    trend: CommitTrend
    authors: list[CommitAuthor]     # Top 10 authors
    message_patterns: CommitMessage
    
    # Advanced metrics
    longest_commit_streak: int      # Longest consecutive days with commits
    most_active_hour: Optional[int] # 0-23, UTC
    most_active_day_of_week: Optional[str]  # "Monday", "Tuesday", etc
    
    # Detection signals
    single_author_ratio: float      # Top author % of commits
    commit_message_quality: str     # "excellent", "good", "poor"
    commit_frequency_rating: str    # "very_active", "active", "stable", "inactive"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "frequency": asdict(self.frequency),
            "trend": asdict(self.trend),
            "authors": [asdict(a) for a in self.authors],
            "message_patterns": asdict(self.message_patterns),
            "longest_commit_streak": self.longest_commit_streak,
            "most_active_hour": self.most_active_hour,
            "most_active_day_of_week": self.most_active_day_of_week,
            "single_author_ratio": self.single_author_ratio,
            "commit_message_quality": self.commit_message_quality,
            "commit_frequency_rating": self.commit_frequency_rating,
        }


# ─── Git Command Wrappers ─────────────────────────────────────────────────────


async def _git_log_oneline(repo_path: str) -> list[str]:
    """Get git log as oneline format (hash + message)."""
    try:
        result = await asyncio.to_thread(
            subprocess.run,
            ["git", "log", "--oneline", "--date=short"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            log.warning("git log failed: %s", result.stderr)
            return []
        return result.stdout.strip().split("\n") if result.stdout.strip() else []
    except subprocess.TimeoutExpired:
        log.warning("git log timed out for %s", repo_path)
        return []
    except Exception as exc:
        log.error("Failed to run git log: %s", exc)
        return []


async def _git_log_detailed(
    repo_path: str,
    format_str: str,
    max_commits: Optional[int] = None,
) -> list[str]:
    """Get detailed git log with custom format."""
    try:
        cmd = ["git", "log", f"--format={format_str}"]
        if max_commits:
            cmd.append(f"-n {max_commits}")
        
        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return []
        return result.stdout.strip().split("\n") if result.stdout.strip() else []
    except subprocess.TimeoutExpired:
        log.warning("git log detailed timed out")
        return []
    except Exception as exc:
        log.error("Failed to run git log detailed: %s", exc)
        return []


async def _git_log_with_timestamp(repo_path: str) -> list[tuple[str, int]]:
    """Get commits with timestamps (ISO format)."""
    format_str = "%H%n%aI"  # hash + author date in ISO format
    lines = await _git_log_detailed(repo_path, format_str)
    
    commits = []
    for i in range(0, len(lines), 2):
        if i + 1 < len(lines):
            hash_val = lines[i].strip()
            try:
                # Parse ISO 8601 timestamp
                dt = datetime.fromisoformat(lines[i+1].strip().replace("Z", "+00:00"))
                commits.append((hash_val, int(dt.timestamp())))
            except (ValueError, IndexError):
                continue
    
    return commits


async def _git_log_authors(repo_path: str) -> list[str]:
    """Get author information (name <email>)."""
    format_str = "%aN%n%aE"  # Author name + email
    return await _git_log_detailed(repo_path, format_str)


async def _git_log_messages(repo_path: str) -> list[str]:
    """Get all commit messages."""
    format_str = "%s%n---END---"  # Subject + separator
    lines = await _git_log_detailed(repo_path, format_str)
    
    messages = []
    current = []
    for line in lines:
        if line == "---END---":
            messages.append("\n".join(current))
            current = []
        else:
            current.append(line)
    
    return [m for m in messages if m.strip()]


async def _git_show_timestamp(repo_path: str, commit_hash: str) -> Optional[int]:
    """Get timestamp of a specific commit."""
    try:
        result = await asyncio.to_thread(
            subprocess.run,
            ["git", "show", "-s", "--format=%aI", commit_hash],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            dt = datetime.fromisoformat(
                result.stdout.strip().replace("Z", "+00:00")
            )
            return int(dt.timestamp())
    except Exception:
        pass
    return None


# ─── Analysis Functions ───────────────────────────────────────────────────────


def _compute_frequency(commits_list: list[tuple[str, int]]) -> CommitFrequency:
    """Compute commit frequency metrics."""
    now = datetime.now().timestamp()
    thirty_days_ago = now - (30 * 24 * 3600)
    ninety_days_ago = now - (90 * 24 * 3600)
    year_ago = now - (365 * 24 * 3600)
    
    commits_30 = sum(1 for _, ts in commits_list if ts > thirty_days_ago)
    commits_90 = sum(1 for _, ts in commits_list if ts > ninety_days_ago)
    commits_year = sum(1 for _, ts in commits_list if ts > year_ago)
    total = len(commits_list)
    
    if commits_list:
        oldest_ts = min(ts for _, ts in commits_list)
        days_elapsed = (now - oldest_ts) / (24 * 3600)
        weeks_elapsed = max(days_elapsed / 7, 1)  # Avoid division by zero
        avg_per_week = total / weeks_elapsed
        avg_per_month = total / max(weeks_elapsed / 4.33, 1)
    else:
        avg_per_week = 0
        avg_per_month = 0
    
    return CommitFrequency(
        commits_total=total,
        commits_last_30_days=commits_30,
        commits_last_90_days=commits_90,
        commits_last_year=commits_year,
        avg_commits_per_week=round(avg_per_week, 2),
        avg_commits_per_month=round(avg_per_month, 2),
    )


def _compute_trend(commits_list: list[tuple[str, int]]) -> CommitTrend:
    """Compute commit trend (increasing, stable, declining)."""
    now = datetime.now().timestamp()
    thirty_days_ago = now - (30 * 24 * 3600)
    ninety_days_ago = now - (90 * 24 * 3600)
    
    commits_30 = [ts for _, ts in commits_list if ts > thirty_days_ago]
    commits_90 = [ts for _, ts in commits_list if ts > ninety_days_ago]
    
    rate_30 = len(commits_30) / 4.3 if commits_30 else 0  # commits/week
    rate_90 = len(commits_90) / 13 if commits_90 else 0   # commits/week
    
    # Determine trend
    if rate_30 > rate_90 * 1.2:
        trend = "increasing"
    elif rate_30 < rate_90 * 0.8:
        trend = "declining"
    else:
        trend = "stable"
    
    # Days since last commit
    if commits_list:
        last_commit_ts = max(ts for _, ts in commits_list)
        days_since = (now - last_commit_ts) / (24 * 3600)
    else:
        days_since = 999
    
    months_since = int(days_since / 30)
    is_active = days_since < 30
    
    return CommitTrend(
        trend=trend,
        last_30_days_rate=round(rate_30, 2),
        last_90_days_rate=round(rate_90, 2),
        months_since_last_commit=months_since,
        is_active=is_active,
    )


def _extract_authors(authors_raw: list[str]) -> list[CommitAuthor]:
    """Extract and rank authors from git log."""
    author_commits: dict[str, int] = {}
    
    # Group by name + email
    for i in range(0, len(authors_raw), 2):
        if i + 1 < len(authors_raw):
            name = authors_raw[i].strip()
            email = authors_raw[i + 1].strip()
            key = f"{name} <{email}>"
            author_commits[key] = author_commits.get(key, 0) + 1
    
    total_commits = sum(author_commits.values())
    if total_commits == 0:
        return []
    
    # Sort by commit count and take top 10
    sorted_authors = sorted(
        author_commits.items(),
        key=lambda x: x[1],
        reverse=True,
    )[:10]
    
    result = []
    for author_str, count in sorted_authors:
        # Parse "Name <email>"
        if "<" in author_str and ">" in author_str:
            name = author_str[:author_str.index("<")].strip()
            email = author_str[author_str.index("<")+1:author_str.index(">")]
        else:
            name = author_str
            email = "unknown"
        
        result.append(CommitAuthor(
            name=name,
            email=email,
            commit_count=count,
            percentage=round(count / total_commits * 100, 1),
        ))
    
    return result


def _analyze_commit_messages(messages: list[str]) -> CommitMessage:
    """Analyze patterns in commit messages."""
    if not messages:
        return CommitMessage(
            avg_length=0,
            conventional_commits=0,
            has_issues_refs=0,
            has_breaking_changes=0,
            message_quality_score=0,
        )
    
    lengths = [len(m) for m in messages]
    avg_length = int(sum(lengths) / len(lengths)) if lengths else 0
    
    # Conventional Commits format: type(scope): message
    conventional_count = sum(
        1 for m in messages
        if any(m.lower().startswith(t) for t in [
            "feat:", "fix:", "docs:", "style:", "refactor:",
            "perf:", "test:", "chore:", "ci:", "build:"
        ])
    )
    
    # Issue references (#123, fixes #456, etc)
    issues_count = sum(
        1 for m in messages
        if "#" in m and any(c.isdigit() for c in m.split("#")[1:])
    )
    
    # Breaking changes
    breaking_count = sum(
        1 for m in messages
        if "BREAKING CHANGE" in m or "BREAKING_CHANGE" in m
    )
    
    # Quality score: higher if conventional, has references, good length
    score = 0
    score += (conventional_count / len(messages)) * 5 if messages else 0
    score += min(issues_count / max(len(messages) / 2, 1), 1) * 3
    score += 2 if 50 <= avg_length <= 150 else 0
    
    return CommitMessage(
        avg_length=avg_length,
        conventional_commits=conventional_count,
        has_issues_refs=issues_count,
        has_breaking_changes=breaking_count,
        message_quality_score=round(score, 1),
    )


def _compute_commit_streaks(commits_list: list[tuple[str, int]]) -> int:
    """Find longest consecutive days with commits."""
    if not commits_list:
        return 0
    
    # Group commits by day
    commits_by_day: dict[int, bool] = {}
    for _, ts in commits_list:
        day = ts // (24 * 3600)  # Convert to day number
        commits_by_day[day] = True
    
    if not commits_by_day:
        return 0
    
    sorted_days = sorted(commits_by_day.keys())
    max_streak = 1
    current_streak = 1
    
    for i in range(1, len(sorted_days)):
        if sorted_days[i] - sorted_days[i-1] == 1:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 1
    
    return max_streak


def _compute_time_patterns(commits_list: list[tuple[str, int]]) -> tuple[Optional[int], Optional[str]]:
    """Find most active hour and day of week."""
    if not commits_list:
        return None, None
    
    # Analyze hour of day (UTC)
    hour_counts: dict[int, int] = {}
    day_counts: dict[str, int] = {}
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    for _, ts in commits_list:
        dt = datetime.utcfromtimestamp(ts)
        hour = dt.hour
        day_name = days[dt.weekday()]
        
        hour_counts[hour] = hour_counts.get(hour, 0) + 1
        day_counts[day_name] = day_counts.get(day_name, 0) + 1
    
    most_active_hour = max(hour_counts.keys(), key=lambda h: hour_counts[h]) if hour_counts else None
    most_active_day = max(day_counts.keys(), key=lambda d: day_counts[d]) if day_counts else None
    
    return most_active_hour, most_active_day


def _classify_frequency(frequency: CommitFrequency) -> str:
    """Classify commit frequency as activity level."""
    if frequency.avg_commits_per_week >= 5:
        return "very_active"
    elif frequency.avg_commits_per_week >= 2:
        return "active"
    elif frequency.avg_commits_per_week >= 0.5:
        return "stable"
    else:
        return "inactive"


def _classify_message_quality(msg: CommitMessage) -> str:
    """Classify message quality based on patterns."""
    if msg.message_quality_score >= 7:
        return "excellent"
    elif msg.message_quality_score >= 4:
        return "good"
    else:
        return "poor"


# ─── Public API ───────────────────────────────────────────────────────────────


async def analyze_commits(repo_path: str) -> CommitAnalysis:
    """
    Analyze commit history of a cloned repository.
    
    Parameters
    ----------
    repo_path : str
        Path to cloned git repository
    
    Returns
    -------
    CommitAnalysis
        Structured analysis of commit patterns, frequency, authors, etc.
    """
    log.info("Analyzing commits in %s", repo_path)
    
    try:
        # Fetch commit data in parallel
        commits_with_ts, authors_raw, messages = await asyncio.gather(
            _git_log_with_timestamp(repo_path),
            _git_log_authors(repo_path),
            _git_log_messages(repo_path),
        )
        
        # Compute analysis metrics
        frequency = _compute_frequency(commits_with_ts)
        trend = _compute_trend(commits_with_ts)
        authors = _extract_authors(authors_raw)
        messages_analysis = _analyze_commit_messages(messages)
        longest_streak = _compute_commit_streaks(commits_with_ts)
        most_active_hour, most_active_day = _compute_time_patterns(commits_with_ts)
        
        single_author_pct = authors[0].percentage if authors else 0
        
        result = CommitAnalysis(
            frequency=frequency,
            trend=trend,
            authors=authors,
            message_patterns=messages_analysis,
            longest_commit_streak=longest_streak,
            most_active_hour=most_active_hour,
            most_active_day_of_week=most_active_day,
            single_author_ratio=single_author_pct,
            commit_message_quality=_classify_message_quality(messages_analysis),
            commit_frequency_rating=_classify_frequency(frequency),
        )
        
        log.info(
            "Commit analysis complete: %d commits, %d authors, trend=%s",
            frequency.commits_total,
            len(authors),
            trend.trend,
        )
        
        return result
    
    except Exception as exc:
        log.exception("Error analyzing commits: %s", exc)
        # Return minimal empty result on error
        return CommitAnalysis(
            frequency=CommitFrequency(0, 0, 0, 0, 0, 0),
            trend=CommitTrend("unknown", 0, 0, 0, False),
            authors=[],
            message_patterns=CommitMessage(0, 0, 0, 0, 0),
            longest_commit_streak=0,
            most_active_hour=None,
            most_active_day_of_week=None,
            single_author_ratio=0,
            commit_message_quality="poor",
            commit_frequency_rating="inactive",
        )