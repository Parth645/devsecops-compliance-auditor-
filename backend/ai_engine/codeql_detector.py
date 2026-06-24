"""
CodeQL Detector Module
Layer 1b: Advanced graph-based detection using CodeQL
Detects complex vulnerabilities beyond pattern matching
"""

import logging
import json
import subprocess
import tempfile
from typing import Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class CodeQLDetector:
    """
    CodeQL-based detection for advanced vulnerability analysis
    - Graph-based analysis (understands data flow)
    - Can detect complex vulnerabilities
    - Language-specific support (JavaScript, Python, Java, etc.)
    """
    
    def __init__(self):
        """Initialize CodeQL detector"""
        self.codeql_available = self._check_codeql()
        self.supported_languages = ["javascript", "python", "java", "cpp", "csharp"]
        
    def _check_codeql(self) -> bool:
        """Check if CodeQL is installed"""
        try:
            result = subprocess.run(
                ["codeql", "--version"],
                capture_output=True,
                timeout=5
            )
            available = result.returncode == 0
            if available:
                logger.info("✓ CodeQL detected and available")
            else:
                logger.warning("⚠ CodeQL not found. Install from: https://github.com/github/codeql-cli-binaries/releases")
            return available
        except Exception as e:
            logger.warning(f"CodeQL check failed: {e}")
            return False
    
    async def scan_repository(self, repo_path: str, language: str = "javascript") -> Dict[str, Any]:
        """
        Run CodeQL scan on repository
        
        Args:
            repo_path: Path to repository
            language: Programming language (javascript, python, java, etc.)
            
        Returns:
            Structured findings with data flow information
        """
        if not self.codeql_available:
            logger.warning("CodeQL not available")
            return {
                "findings": [],
                "detector": "codeql",
                "status": "codeql_not_available"
            }
        
        try:
            logger.info(f"[CodeQL] Scanning {language} repository: {repo_path}")
            
            # Create temp database directory
            with tempfile.TemporaryDirectory() as tmpdir:
                db_path = Path(tmpdir) / "codeql_db"
                
                # Step 1: Create CodeQL database
                logger.info(f"  [1/3] Creating CodeQL database for {language}...")
                create_cmd = [
                    "codeql",
                    "database",
                    "create",
                    "--language", language,
                    "--source-root", str(repo_path),
                    str(db_path)
                ]
                
                result = subprocess.run(create_cmd, capture_output=True, timeout=300)
                if result.returncode != 0:
                    logger.warning(f"CodeQL database creation failed: {result.stderr.decode()}")
                    return {"findings": [], "detector": "codeql", "status": "db_creation_failed"}
                
                # Step 2: Query for security issues
                logger.info(f"  [2/3] Running security queries...")
                findings = await self._run_queries(str(db_path), language)
                
                logger.info(f"  ✓ Found {len(findings)} CodeQL issues")
                
                return {
                    "findings": findings,
                    "detector": "codeql",
                    "status": "completed",
                    "total_findings": len(findings)
                }
                
        except subprocess.TimeoutExpired:
            logger.error("CodeQL scan timed out")
            return {"findings": [], "detector": "codeql", "status": "timeout"}
        except Exception as e:
            logger.error(f"CodeQL scan failed: {e}")
            return {"findings": [], "detector": "codeql", "status": "error"}
    
    async def _run_queries(self, db_path: str, language: str) -> List[Dict[str, Any]]:
        """Run CodeQL queries and parse results"""
        findings = []
        
        # Built-in CodeQL query suites for security
        if language == "javascript":
            queries = [
                "security-and-quality",
                "security-extended"
            ]
        elif language == "python":
            queries = ["security-and-quality"]
        else:
            queries = ["security-extended"]
        
        try:
            for query_suite in queries:
                cmd = [
                    "codeql",
                    "database",
                    "analyze",
                    db_path,
                    f"--library-path=/codeql/codeql-repo",
                    f"{query_suite}",
                    "--format=json",
                    "--output=/tmp/codeql_results.json"
                ]
                
                result = subprocess.run(cmd, capture_output=True, timeout=180)
                
                if result.returncode == 0:
                    # Parse results from file
                    try:
                        with open("/tmp/codeql_results.json", "r") as f:
                            results = json.load(f)
                            findings.extend(self._parse_codeql_results(results))
                    except Exception as e:
                        logger.debug(f"Failed to parse CodeQL results: {e}")
        
        except subprocess.TimeoutExpired:
            logger.warning("CodeQL query timeout")
        except Exception as e:
            logger.debug(f"CodeQL query execution failed: {e}")
        
        return findings
    
    def _parse_codeql_results(self, results: Dict) -> List[Dict[str, Any]]:
        """Convert CodeQL results to standardized format"""
        findings = []
        
        for result_set in results.get("run", []):
            for result in result_set.get("results", []):
                # Extract location info
                location = result.get("locations", [{}])[0]
                physical_loc = location.get("physicalLocation", {})
                file_loc = physical_loc.get("fileLocations", [{}])[0] if physical_loc.get("fileLocations") else {}
                
                finding = {
                    "detector": "codeql",
                    "rule_id": result.get("ruleId", "unknown"),
                    "file": Path(file_loc.get("uri", "")).name,
                    "file_path": file_loc.get("uri", ""),
                    "line_start": file_loc.get("startLine", 0),
                    "line_end": file_loc.get("endLine", 0),
                    "severity": self._map_codeql_severity(result.get("level", "warning")),
                    "message": result.get("message", {}).get("text", ""),
                    "framework": self._detect_framework_from_rule(result.get("ruleId", "")),
                    "evidence": {
                        "file": file_loc.get("uri", ""),
                        "line": file_loc.get("startLine", 0),
                        "rule_id": result.get("ruleId", "")
                    }
                }
                findings.append(finding)
        
        return findings
    
    def _map_codeql_severity(self, level: str) -> str:
        """Map CodeQL level to standard severity"""
        level_map = {
            "error": "critical",
            "warning": "high",
            "note": "medium"
        }
        return level_map.get(level.lower(), "medium")
    
    def _detect_framework_from_rule(self, rule_id: str) -> str:
        """Map CodeQL rule to compliance framework"""
        rule_lower = rule_id.lower()
        
        if any(x in rule_lower for x in ["sql", "injection", "xss", "csrf"]):
            return "IT_ACT_2000"
        elif any(x in rule_lower for x in ["auth", "crypto", "password"]):
            return "IT_ACT_2000"
        elif any(x in rule_lower for x in ["path", "traverse"]):
            return "IT_ACT_2000"
        else:
            return "IT_ACT_2000"
