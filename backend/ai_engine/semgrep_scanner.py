"""
Semgrep Integration for Enhanced Code Scanning
Replaces regex-based checkers with Semgrep's powerful pattern matching
"""

import subprocess
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import tempfile
import os

logger = logging.getLogger(__name__)


class SemgrepScanner:
    """
    Wrapper for Semgrep code scanning engine
    Integrates with existing compliance checking pipeline
    """
    
    def __init__(self, rules_path: Optional[str] = None):
        """
        Initialize Semgrep scanner
        
        Args:
            rules_path: Path to custom Semgrep rules directory
        """
        self.rules_path = rules_path or self._get_default_rules_path()
        self.semgrep_available = self._check_semgrep_installed()
        
        if not self.semgrep_available:
            logger.warning("Semgrep not installed. Install with: pip install semgrep")
        else:
            logger.info("✓ Semgrep scanner initialized")
    
    def _check_semgrep_installed(self) -> bool:
        """Check if Semgrep is installed"""
        try:
            result = subprocess.run(
                ['semgrep', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"Semgrep version: {version}")
                return True
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _get_default_rules_path(self) -> str:
        """Get path to default Semgrep rules"""
        # Use built-in Semgrep rulesets
        return "p/security-audit"  # Semgrep registry path
    
    def scan_repository(self, repo_path: str, config: Optional[str] = None) -> Dict[str, Any]:
        """
        Scan repository using Semgrep
        
        Args:
            repo_path: Path to repository
            config: Semgrep config/ruleset to use (default: security-audit)
            
        Returns:
            Scan results with violations
        """
        if not self.semgrep_available:
            logger.error("Semgrep not available")
            return {
                "status": "error",
                "message": "Semgrep not installed",
                "violations": []
            }
        
        try:
            # Build Semgrep command
            config_to_use = config or self.rules_path
            
            cmd = [
                'semgrep',
                '--config', config_to_use,
                '--json',
                '--quiet',
                '--no-git-ignore',  # Scan all files (we handle filtering)
                repo_path
            ]
            
            logger.info(f"Running Semgrep scan on {repo_path}...")
            
            # Run Semgrep
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Parse JSON output
            if result.stdout:
                semgrep_output = json.loads(result.stdout)
                violations = self._parse_semgrep_results(semgrep_output, repo_path)
                
                logger.info(f"Semgrep found {len(violations)} potential violations")
                
                return {
                    "status": "success",
                    "violations": violations,
                    "scan_summary": {
                        "total_violations": len(violations),
                        "rules_applied": len(semgrep_output.get("results", [])),
                    }
                }
            else:
                logger.warning("Semgrep returned no output")
                return {
                    "status": "success",
                    "violations": [],
                    "scan_summary": {"total_violations": 0}
                }
                
        except subprocess.TimeoutExpired:
            logger.error("Semgrep scan timed out")
            return {
                "status": "error",
                "message": "Scan timed out",
                "violations": []
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Semgrep output: {e}")
            return {
                "status": "error",
                "message": f"Failed to parse results: {e}",
                "violations": []
            }
        except Exception as e:
            logger.error(f"Semgrep scan failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "violations": []
            }
    
    def _parse_semgrep_results(self, semgrep_output: Dict, repo_path: str) -> List[Dict[str, Any]]:
        """
        Parse Semgrep JSON output into our violation format
        
        Args:
            semgrep_output: Raw Semgrep JSON output
            repo_path: Repository path for relative paths
            
        Returns:
            List of violations in our format
        """
        violations = []
        repo_path_obj = Path(repo_path)
        
        for result in semgrep_output.get("results", []):
            try:
                # Extract file path (make it relative)
                file_path = result.get("path", "")
                try:
                    file_path = str(Path(file_path).relative_to(repo_path_obj))
                except ValueError:
                    # If relative path fails, use as-is
                    pass
                
                # Map Semgrep severity to our format
                semgrep_severity = result.get("extra", {}).get("severity", "WARNING")
                severity_map = {
                    "ERROR": "HIGH",
                    "WARNING": "MEDIUM",
                    "INFO": "LOW"
                }
                severity = severity_map.get(semgrep_severity, "MEDIUM")
                
                # Extract rule information
                check_id = result.get("check_id", "unknown")
                message = result.get("extra", {}).get("message", "Security issue detected")
                
                # Extract location
                start_line = result.get("start", {}).get("line", 0)
                end_line = result.get("end", {}).get("line", 0)
                
                # Extract code snippet
                code_snippet = result.get("extra", {}).get("lines", "")
                
                # Determine category from rule ID
                category = self._categorize_rule(check_id)
                
                # Get fix suggestion if available
                fix_suggestion = result.get("extra", {}).get("fix", "Review and remediate according to security best practices")
                
                # Create violation
                violation = {
                    "rule_id": check_id,
                    "regulation": "Semgrep Security",
                    "severity": severity,
                    "category": category,
                    "description": message,
                    "file_path": file_path,
                    "line_number": start_line,
                    "code_snippet": code_snippet,
                    "fix_suggestion": fix_suggestion,
                    "confidence": 0.9,  # Semgrep has high confidence
                    "matched_text": code_snippet,
                    "metadata": {
                        "semgrep_severity": semgrep_severity,
                        "end_line": end_line,
                        "rule_url": result.get("extra", {}).get("metadata", {}).get("source", "")
                    }
                }
                
                violations.append(violation)
                
            except Exception as e:
                logger.warning(f"Failed to parse Semgrep result: {e}")
                continue
        
        return violations
    
    def _categorize_rule(self, rule_id: str) -> str:
        """
        Categorize Semgrep rule into compliance category
        
        Args:
            rule_id: Semgrep rule ID
            
        Returns:
            Category string
        """
        rule_lower = rule_id.lower()
        
        # Map Semgrep rules to compliance categories
        if any(keyword in rule_lower for keyword in ['sql', 'injection', 'xss', 'command']):
            return 'injection_vulnerability'
        elif any(keyword in rule_lower for keyword in ['secret', 'password', 'key', 'token', 'credential']):
            return 'hardcoded_secrets'
        elif any(keyword in rule_lower for keyword in ['crypto', 'hash', 'encrypt', 'ssl', 'tls']):
            return 'weak_cryptography'
        elif any(keyword in rule_lower for keyword in ['auth', 'session', 'cookie']):
            return 'authentication'
        elif any(keyword in rule_lower for keyword in ['pii', 'personal', 'sensitive']):
            return 'data_exposure'
        elif any(keyword in rule_lower for keyword in ['log', 'audit']):
            return 'logging'
        else:
            return 'security_misconfiguration'
    
    def scan_with_custom_rules(self, repo_path: str, rules_file: str) -> Dict[str, Any]:
        """
        Scan with custom Semgrep rules
        
        Args:
            repo_path: Path to repository
            rules_file: Path to custom rules YAML file
            
        Returns:
            Scan results
        """
        if not Path(rules_file).exists():
            logger.error(f"Rules file not found: {rules_file}")
            return {
                "status": "error",
                "message": f"Rules file not found: {rules_file}",
                "violations": []
            }
        
        return self.scan_repository(repo_path, config=rules_file)
    
    def get_available_rulesets(self) -> List[str]:
        """Get list of available Semgrep rulesets"""
        return [
            "p/security-audit",  # General security
            "p/owasp-top-ten",   # OWASP Top 10
            "p/secrets",         # Secret detection
            "p/sql-injection",   # SQL injection
            "p/xss",             # Cross-site scripting
            "p/command-injection",  # Command injection
            "p/python",          # Python-specific
            "p/javascript",      # JavaScript-specific
            "p/java",            # Java-specific
            "p/go",              # Go-specific
        ]


def create_indian_compliance_rules() -> str:
    """
    Create custom Semgrep rules for Indian compliance (DPDP, CERT-In, RBI)
    
    Returns:
        Path to created rules file
    """
    rules_yaml = """
rules:
  - id: dpdp-hardcoded-aadhaar
    pattern-either:
      - pattern: |
          $AADHAAR = "$NUMBER"
      - pattern: |
          aadhaar = "$NUMBER"
    message: "Potential hardcoded Aadhaar number detected (DPDP Act violation)"
    severity: ERROR
    languages: [python, javascript, java]
    metadata:
      category: pii_exposure
      regulation: DPDP Act 2023
      cwe: "CWE-798"
      
  - id: dpdp-missing-consent
    pattern-not: |
      consent
    pattern: |
      def collect_user_data(...):
        ...
    message: "User data collection without consent mechanism (DPDP Act Article 6)"
    severity: WARNING
    languages: [python]
    metadata:
      category: consent_management
      regulation: DPDP Act 2023
      
  - id: certin-missing-logging
    pattern-not: |
      logger.$METHOD(...)
    pattern: |
      def $FUNC(...):
        ...
        authenticate(...)
        ...
    message: "Authentication without security logging (CERT-In Directions)"
    severity: WARNING
    languages: [python]
    metadata:
      category: security_logging
      regulation: CERT-In Directions 2022
      
  - id: rbi-weak-encryption
    pattern-either:
      - pattern: |
          Crypto.Cipher.DES.new(...)
      - pattern: |
          Crypto.Cipher.ARC4.new(...)
      - pattern: |
          md5(...)
    message: "Weak encryption algorithm (RBI Cybersecurity Guidelines)"
    severity: ERROR
    languages: [python]
    metadata:
      category: weak_cryptography
      regulation: RBI Cybersecurity Guidelines
      cwe: "CWE-327"
      
  - id: hardcoded-database-password
    pattern-either:
      - pattern: |
          $DB_URL = "postgresql://$USER:$PASS@..."
      - pattern: |
          password = "$LITERAL"
      - pattern: |
          PASSWORD = "$LITERAL"
    message: "Hardcoded database password detected"
    severity: ERROR
    languages: [python, javascript, java]
    metadata:
      category: hardcoded_secrets
      cwe: "CWE-798"
"""
    
    # Create rules file in temp directory
    rules_dir = Path("backend/ai engine/semgrep_rules")
    rules_dir.mkdir(exist_ok=True)
    
    rules_file = rules_dir / "indian_compliance.yaml"
    rules_file.write_text(rules_yaml)
    
    logger.info(f"Created Indian compliance rules at {rules_file}")
    return str(rules_file)


if __name__ == "__main__":
    # Test Semgrep integration
    logging.basicConfig(level=logging.INFO)
    
    scanner = SemgrepScanner()
    
    if scanner.semgrep_available:
        print("✓ Semgrep is available")
        print(f"\nAvailable rulesets:")
        for ruleset in scanner.get_available_rulesets():
            print(f"  - {ruleset}")
        
        # Create custom rules
        rules_file = create_indian_compliance_rules()
        print(f"\n✓ Created custom rules: {rules_file}")
    else:
        print("✗ Semgrep not installed")
        print("\nTo install Semgrep:")
        print("  pip install semgrep")
        print("\nOr using Homebrew (macOS):")
        print("  brew install semgrep")
