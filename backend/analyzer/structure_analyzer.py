"""
GitFit v2: Structure Analyzer Module
Location: backend/analyzer/structure_analyzer.py

Responsible for detecting repository architecture style, entry points,
architectural layers, and calculating modularity scores.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass, asdict
from enum import Enum


class ArchitectureStyle(str, Enum):
    """Detected architecture patterns"""
    MONOLITH = "monolith"
    MICROSERVICES = "microservices"
    MODULAR_MONOLITH = "modular-monolith"
    LAYERED = "layered"
    MODULAR_MVC = "modular-mvc"
    SERVERLESS = "serverless"
    PLUGIN_BASED = "plugin-based"
    UNKNOWN = "unknown"


# Entry point patterns by language
ENTRY_POINTS = {
    # Python
    "main.py": "Python",
    "__main__.py": "Python",
    "manage.py": "Django",
    "wsgi.py": "Python Web",
    "asgi.py": "Python Async Web",
    
    # JavaScript/Node.js
    "index.js": "JavaScript",
    "app.js": "JavaScript",
    "server.js": "Node.js",
    "index.ts": "TypeScript",
    "app.ts": "TypeScript",
    "server.ts": "TypeScript",
    "index.tsx": "React",
    "app.tsx": "React",
    "main.ts": "TypeScript",
    "main.js": "JavaScript",
    
    # Go
    "main.go": "Go",
    
    # Java
    "Main.java": "Java",
    "Application.java": "Spring Boot",
    
    # Ruby
    "app.rb": "Ruby",
    "main.rb": "Ruby",
    
    # C#
    "Program.cs": "C#",
    "Main.cs": "C#",
    
    # PHP
    "index.php": "PHP",
    "app.php": "PHP",
    
    # Rust
    "main.rs": "Rust",
    "lib.rs": "Rust Library",
}

# Architectural layer patterns
LAYER_PATTERNS = {
    # API/Controller layer
    "api": "API Layer",
    "controller": "Controller Layer",
    "controllers": "Controller Layer",
    "routes": "Routes",
    "routing": "Routes",
    "handler": "Handler Layer",
    "handlers": "Handler Layer",
    "endpoint": "Endpoint Layer",
    "endpoints": "Endpoint Layer",
    "rest": "REST Layer",
    
    # Business/Service layer
    "service": "Business Logic",
    "services": "Business Logic",
    "business": "Business Logic",
    "logic": "Business Logic",
    "usecase": "Use Case",
    "usecases": "Use Case",
    "interactor": "Interactor",
    "interactors": "Interactor",
    
    # Data/Persistence layer
    "model": "Data Model",
    "models": "Data Model",
    "entity": "Entity",
    "entities": "Entity",
    "repository": "Repository",
    "repositories": "Repository",
    "dao": "DAO",
    "persistence": "Persistence",
    "database": "Database",
    "db": "Database",
    "schema": "Schema",
    "migration": "Migration",
    "migrations": "Migration",
    
    # Utilities
    "util": "Utilities",
    "utils": "Utilities",
    "helper": "Utilities",
    "helpers": "Utilities",
    "common": "Common",
    "lib": "Library",
    "libs": "Library",
    "shared": "Shared",
    
    # Configuration
    "config": "Configuration",
    "configuration": "Configuration",
    "settings": "Settings",
    "env": "Environment",
    
    # Testing
    "test": "Tests",
    "tests": "Tests",
    "__tests__": "Tests",
    "spec": "Specs",
    "specs": "Specs",
    
    # Frontend/UI
    "view": "UI/View",
    "views": "UI/View",
    "component": "Components",
    "components": "Components",
    "page": "Pages",
    "pages": "Pages",
    "screen": "Screens",
    "screens": "Screens",
    "ui": "UI",
    "frontend": "Frontend",
    
    # Backend
    "backend": "Backend",
    "server": "Server",
    
    # Infrastructure
    "infra": "Infrastructure",
    "infrastructure": "Infrastructure",
    "deploy": "Deployment",
    "deployment": "Deployment",
    "docker": "Deployment",
    "kubernetes": "Deployment",
    
    # Documentation
    "doc": "Documentation",
    "docs": "Documentation",
    
    # Build/Scripts
    "build": "Build",
    "script": "Scripts",
    "scripts": "Scripts",
    "tool": "Tools",
    "tools": "Tools",
}

# Microservices indicators
MICROSERVICES_INDICATORS = {
    "services",
    "service",
    "microservice",
    "microservices",
    "packages",
    "domains",
    "modules",
}

# Directory purposes
DIRECTORY_PURPOSES = {
    "src": "Source Code",
    "lib": "Libraries",
    "test": "Tests",
    "tests": "Tests",
    "spec": "Specifications",
    "docs": "Documentation",
    "doc": "Documentation",
    "example": "Examples",
    "examples": "Examples",
    "benchmark": "Benchmarks",
    "benchmarks": "Benchmarks",
    "tool": "Tools",
    "tools": "Tools",
    "script": "Scripts",
    "scripts": "Scripts",
    "config": "Configuration",
    "configuration": "Configuration",
    ".github": "CI/CD",
    ".gitlab-ci": "CI/CD",
    ".circleci": "CI/CD",
    "ci": "CI/CD",
    "cd": "CI/CD",
    "deploy": "Deployment",
    "deployment": "Deployment",
    "docker": "Docker",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "infra": "Infrastructure",
    "infrastructure": "Infrastructure",
    "resources": "Resources",
    "assets": "Assets",
    "public": "Public Assets",
    "static": "Static Assets",
    "media": "Media",
    "vendor": "Vendor",
    "node_modules": "Node Packages",
    "venv": "Virtual Environment",
    "env": "Virtual Environment",
}


@dataclass
class DirectoryInfo:
    """Information about a directory"""
    path: str
    purpose: str
    file_count: int
    subdirs: int
    is_layer: bool = False
    layer_type: Optional[str] = None


@dataclass
class StructureAnalysis:
    """Complete structure analysis of a repository"""
    entry_points: List[str]
    architecture_style: str
    layers: List[str]
    modularity_score: float  # 0-10
    key_directories: List[Dict]
    detected_patterns: List[str]
    concerns_separation: Dict[str, int]  # Concern type -> count
    microservices_indicators: List[str]
    testing_structure: str  # "comprehensive", "basic", "minimal", "absent"
    analysis_details: Dict  # Additional metadata
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class StructureAnalyzer:
    """
    Analyzes repository structure, architecture style, and layers.
    
    Attributes:
        repo_path (str): Root path of the repository
        dirs_info (Dict): Information about key directories
    """
    
    def __init__(self, repo_path: str):
        """
        Initialize the structure analyzer.
        
        Args:
            repo_path: Path to the repository root
        """
        self.repo_path = Path(repo_path)
        
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        self.dirs_info: Dict[str, DirectoryInfo] = {}
        print(f"✓ Initialized StructureAnalyzer for: {repo_path}")
    
    def _find_entry_points(self) -> List[str]:
        """
        Find entry points in the repository.
        
        Returns:
            List of entry point file paths
        """
        entry_points = []
        
        # Walk through repo and look for entry point files
        for root, dirs, files in os.walk(self.repo_path):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__', '.venv'}]
            
            for filename in files:
                if filename.lower() in ENTRY_POINTS:
                    file_path = Path(root) / filename
                    relative_path = str(file_path.relative_to(self.repo_path))
                    entry_points.append(relative_path)
        
        # Sort by depth (prefer top-level)
        entry_points.sort(key=lambda x: (x.count(os.sep), x))
        return entry_points[:10]  # Return top 10
    
    def _identify_layers(self) -> List[str]:
        """
        Identify architectural layers in the repository.
        
        Returns:
            List of detected layers
        """
        layers = []
        found_layers = set()
        
        # Check immediate subdirectories
        try:
            for item in self.repo_path.iterdir():
                if item.is_dir():
                    dir_name = item.name.lower()
                    
                    if dir_name in LAYER_PATTERNS:
                        layer_type = LAYER_PATTERNS[dir_name]
                        if layer_type not in found_layers:
                            layers.append(dir_name)
                            found_layers.add(layer_type)
                    
                    # Also check subdirectories
                    if item.is_dir():
                        for subitem in item.iterdir():
                            if subitem.is_dir():
                                subdir_name = subitem.name.lower()
                                if subdir_name in LAYER_PATTERNS:
                                    layer_type = LAYER_PATTERNS[subdir_name]
                                    if layer_type not in found_layers:
                                        layers.append(f"{dir_name}/{subdir_name}")
                                        found_layers.add(layer_type)
        except (OSError, PermissionError):
            pass
        
        return sorted(layers)
    
    def _classify_architecture_style(self, layers: List[str], entry_points: List[str]) -> Tuple[str, List[str]]:
        """
        Detect the architecture style of the project.
        
        Args:
            layers: List of detected layers
            entry_points: List of entry points
            
        Returns:
            Tuple of (architecture_style, detected_patterns)
        """
        patterns = []
        style = ArchitectureStyle.UNKNOWN.value
        
        # Check for microservices pattern
        has_microservices_indicator = False
        try:
            for item in self.repo_path.iterdir():
                if item.is_dir() and item.name.lower() in MICROSERVICES_INDICATORS:
                    has_microservices_indicator = True
                    break
        except (OSError, PermissionError):
            pass
        
        # Check for API indicators
        has_api = any(layer for layer in layers if "api" in layer.lower())
        has_controller = any(layer for layer in layers if "controller" in layer.lower())
        
        # Check for service/business logic
        has_service = any(layer for layer in layers if "service" in layer.lower() or "business" in layer.lower())
        
        # Check for data/model layer
        has_model = any(layer for layer in layers if "model" in layer.lower() or "entity" in layer.lower() or "repository" in layer.lower())
        
        # Check for UI/components
        has_ui = any(layer for layer in layers if any(ui_marker in layer.lower() for ui_marker in ["component", "view", "page", "ui"]))
        
        # Check for frontend/backend separation
        has_frontend = any(layer for layer in layers if "frontend" in layer.lower())
        has_backend = any(layer for layer in layers if "backend" in layer.lower())
        
        # Detect architecture
        if has_microservices_indicator:
            style = ArchitectureStyle.MICROSERVICES.value
            patterns.append("Microservices Pattern")
        elif has_frontend and has_backend:
            style = ArchitectureStyle.MODULAR_MONOLITH.value
            patterns.append("Frontend/Backend Separation")
        elif has_api and has_service and has_model:
            style = ArchitectureStyle.MODULAR_MVC.value
            patterns.append("Layered MVC Pattern")
            if has_controller:
                patterns.append("Controller Pattern")
        elif has_api or has_controller:
            if has_ui:
                style = ArchitectureStyle.LAYERED.value
                patterns.append("Layered Architecture")
            else:
                style = ArchitectureStyle.MONOLITH.value
                patterns.append("API Monolith")
        elif has_ui and has_service:
            style = ArchitectureStyle.MODULAR_MVC.value
            patterns.append("MVC Pattern")
        else:
            style = ArchitectureStyle.MONOLITH.value
            patterns.append("Monolithic Structure")
        
        # Check for plugin-based
        has_plugins = False
        try:
            for item in self.repo_path.iterdir():
                if item.is_dir() and item.name.lower() in {"plugin", "plugins", "addon", "addons", "extension", "extensions"}:
                    has_plugins = True
                    break
        except (OSError, PermissionError):
            pass
        
        if has_plugins:
            style = ArchitectureStyle.PLUGIN_BASED.value
            patterns.insert(0, "Plugin-Based Architecture")
        
        # Check for serverless
        serverless_files = {"serverless.yml", "serverless.yaml", "sam.yaml", "template.yaml"}
        for fname in serverless_files:
            if (self.repo_path / fname).exists():
                style = ArchitectureStyle.SERVERLESS.value
                patterns.insert(0, "Serverless Architecture")
                break
        
        return style, patterns
    
    def _calculate_modularity_score(self, layers: List[str], entry_points: List[str], patterns: List[str]) -> float:
        """
        Calculate a modularity score (0-10) based on code organization.
        
        Args:
            layers: Detected layers
            entry_points: Entry points
            patterns: Detected patterns
            
        Returns:
            Modularity score from 0 to 10
        """
        score = 5.0  # Base score
        
        # Increase score based on layer separation
        unique_layer_types = set()
        for layer in layers:
            layer_lower = layer.lower()
            for pattern, layer_type in LAYER_PATTERNS.items():
                if pattern in layer_lower:
                    unique_layer_types.add(layer_type)
                    break
        
        # More layer types = better separation
        layer_bonus = min(len(unique_layer_types) * 0.5, 2.5)
        score += layer_bonus
        
        # Bonus for specific patterns
        if "Plugin-Based Architecture" in patterns:
            score += 1.5
        elif "Microservices Pattern" in patterns:
            score += 1.5
        elif "MVC Pattern" in patterns or "Layered Architecture" in patterns:
            score += 1.0
        
        # Check for test organization
        has_tests = False
        try:
            for item in self.repo_path.rglob("test*"):
                if item.is_dir() or "test" in item.name.lower():
                    has_tests = True
                    break
        except (OSError, PermissionError):
            pass
        
        if has_tests:
            score += 0.5
        
        # Check for documentation
        has_docs = False
        try:
            for item in self.repo_path.iterdir():
                if item.is_dir() and item.name.lower() in {"docs", "doc", "documentation"}:
                    has_docs = True
                    break
        except (OSError, PermissionError):
            pass
        
        if has_docs:
            score += 0.5
        
        # Cap at 10
        return min(score, 10.0)
    
    def _identify_key_directories(self) -> List[DirectoryInfo]:
        """
        Identify key directories and their purposes.
        
        Returns:
            List of DirectoryInfo objects
        """
        key_dirs = []
        
        try:
            for item in self.repo_path.iterdir():
                if not item.is_dir() or item.name.startswith('.'):
                    continue
                
                dir_name = item.name.lower()
                
                # Determine purpose
                purpose = DIRECTORY_PURPOSES.get(dir_name, "Other")
                
                # Check if it's a layer
                is_layer = any(pattern in dir_name for pattern in LAYER_PATTERNS.keys())
                layer_type = LAYER_PATTERNS.get(dir_name) if is_layer else None
                
                # Count files and subdirs
                try:
                    file_count = sum(1 for _ in item.rglob("*") if _.is_file())
                    subdir_count = sum(1 for _ in item.iterdir() if _.is_dir())
                except (OSError, PermissionError):
                    file_count = 0
                    subdir_count = 0
                
                if file_count > 0 or subdir_count > 0:
                    key_dirs.append(DirectoryInfo(
                        path=item.name,
                        purpose=purpose,
                        file_count=file_count,
                        subdirs=subdir_count,
                        is_layer=is_layer,
                        layer_type=layer_type
                    ))
        except (OSError, PermissionError):
            pass
        
        # Sort by file count
        key_dirs.sort(key=lambda x: x.file_count, reverse=True)
        return key_dirs[:15]  # Top 15
    
    def _analyze_testing_structure(self) -> str:
        """
        Analyze the testing structure of the project.
        
        Returns:
            Testing structure level: "comprehensive", "basic", "minimal", "absent"
        """
        test_files = 0
        test_dirs = 0
        
        try:
            for item in self.repo_path.rglob("*"):
                if item.is_file():
                    name = item.name.lower()
                    if any(test_pattern in name for test_pattern in ["test_", "_test.", "spec_", ".spec.", ".test."]):
                        test_files += 1
                elif item.is_dir():
                    name = item.name.lower()
                    if any(test_pattern in name for test_pattern in ["test", "spec", "__tests__"]):
                        test_dirs += 1
        except (OSError, PermissionError):
            pass
        
        if test_files == 0 and test_dirs == 0:
            return "absent"
        elif test_files < 5 or test_dirs == 0:
            return "minimal"
        elif test_files < 20:
            return "basic"
        else:
            return "comprehensive"
    
    def analyze(self) -> StructureAnalysis:
        """
        Perform complete structure analysis.
        
        Returns:
            StructureAnalysis object
        """
        print(f"🔍 Analyzing repository structure: {self.repo_path}")
        
        # Detect components
        entry_points = self._find_entry_points()
        layers = self._identify_layers()
        architecture_style, patterns = self._classify_architecture_style(layers, entry_points)
        modularity_score = self._calculate_modularity_score(layers, entry_points, patterns)
        key_directories = self._identify_key_directories()
        testing_structure = self._analyze_testing_structure()
        
        # Count concerns
        concerns_separation = defaultdict(int)
        for dir_info in key_directories:
            if dir_info.layer_type:
                concerns_separation[dir_info.layer_type] += 1
        
        # Find microservices indicators
        microservices_indicators = []
        for dir_info in key_directories:
            if dir_info.path.lower() in MICROSERVICES_INDICATORS:
                microservices_indicators.append(dir_info.path)
        
        # Create output
        analysis = StructureAnalysis(
            entry_points=entry_points,
            architecture_style=architecture_style,
            layers=layers,
            modularity_score=round(modularity_score, 1),
            key_directories=[asdict(d) for d in key_directories],
            detected_patterns=patterns,
            concerns_separation=dict(concerns_separation),
            microservices_indicators=microservices_indicators,
            testing_structure=testing_structure,
            analysis_details={
                "total_directories": len(key_directories),
                "unique_layer_types": len(set(d.layer_type for d in key_directories if d.layer_type)),
                "has_tests": testing_structure != "absent",
            }
        )
        
        # Print summary
        print(f"✓ Analysis complete!")
        print(f"  Architecture Style: {architecture_style}")
        print(f"  Modularity Score: {modularity_score}/10")
        print(f"  Layers Found: {len(layers)}")
        print(f"  Entry Points: {len(entry_points)}")
        print(f"  Testing: {testing_structure}")
        
        return analysis


def analyze_repository(repo_path: str) -> StructureAnalysis:
    """
    Convenience function to analyze a repository structure.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        StructureAnalysis object
    """
    analyzer = StructureAnalyzer(repo_path)
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
        analysis = analyze_repository(test_repo)
        
        # Print detailed results
        print("\n" + "="*60)
        print("STRUCTURE ANALYSIS RESULTS")
        print("="*60)
        
        print(f"\n🏗️ Architecture:")
        print(f"  Style: {analysis.architecture_style}")
        print(f"  Modularity Score: {analysis.modularity_score}/10")
        
        print(f"\n📍 Entry Points:")
        for ep in analysis.entry_points:
            print(f"  {ep}")
        
        print(f"\n📚 Layers Detected:")
        for layer in analysis.layers:
            print(f"  {layer}")
        
        print(f"\n🎯 Detected Patterns:")
        for pattern in analysis.detected_patterns:
            print(f"  {pattern}")
        
        print(f"\n📁 Key Directories:")
        for dir_info in analysis.key_directories[:5]:
            print(f"  {dir_info['path']}: {dir_info['purpose']} ({dir_info['file_count']} files)")
        
        print(f"\n🧪 Testing Structure: {analysis.testing_structure}")
        
        print(f"\n💔 Concerns Separation:")
        for concern, count in analysis.concerns_separation.items():
            print(f"  {concern}: {count}")
        
        # Print as JSON
        print("\n" + "="*60)
        print("JSON OUTPUT:")
        print("="*60)
        print(json.dumps(analysis.to_dict(), indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()