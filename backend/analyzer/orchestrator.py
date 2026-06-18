# ─── backend/analyzer/orchestrator.py ────────────────────────────────────────
# GitFit v2 Orchestrator
#
# Coordinates all 11 analyzers to run in parallel, aggregates results,
# and formats data for LLM synthesis.
#
# Entry point: orchestrate_analysis(repo_path, repo_full_name, ...)
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Any
from dataclasses import asdict

# Import all analyzers
from analyzer.file_scanner import scan_repository
from analyzer.structure_analyzer import analyze_repository as analyze_structure
from analyzer.dependency_analyzer import analyze_dependencies
from analyzer.contributor_analyzer import analyze_contributors
from analyzer.commit_analyzer import analyze_commits

log = logging.getLogger("github_analyzer.orchestrator")


# ─── Data Model for Aggregated Analysis ───────────────────────────────────────


class AggregatedAnalysis:
    """Container for all analyzer results."""
    
    def __init__(self):
        self.files: dict = {}
        self.structure: dict = {}
        self.dependencies: dict = {}
        self.contributors: dict = {}
        self.commits: dict = {}
    
    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            "files": self.files,
            "structure": self.structure,
            "dependencies": self.dependencies,
            "contributors": self.contributors,
            "commits": self.commits,
        }


# ─── Core Orchestrator Class ──────────────────────────────────────────────────


class RepositoryAnalyzer:
    """
    Orchestrates all analyzers to run in parallel.
    
    Takes a cloned repo path and runs:
    - File Scanner
    - Structure Analyzer
    - Dependency Analyzer
    - Contributor Analyzer
    - Commit Analyzer
    
    All run concurrently using asyncio.gather().
    """
    
    def __init__(
        self,
        repo_path: str,
        github_owner: Optional[str] = None,
        github_repo: Optional[str] = None,
        github_token: Optional[str] = None,
    ):
        """
        Initialize the orchestrator.
        
        Args:
            repo_path: Path to cloned repository
            github_owner: GitHub username (for API enrichment)
            github_repo: GitHub repo name (for API enrichment)
            github_token: GitHub API token
        """
        self.repo_path = Path(repo_path)
        self.github_owner = github_owner
        self.github_repo = github_repo
        self.github_token = github_token
        
        if not self.repo_path.exists():
            raise ValueError(f"Repo path does not exist: {repo_path}")
        
        log.info("Orchestrator initialized for %s", repo_path)
    
    async def analyze_all(self) -> AggregatedAnalysis:
        """
        Run all analyzers in parallel and aggregate results.
        
        Returns:
            AggregatedAnalysis with all analyzer outputs
        """
        log.info("🚀 Starting parallel analysis...")
        
        try:
            # Run all 5 analyzers concurrently
            (
                file_stats,
                structure,
                dependencies,
                contributors,
                commits,
            ) = await asyncio.gather(
                self._run_file_scanner(),
                self._run_structure_analyzer(),
                self._run_dependency_analyzer(),
                self._run_contributor_analyzer(),
                self._run_commit_analyzer(),
                return_exceptions=True,  # Don't crash if one fails
            )
            
            # Aggregate results
            aggregated = AggregatedAnalysis()
            
            # Convert dataclass results to dicts
            if file_stats and not isinstance(file_stats, Exception):
                aggregated.files = file_stats.to_dict() if hasattr(file_stats, 'to_dict') else asdict(file_stats)
                log.info("✓ File Scanner: %d files analyzed", file_stats.total_files)
            else:
                log.warning("⚠ File Scanner failed: %s", file_stats)
            
            if structure and not isinstance(structure, Exception):
                aggregated.structure = structure.to_dict() if hasattr(structure, 'to_dict') else asdict(structure)
                log.info("✓ Structure Analyzer: %s", structure.architecture_style)
            else:
                log.warning("⚠ Structure Analyzer failed: %s", structure)
            
            if dependencies and not isinstance(dependencies, Exception):
                aggregated.dependencies = dependencies.to_dict() if hasattr(dependencies, 'to_dict') else asdict(dependencies)
                log.info("✓ Dependency Analyzer: %d deps, %d vulnerabilities", 
                        dependencies.total_dependencies, dependencies.vulnerable_count)
            else:
                log.warning("⚠ Dependency Analyzer failed: %s", dependencies)
            
            if contributors and not isinstance(contributors, Exception):
                aggregated.contributors = contributors.to_dict() if hasattr(contributors, 'to_dict') else asdict(contributors)
                log.info("✓ Contributor Analyzer: %d contributors", contributors.total_contributors)
            else:
                log.warning("⚠ Contributor Analyzer failed: %s", contributors)
            
            if commits and not isinstance(commits, Exception):
    # CommitAnalysis now has to_dict() method
                if hasattr(commits, 'to_dict'):
                    aggregated.commits = commits.to_dict()
                else:
                    log.warning("⚠ CommitAnalysis missing to_dict() method")
                log.info("✓ Commit Analyzer: %d commits analyzed", 
                        commits.frequency.commits_total if commits.frequency else 0)
            else:
                log.warning("⚠ Commit Analyzer failed: %s", commits)
            
            log.info("✅ All analyzers complete")
            return aggregated
        
        except Exception as exc:
            log.exception("Error during parallel analysis: %s", exc)
            raise
    
    async def _run_file_scanner(self):
        """Run file scanner in thread pool."""
        try:
            return await asyncio.to_thread(scan_repository, str(self.repo_path))
        except Exception as e:
            log.error("File scanner error: %s", e)
            raise
    
    async def _run_structure_analyzer(self):
        """Run structure analyzer in thread pool."""
        try:
            return await asyncio.to_thread(analyze_structure, str(self.repo_path))
        except Exception as e:
            log.error("Structure analyzer error: %s", e)
            raise
    
    async def _run_dependency_analyzer(self):
        """Run dependency analyzer in thread pool."""
        try:
            return await asyncio.to_thread(analyze_dependencies, str(self.repo_path))
        except Exception as e:
            log.error("Dependency analyzer error: %s", e)
            raise
    
    async def _run_contributor_analyzer(self):
        """Run contributor analyzer in thread pool."""
        try:
            return await asyncio.to_thread(
                analyze_contributors,
                str(self.repo_path),
                self.github_token,
                self.github_owner,
                self.github_repo,
            )
        except Exception as e:
            log.error("Contributor analyzer error: %s", e)
            raise
    
    async def _run_commit_analyzer(self):
        """Run commit analyzer (already async)."""
        try:
            return await analyze_commits(str(self.repo_path))
        except Exception as e:
            log.error("Commit analyzer error: %s", e)
            raise


# ─── Format Analysis Data for LLM ─────────────────────────────────────────────


def _format_analysis_for_llm(
    analysis: AggregatedAnalysis,
    repo_full_name: str,
    readme: Optional[str] = None,
) -> str:
    """
    Convert aggregated analyzer outputs into human-readable text for LLM.
    
    Returns a formatted string that becomes the 'user_prompt' for the LLM.
    """
    sections = [f"# Repository: {repo_full_name}\n"]
    
    # README
    if readme:
        truncated = readme[:2000]
        if len(readme) > 2000:
            truncated += "\n\n[... README truncated ...]"
        sections.append(f"## README\n{truncated}")
    
    # File Statistics
    files = analysis.files
    if files:
        sections.append("\n## File Statistics")
        sections.append(f"- Total files: {files.get('total_files', 0):,}")
        sections.append(f"- Total size: {files.get('total_size_bytes', 0) / (1024**2):.1f} MB")
        sections.append(f"- Total lines of code: {files.get('total_lines', 0):,}")
        
        # Languages
        langs = files.get('languages', {})
        if langs:
            lang_str = ", ".join([f"{lang}: {count}" for lang, count in list(langs.items())[:5]])
            sections.append(f"- Primary languages: {lang_str}")
        
        # Largest files
        largest = files.get('largest_files', [])
        if largest:
            sections.append("\n### Largest Files")
            for f in largest[:3]:
                sections.append(f"- {f['path']}: {f['lines']:,} lines")
    
    # Architecture & Structure
    structure = analysis.structure
    if structure:
        sections.append("\n## Architecture & Structure")
        sections.append(f"- Architecture style: {structure.get('architecture_style', 'unknown')}")
        sections.append(f"- Modularity score: {structure.get('modularity_score', 'N/A')}/10")
        sections.append(f"- Testing coverage: {structure.get('testing_structure', 'unknown')}")
        
        # Patterns
        patterns = structure.get('detected_patterns', [])
        if patterns:
            sections.append(f"- Detected patterns: {', '.join(patterns)}")
        
        # Entry points
        entries = structure.get('entry_points', [])
        if entries:
            sections.append(f"- Entry points: {', '.join(entries[:3])}")
    
    # Dependencies
    deps = analysis.dependencies
    if deps:
        sections.append("\n## Dependencies")
        sections.append(f"- Total dependencies: {deps.get('total_dependencies', 0)}")
        sections.append(f"- Security issues: {deps.get('vulnerable_count', 0)}")
        sections.append(f"- Outdated packages: {deps.get('outdated_count', 0)}")
        
        # Ecosystems
        ecosystems = deps.get('ecosystems', {})
        if ecosystems:
            eco_str = ", ".join([f"{e}: {c}" for e, c in list(ecosystems.items())[:3]])
            sections.append(f"- Package ecosystems: {eco_str}")
        
        # Security issues
        vulns = deps.get('security_issues', [])
        if vulns:
            sections.append("\n### Vulnerabilities")
            for v in vulns[:3]:
                sections.append(f"- {v['package']} ({v['version']}): {v['vulnerability']} [Severity: {v['severity']}]")
    
    # Contributors
    contribs = analysis.contributors
    if contribs:
        sections.append("\n## Contributors & Team")
        sections.append(f"- Total contributors: {contribs.get('total_contributors', 0)}")
        sections.append(f"- Total commits: {contribs.get('total_commits', 0)}")
        sections.append(f"- Team concentration: {contribs.get('team_concentration', 'unknown')}")
        
        # Top contributors
        top = contribs.get('top_contributors', [])
        if top:
            sections.append("\n### Top Contributors")
            for c in top[:3]:
                sections.append(f"- {c.get('name', 'Unknown')}: {c.get('commits', 0)} commits ({c.get('percent', 0):.1f}%)")
        
        # Trend
        trend = contribs.get('contributor_trend', 'unknown')
        sections.append(f"- Contribution trend: {trend}")
    
    # Commits
    commits = analysis.commits
    if commits:
        sections.append("\n## Commit Activity")
        freq = commits.get('frequency', {})
        if freq:
            sections.append(f"- Total commits: {freq.get('commits_total', 0)}")
            sections.append(f"- Last 30 days: {freq.get('commits_last_30_days', 0)}")
            sections.append(f"- Avg per week: {freq.get('avg_commits_per_week', 0):.1f}")
        
        trend = commits.get('trend', {})
        if trend:
            sections.append(f"- Trend: {trend.get('trend', 'unknown')}")
            sections.append(f"- Active: {'Yes' if trend.get('is_active') else 'No'}")
        
        # Message quality
        msg = commits.get('message_patterns', {})
        if msg:
            sections.append(f"- Conventional commits: {msg.get('conventional_commits', 0)}")
            sections.append(f"- Message quality score: {msg.get('message_quality_score', 0)}/10")
    
    sections.append("\n---\nAnalyze this data and provide insights.")
    return "\n".join(sections)


# ─── Public API ───────────────────────────────────────────────────────────────


async def orchestrate_analysis(
    repo_path: str,
    repo_full_name: str,
    readme: Optional[str] = None,
    github_owner: Optional[str] = None,
    github_repo: Optional[str] = None,
    github_token: Optional[str] = None,
) -> dict:
    """
    Main entry point: orchestrate full v2 analysis.
    
    Steps:
    1. Run all analyzers in parallel
    2. Aggregate results
    3. Format for LLM
    4. Return everything
    
    Parameters
    ----------
    repo_path : str
        Path to cloned repository
    repo_full_name : str
        Repository full name (e.g., "facebook/react")
    readme : str, optional
        README content
    github_owner : str, optional
        GitHub owner (for API enrichment)
    github_repo : str, optional
        GitHub repo name (for API enrichment)
    github_token : str, optional
        GitHub API token
    
    Returns
    -------
    dict
        {
            "analysis_data": AggregatedAnalysis.to_dict(),
            "llm_prompt": str,
        }
    """
    
    log.info("Starting orchestration for %s", repo_full_name)
    
    try:
        # Step 1: Run all analyzers in parallel
        orchestrator = RepositoryAnalyzer(
            repo_path,
            github_owner=github_owner,
            github_repo=github_repo,
            github_token=github_token,
        )
        
        analysis = await orchestrator.analyze_all()
        analysis_dict = analysis.to_dict()
        
        # Step 2: Format for LLM
        llm_prompt = _format_analysis_for_llm(analysis, repo_full_name, readme)
        
        log.info("Orchestration complete for %s", repo_full_name)
        
        return {
            "analysis_data": analysis_dict,
            "llm_prompt": llm_prompt,
        }
    
    except Exception as exc:
        log.exception("Orchestration failed for %s: %s", repo_full_name, exc)
        raise