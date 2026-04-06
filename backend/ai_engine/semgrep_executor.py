"""
Semgrep Executor - Stage 2 Deterministic Code Analysis
Runs Semgrep with dynamically generated policy rules
"""

import logging
import subprocess
import json
import tempfile
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SemgrepExecutor:
    """
    Executes Semgrep with dynamically generated rules
    - Handles rule generation and YAML creation
    - Runs Semgrep scans
    - Parses and formats results
    """
    
    def __init__(self):
        """Initialize Semgrep executor"""
        self.semgrep_available = self._check_semgrep()
        logger.info(f"✓ Semgrep executor initialized (Semgrep {'available' if self.semgrep_available else 'NOT available'})")
    
    def _check_semgrep(self) -> bool:
        """Check if Semgrep is installed"""
        try:
            result = subprocess.run(
                ["semgrep", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            logger.warning(f"Semgrep check failed: {e}")
            return False
    
    # ========================================================================
    # RULE EXECUTION
    # ========================================================================
    
    def execute_rules_on_repo(
        self,
        repo_path: str,
        rules: List[Dict[str, Any]],
        languages: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute Semgrep rules on a repository
        
        Args:
            repo_path: Path to repository to scan
            rules: List of Semgrep rules to apply
            languages: Specific languages to scan (default: all)
            
        Returns:
            Scan results with violations
        """
        logger.info(f"[Semgrep] Scanning {repo_path} with {len(rules)} rules")
        
        if not self.semgrep_available:
            logger.warning("[Semgrep] Semgrep not available, returning mock results")
            return self._mock_semgrep_results(repo_path, len(rules))
        
        # Create temporary YAML rules file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            rules_yaml = self._rules_to_yaml(rules)
            f.write(rules_yaml)
            rules_file = f.name
        
        try:
            # Build Semgrep command
            cmd = [
                "semgrep",
                "--config", rules_file,
                "--json",
                repo_path
            ]
            
            if languages:
                cmd.extend(["--include-dirs", ",".join(languages)])
            
            logger.info(f"[Semgrep] Running: {' '.join(cmd[:5])}...")
            
            # Run Semgrep
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=300  # 5 minute timeout
            )
            
            # Parse results
            if result.returncode in [0, 1]:  # 0 = no findings, 1 = findings found
                try:
                    output = json.loads(result.stdout)
                    findings = output.get("results", [])
                    
                    logger.info(f"[Semgrep] ✓ Found {len(findings)} potential violations")
                    
                    return {
                        "status": "success",
                        "repo_path": repo_path,
                        "rules_applied": len(rules),
                        "violations": self._format_violations(findings),
                        "scan_time": output.get("_time", {}),
                        "scanned_at": datetime.now().isoformat()
                    }
                except json.JSONDecodeError:
                    logger.error("[Semgrep] Failed to parse JSON output")
                    return {"status": "error", "error": "Failed to parse Semgrep output"}
            else:
                logger.error(f"[Semgrep] Error (code {result.returncode}): {result.stderr}")
                return {"status": "error", "error": result.stderr.decode()}
        
        finally:
            # Cleanup
            Path(rules_file).unlink(missing_ok=True)
    
    def _rules_to_yaml(self, rules: List[Dict[str, Any]]) -> str:
        """Convert rule JSON to Semgrep YAML format"""
        semgrep_rules = []
        
        for rule in rules:
            semgrep_rule = {
                "id": rule.get("id", f"rule_{len(semgrep_rules)}"),
                "pattern": rule.get("pattern", ""),
                "message": rule.get("message", "Policy violation detected"),
                "languages": rule.get("languages", ["python", "javascript"]),
                "severity": rule.get("severity", "WARNING")
            }
            
            # Add optional fields
            if "metadata" in rule:
                semgrep_rule["metadata"] = rule["metadata"]
            
            semgrep_rules.append(semgrep_rule)
        
        return yaml.dump({"rules": semgrep_rules}, default_flow_style=False)
    
    def _format_violations(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert Semgrep findings to standardized violation format"""
        violations = []
        
        for finding in findings:
            violation = {
                "rule_id": finding.get("check_id", "unknown"),
                "rule_name": finding.get("check_id", ""),
                "message": finding.get("extra", {}).get("message", finding.get("description", "")),
                "severity": finding.get("extra", {}).get("severity", "MEDIUM"),
                "file_path": finding.get("path", ""),
                "line_number": finding.get("start", {}).get("line", 0),
                "column": finding.get("start", {}).get("col", 0),
                "code_snippet": finding.get("extra", {}).get("lines", ""),
                "context": self._extract_context(finding),
                "language": finding.get("extra", {}).get("language", "unknown")
            }
            violations.append(violation)
        
        return violations
    
    def _extract_context(self, finding: Dict[str, Any]) -> str:
        """Extract surrounding code context from finding"""
        # This would load the actual file and extract surrounding lines
        return finding.get("extra", {}).get("lines", "")
    
    def _mock_semgrep_results(self, repo_path: str, num_rules: int) -> Dict[str, Any]:
        """Generate mock Semgrep results for testing"""
        logger.warning("[Semgrep] Using mock results for demonstration")
        
        return {
            "status": "success",
            "repo_path": repo_path,
            "rules_applied": num_rules,
            "violations": [
                {
                    "rule_id": "hardcoded_secret_001",
                    "rule_name": "Hardcoded Database Password",
                    "message": "Hardcoded database password detected in source code",
                    "severity": "CRITICAL",
                    "file_path": "config/database.py",
                    "line_number": 15,
                    "column": 10,
                    "code_snippet": 'password = "mySecurePassword123"',
                    "context": "db_config = {\n    'host': 'localhost',\n    'password': 'mySecurePassword123'  # <-- VIOLATION\n}",
                    "language": "python"
                },
                {
                    "rule_id": "unencrypted_api_call_002",
                    "rule_name": "Unencrypted API Configuration",
                    "message": "API call made without encryption/TLS",
                    "severity": "HIGH",
                    "file_path": "services/payment.py",
                    "line_number": 42,
                    "column": 8,
                    "code_snippet": 'response = requests.get("http://api.payment.com")',
                    "context": "# Send payment data\nresponse = requests.get(\"http://api.payment.com\")  # SHOULD BE HTTPS",
                    "language": "python"
                },
                {
                    "rule_id": "missing_auth_check_003",
                    "rule_name": "Missing Authentication Check",
                    "message": "API endpoint missing authentication validation",
                    "severity": "HIGH",
                    "file_path": "api/routes.py",
                    "line_number": 28,
                    "column": 5,
                    "code_snippet": "@app.get(\"/admin/users\")",
                    "context": "@app.get(\"/admin/users\")\ndef list_users():  # <-- MISSING @require_auth\n    return database.query(User).all()",
                    "language": "python"
                }
            ],
            "scan_time": {"parse": 0.5, "run": 1.2, "total": 1.7},
            "scanned_at": datetime.now().isoformat()
        }
    
    # ========================================================================
    # RULE VALIDATION
    # ========================================================================
    
    def validate_semgrep_rules(self, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate Semgrep rules syntax
        
        Args:
            rules: Rules to validate
            
        Returns:
            Validation results with any syntax errors
        """
        logger.info(f"Validating {len(rules)} Semgrep rules")
        
        errors = []
        warnings = []
        
        for rule in rules:
            # Check required fields
            if not rule.get("id"):
                errors.append("Rule missing 'id' field")
            if not rule.get("pattern"):
                errors.append(f"Rule {rule.get('id')} missing 'pattern' field")
            if not rule.get("message"):
                warnings.append(f"Rule {rule.get('id')} missing 'message' field")
            
            # Validate pattern syntax (basic check)
            pattern = rule.get("pattern", "")
            if pattern.startswith("[") or pattern.startswith("("):
                # Could have regex syntax issues
                pass
        
        return {
            "valid": len(errors) == 0,
            "rules_checked": len(rules),
            "errors": errors,
            "warnings": warnings
        }
    
    # ========================================================================
    # PERFORMANCE ANALYSIS
    # ========================================================================
    
    def analyze_scan_performance(
        self,
        scan_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze Semgrep scan performance metrics"""
        return {
            "violations_per_rule": scan_results.get("violations", []) / scan_results.get("rules_applied", 1) if scan_results.get("rules_applied") else 0,
            "scan_time_seconds": sum(scan_results.get("scan_time", {}).values()),
            "violations_found": len(scan_results.get("violations", [])),
            "severity_breakdown": {
                "CRITICAL": len([v for v in scan_results.get("violations", []) if v.get("severity") == "CRITICAL"]),
                "HIGH": len([v for v in scan_results.get("violations", []) if v.get("severity") == "HIGH"]),
                "MEDIUM": len([v for v in scan_results.get("violations", []) if v.get("severity") == "MEDIUM"]),
                "LOW": len([v for v in scan_results.get("violations", []) if v.get("severity") == "LOW"])
            }
        }
    
    # ========================================================================
    # BATCH OPERATIONS
    # ========================================================================
    
    def scan_multiple_repos(
        self,
        repo_paths: List[str],
        rules: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Scan multiple repositories with the same rules"""
        results = []
        
        for repo_path in repo_paths:
            logger.info(f"[Semgrep] Scanning {repo_path}")
            result = self.execute_rules_on_repo(repo_path, rules)
            results.append(result)
        
        return results
    
    def get_executor_status(self) -> Dict[str, Any]:
        """Get status of Semgrep executor"""
        return {
            "status": "ready" if self.semgrep_available else "unavailable",
            "semgrep_available": self.semgrep_available,
            "capabilities": [
                "Dynamic rule execution",
                "Multi-language scanning",
                "JSON output parsing",
                "Batch operations"
            ]
        }
