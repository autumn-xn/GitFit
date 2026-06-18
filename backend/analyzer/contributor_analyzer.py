"""
GitFit v2: Contributor Analyzer Module
Location: backend/analyzer/contributor_analyzer.py

Responsible for analyzing git history to identify contributors,
calculate contribution distribution, and assess team concentration.
"""

import os
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
import requests


@dataclass
class Contributor:
    """Represents a project contributor"""
    name: str
    email: Optional[str] = None
    commits: int = 0
    percent: float = 0.0
    avatar_url: Optional[str] = None
    first_commit_date: Optional[str] = None
    last_commit_date: Optional[str] = None
    is_bot: bool = False
    languages: Dict[str, int] = field(default_factory=dict)


@dataclass
class ContributorAnalysis:
    """Complete contributor analysis"""
    total_contributors: int
    total_commits: int
    top_contributors: List[Dict]
    team_concentration: str  # "solo", "concentrated", "distributed", "highly-distributed"
    concentration_score: float  # 0-100, higher = more concentrated
    pareto_ratio: float  # % of commits by top 20%
    inactive_contributors: int  # Contributors with 1 commit only
    bot_contributors: List[str]
    contributor_trend: str  # "growing", "stable", "declining"
    average_commits_per_contributor: float
    most_active_month: Optional[str]
    contribution_distribution: Dict  # Commit distribution buckets
    team_diversity: Dict  # Stats about team diversity
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class ContributorAnalyzer:
    """
    Analyzes git history to extract contributor information,
    calculate contribution distribution, and assess team dynamics.
    
    Attributes:
        repo_path (str): Root path of the repository
        github_token (str, optional): GitHub API token for avatar/info lookup
        github_owner (str, optional): GitHub owner for API calls
        github_repo (str, optional): GitHub repo name for API calls
    """
    
    # Common bot identifiers
    BOT_PATTERNS = {
        "dependabot", "renovate", "snyk", "codeql", "github",
        "circleci", "travis", "appveyor", "jenkins", "gitlab",
        "bot", "automation", "ci", "cd", "action",
        "codecov", "coveralls", "sonarqube", "deepsource"
    }
    
    def __init__(
        self,
        repo_path: str,
        github_token: Optional[str] = None,
        github_owner: Optional[str] = None,
        github_repo: Optional[str] = None
    ):
        """
        Initialize the contributor analyzer.
        
        Args:
            repo_path: Path to the repository root
            github_token: GitHub API token
            github_owner: GitHub owner username
            github_repo: GitHub repository name
        """
        self.repo_path = Path(repo_path)
        
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.github_owner = github_owner
        self.github_repo = github_repo
        self.contributors: Dict[str, Contributor] = {}
        
        print(f"✓ Initialized ContributorAnalyzer for: {repo_path}")
    
    @staticmethod
    def _is_bot(name: str, email: str = "") -> bool:
        """
        Determine if a contributor is a bot based on name/email patterns.
        
        Args:
            name: Contributor name
            email: Contributor email
            
        Returns:
            True if likely a bot, False otherwise
        """
        combined = (name + " " + email).lower()
        return any(bot_pattern in combined for bot_pattern in ContributorAnalyzer.BOT_PATTERNS)
    
    def _parse_git_log(self) -> Dict[str, Contributor]:
        """
        Parse git log to extract contributor information.
        
        Returns:
            Dictionary mapping email -> Contributor
        """
        contributors = {}
        
        try:
            # Get all commits with author info
            # Format: email|name|date
            cmd = [
                "git",
                "-C", str(self.repo_path),
                "log",
                "--all",
                "--format=%aE|%aN|%ai",
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                print(f"⚠ Git log failed: {result.stderr}")
                return {}
            
            lines = result.stdout.strip().split('\n')
            print(f"✓ Parsed {len(lines)} commits from git log")
            
            for line in lines:
                if not line.strip():
                    continue
                
                try:
                    parts = line.split('|')
                    if len(parts) < 3:
                        continue
                    
                    email = parts[0].strip()
                    name = parts[1].strip()
                    date_str = parts[2].strip()
                    
                    if not email or not name:
                        continue
                    
                    # Normalize email
                    email_key = email.lower()
                    
                    if email_key not in contributors:
                        contributors[email_key] = Contributor(
                            name=name,
                            email=email,
                            is_bot=self._is_bot(name, email)
                        )
                    
                    contributor = contributors[email_key]
                    contributor.commits += 1
                    
                    # Update name (prefer longer names)
                    if len(name) > len(contributor.name):
                        contributor.name = name
                    
                    # Track dates
                    try:
                        commit_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        date_str_formatted = commit_date.strftime("%Y-%m-%d")
                        
                        if not contributor.first_commit_date:
                            contributor.first_commit_date = date_str_formatted
                        
                        contributor.last_commit_date = date_str_formatted
                    except (ValueError, AttributeError):
                        pass
                
                except (ValueError, IndexError):
                    continue
        
        except subprocess.TimeoutExpired:
            print("⚠ Git log timeout")
        except Exception as e:
            print(f"⚠ Error parsing git log: {e}")
        
        return contributors
    
    def _get_github_user_info(self, username: str) -> Optional[Dict]:
        """
        Fetch user info from GitHub API.
        
        Args:
            username: GitHub username
            
        Returns:
            Dict with avatar_url or None
        """
        if not self.github_token:
            return None
        
        try:
            url = f"https://api.github.com/users/{username}"
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"⚠ Error fetching GitHub info for {username}: {e}")
            return None
    
    def _enrich_with_github_data(self, contributors: Dict[str, Contributor]) -> None:
        """
        Enrich contributor data with GitHub API information.
        
        Args:
            contributors: Dictionary of contributors to enrich
        """
        if not self.github_token or not self.github_owner or not self.github_repo:
            print("⚠ Skipping GitHub enrichment (no token or owner/repo)")
            return
        
        try:
            # Get contributors from GitHub API
            url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/contributors"
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                github_contributors = response.json()
                
                for gh_contrib in github_contributors:
                    if isinstance(gh_contrib, dict):
                        login = gh_contrib.get("login", "").lower()
                        avatar_url = gh_contrib.get("avatar_url")
                        
                        # Try to match with git contributors
                        for contrib in contributors.values():
                            # Match by email domain or name
                            if login in contrib.email.lower() or login in contrib.name.lower():
                                contrib.avatar_url = avatar_url
                                break
            
            print(f"✓ Enriched with GitHub data")
        except Exception as e:
            print(f"⚠ Error enriching GitHub data: {e}")
    
    def _calculate_concentration(self, contributors: Dict[str, Contributor], total_commits: int) -> Tuple[str, float, float]:
        """
        Calculate team concentration metrics.
        
        Args:
            contributors: Dictionary of contributors
            total_commits: Total commit count
            
        Returns:
            Tuple of (concentration_level, concentration_score, pareto_ratio)
        """
        if not contributors:
            return "solo", 100.0, 100.0
        
        # Sort by commits
        sorted_contribs = sorted(contributors.values(), key=lambda x: x.commits, reverse=True)
        
        # Calculate Pareto: % of commits by top 20%
        top_20_percent_count = max(1, len(sorted_contribs) // 5)
        top_20_commits = sum(c.commits for c in sorted_contribs[:top_20_percent_count])
        pareto_ratio = (top_20_commits / total_commits * 100) if total_commits > 0 else 0
        
        # Calculate concentration score (0-100)
        # Based on Herfindahl index
        concentration_score = 0.0
        for contrib in contributors.values():
            percent = (contrib.commits / total_commits * 100) if total_commits > 0 else 0
            concentration_score += percent ** 2
        
        # Normalize to 0-100 scale
        max_concentration = 100.0 * 100.0  # Single contributor
        concentration_score = (concentration_score / max_concentration) * 100
        
        # Classify concentration
        if len(sorted_contribs) == 1:
            level = "solo"
        elif concentration_score >= 70:
            level = "concentrated"
        elif concentration_score >= 40:
            level = "distributed"
        else:
            level = "highly-distributed"
        
        return level, round(concentration_score, 1), round(pareto_ratio, 1)
    
    def _calculate_trend(self, contributors: Dict[str, Contributor]) -> str:
        """
        Determine if contribution trend is growing, stable, or declining.
        
        Args:
            contributors: Dictionary of contributors
            
        Returns:
            Trend: "growing", "stable", or "declining"
        """
        try:
            # Get commits per month for last 12 months
            cmd = [
                "git",
                "-C", str(self.repo_path),
                "log",
                "--all",
                "--format=%ai",
                "--since=12 months ago"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return "unknown"
            
            # Count commits by month
            monthly_counts = defaultdict(int)
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        date = datetime.fromisoformat(line.replace('Z', '+00:00'))
                        month = date.strftime("%Y-%m")
                        monthly_counts[month] += 1
                    except (ValueError, AttributeError):
                        pass
            
            if len(monthly_counts) < 2:
                return "unknown"
            
            # Get last 3 and first 3 months
            sorted_months = sorted(monthly_counts.items())
            first_3 = sum(count for _, count in sorted_months[:3])
            last_3 = sum(count for _, count in sorted_months[-3:])
            
            if first_3 == 0:
                return "unknown"
            
            growth_rate = (last_3 - first_3) / first_3
            
            if growth_rate > 0.2:
                return "growing"
            elif growth_rate < -0.2:
                return "declining"
            else:
                return "stable"
        
        except Exception as e:
            print(f"⚠ Error calculating trend: {e}")
            return "unknown"
    
    def _get_most_active_month(self) -> Optional[str]:
        """
        Find the month with most commits.
        
        Returns:
            Month in YYYY-MM format or None
        """
        try:
            cmd = [
                "git",
                "-C", str(self.repo_path),
                "log",
                "--all",
                "--format=%ai",
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return None
            
            monthly_counts = defaultdict(int)
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        date = datetime.fromisoformat(line.replace('Z', '+00:00'))
                        month = date.strftime("%Y-%m")
                        monthly_counts[month] += 1
                    except (ValueError, AttributeError):
                        pass
            
            if monthly_counts:
                return max(monthly_counts.items(), key=lambda x: x[1])[0]
            return None
        
        except Exception as e:
            print(f"⚠ Error finding most active month: {e}")
            return None
    
    def analyze(self) -> ContributorAnalysis:
        """
        Perform complete contributor analysis.
        
        Returns:
            ContributorAnalysis object
        """
        print(f"🔍 Analyzing contributors: {self.repo_path}")
        
        # Parse git log
        self.contributors = self._parse_git_log()
        
        if not self.contributors:
            print("⚠ No contributors found")
            return ContributorAnalysis(
                total_contributors=0,
                total_commits=0,
                top_contributors=[],
                team_concentration="unknown",
                concentration_score=0.0,
                pareto_ratio=0.0,
                inactive_contributors=0,
                bot_contributors=[],
                contributor_trend="unknown",
                average_commits_per_contributor=0.0,
                most_active_month=None,
                contribution_distribution={},
                team_diversity={}
            )
        
        # Enrich with GitHub data if available
        self._enrich_with_github_data(self.contributors)
        
        # Calculate statistics
        total_commits = sum(c.commits for c in self.contributors.values())
        total_contributors = len(self.contributors)
        
        # Calculate contribution percentages
        for contrib in self.contributors.values():
            contrib.percent = (contrib.commits / total_commits * 100) if total_commits > 0 else 0
        
        # Get top contributors
        sorted_contribs = sorted(
            self.contributors.values(),
            key=lambda x: x.commits,
            reverse=True
        )
        top_contributors = [asdict(c) for c in sorted_contribs[:20]]
        
        # Separate bots and inactive
        bot_contributors = [c.name for c in self.contributors.values() if c.is_bot]
        inactive_contributors = sum(1 for c in self.contributors.values() if c.commits == 1)
        
        # Calculate concentration
        concentration_level, concentration_score, pareto_ratio = self._calculate_concentration(
            self.contributors,
            total_commits
        )
        
        # Calculate trend
        trend = self._calculate_trend(self.contributors)
        
        # Find most active month
        most_active_month = self._get_most_active_month()
        
        # Distribution buckets
        distribution = defaultdict(int)
        for contrib in self.contributors.values():
            if contrib.commits >= 100:
                distribution["100+"] += 1
            elif contrib.commits >= 50:
                distribution["50-99"] += 1
            elif contrib.commits >= 20:
                distribution["20-49"] += 1
            elif contrib.commits >= 5:
                distribution["5-19"] += 1
            else:
                distribution["1-4"] += 1
        
        # Team diversity
        active_contributors = sum(1 for c in self.contributors.values() if c.commits > 1)
        team_diversity = {
            "active_contributors": active_contributors,
            "inactive_contributors": inactive_contributors,
            "bot_contributors": len(bot_contributors),
            "human_contributors": total_contributors - len(bot_contributors),
            "participation_ratio": round(
                (active_contributors / total_contributors * 100) if total_contributors > 0 else 0,
                1
            )
        }
        
        # Create output
        analysis = ContributorAnalysis(
            total_contributors=total_contributors,
            total_commits=total_commits,
            top_contributors=top_contributors,
            team_concentration=concentration_level,
            concentration_score=concentration_score,
            pareto_ratio=pareto_ratio,
            inactive_contributors=inactive_contributors,
            bot_contributors=bot_contributors,
            contributor_trend=trend,
            average_commits_per_contributor=round(
                total_commits / total_contributors if total_contributors > 0 else 0,
                1
            ),
            most_active_month=most_active_month,
            contribution_distribution=dict(distribution),
            team_diversity=team_diversity
        )
        
        # Print summary
        print(f"✓ Analysis complete!")
        print(f"  Total Contributors: {analysis.total_contributors}")
        print(f"  Total Commits: {analysis.total_commits}")
        print(f"  Avg Commits/Contributor: {analysis.average_commits_per_contributor}")
        print(f"  Team Concentration: {analysis.team_concentration}")
        print(f"  Contributor Trend: {analysis.contributor_trend}")
        
        return analysis


def analyze_contributors(
    repo_path: str,
    github_token: Optional[str] = None,
    github_owner: Optional[str] = None,
    github_repo: Optional[str] = None
) -> ContributorAnalysis:
    """
    Convenience function to analyze repository contributors.
    
    Args:
        repo_path: Path to the repository
        github_token: GitHub API token
        github_owner: GitHub owner
        github_repo: GitHub repository name
        
    Returns:
        ContributorAnalysis object
    """
    analyzer = ContributorAnalyzer(repo_path, github_token, github_owner, github_repo)
    return analyzer.analyze()


def main():
    """Example usage"""
    import json
    
    # Example: analyze a repository
    test_repo = "/tmp/gitfit-repos/test-repo"
    
    if not os.path.exists(test_repo):
        print(f"Repository not found at {test_repo}")
        print("This example requires a cloned repository to exist")
        return
    
    try:
        analysis = analyze_contributors(test_repo)
        
        # Print detailed results
        print("\n" + "="*60)
        print("CONTRIBUTOR ANALYSIS RESULTS")
        print("="*60)
        
        print(f"\n👥 Statistics:")
        print(f"  Total Contributors: {analysis.total_contributors}")
        print(f"  Total Commits: {analysis.total_commits}")
        print(f"  Avg Commits/Contributor: {analysis.average_commits_per_contributor}")
        
        print(f"\n🎯 Team Metrics:")
        print(f"  Concentration Level: {analysis.team_concentration}")
        print(f"  Concentration Score: {analysis.concentration_score}/100")
        print(f"  Pareto Ratio (Top 20%): {analysis.pareto_ratio}%")
        print(f"  Contributor Trend: {analysis.contributor_trend}")
        
        if analysis.most_active_month:
            print(f"  Most Active Month: {analysis.most_active_month}")
        
        print(f"\n🏆 Top Contributors:")
        for contrib in analysis.top_contributors[:5]:
            print(f"  {contrib['name']}: {contrib['commits']} commits ({contrib['percent']:.1f}%)")
        
        print(f"\n🤖 Bots: {len(analysis.bot_contributors)}")
        if analysis.bot_contributors:
            for bot in analysis.bot_contributors[:5]:
                print(f"  {bot}")
        
        print(f"\n📊 Contribution Distribution:")
        for bucket, count in sorted(analysis.contribution_distribution.items()):
            print(f"  {bucket} commits: {count} contributors")
        
        print(f"\n🌍 Team Diversity:")
        for key, value in analysis.team_diversity.items():
            print(f"  {key}: {value}")
        
        # Print as JSON
        print("\n" + "="*60)
        print("JSON OUTPUT:")
        print("="*60)
        print(json.dumps(analysis.to_dict(), indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()