"""
GitFit v2: Repository Cloner Module
Location: backend/github/cloner.py

Responsible for cloning repositories to /tmp/gitfit-repos/{repo_id}/
Handles authentication and cleanup as per GitFit v2 Architecture Guide
"""

import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse


class RepoCloner:
    """
    Clones GitHub repositories to local filesystem.
    
    Attributes:
        base_path (str): Base directory for clones (/tmp/gitfit-repos/)
        github_token (str, optional): GitHub token for private repo access
    """
    
    def __init__(self, base_path: str = "/tmp/gitfit-repos", github_token: Optional[str] = None):
        """
        Initialize the cloner.
        
        Args:
            base_path: Directory where repos will be cloned
            github_token: GitHub authentication token (for private repos)
        """
        self.base_path = base_path
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        
        # Ensure base directory exists
        Path(self.base_path).mkdir(parents=True, exist_ok=True)
        print(f"✓ Initialized cloner with base path: {self.base_path}")
    
    @staticmethod
    def generate_id() -> str:
        """
        Generate a unique ID for this analysis session.
        
        Returns:
            Unique identifier string (UUID4)
        """
        return str(uuid.uuid4())[:8]  # Use first 8 chars for brevity
    
    @staticmethod
    def parse_github_url(url: str) -> Tuple[str, str]:
        """
        Parse GitHub URL to extract owner and repo name.
        
        Args:
            url: GitHub repository URL
            
        Returns:
            Tuple of (owner, repo_name)
            
        Raises:
            ValueError: If URL is not a valid GitHub repository URL
        """
        parsed = urlparse(url)
        
        # Handle both https and http
        if "github.com" not in parsed.netloc:
            raise ValueError(f"Invalid GitHub URL: {url}")
        
        # Extract path and remove .git suffix if present
        path = parsed.path.strip("/")
        if path.endswith(".git"):
            path = path[:-4]
        
        parts = path.split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub URL format: {url}")
        
        owner, repo = parts[0], parts[1]
        
        if not owner or not repo:
            raise ValueError(f"Could not parse GitHub URL: {url}")
        
        return owner, repo
    
    def clone_repo(self, url: str, repo_id: Optional[str] = None) -> str:
        """
        Clone a GitHub repository to /tmp/gitfit-repos/{repo_id}/
        
        Args:
            url: GitHub repository URL (e.g., https://github.com/user/repo)
            repo_id: Optional unique ID. If not provided, generates one.
            
        Returns:
            Path to cloned repository
            
        Raises:
            ValueError: If URL is invalid
            RuntimeError: If git clone fails
        """
        # Validate URL
        try:
            owner, repo_name = self.parse_github_url(url)
            print(f"✓ Parsed repository: {owner}/{repo_name}")
        except ValueError as e:
            raise ValueError(f"URL parsing failed: {e}")
        
        # Generate ID if not provided
        if repo_id is None:
            repo_id = self.generate_id()
        
        # Create clone path
        clone_path = os.path.join(self.base_path, repo_id)
        
        # Ensure the directory doesn't already exist
        if os.path.exists(clone_path):
            print(f"⚠ Directory already exists: {clone_path}")
            return clone_path
        
        try:
            print(f"🔄 Cloning repository to: {clone_path}")
            
            # Prepare git command with authentication if token is available
            git_url = url
            if self.github_token:
                # Insert token into URL for authentication
                git_url = url.replace(
                    "https://github.com/",
                    f"https://oauth2:{self.github_token}@github.com/"
                )
                print("✓ Using GitHub token for authentication")
            
            # Execute git clone
            result = subprocess.run(
                ["git", "clone", "--depth", "1", git_url, clone_path],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise RuntimeError(
                    f"Git clone failed: {result.stderr}\n"
                    f"Return code: {result.returncode}"
                )
            
            print(f"✓ Successfully cloned to: {clone_path}")
            return clone_path
            
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Git clone timed out for {url}")
        except Exception as e:
            # Clean up partial clone on failure
            if os.path.exists(clone_path):
                shutil.rmtree(clone_path)
            raise RuntimeError(f"Clone operation failed: {e}")
    
    def cleanup_repo(self, path: str) -> None:
        """
        Delete cloned repository to save disk space.
        This should be called after analysis completes.
        
        Args:
            path: Path to the cloned repository to delete
        """
        if not os.path.exists(path):
            print(f"⚠ Path does not exist: {path}")
            return
        
        try:
            print(f"🧹 Cleaning up: {path}")
            shutil.rmtree(path)
            print(f"✓ Successfully deleted: {path}")
        except Exception as e:
            print(f"❌ Failed to delete {path}: {e}")
    
    def cleanup_old_repos(self, max_age_hours: int = 24) -> None:
        """
        Clean up repositories older than specified age.
        Useful for periodic maintenance.
        
        Args:
            max_age_hours: Delete repos older than this many hours
        """
        import time
        
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)
        
        if not os.path.exists(self.base_path):
            return
        
        deleted_count = 0
        try:
            for item in os.listdir(self.base_path):
                item_path = os.path.join(self.base_path, item)
                if os.path.isdir(item_path):
                    item_time = os.path.getmtime(item_path)
                    if item_time < cutoff_time:
                        self.cleanup_repo(item_path)
                        deleted_count += 1
            
            print(f"✓ Cleanup complete: {deleted_count} old repos deleted")
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")


def main():
    """
    Example usage of the RepoCloner
    """
    # Initialize cloner
    cloner = RepoCloner(
        base_path="/tmp/gitfit-repos",
        github_token=None  # Will use GITHUB_TOKEN env var if available
    )
    
    # Example: Clone a repository
    example_repos = [
        "https://github.com/autumn-xn/github-analyzer",
        "https://github.com/facebook/react",
        "https://github.com/torvalds/linux"
    ]
    
    cloned_paths = []
    
    for repo_url in example_repos:
        try:
            path = cloner.clone_repo(repo_url)
            cloned_paths.append(path)
            print(f"Repository info: {path}")
            print(f"  Size: {get_dir_size(path)}")
        except Exception as e:
            print(f"❌ Error cloning {repo_url}: {e}")
    
    # Cleanup after analysis (uncomment to use)
    # for path in cloned_paths:
    #     cloner.cleanup_repo(path)


def get_dir_size(path: str) -> str:
    """
    Calculate total size of a directory.
    
    Args:
        path: Directory path
        
    Returns:
        Human-readable size string
    """
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(filepath)
            except (OSError, FileNotFoundError):
                pass
    
    # Convert to human-readable format
    for unit in ['B', 'KB', 'MB', 'GB']:
        if total_size < 1024.0:
            return f"{total_size:.2f} {unit}"
        total_size /= 1024.0
    return f"{total_size:.2f} TB"


if __name__ == "__main__":
    main()