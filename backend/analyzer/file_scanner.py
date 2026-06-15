"""
GitFit v2: File Scanner Module
Location: backend/analyzer/file_scanner.py

Responsible for walking repository directory tree, counting files,
grouping by language, and identifying largest/common files.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, asdict


# Extension to Language mapping
EXTENSION_MAP = {
    # Python
    ".py": "Python",
    ".pyx": "Python",
    ".pyi": "Python",
    
    # JavaScript/TypeScript
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".vue": "Vue",
    
    # Java
    ".java": "Java",
    ".class": "Java",
    ".jar": "Java",
    
    # C/C++
    ".c": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".h": "C/C++",
    ".hpp": "C++",
    
    # Go
    ".go": "Go",
    
    # Rust
    ".rs": "Rust",
    
    # Ruby
    ".rb": "Ruby",
    
    # PHP
    ".php": "PHP",
    
    # C#
    ".cs": "C#",
    
    # Swift
    ".swift": "Swift",
    
    # Kotlin
    ".kt": "Kotlin",
    
    # R
    ".r": "R",
    ".R": "R",
    
    # Data/Config
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".xml": "XML",
    ".toml": "TOML",
    ".ini": "INI",
    ".conf": "Config",
    ".config": "Config",
    ".cfg": "Config",
    
    # Markup
    ".md": "Markdown",
    ".markdown": "Markdown",
    ".rst": "ReStructuredText",
    ".html": "HTML",
    ".htm": "HTML",
    ".tex": "LaTeX",
    
    # CSS/Styling
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "SASS",
    ".less": "LESS",
    
    # Shell/Scripting
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".fish": "Shell",
    ".bat": "Batch",
    ".cmd": "Batch",
    ".ps1": "PowerShell",
    
    # SQL
    ".sql": "SQL",
    
    # SQL Dialects
    ".pl": "PL/SQL",
    ".plpgsql": "PL/pgSQL",
    
    # Documentation
    ".txt": "Text",
    ".doc": "Document",
    ".docx": "Document",
    
    # Docker/Kubernetes
    "dockerfile": "Docker",
    ".dockerfile": "Docker",
    
    # CI/CD
    ".yml": "YAML",
    ".yaml": "YAML",
    
    # Other
    ".gradle": "Gradle",
    ".maven": "Maven",
    ".sbt": "Scala",
    ".scala": "Scala",
    ".clj": "Clojure",
    ".cljs": "ClojureScript",
    ".edn": "Clojure",
}

# Common configuration files
COMMON_FILES = {
    "package.json": "Node.js",
    "requirements.txt": "Python",
    "setup.py": "Python",
    "setup.cfg": "Python",
    "pyproject.toml": "Python",
    "Pipfile": "Python",
    "go.mod": "Go",
    "go.sum": "Go",
    "Cargo.toml": "Rust",
    "Cargo.lock": "Rust",
    "pom.xml": "Maven",
    "build.gradle": "Gradle",
    "Gemfile": "Ruby",
    "Rakefile": "Ruby",
    "composer.json": "PHP",
    "pubspec.yaml": "Dart",
    "mix.exs": "Elixir",
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker",
    "docker-compose.yaml": "Docker",
    ".dockerignore": "Docker",
    ".gitignore": "Git",
    ".gitattributes": "Git",
    ".github": "GitHub",
    ".gitlab-ci.yml": "GitLab CI",
    ".travis.yml": "Travis CI",
    ".circleci": "CircleCI",
    "Jenkinsfile": "Jenkins",
    "sonar-project.properties": "SonarQube",
    "tox.ini": "Python Testing",
    "pytest.ini": "Python Testing",
    "Makefile": "Build",
    "CMakeLists.txt": "CMake",
    "configure": "Build",
    ".editorconfig": "EditorConfig",
    ".env": "Environment",
    ".env.example": "Environment",
    "LICENSE": "License",
    "README.md": "Documentation",
    "CONTRIBUTING.md": "Documentation",
    "CHANGELOG.md": "Documentation",
}

# Directories to skip (binary/unnecessary)
SKIP_DIRS = {
    ".git",
    ".github",
    ".gitlab",
    ".hg",
    ".svn",
    ".bzr",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".tox",
    "venv",
    "env",
    ".venv",
    ".env",
    "dist",
    "build",
    ".build",
    "target",
    "out",
    ".gradle",
    ".m2",
    "vendor",
    "Pods",
    ".CocoaPods",
    ".bundle",
    ".cache",
    ".next",
    ".nuxt",
    ".vuepress",
    "coverage",
    ".nyc_output",
    ".eslintcache",
    "*.egg-info",
    ".eggs",
    ".mypy_cache",
    ".dmypy.json",
    ".pyre",
    "site-packages",
    "htmlcov",
    ".idea",
    ".vscode",
    ".DS_Store",
}

# Binary file extensions
BINARY_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd",
    ".o", ".a", ".so", ".dylib", ".dll",
    ".exe", ".com", ".bat",
    ".jar", ".class", ".dex",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
    ".mp3", ".mp4", ".avi", ".mov", ".mkv",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".bin", ".hex", ".elf",
}


@dataclass
class FileInfo:
    """Information about a single file"""
    path: str  # Relative path from repo root
    extension: str
    lines: int
    size_bytes: int


@dataclass
class FileStats:
    """Complete file statistics for a repository"""
    total_files: int
    total_lines: int
    total_size_bytes: int
    languages: Dict[str, int]  # Language -> file count
    file_types: Dict[str, int]  # Extension -> file count
    largest_files: List[Dict]  # List of largest files with path, lines, size
    common_files_found: Dict[str, str]  # Filename -> type
    largest_directories: List[Dict]  # Directories by file count
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class FileScanner:
    """
    Scans repository directory tree and collects file statistics.
    
    Attributes:
        repo_path (str): Root path of the repository
        skip_dirs (set): Directories to skip during scan
        text_extensions (set): Extensions to count lines for
    """
    
    def __init__(self, repo_path: str, skip_dirs: Optional[set] = None):
        """
        Initialize the file scanner.
        
        Args:
            repo_path: Path to the repository root
            skip_dirs: Set of directory names to skip
        """
        self.repo_path = Path(repo_path)
        
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        self.skip_dirs = skip_dirs or SKIP_DIRS
        print(f"✓ Initialized FileScanner for: {repo_path}")
    
    @staticmethod
    def _should_skip_dir(dir_name: str, skip_dirs: set) -> bool:
        """Check if directory should be skipped"""
        return dir_name in skip_dirs or dir_name.startswith(".")
    
    @staticmethod
    def _is_binary_file(extension: str) -> bool:
        """Check if file is binary based on extension"""
        return extension.lower() in BINARY_EXTENSIONS
    
    @staticmethod
    def _get_language(extension: str, filename: str) -> str:
        """
        Determine language from file extension.
        
        Args:
            extension: File extension (e.g., ".py")
            filename: Full filename (e.g., "Dockerfile")
            
        Returns:
            Language name or "Other"
        """
        # Check common files first
        if filename.lower() in COMMON_FILES:
            return COMMON_FILES[filename.lower()]
        
        # Then check extension
        if extension:
            return EXTENSION_MAP.get(extension.lower(), "Other")
        
        return "Other"
    
    @staticmethod
    def _count_lines(file_path: Path) -> int:
        """
        Count lines in a text file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Number of lines, or 0 if file can't be read
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except (OSError, IOError):
            return 0
    
    def scan(self) -> FileStats:
        """
        Scan the repository and collect statistics.
        
        Returns:
            FileStats object with comprehensive file statistics
        """
        print(f"🔍 Scanning repository: {self.repo_path}")
        
        files = []
        languages = defaultdict(int)
        file_types = defaultdict(int)
        dir_file_counts = defaultdict(int)
        
        total_lines = 0
        total_size = 0
        
        # Walk directory tree
        for root, dirs, filenames in os.walk(self.repo_path):
            # Remove directories we should skip
            dirs[:] = [
                d for d in dirs 
                if not self._should_skip_dir(d, self.skip_dirs)
            ]
            
            # Process files
            for filename in filenames:
                file_path = Path(root) / filename
                
                # Skip symlinks
                if file_path.is_symlink():
                    continue
                
                try:
                    # Get file info
                    extension = file_path.suffix
                    relative_path = str(file_path.relative_to(self.repo_path))
                    file_size = file_path.stat().st_size
                    
                    # Count by directory
                    dir_path = str(file_path.parent.relative_to(self.repo_path))
                    dir_file_counts[dir_path] += 1
                    
                    # Skip binary files
                    if self._is_binary_file(extension):
                        continue
                    
                    # Get language
                    language = self._get_language(extension, filename)
                    languages[language] += 1
                    file_types[extension or "no_extension"] += 1
                    
                    # Count lines for text files
                    lines = self._count_lines(file_path) if not extension else \
                            self._count_lines(file_path) if language != "Other" or extension in {".txt", ".md", ".rst"} else 0
                    
                    total_lines += lines
                    total_size += file_size
                    
                    files.append(FileInfo(
                        path=relative_path,
                        extension=extension or "no_extension",
                        lines=lines,
                        size_bytes=file_size
                    ))
                    
                except (OSError, IOError) as e:
                    print(f"⚠ Could not process file {file_path}: {e}")
                    continue
        
        # Find largest files
        files_sorted = sorted(files, key=lambda f: f.lines, reverse=True)
        largest_files = [
            {
                "path": f.path,
                "lines": f.lines,
                "size_bytes": f.size_bytes,
                "extension": f.extension
            }
            for f in files_sorted[:20]  # Top 20
        ]
        
        # Find largest directories
        dirs_sorted = sorted(
            dir_file_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        largest_directories = [
            {
                "path": path,
                "file_count": count
            }
            for path, count in dirs_sorted[:10]  # Top 10
        ]
        
        # Find common files
        common_files_found = {}
        for filename, file_type in COMMON_FILES.items():
            search_path = self.repo_path / filename
            if search_path.exists():
                common_files_found[filename] = file_type
        
        # Create stats object
        stats = FileStats(
            total_files=len(files),
            total_lines=total_lines,
            total_size_bytes=total_size,
            languages=dict(sorted(languages.items(), key=lambda x: x[1], reverse=True)),
            file_types=dict(sorted(file_types.items(), key=lambda x: x[1], reverse=True)),
            largest_files=largest_files,
            common_files_found=common_files_found,
            largest_directories=largest_directories
        )
        
        # Print summary
        print(f"✓ Scan complete!")
        print(f"  Total files: {stats.total_files}")
        print(f"  Total lines: {stats.total_lines:,}")
        print(f"  Total size: {self._format_bytes(stats.total_size_bytes)}")
        print(f"  Languages: {len(stats.languages)}")
        
        return stats
    
    @staticmethod
    def _format_bytes(size_bytes: int) -> str:
        """Format bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"


def scan_repository(repo_path: str) -> FileStats:
    """
    Convenience function to scan a repository and return statistics.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        FileStats object with comprehensive statistics
    """
    scanner = FileScanner(repo_path)
    return scanner.scan()


def main():
    """Example usage"""
    import json
    
    # Example: scan a repository
    test_repo = "/tmp/gitfit-repos/test-repo"
    
    if not os.path.exists(test_repo):
        print(f"Repository not found at {test_repo}")
        print("This example requires a cloned repository to exist")
        return
    
    try:
        stats = scan_repository(test_repo)
        
        # Print detailed results
        print("\n" + "="*60)
        print("FILE SCANNER RESULTS")
        print("="*60)
        
        print(f"\n📊 Overall Statistics:")
        print(f"  Total Files: {stats.total_files}")
        print(f"  Total Lines: {stats.total_lines:,}")
        print(f"  Total Size: {FileScanner._format_bytes(stats.total_size_bytes)}")
        
        print(f"\n💬 Languages:")
        for lang, count in list(stats.languages.items())[:10]:
            print(f"  {lang}: {count} files")
        
        print(f"\n📁 Largest Directories:")
        for dir_info in stats.largest_directories[:5]:
            print(f"  {dir_info['path']}: {dir_info['file_count']} files")
        
        print(f"\n📄 Largest Files:")
        for file_info in stats.largest_files[:5]:
            print(f"  {file_info['path']}")
            print(f"    Lines: {file_info['lines']:,}, Size: {FileScanner._format_bytes(file_info['size_bytes'])}")
        
        print(f"\n🔧 Common Files Found:")
        for filename, file_type in stats.common_files_found.items():
            print(f"  {filename}: {file_type}")
        
        # Print as JSON
        print("\n" + "="*60)
        print("JSON OUTPUT:")
        print("="*60)
        print(json.dumps(stats.to_dict(), indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()