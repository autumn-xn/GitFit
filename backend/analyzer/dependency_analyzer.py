"""
GitFit v2: Dependency Analyzer Module
Location: backend/analyzer/dependency_analyzer.py

Responsible for parsing dependency files, building dependency graphs,
and checking for known vulnerabilities.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass, asdict
from packaging import version as pkg_version


# Known security vulnerabilities database
# Format: (package, affected_version_range, vulnerability, severity, fix_version)
KNOWN_VULNERABILITIES = [
    # Python
    ("lodash", "4.17.20", "Prototype Pollution", "high", "4.17.21"),
    ("lodash", "<4.7.11", "Lodash Prototype Pollution", "high", "4.7.11"),
    ("requests", "<2.20.0", "Information Disclosure", "medium", "2.20.0"),
    ("django", "<1.11.27", "SQL Injection", "high", "1.11.27"),
    ("django", "<2.0.10", "SQL Injection", "high", "2.0.10"),
    ("pillow", "<5.4.0", "Image Processing Vulnerability", "medium", "5.4.0"),
    ("pyyaml", "<5.4", "Code Execution", "critical", "5.4"),
    ("jinja2", "<2.11.3", "Code Injection", "medium", "2.11.3"),
    ("werkzeug", "<0.15.3", "Directory Traversal", "medium", "0.15.3"),
    ("flask", "<1.1.2", "Open Redirect", "medium", "1.1.2"),
    
    # JavaScript/Node.js
    ("lodash", "<4.7.11", "Lodash Prototype Pollution", "high", "4.7.11"),
    ("moment", "<2.24.0", "Regular Expression DoS", "medium", "2.24.0"),
    ("handlebars", "<4.5.3", "Code Injection", "high", "4.5.3"),
    ("underscore", "<1.13.0", "Prototype Pollution", "high", "1.13.0"),
    ("serialize-javascript", "<2.1.1", "Code Execution", "high", "2.1.1"),
    ("jquery", "<3.5.0", "XSS Vulnerability", "medium", "3.5.0"),
    ("express", "<4.16.3", "Open Redirect", "low", "4.16.3"),
    ("helmet", "<3.12.1", "Information Disclosure", "low", "3.12.1"),
    ("body-parser", "<1.19.0", "Denial of Service", "high", "1.19.0"),
    ("axios", "<0.21.2", "SSRF", "medium", "0.21.2"),
    
    # Go
    ("golang.org/x/crypto", "<0.0.0-20191206172530-e9b2fee46413", "Denial of Service", "high", "latest"),
    ("gopkg.in/yaml.v2", "<2.2.8", "Code Execution", "critical", "2.2.8"),
    
    # Ruby
    ("rails", "<4.2.10", "SQL Injection", "high", "4.2.10"),
    ("rails", "<5.0.7", "SQL Injection", "high", "5.0.7"),
    ("rails", "<5.1.6", "SQL Injection", "high", "5.1.6"),
    ("nokogiri", "<1.10.4", "XXE Injection", "high", "1.10.4"),
    ("devise", "<4.6.2", "Authentication Bypass", "high", "4.6.2"),
    
    # Java
    ("log4j", "<2.17.0", "Code Execution (Log4Shell)", "critical", "2.17.0"),
    ("struts2", "<2.5.25", "RCE", "critical", "2.5.25"),
    ("jackson-databind", "<2.9.8", "Code Execution", "high", "2.9.8"),
    ("commons-collections", "<3.2.2", "Code Execution", "high", "3.2.2"),
    
    # General
    ("openssl", "<1.1.1j", "Certificate Verification Bypass", "high", "1.1.1j"),
]

# Dependency file patterns
DEPENDENCY_FILES = {
    "package.json": "npm",
    "package-lock.json": "npm",
    "yarn.lock": "yarn",
    "requirements.txt": "pip",
    "Pipfile": "pipenv",
    "Pipfile.lock": "pipenv",
    "setup.py": "pip",
    "setup.cfg": "pip",
    "pyproject.toml": "poetry",
    "poetry.lock": "poetry",
    "go.mod": "go",
    "go.sum": "go",
    "pom.xml": "maven",
    "build.gradle": "gradle",
    "Gemfile": "bundler",
    "Gemfile.lock": "bundler",
    "Cargo.toml": "cargo",
    "Cargo.lock": "cargo",
    "composer.json": "composer",
    "composer.lock": "composer",
    "pubspec.yaml": "pub",
    "mix.exs": "mix",
}


@dataclass
class Dependency:
    """Represents a single dependency"""
    name: str
    version: str
    ecosystem: str
    is_dev: bool = False
    is_indirect: bool = False


@dataclass
class SecurityIssue:
    """Represents a security vulnerability"""
    package: str
    version: str
    vulnerability: str
    severity: str  # critical, high, medium, low
    fix_version: str
    cve_id: Optional[str] = None
    affected_range: Optional[str] = None


@dataclass
class DependencyInfo:
    """Complete dependency analysis"""
    total_dependencies: int
    direct_dependencies: int
    dev_dependencies: int
    vulnerable_count: int
    outdated_count: int
    ecosystems: Dict[str, int]  # Ecosystem -> count
    graph: Dict[str, List[str]]  # Package -> [dependencies]
    security_issues: List[Dict]
    dependency_files_found: List[str]
    license_types: Dict[str, int]  # License -> count
    largest_dependencies: List[Dict]  # By dependency count
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class DependencyAnalyzer:
    """
    Analyzes project dependencies, builds dependency graphs,
    and detects security vulnerabilities.
    
    Attributes:
        repo_path (str): Root path of the repository
        dependencies (List[Dependency]): List of found dependencies
        security_issues (List[SecurityIssue]): List of detected vulnerabilities
    """
    
    def __init__(self, repo_path: str):
        """
        Initialize the dependency analyzer.
        
        Args:
            repo_path: Path to the repository root
        """
        self.repo_path = Path(repo_path)
        
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        self.dependencies: List[Dependency] = []
        self.security_issues: List[SecurityIssue] = []
        self.dependency_files_found: List[str] = []
        
        print(f"✓ Initialized DependencyAnalyzer for: {repo_path}")
    
    def _parse_package_json(self, filepath: Path) -> List[Dependency]:
        """Parse package.json (npm/yarn)"""
        deps = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Regular dependencies
            if "dependencies" in data:
                for name, version in data["dependencies"].items():
                    deps.append(Dependency(name, version, "npm", is_dev=False))
            
            # Dev dependencies
            if "devDependencies" in data:
                for name, version in data["devDependencies"].items():
                    deps.append(Dependency(name, version, "npm", is_dev=True))
            
            # Optional dependencies
            if "optionalDependencies" in data:
                for name, version in data["optionalDependencies"].items():
                    deps.append(Dependency(name, version, "npm", is_dev=False))
            
            print(f"✓ Parsed package.json: {len(deps)} dependencies")
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠ Error parsing package.json: {e}")
        
        return deps
    
    def _parse_requirements_txt(self, filepath: Path) -> List[Dependency]:
        """Parse requirements.txt (pip)"""
        deps = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse requirement format: package==version
                match = re.match(r'^([a-zA-Z0-9_-]+)\s*([><=!~]+)\s*(.+)$', line)
                if match:
                    name, op, version = match.groups()
                    deps.append(Dependency(name.strip(), version.strip(), "pip", is_dev=False))
            
            print(f"✓ Parsed requirements.txt: {len(deps)} dependencies")
        except IOError as e:
            print(f"⚠ Error parsing requirements.txt: {e}")
        
        return deps
    
    def _parse_go_mod(self, filepath: Path) -> List[Dependency]:
        """Parse go.mod"""
        deps = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            in_require = False
            for line in lines:
                line = line.strip()
                
                if line.startswith("require"):
                    in_require = True
                    continue
                
                if line.startswith(")"):
                    in_require = False
                    continue
                
                if in_require and line:
                    # Parse: github.com/package v1.2.3
                    parts = line.split()
                    if len(parts) >= 2:
                        name = parts[0]
                        version = parts[1] if len(parts) > 1 else "unknown"
                        deps.append(Dependency(name, version, "go", is_dev=False))
            
            print(f"✓ Parsed go.mod: {len(deps)} dependencies")
        except IOError as e:
            print(f"⚠ Error parsing go.mod: {e}")
        
        return deps
    
    def _parse_gemfile(self, filepath: Path) -> List[Dependency]:
        """Parse Gemfile (Ruby)"""
        deps = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse: gem 'name', '~> 1.0'
                match = re.match(r"gem\s+['\"]([^'\"]+)['\"]\s*(?:,\s*['\"]([^'\"]+)['\"])?", line)
                if match:
                    name = match.group(1)
                    version = match.group(2) or "unknown"
                    is_dev = "development" in line or "test" in line
                    deps.append(Dependency(name, version, "bundler", is_dev=is_dev))
            
            print(f"✓ Parsed Gemfile: {len(deps)} dependencies")
        except IOError as e:
            print(f"⚠ Error parsing Gemfile: {e}")
        
        return deps
    
    def _parse_cargo_toml(self, filepath: Path) -> List[Dependency]:
        """Parse Cargo.toml (Rust)"""
        deps = []
        try:
            import tomllib if hasattr(__import__('sys'), 'version_info') and __import__('sys').version_info >= (3, 11) else None
            
            # Fallback TOML parsing for older Python versions
            if tomllib is None:
                # Simple regex-based parsing for basic cases
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse dependencies section
                deps_match = re.search(r'\[dependencies\](.*?)(?:\[|$)', content, re.DOTALL)
                if deps_match:
                    deps_section = deps_match.group(1)
                    for match in re.finditer(r'(\w+)\s*=\s*["\{]([^"\}]+)', deps_section):
                        name, version = match.groups()
                        deps.append(Dependency(name, version, "cargo", is_dev=False))
            else:
                with open(filepath, 'rb') as f:
                    data = tomllib.load(f)
                
                if "dependencies" in data:
                    for name, spec in data["dependencies"].items():
                        version = spec if isinstance(spec, str) else spec.get("version", "unknown")
                        deps.append(Dependency(name, version, "cargo", is_dev=False))
            
            print(f"✓ Parsed Cargo.toml: {len(deps)} dependencies")
        except Exception as e:
            print(f"⚠ Error parsing Cargo.toml: {e}")
        
        return deps
    
    def _parse_pom_xml(self, filepath: Path) -> List[Dependency]:
        """Parse pom.xml (Maven)"""
        deps = []
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # Define namespace
            namespace = {'pom': 'http://maven.apache.org/POM/4.0.0'}
            
            # Find all dependency elements
            for dep in root.findall('.//pom:dependency', namespace):
                artifact_id_elem = dep.find('pom:artifactId', namespace)
                version_elem = dep.find('pom:version', namespace)
                scope_elem = dep.find('pom:scope', namespace)
                
                if artifact_id_elem is not None:
                    name = artifact_id_elem.text
                    version = version_elem.text if version_elem is not None else "unknown"
                    scope = scope_elem.text if scope_elem is not None else "compile"
                    is_dev = scope in ["test", "provided"]
                    
                    deps.append(Dependency(name, version, "maven", is_dev=is_dev))
            
            print(f"✓ Parsed pom.xml: {len(deps)} dependencies")
        except Exception as e:
            print(f"⚠ Error parsing pom.xml: {e}")
        
        return deps
    
    def _check_vulnerabilities(self, dependency: Dependency) -> List[SecurityIssue]:
        """
        Check if a dependency has known vulnerabilities.
        
        Args:
            dependency: The dependency to check
            
        Returns:
            List of SecurityIssue objects if vulnerabilities found
        """
        issues = []
        
        for vuln_package, affected_version, vuln_name, severity, fix_version in KNOWN_VULNERABILITIES:
            # Case-insensitive package name comparison
            if dependency.name.lower() == vuln_package.lower():
                # Check if current version is affected
                try:
                    # Clean version string
                    current_version = re.sub(r'^[=~^><v]+', '', dependency.version).split()[0]
                    
                    # Simple version comparison
                    if current_version == affected_version or \
                       (self._version_is_affected(current_version, affected_version)):
                        issues.append(SecurityIssue(
                            package=dependency.name,
                            version=dependency.version,
                            vulnerability=vuln_name,
                            severity=severity,
                            fix_version=fix_version
                        ))
                except Exception:
                    # If version parsing fails, skip
                    pass
        
        return issues
    
    @staticmethod
    def _version_is_affected(current: str, affected: str) -> bool:
        """
        Check if current version matches affected version pattern.
        Handles version ranges like <2.0.0, >=1.0 etc.
        """
        try:
            # Try to parse as versions
            current_v = pkg_version.parse(current)
            affected_v = pkg_version.parse(affected)
            
            # Simple check: if current is less than or equal to affected
            return current_v <= affected_v
        except Exception:
            # Fallback to string comparison
            return current <= affected
    
    def _find_dependency_files(self) -> List[str]:
        """Find all dependency files in the repository"""
        found_files = []
        
        try:
            for root, dirs, files in os.walk(self.repo_path):
                # Skip certain directories
                dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__', '.venv'}]
                
                for filename in files:
                    if filename in DEPENDENCY_FILES:
                        filepath = Path(root) / filename
                        relative_path = str(filepath.relative_to(self.repo_path))
                        found_files.append(relative_path)
        except (OSError, PermissionError):
            pass
        
        return found_files
    
    def analyze(self) -> DependencyInfo:
        """
        Perform complete dependency analysis.
        
        Returns:
            DependencyInfo object
        """
        print(f"🔍 Analyzing dependencies: {self.repo_path}")
        
        # Find and parse dependency files
        dep_files = self._find_dependency_files()
        self.dependency_files_found = dep_files
        print(f"✓ Found {len(dep_files)} dependency files")
        
        # Parse each dependency file
        for dep_file in dep_files:
            filepath = self.repo_path / dep_file
            filename = filepath.name
            
            if filename == "package.json":
                self.dependencies.extend(self._parse_package_json(filepath))
            elif filename == "requirements.txt":
                self.dependencies.extend(self._parse_requirements_txt(filepath))
            elif filename == "go.mod":
                self.dependencies.extend(self._parse_go_mod(filepath))
            elif filename == "Gemfile":
                self.dependencies.extend(self._parse_gemfile(filepath))
            elif filename == "Cargo.toml":
                self.dependencies.extend(self._parse_cargo_toml(filepath))
            elif filename == "pom.xml":
                self.dependencies.extend(self._parse_pom_xml(filepath))
        
        # Remove duplicates
        seen = set()
        unique_deps = []
        for dep in self.dependencies:
            key = (dep.name.lower(), dep.version)
            if key not in seen:
                seen.add(key)
                unique_deps.append(dep)
        self.dependencies = unique_deps
        
        print(f"✓ Found {len(self.dependencies)} unique dependencies")
        
        # Check for vulnerabilities
        for dep in self.dependencies:
            issues = self._check_vulnerabilities(dep)
            self.security_issues.extend(issues)
        
        print(f"✓ Detected {len(self.security_issues)} security issues")
        
        # Build dependency graph (simplified)
        graph = self._build_dependency_graph()
        
        # Count by ecosystem
        ecosystems = defaultdict(int)
        for dep in self.dependencies:
            ecosystems[dep.ecosystem] += 1
        
        # Calculate statistics
        direct_deps = sum(1 for d in self.dependencies if not d.is_indirect)
        dev_deps = sum(1 for d in self.dependencies if d.is_dev)
        
        # Find largest dependencies
        graph_with_counts = {k: len(v) for k, v in graph.items()}
        largest = sorted(graph_with_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        largest_deps = [{"name": name, "dependency_count": count} for name, count in largest]
        
        # Create output
        info = DependencyInfo(
            total_dependencies=len(self.dependencies),
            direct_dependencies=direct_deps,
            dev_dependencies=dev_deps,
            vulnerable_count=len(self.security_issues),
            outdated_count=0,  # Would require version API calls
            ecosystems=dict(ecosystems),
            graph=graph,
            security_issues=[asdict(issue) for issue in self.security_issues],
            dependency_files_found=dep_files,
            license_types={},  # Would require additional analysis
            largest_dependencies=largest_deps
        )
        
        # Print summary
        print(f"✓ Analysis complete!")
        print(f"  Total Dependencies: {info.total_dependencies}")
        print(f"  Ecosystems: {len(info.ecosystems)}")
        print(f"  Security Issues: {info.vulnerable_count}")
        
        return info
    
    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """
        Build simplified dependency graph.
        In a real scenario, this would parse actual dependency trees.
        
        Returns:
            Dictionary mapping package -> [dependencies]
        """
        graph = defaultdict(list)
        
        # For this implementation, we create a simple graph
        # In production, this would parse lock files for actual relationships
        for dep in self.dependencies:
            if dep.name not in graph:
                graph[dep.name] = []
        
        return dict(graph)


def analyze_dependencies(repo_path: str) -> DependencyInfo:
    """
    Convenience function to analyze repository dependencies.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        DependencyInfo object
    """
    analyzer = DependencyAnalyzer(repo_path)
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
        info = analyze_dependencies(test_repo)
        
        # Print detailed results
        print("\n" + "="*60)
        print("DEPENDENCY ANALYSIS RESULTS")
        print("="*60)
        
        print(f"\n📊 Statistics:")
        print(f"  Total Dependencies: {info.total_dependencies}")
        print(f"  Direct Dependencies: {info.direct_dependencies}")
        print(f"  Dev Dependencies: {info.dev_dependencies}")
        print(f"  Security Issues: {info.vulnerable_count}")
        
        print(f"\n🌍 Ecosystems:")
        for ecosystem, count in info.ecosystems.items():
            print(f"  {ecosystem}: {count}")
        
        print(f"\n📁 Dependency Files Found:")
        for dep_file in info.dependency_files_found:
            print(f"  {dep_file}")
        
        if info.security_issues:
            print(f"\n⚠️ Security Issues:")
            for issue in info.security_issues[:10]:
                print(f"  {issue['package']} ({issue['version']})")
                print(f"    Issue: {issue['vulnerability']} [Severity: {issue['severity']}]")
                print(f"    Fix: Update to {issue['fix_version']}")
        
        print(f"\n📈 Largest Dependencies:")
        for dep in info.largest_dependencies[:5]:
            print(f"  {dep['name']}: {dep['dependency_count']} deps")
        
        # Print as JSON
        print("\n" + "="*60)
        print("JSON OUTPUT:")
        print("="*60)
        print(json.dumps(info.to_dict(), indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()