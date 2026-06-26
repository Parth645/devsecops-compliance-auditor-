"""
Gap Analysis Module - Layer 3
Detects missing compliance features using AI profiling
Updated to use GroqRepoProfiler instead of keyword-based analysis
"""

import logging
from typing import Dict, List, Any
from pathlib import Path
from groq import Groq
from .groq_repo_profiler import GroqRepoProfiler

logger = logging.getLogger(__name__)


class GapAnalyzer:
    """
    AI-Driven Gap Analysis (Layer 3)
    Uses GroqRepoProfiler for intelligent feature detection
    Identifies structural gaps in compliance requirements
    """
    
    def __init__(self, api_key: str):
        """Initialize gap analyzer with AI profiler"""
        self.client = Groq(api_key=api_key)
        self.models = ["llama-3.1-8b-instant", "mixtral-8x7b-32768", "llama-3.3-70b-versatile"]
        self.model = self.models[0]  # Start with cheapest
        self.repo_profiler = GroqRepoProfiler(api_key)
    
    async def analyze_gaps(self, repo_path: str, all_files: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze repository for missing compliance features
        Uses AI profiling instead of keyword matching
        
        Returns:
            List of gap findings (absence of required features)
        """
        logger.info("[LAYER 3: GAP ANALYSIS] Analyzing for missing compliance features...")
        
        # Use AI profiler to understand repository
        repo_profile = await self.repo_profiler.profile_repository(repo_path, all_files)
        
        # Analyze gaps based on profile
        gaps = await self._analyze_gaps_from_profile(repo_profile)
        
        logger.info(f"  ✓ Found {len(gaps)} compliance gaps")
        
        return gaps
    
    def _build_repo_profile(self, repo_path: str, all_files: List[str]) -> Dict[str, Any]:
        """Build high-level repository profile"""
        logger.info(f"  Building repository profile from {len(all_files)} files...")
        
        file_patterns = {
            "auth_files": [],
            "data_files": [],
            "api_files": [],
            "config_files": [],
            "test_files": [],
            "other": []
        }
        
        endpoint_patterns = []
        tech_stack = set()
        
        for file_path in all_files[:50]:  # Analyze first 50 files
            file_name = Path(file_path).name.lower()
            ext = Path(file_path).suffix
            
            # Categorize files
            if any(x in file_name for x in ["auth", "login", "user"]):
                file_patterns["auth_files"].append(file_name)
            elif any(x in file_name for x in ["data", "db", "model", "schema"]):
                file_patterns["data_files"].append(file_name)
            elif any(x in file_name for x in ["route", "controller", "handler", "api"]):
                file_patterns["api_files"].append(file_name)
            elif any(x in file_name for x in ["config", "env", "settings"]):
                file_patterns["config_files"].append(file_name)
            elif "test" in file_name or "spec" in file_name:
                file_patterns["test_files"].append(file_name)
            else:
                file_patterns["other"].append(file_name)
            
            # Detect tech stack
            if ext == ".js" or ext == ".jsx":
                tech_stack.add("JavaScript/Node.js")
            elif ext == ".ts" or ext == ".tsx":
                tech_stack.add("TypeScript")
            elif ext == ".py":
                tech_stack.add("Python")
            elif ext == ".java":
                tech_stack.add("Java")
        
        # Scan for keywords
        file_contents = self._scan_file_keywords(all_files[:30])
        
        profile = {
            "total_files": len(all_files),
            "tech_stack": list(tech_stack),
            "file_patterns": file_patterns,
            "keywords_found": file_contents,
            "endpoints": endpoint_patterns
        }
    
    def _build_repo_profile(self, repo_path: str, all_files: List[str]) -> Dict[str, Any]:
        """Build high-level repository profile"""
        logger.info(f"  Building repository profile from {len(all_files)} files...")
        
        file_patterns = {
            "auth_files": [],
            "data_files": [],
            "api_files": [],
            "config_files": [],
            "test_files": [],
            "other": []
        }
        
        endpoint_patterns = []
        tech_stack = set()
        
        for file_path in all_files[:50]:  # Analyze first 50 files
            file_name = Path(file_path).name.lower()
            ext = Path(file_path).suffix
            
            # Categorize files
            if any(x in file_name for x in ["auth", "login", "user"]):
                file_patterns["auth_files"].append(file_name)
            elif any(x in file_name for x in ["data", "db", "model", "schema"]):
                file_patterns["data_files"].append(file_name)
            elif any(x in file_name for x in ["route", "controller", "handler", "api"]):
                file_patterns["api_files"].append(file_name)
            elif any(x in file_name for x in ["config", "env", "settings"]):
                file_patterns["config_files"].append(file_name)
            elif "test" in file_name or "spec" in file_name:
                file_patterns["test_files"].append(file_name)
            else:
                file_patterns["other"].append(file_name)
            
            # Detect tech stack
            if ext == ".js" or ext == ".jsx":
                tech_stack.add("JavaScript/Node.js")
            elif ext == ".ts" or ext == ".tsx":
                tech_stack.add("TypeScript")
            elif ext == ".py":
                tech_stack.add("Python")
            elif ext == ".java":
                tech_stack.add("Java")
        
        # Scan for keywords
        file_contents = self._scan_file_keywords(all_files[:30])
        
        profile = {
            "total_files": len(all_files),
            "tech_stack": list(tech_stack),
            "file_patterns": file_patterns,
            "keywords_found": file_contents,
            "endpoints": endpoint_patterns
        }
        
        return profile
    
    def _scan_file_keywords(self, files: List[str]) -> Dict[str, List[str]]:
        """Scan files for compliance-related keywords"""
        keywords_found = {
            "authentication": [],
            "authorization": [],
            "encryption": [],
            "logging": [],
            "consent": [],
            "data_retention": [],
            "breach_notification": [],
            "user_rights": [],
            "security_headers": [],
            "rate_limiting": [],
            "input_validation": []
        }
        
        keyword_patterns = {
            "authentication": ["auth", "login", "password", "jwt", "oauth", "session"],
            "authorization": ["role", "permission", "access", "privilege"],
            "encryption": ["encrypt", "hash", "bcrypt", "aes", "rsa"],
            "logging": ["log", "audit", "logger", "trace"],
            "consent": ["consent", "permission", "agree", "accept"],
            "data_retention": ["retention", "ttl", "expiration", "delete", "purge"],
            "breach_notification": ["breach", "incident", "alert", "notify"],
            "user_rights": ["download", "export", "access", "erasure"],
            "security_headers": ["helmet", "hsts", "csp", "x-frame"],
            "rate_limiting": ["ratelimit", "throttle", "limit"],
            "input_validation": ["validate", "sanitize", "shield"]
        }
        
        try:
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()[:5000]  # First 5KB
                        
                        for category, patterns in keyword_patterns.items():
                            for pattern in patterns:
                                if pattern in content:
                                    keywords_found[category].append(Path(file_path).name)
                                    break
                except:
                    pass
        except Exception as e:
            logger.debug(f"Keyword scan error: {e}")
        
        return keywords_found
    
    async def _analyze_gaps_from_profile(self, repo_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze compliance gaps based on AI profile"""
        
        # Skip if profile has error
        if repo_profile.get("error"):
            logger.warning(f"  ⚠ Repo profiler error: {repo_profile.get('error')}")
            return []
        
        # Get compliance features from profile
        compliance_features = repo_profile.get("compliance_features", {})
        critical_gaps = repo_profile.get("critical_gaps", [])
        
        gaps = []
        gap_mapping = {
            "User Consent Mechanism": {
                "framework": "DPDPA",
                "severity": "critical",
                "impact": "Violates DPDPA Section 7 consent requirements",
                "remediation": "Implement consent banner + audit trail for data processing",
                "estimated_effort": "3-5 days"
            },
            "Breach Notification System": {
                "framework": "DPDPA",
                "severity": "critical",
                "impact": "Violates DPDPA Section 8 (72-hour notification requirement)",
                "remediation": "Implement automatic breach detection and notification system",
                "estimated_effort": "5-7 days"
            },
            "Data Retention/Deletion": {
                "framework": "DPDPA",
                "severity": "high",
                "impact": "Violates DPDPA data minimization principle",
                "remediation": "Implement TTL indexes and automated data purging",
                "estimated_effort": "2-3 days"
            },
            "Security Headers": {
                "framework": "RBI",
                "severity": "high",
                "impact": "Violates RBI security requirements",
                "remediation": "Implement CSP, HSTS, X-Frame-Options, X-Content-Type-Options",
                "estimated_effort": "1-2 days"
            },
            "Input Validation": {
                "framework": "IT Act",
                "severity": "high",
                "impact": "Violates IT Act XSS/injection protection requirements",
                "remediation": "Implement comprehensive input validation and sanitization",
                "estimated_effort": "2-3 days"
            },
            "Rate Limiting": {
                "framework": "RBI",
                "severity": "high",
                "impact": "Violates RBI brute-force attack protection",
                "remediation": "Implement API rate limiting (100-1000 req/min based on endpoint)",
                "estimated_effort": "1-2 days"
            },
            "TLS/HTTPS": {
                "framework": "RBI",
                "severity": "medium",
                "impact": "Violates RBI encrypted transmission requirements",
                "remediation": "Force TLS 1.2+ and implement HSTS",
                "estimated_effort": "1-2 days"
            },
            "Privacy Policy": {
                "framework": "IT Act SPDI",
                "severity": "medium",
                "impact": "Violates IT Act SPDI requirements for published policy",
                "remediation": "Create and publish clear privacy policy",
                "estimated_effort": "1 day"
            }
        }
        
        gap_id = 1
        detected_gaps = set()
        
        # Check which features are missing from profile
        for feature, present in compliance_features.items():
            if not present.get("present", True):
                feature_name = feature.replace("_", " ").title()
                if feature_name not in detected_gaps:
                    detected_gaps.add(feature_name)
        
        # Add explicitly detected gaps from AI analysis
        for gap_text in critical_gaps:
            detected_gaps.add(gap_text)
        
        # Create gap findings
        for gap_name in detected_gaps:
            gap_config = gap_mapping.get(gap_name, {
                "framework": "General",
                "severity": "medium",
                "impact": f"Missing compliance feature: {gap_name}",
                "remediation": f"Implement {gap_name}",
                "estimated_effort": "2-3 days"
            })
            
            gap = {
                "gap_id": f"gap_{gap_id:03d}",
                "feature": gap_name,
                "framework": gap_config.get("framework", "General"),
                "severity": gap_config.get("severity", "medium"),
                "issue": f"No evidence of {gap_name.lower()} implementation",
                "impact": gap_config.get("impact", f"Missing {gap_name}"),
                "remediation": gap_config.get("remediation", f"Implement {gap_name}"),
                "estimated_effort": gap_config.get("estimated_effort", "2-3 days"),
                "type": "missing_feature",
                "detector": "ai_gap_analyzer",
                "evidence": {
                    "method": "ai_profile_analysis",
                    "profile_data": {
                        "application": repo_profile.get("application_purpose", "unknown"),
                        "tech_stack": repo_profile.get("tech_stack", "unknown"),
                        "framework": repo_profile.get("framework", "unknown")
                    }
                },
                "evidence_chain": {
                    "detector": "ai_gap_analyzer",
                    "rule_id": f"gap_{gap_id:03d}",
                    "file_path": "",
                    "line_number": 0,
                    "confidence": 0.8,
                    "compliance_mapping": {}
                }
            }
            
            gaps.append(gap)
            gap_id += 1
        
        return gaps
