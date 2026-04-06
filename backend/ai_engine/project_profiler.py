"""
Project Profiler - Analyzes repository to understand project context
Makes AI context-aware of what it's scanning
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from collections import Counter


class ProjectProfile:
    """Represents a project's profile and characteristics"""
    
    def __init__(self):
        self.project_type: str = "unknown"  # web, mobile, blockchain, ml, etc.
        self.tech_stack: List[str] = []
        self.languages: Dict[str, int] = {}  # language -> file count
        self.frameworks: List[str] = []
        self.is_test_heavy: bool = False
        self.has_examples: bool = False
        self.has_documentation: bool = False
        self.is_library: bool = False
        self.is_application: bool = True
        self.deployment_targets: List[str] = []  # cloud, on-premise, etc.
        self.data_handling: List[str] = []  # database, api, file storage
        self.security_features: List[str] = []
        self.compliance_indicators: List[str] = []
        self.project_maturity: str = "unknown"  # prototype, development, production
        self.team_size_indicator: str = "small"  # small, medium, large
        self.confidence: float = 0.0


class ProjectProfiler:
    """
    Analyzes a repository to understand project context
    Makes compliance checking project-aware
    """
    
    def __init__(self):
        self.profile = ProjectProfile()
        
        # Tech stack indicators
        self.tech_indicators = {
            # Web frameworks
            "react": ["package.json:react", "jsx", "tsx"],
            "vue": ["package.json:vue", "vue"],
            "angular": ["package.json:angular", "angular.json"],
            "django": ["manage.py", "settings.py", "requirements.txt:django"],
            "flask": ["requirements.txt:flask", "app.py"],
            "express": ["package.json:express", "app.js"],
            "spring": ["pom.xml:spring", "build.gradle:spring"],
            
            # Mobile
            "react-native": ["package.json:react-native"],
            "flutter": ["pubspec.yaml:flutter"],
            "android": ["AndroidManifest.xml", "build.gradle"],
            "ios": ["Info.plist", "Podfile"],
            
            # Blockchain
            "ethereum": ["truffle-config.js", "hardhat.config.js", "contracts/"],
            "solidity": [".sol"],
            "web3": ["package.json:web3"],
            
            # ML/AI
            "tensorflow": ["requirements.txt:tensorflow"],
            "pytorch": ["requirements.txt:torch"],
            "scikit-learn": ["requirements.txt:scikit-learn"],
            
            # Cloud
            "aws": ["serverless.yml", "cloudformation", "cdk"],
            "azure": ["azure-pipelines.yml"],
            "gcp": ["app.yaml", "cloudbuild.yaml"],
            "docker": ["Dockerfile", "docker-compose.yml"],
            "kubernetes": ["deployment.yaml", "k8s/"],
        }
        
        # Project type indicators
        self.project_type_indicators = {
            "blockchain": ["contracts/", "truffle", "hardhat", ".sol"],
            "web_app": ["src/", "public/", "index.html", "app.js"],
            "api": ["api/", "routes/", "controllers/", "endpoints/"],
            "library": ["lib/", "dist/", "package.json:main"],
            "mobile": ["android/", "ios/", "mobile/"],
            "ml": ["models/", "training/", "notebooks/", ".ipynb"],
            "devops": ["terraform/", "ansible/", "kubernetes/"],
        }
    
    def profile_repository(self, repo_path: str) -> ProjectProfile:
        """
        Analyze repository and create project profile
        
        Args:
            repo_path: Path to repository root
            
        Returns:
            ProjectProfile with detected characteristics
        """
        repo_path = Path(repo_path)
        
        if not repo_path.exists():
            return self.profile
        
        # Analyze different aspects
        self._analyze_file_structure(repo_path)
        self._analyze_languages(repo_path)
        self._analyze_tech_stack(repo_path)
        self._analyze_project_type(repo_path)
        self._analyze_maturity(repo_path)
        self._analyze_data_handling(repo_path)
        self._analyze_security_features(repo_path)
        self._analyze_compliance_indicators(repo_path)
        
        # Calculate confidence
        self.profile.confidence = self._calculate_confidence()
        
        return self.profile
    
    def _analyze_file_structure(self, repo_path: Path):
        """Analyze repository file structure"""
        
        # Check for common directories
        test_dirs = ["test", "tests", "__tests__", "spec", "specs"]
        example_dirs = ["examples", "example", "samples", "demo", "demos"]
        doc_dirs = ["docs", "documentation", "doc"]
        
        for item in repo_path.iterdir():
            if item.is_dir():
                name_lower = item.name.lower()
                
                if any(test_dir in name_lower for test_dir in test_dirs):
                    self.profile.is_test_heavy = True
                
                if any(ex_dir in name_lower for ex_dir in example_dirs):
                    self.profile.has_examples = True
                
                if any(doc_dir in name_lower for doc_dir in doc_dirs):
                    self.profile.has_documentation = True
        
        # Check for README
        readme_files = list(repo_path.glob("README*"))
        if readme_files:
            self.profile.has_documentation = True
    
    def _analyze_languages(self, repo_path: Path):
        """Detect programming languages used"""
        
        language_extensions = {
            "python": [".py"],
            "javascript": [".js", ".jsx"],
            "typescript": [".ts", ".tsx"],
            "java": [".java"],
            "go": [".go"],
            "rust": [".rs"],
            "solidity": [".sol"],
            "c++": [".cpp", ".cc", ".cxx"],
            "c": [".c"],
            "ruby": [".rb"],
            "php": [".php"],
            "swift": [".swift"],
            "kotlin": [".kt"],
        }
        
        language_counts = Counter()
        
        for ext_list in language_extensions.values():
            for ext in ext_list:
                files = list(repo_path.rglob(f"*{ext}"))
                # Exclude node_modules, venv, etc.
                files = [f for f in files if not any(
                    exclude in str(f) for exclude in 
                    ["node_modules", "venv", ".venv", "vendor", "dist", "build"]
                )]
                
                for lang, exts in language_extensions.items():
                    if ext in exts:
                        language_counts[lang] += len(files)
        
        self.profile.languages = dict(language_counts.most_common())
    
    def _analyze_tech_stack(self, repo_path: Path):
        """Detect frameworks and technologies"""
        
        detected_tech = []
        
        for tech, indicators in self.tech_indicators.items():
            for indicator in indicators:
                if ":" in indicator:
                    # File content check
                    file_name, content_pattern = indicator.split(":", 1)
                    file_path = repo_path / file_name
                    
                    if file_path.exists():
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if content_pattern.lower() in content.lower():
                                    detected_tech.append(tech)
                                    break
                        except Exception:
                            pass
                else:
                    # File/directory existence check
                    if indicator.endswith("/"):
                        # Directory
                        if (repo_path / indicator.rstrip("/")).exists():
                            detected_tech.append(tech)
                            break
                    else:
                        # File or extension
                        if indicator.startswith("."):
                            # Extension
                            if list(repo_path.rglob(f"*{indicator}")):
                                detected_tech.append(tech)
                                break
                        else:
                            # Specific file
                            if (repo_path / indicator).exists():
                                detected_tech.append(tech)
                                break
        
        self.profile.tech_stack = detected_tech
        self.profile.frameworks = [t for t in detected_tech if t in [
            "react", "vue", "angular", "django", "flask", "express", "spring"
        ]]
    
    def _analyze_project_type(self, repo_path: Path):
        """Determine project type"""
        
        type_scores = Counter()
        
        for proj_type, indicators in self.project_type_indicators.items():
            for indicator in indicators:
                if indicator.endswith("/"):
                    if (repo_path / indicator.rstrip("/")).exists():
                        type_scores[proj_type] += 1
                elif indicator.startswith("."):
                    if list(repo_path.rglob(f"*{indicator}")):
                        type_scores[proj_type] += 1
                else:
                    if (repo_path / indicator).exists():
                        type_scores[proj_type] += 1
        
        if type_scores:
            self.profile.project_type = type_scores.most_common(1)[0][0]
        
        # Check if it's a library
        package_json = repo_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    if "main" in data and "bin" not in data:
                        self.profile.is_library = True
                        self.profile.is_application = False
            except Exception:
                pass
    
    def _analyze_maturity(self, repo_path: Path):
        """Assess project maturity"""
        
        maturity_score = 0
        
        # Check for CI/CD
        ci_files = [".github/workflows", ".gitlab-ci.yml", "Jenkinsfile", ".travis.yml"]
        if any((repo_path / f).exists() for f in ci_files):
            maturity_score += 2
        
        # Check for tests
        if self.profile.is_test_heavy:
            maturity_score += 2
        
        # Check for documentation
        if self.profile.has_documentation:
            maturity_score += 1
        
        # Check for Docker
        if (repo_path / "Dockerfile").exists():
            maturity_score += 1
        
        # Check for environment configs
        env_files = [".env.example", ".env.sample", "config/"]
        if any((repo_path / f).exists() for f in env_files):
            maturity_score += 1
        
        # Check for package management
        pkg_files = ["package.json", "requirements.txt", "Gemfile", "go.mod", "Cargo.toml"]
        if any((repo_path / f).exists() for f in pkg_files):
            maturity_score += 1
        
        # Determine maturity level
        if maturity_score >= 6:
            self.profile.project_maturity = "production"
        elif maturity_score >= 3:
            self.profile.project_maturity = "development"
        else:
            self.profile.project_maturity = "prototype"
    
    def _analyze_data_handling(self, repo_path: Path):
        """Detect data handling patterns"""
        
        data_patterns = []
        
        # Database
        db_indicators = ["models/", "migrations/", "schema/", "database/"]
        if any((repo_path / ind.rstrip("/")).exists() for ind in db_indicators):
            data_patterns.append("database")
        
        # API
        api_indicators = ["api/", "routes/", "controllers/", "endpoints/"]
        if any((repo_path / ind.rstrip("/")).exists() for ind in api_indicators):
            data_patterns.append("api")
        
        # File storage
        storage_indicators = ["uploads/", "storage/", "media/", "files/"]
        if any((repo_path / ind.rstrip("/")).exists() for ind in storage_indicators):
            data_patterns.append("file_storage")
        
        # Cache
        if any(tech in self.profile.tech_stack for tech in ["redis", "memcached"]):
            data_patterns.append("cache")
        
        self.profile.data_handling = data_patterns
    
    def _analyze_security_features(self, repo_path: Path):
        """Detect existing security features"""
        
        security_features = []
        
        # Authentication
        auth_indicators = ["auth/", "authentication/", "login/", "oauth/"]
        if any((repo_path / ind.rstrip("/")).exists() for ind in auth_indicators):
            security_features.append("authentication")
        
        # Encryption
        crypto_files = list(repo_path.rglob("*crypto*")) + list(repo_path.rglob("*encrypt*"))
        if crypto_files:
            security_features.append("encryption")
        
        # Security headers
        if "express" in self.profile.tech_stack:
            # Check for helmet or similar
            package_json = repo_path / "package.json"
            if package_json.exists():
                try:
                    with open(package_json, 'r') as f:
                        content = f.read()
                        if "helmet" in content or "cors" in content:
                            security_features.append("security_headers")
                except Exception:
                    pass
        
        self.profile.security_features = security_features
    
    def _analyze_compliance_indicators(self, repo_path: Path):
        """Detect compliance-related indicators"""
        
        compliance_indicators = []
        
        # Privacy policy
        privacy_files = list(repo_path.rglob("*privacy*"))
        if privacy_files:
            compliance_indicators.append("privacy_policy")
        
        # Terms of service
        tos_files = list(repo_path.rglob("*terms*"))
        if tos_files:
            compliance_indicators.append("terms_of_service")
        
        # GDPR
        gdpr_files = list(repo_path.rglob("*gdpr*"))
        if gdpr_files:
            compliance_indicators.append("gdpr")
        
        # Security policy
        security_files = list(repo_path.rglob("SECURITY.md"))
        if security_files:
            compliance_indicators.append("security_policy")
        
        self.profile.compliance_indicators = compliance_indicators
    
    def _calculate_confidence(self) -> float:
        """Calculate confidence in profile accuracy"""
        
        confidence = 0.0
        
        # Language detection confidence
        if self.profile.languages:
            confidence += 0.2
        
        # Tech stack detection confidence
        if self.profile.tech_stack:
            confidence += 0.2
        
        # Project type confidence
        if self.profile.project_type != "unknown":
            confidence += 0.2
        
        # Maturity confidence
        if self.profile.project_maturity != "unknown":
            confidence += 0.2
        
        # Data handling confidence
        if self.profile.data_handling:
            confidence += 0.1
        
        # Security features confidence
        if self.profile.security_features:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get human-readable summary of project context"""
        
        return {
            "project_type": self.profile.project_type,
            "primary_language": list(self.profile.languages.keys())[0] if self.profile.languages else "unknown",
            "tech_stack": self.profile.tech_stack,
            "maturity": self.profile.project_maturity,
            "is_library": self.profile.is_library,
            "has_tests": self.profile.is_test_heavy,
            "has_docs": self.profile.has_documentation,
            "data_handling": self.profile.data_handling,
            "security_features": self.profile.security_features,
            "compliance_indicators": self.profile.compliance_indicators,
            "confidence": self.profile.confidence
        }
    
    def should_apply_strict_checking(self) -> bool:
        """Determine if strict compliance checking should be applied"""
        
        # Apply strict checking for production-ready projects
        if self.profile.project_maturity == "production":
            return True
        
        # Apply strict checking for projects handling sensitive data
        if "database" in self.profile.data_handling or "api" in self.profile.data_handling:
            return True
        
        # Relax for prototypes and examples
        if self.profile.project_maturity == "prototype" or self.profile.has_examples:
            return False
        
        return True
    
    def get_relevant_compliance_frameworks(self) -> List[str]:
        """Get relevant compliance frameworks based on project profile"""
        
        frameworks = []
        
        # Indian compliance for Indian projects
        if "india" in str(self.profile).lower():
            frameworks.extend(["DPDP", "RBI", "CERT-In"])
        
        # GDPR for EU projects
        if "gdpr" in self.profile.compliance_indicators:
            frameworks.append("GDPR")
        
        # PCI-DSS for payment processing
        if "payment" in str(self.profile).lower() or "stripe" in self.profile.tech_stack:
            frameworks.append("PCI-DSS")
        
        # HIPAA for healthcare
        if "health" in str(self.profile).lower() or "medical" in str(self.profile).lower():
            frameworks.append("HIPAA")
        
        # SOC 2 for SaaS
        if self.profile.project_type == "web_app" and self.profile.project_maturity == "production":
            frameworks.append("SOC2")
        
        return frameworks
