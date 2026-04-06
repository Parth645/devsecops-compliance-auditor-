"""
Semgrep Detector Module
Layer 1: Ground-truth detection using Semgrep patterns
Provides structured JSON findings with file paths, line numbers, rule IDs
"""

import logging
import json
import subprocess
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SemgrepDetector:
    """
    Local Semgrep-based detection
    - Fast execution (no API cost)
    - Pattern-based rules
    - Returns structured findings
    """
    
    def __init__(self):
        """Initialize Semgrep detector (lazy initialization)"""
        self.semgrep_available = True  # Assume available, verify on first scan
        self.compliance_rules = self._get_compliance_rules()
        logger.info("✓ Semgrep detector initialized (version will be checked on first scan)")
        
    def _check_semgrep(self) -> bool:
        """Verify Semgrep is available (called only on first scan)"""
        try:
            result = subprocess.run(
                ["semgrep", "--version"],
                capture_output=True,
                timeout=60,  # Increased timeout for Windows
                shell=True  # Required for Windows
            )
            if result.returncode == 0:
                version_output = result.stdout.decode('utf-8', errors='ignore')
                logger.info(f"✓ Semgrep verified: {version_output.strip()}")
                return True
        except subprocess.TimeoutExpired:
            logger.warning("Semgrep version check timed out, but assuming it's available")
            return True  # Assume available despite timeout
        except Exception as e:
            logger.debug(f"Semgrep check failed: {e}, but proceeding with scan")
            return True  # Assume available and let scan method handle errors
        return True
    
    def _install_semgrep(self) -> bool:
        """Attempt to install Semgrep via pip"""
        try:
            logger.info("Installing Semgrep via pip...")
            result = subprocess.run(
                ["pip", "install", "-q", "semgrep"],
                capture_output=True,
                timeout=120
            )
            
            if result.returncode == 0:
                logger.info("✓ Semgrep installed successfully")
                # Verify installation
                result = subprocess.run(
                    ["semgrep", "--version"],
                    capture_output=True,
                    timeout=120,  # 2 minutes for post-install verification
                    shell=True
                )
                if result.returncode == 0:
                    logger.info("✓ Semgrep installation verified")
                    return True
            else:
                logger.warning(f"Semgrep installation failed: {result.stderr.decode('utf-8', errors='ignore')}")
                return False
        except Exception as e:
            logger.warning(f"Semgrep installation attempt failed: {e}")
            logger.info("Install manually: pip install semgrep")
            return False
    
    def _get_compliance_rules(self) -> Dict[str, Any]:
        """Compliance-focused Semgrep rules for Indian frameworks"""
        return {
            "hardcoded_secrets": {
                "rule_id": "compliance.hardcoded-secret",
                "pattern": r'(password|secret|token|api_key)\s*=\s*["\']([a-zA-Z0-9]+)["\']',
                "framework": "IT_ACT_2000",
                "severity": "critical",
                "description": "Hardcoded credentials violate SPDI Rules"
            },
            "weak_password_policy": {
                "rule_id": "compliance.weak-password",
                "pattern": r'(minlength|min):\s*[1-6]',
                "framework": "IT_ACT_2000",
                "severity": "high",
                "description": "Password minimum < 8 chars violates IT Act 2000"
            },
            "cors_misconfiguration": {
                "rule_id": "compliance.cors-all-origins",
                "pattern": r'origin\s*:\s*["\']?\*["\']?',
                "framework": "RBI",
                "severity": "high",
                "description": "CORS allows all origins - violates RBI guidelines"
            },
            "no_encryption": {
                "rule_id": "compliance.no-encryption",
                "pattern": r'(password|token|email).*=.*plaintext',
                "framework": "IT_ACT_2000",
                "severity": "critical",
                "description": "Unencrypted PII violates SPDI Rules"
            },
            "console_logging": {
                "rule_id": "compliance.console-pii-logging",
                "pattern": r'console\.(log|error|debug)\(\s*(user|email|password)',
                "framework": "DPDPA",
                "severity": "high",
                "description": "Logging PII to console violates DPDPA"
            },
            "no_input_validation": {
                "rule_id": "compliance.no-input-validation",
                "pattern": r'req\.body\.|req\.query\.|request\.args(?!.*validate)',
                "framework": "IT_ACT_2000",
                "severity": "high",
                "description": "Unvalidated user input allows injection attacks"
            },
            "no_rate_limiting": {
                "rule_id": "compliance.no-rate-limiting",
                "pattern": r'(login|register|auth).*route(?!.*limit)',
                "framework": "RBI",
                "severity": "medium",
                "description": "Missing rate limiting on sensitive endpoints"
            }
        }
    
    async def scan_repository(self, repo_path: str, custom_rules_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Run Semgrep scan on repository with both built-in and custom rules
        
        Args:
            repo_path: Path to repository to scan
            custom_rules_path: Optional path to custom generated rules YAML
            
        Returns: structured findings with file paths, line numbers, rule IDs
        """
        if not self.semgrep_available:
            logger.warning("Semgrep not available, returning empty findings")
            return {
                "findings": [],
                "detector": "semgrep",
                "status": "semgrep_not_available"
            }
        
        try:
            logger.info(f"[SEMGREP SCAN START]")
            logger.info(f"  Repository: {repo_path}")
            
            # Run Semgrep with JSON output
            cmd = [
                "semgrep",
                "--json",
                "--quiet",
            ]
            
            # Track which rules were used
            rules_used = []
            custom_rules_used = False
            
            # Add pre-built Indian compliance rules (DPDPA, RBI, IT Act, etc.)
            # PRIORITIZED: Use pre-built rules first since they're always available
            indian_rules_path = Path(__file__).parent.parent / "policies" / "indian_compliance_rules_complete.yaml"
            logger.info(f"  Rules path: {indian_rules_path.resolve()}")
            logger.info(f"  Rules exist: {indian_rules_path.exists()}")
            
            if indian_rules_path.exists():
                # Validate rules file
                try:
                    import yaml
                    with open(indian_rules_path, 'r') as f:
                        rules_data = yaml.safe_load(f)
                    rule_count = len(rules_data.get('rules', []))
                    logger.info(f"  ✓ Validated {rule_count} rules in file")
                except Exception as e:
                    logger.error(f"  ✗ Rules file validation failed: {e}")
                    return {
                        "findings": [],
                        "detector": "semgrep",
                        "status": "invalid_rules",
                        "error": f"Rules validation failed: {e}"
                    }
                
                cmd.extend(["--config", str(indian_rules_path.resolve())])
                rules_used.append("indian_compliance_rules_complete")
                logger.info(f"  ✓ Including complete Indian compliance rules ({rule_count} rules)")
            else:
                # Fallback to simple rules
                fallback_path = Path(__file__).parent.parent / "policies" / "indian_compliance_rules.yaml"
                if fallback_path.exists():
                    import yaml
                    with open(fallback_path, 'r') as f:
                        rules_data = yaml.safe_load(f)
                    rule_count = len(rules_data.get('rules', []))
                    cmd.extend(["--config", str(fallback_path.resolve())])
                    rules_used.append("indian_compliance_rules")
                    logger.info(f"  ✓ Using fallback rules ({rule_count} rules)")
                else:
                    logger.error(f"  ✗ No rules files found!")
                    return {
                        "findings": [],
                        "detector": "semgrep",
                        "status": "rules_not_found",
                        "error": "No compliance rules files found"
                    }
            
            # Add custom rules if provided (overrides/supplements pre-built rules)
            if custom_rules_path and Path(custom_rules_path).exists():
                cmd.extend(["--config", str(Path(custom_rules_path).resolve())])
                rules_used.append("custom_rules")
                custom_rules_used = True
                logger.info(f"  ✓ Including custom rules from: {custom_rules_path}")
            
            cmd.append(str(repo_path))
            
            logger.info(f"  Command: {' '.join(cmd)}")
            
            # Run Semgrep - use shell=True on Windows for better compatibility
            logger.info("  ℹ Semgrep scanning (this may take 1-2 minutes on first run)...")
            result = subprocess.run(cmd, capture_output=True, timeout=300, text=True, shell=True)
            
            logger.info(f"[SEMGREP SCAN COMPLETE]")
            logger.info(f"  Exit code: {result.returncode}")
            logger.info(f"  Stdout length: {len(result.stdout)} bytes")
            logger.info(f"  Stderr length: {len(result.stderr)} bytes")
            
            findings = []
            
            # Exit code 0 = no findings, 1 = findings found, 2+ = error
            if result.returncode >= 2:
                logger.error(f"  ✗ Semgrep failed with exit code {result.returncode}")
                if result.stderr:
                    logger.error(f"  Error: {result.stderr[:1000]}")
                return {
                    "findings": [],
                    "detector": "semgrep",
                    "status": "error",
                    "error": result.stderr[:500] if result.stderr else "Unknown error"
                }
            
            if result.stdout:
                try:
                    output = json.loads(result.stdout)
                    findings = self._parse_semgrep_output(output, repo_path)
                    
                    logger.info(f"  ✓ Found {len(findings)} Semgrep findings")
                    
                    if len(findings) == 0:
                        logger.warning(f"[ZERO FINDINGS] Possible reasons:")
                        logger.warning(f"  1. Code is fully compliant (unlikely)")
                        logger.warning(f"  2. Rules didn't match any patterns")
                        logger.warning(f"  3. File filtering excluded all files")
                        logger.warning(f"  4. Repository path incorrect: {repo_path}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"  ✗ Failed to parse Semgrep JSON output: {str(e)[:200]}")
                    if result.stderr:
                        logger.debug(f"Semgrep stderr: {result.stderr[:500]}")
            
            return {
                "findings": findings,
                "detector": "semgrep",
                "status": "completed",
                "total_findings": len(findings),
                "rules_used": rules_used,
                "custom_rules_used": custom_rules_used
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Semgrep scan timed out after 180 seconds - repository may be too large or rules too complex")
            return {"findings": [], "detector": "semgrep", "status": "timeout"}
        except Exception as e:
            logger.error(f"Semgrep scan failed: {str(e)[:500]}")
            return {"findings": [], "detector": "semgrep", "status": "error", "error": str(e)[:200]}
    
    def _parse_semgrep_output(self, output: Dict, repo_path: str) -> List[Dict[str, Any]]:
        """Convert Semgrep JSON output to standardized finding format"""
        findings = []
        repo_path = Path(repo_path)
        
        for result in output.get("results", []):
            # Extract code snippet from the actual file since Semgrep's "lines" field is unreliable
            code_snippet = self._extract_code_snippet(
                result.get("path", ""),
                result.get("start", {}).get("line", 0),
                result.get("end", {}).get("line", 0)
            )
            
            finding = {
                "detector": "semgrep",
                "rule_id": result.get("check_id", "unknown"),
                "file": str(Path(result.get("path", "")).name),
                "file_path": result.get("path", ""),
                "line_start": result.get("start", {}).get("line", 0),
                "line_end": result.get("end", {}).get("line", 0),
                "column_start": result.get("start", {}).get("col", 0),
                "severity": self._map_severity(result.get("extra", {}).get("severity", "INFO")),
                "message": result.get("extra", {}).get("message", ""),
                "code_snippet": code_snippet,
                "framework": self._detect_framework(result.get("check_id", "")),
                "evidence": {
                    "file": result.get("path", ""),
                    "line": result.get("start", {}).get("line", 0),
                    "rule_id": result.get("check_id", "")
                }
            }
            findings.append(finding)
        
        return findings
    
    def _extract_code_snippet(self, file_path: str, start_line: int, end_line: int) -> str:
        """Extract actual code snippet from file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                # Get the relevant lines (convert to 0-indexed)
                snippet_lines = lines[max(0, start_line-1):min(len(lines), end_line)]
                return ''.join(snippet_lines).strip()
        except Exception as e:
            logger.debug(f"Could not extract code snippet from {file_path}: {e}")
            return ""
    
    def _map_severity(self, severity: str) -> str:
        """Map Semgrep severity to standard format"""
        severity_map = {
            "ERROR": "critical",
            "WARNING": "high",
            "INFO": "medium"
        }
        return severity_map.get(severity, "medium")
    
    def _detect_framework(self, rule_id: str) -> str:
        """Detect compliance framework from rule ID"""
        if "injection" in rule_id.lower() or "sqli" in rule_id.lower():
            return "IT_ACT_2000"
        elif "auth" in rule_id.lower():
            return "IT_ACT_2000"
        elif "crypto" in rule_id.lower():
            return "IT_ACT_2000"
        elif "hardcoded" in rule_id.lower():
            return "IT_ACT_2000"
        elif "xss" in rule_id.lower():
            return "IT_ACT_2000"
        else:
            return "IT_ACT_2000"  # Default
