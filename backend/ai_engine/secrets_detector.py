"""
Secrets Detector - Detects hardcoded secrets, API keys, and PII
High-priority patterns for production security
Uses AI-powered context analysis and project awareness to eliminate false positives
"""

import re
import base64
from typing import List, Dict, Any, Optional
from context_analyzer import ContextAnalyzer


class SecretsDetector:
    """Detect hardcoded secrets and sensitive data with project-aware false positive filtering"""
    
    def __init__(self, enable_context_analysis: bool = True, project_profile=None):
        self.patterns = self._initialize_patterns()
        self.enable_context_analysis = enable_context_analysis
        self.project_profile = project_profile  # Project context for smarter analysis
        self.context_analyzer = ContextAnalyzer(project_profile=project_profile) if enable_context_analysis else None
    
    def _initialize_patterns(self) -> List[Dict[str, Any]]:
        """Initialize detection patterns for secrets and PII"""
        return [
            # 1. AWS Access Keys
            {
                "rule_id": "SECRET_AWS_KEY",
                "name": "AWS Access Key",
                "pattern": r'(AKIA|ASIA)[A-Z0-9]{16}',
                "severity": "CRITICAL",
                "category": "secrets",
                "description": "Hardcoded AWS access key detected",
                "suggestion": "Move to environment variables or AWS Secrets Manager"
            },
            
            # 2. API Keys (OpenAI, Stripe, etc.)
            {
                "rule_id": "SECRET_API_KEY",
                "name": "API Key",
                "pattern": r'(sk-|sk_live_|pk_live_|pk_test_)[a-zA-Z0-9_]{20,}',
                "severity": "CRITICAL",
                "category": "secrets",
                "description": "Hardcoded API key detected (OpenAI/Stripe/etc)",
                "suggestion": "Store in environment variables or secret management system"
            },
            
            # 3. Aadhaar Number (Indian ID) - Improved detection
            {
                "rule_id": "PII_AADHAAR",
                "name": "Aadhaar Number",
                "pattern": r'\b\d{4}\s?\d{4}\s?\d{4}\b',
                "severity": "HIGH",
                "category": "pii",
                "description": "Aadhaar number detected (Indian national ID)",
                "suggestion": "Encrypt or mask Aadhaar numbers, comply with DPDP Act",
                "validation": "aadhaar"  # Special validation flag
            },
            
            # 4. Hardcoded Passwords
            {
                "rule_id": "SECRET_PASSWORD",
                "name": "Hardcoded Password",
                "pattern": r'(password|pwd|passwd)\s*[=:]\s*["\']([^"\']{8,})["\']',
                "severity": "HIGH",
                "category": "secrets",
                "description": "Hardcoded password detected",
                "suggestion": "Use environment variables or secure credential management"
            },
            
            # 5. Private Keys
            {
                "rule_id": "SECRET_PRIVATE_KEY",
                "name": "Private Key",
                "pattern": r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----',
                "severity": "CRITICAL",
                "category": "secrets",
                "description": "Private key detected in code",
                "suggestion": "Store private keys in secure key management system"
            },
            
            # 6. JWT Tokens
            {
                "rule_id": "SECRET_JWT",
                "name": "JWT Token",
                "pattern": r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}',
                "severity": "HIGH",
                "category": "secrets",
                "description": "JWT token detected in code",
                "suggestion": "Never hardcode JWT tokens, generate at runtime"
            },
            
            # 7. Database Connection Strings
            {
                "rule_id": "SECRET_DB_CONNECTION",
                "name": "Database Connection String",
                "pattern": r'(mongodb|mysql|postgresql|postgres)://[^:]+:[^@]+@',
                "severity": "CRITICAL",
                "category": "secrets",
                "description": "Database connection string with credentials",
                "suggestion": "Use environment variables for database credentials"
            },
            
            # 8. Credit Card Numbers
            {
                "rule_id": "PII_CREDIT_CARD",
                "name": "Credit Card Number",
                "pattern": r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b',
                "severity": "CRITICAL",
                "category": "pii",
                "description": "Credit card number detected",
                "suggestion": "Never store credit card numbers in code, use PCI-compliant payment gateway"
            },
            
            # 9. Email Addresses (potential PII)
            {
                "rule_id": "PII_EMAIL",
                "name": "Email Address",
                "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                "severity": "MEDIUM",
                "category": "pii",
                "description": "Email address detected in code",
                "suggestion": "Avoid hardcoding email addresses, use configuration"
            },
            
            # 10. Phone Numbers (Indian format)
            {
                "rule_id": "PII_PHONE",
                "name": "Phone Number",
                "pattern": r'\b(\+91|0)?[6-9]\d{9}\b',
                "severity": "MEDIUM",
                "category": "pii",
                "description": "Indian phone number detected",
                "suggestion": "Avoid hardcoding phone numbers, use configuration"
            }
        ]
    
    def scan_content(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Scan content for secrets and PII with context-aware filtering
        
        Args:
            content: File content to scan
            file_path: Path to file being scanned
            
        Returns:
            List of detected secrets/PII violations (filtered for false positives)
        """
        violations = []
        lines = content.split('\n')
        
        for pattern_def in self.patterns:
            pattern = re.compile(pattern_def["pattern"], re.IGNORECASE)
            
            for line_num, line in enumerate(lines, 1):
                matches = pattern.finditer(line)
                
                for match in matches:
                    matched_text = match.group()
                    
                    # Use context analyzer if enabled
                    if self.enable_context_analysis and self.context_analyzer:
                        # Get surrounding lines for context
                        start_line = max(0, line_num - 3)
                        end_line = min(len(lines), line_num + 3)
                        surrounding_lines = lines[start_line:line_num-1] + lines[line_num:end_line]
                        
                        # Analyze context
                        analysis = self.context_analyzer.analyze_detection(
                            matched_text=matched_text,
                            line=line,
                            file_path=file_path,
                            rule_id=pattern_def["rule_id"],
                            surrounding_lines=surrounding_lines
                        )
                        
                        # Skip if it's a false positive
                        if analysis["is_false_positive"]:
                            continue
                        
                        # Add context analysis to violation
                        violation = {
                            "rule_id": pattern_def["rule_id"],
                            "file_path": file_path,
                            "line_number": line_num,
                            "matched_text": self._mask_sensitive(matched_text, pattern_def["rule_id"]),
                            "line_content": line.strip()[:100],
                            "category": pattern_def["category"],
                            "severity": pattern_def["severity"],
                            "description": pattern_def["description"],
                            "suggestion": pattern_def["suggestion"],
                            "context_analysis": {
                                "confidence": analysis["confidence"],
                                "file_context": analysis["file_context"],
                                "data_type": analysis["data_type"],
                                "recommendation": analysis["recommendation"]
                            }
                        }
                    else:
                        # Fallback to basic false positive check
                        if self._is_false_positive(pattern_def["rule_id"], line, match):
                            continue
                        
                        violation = {
                            "rule_id": pattern_def["rule_id"],
                            "file_path": file_path,
                            "line_number": line_num,
                            "matched_text": self._mask_sensitive(matched_text, pattern_def["rule_id"]),
                            "line_content": line.strip()[:100],
                            "category": pattern_def["category"],
                            "severity": pattern_def["severity"],
                            "description": pattern_def["description"],
                            "suggestion": pattern_def["suggestion"]
                        }
                    
                    violations.append(violation)
        
        # Check for base64-encoded secrets
        violations.extend(self._check_base64_secrets(content, file_path))
        
        return violations
    
    def _is_comment(self, line: str) -> bool:
        """Check if line is a comment"""
        stripped = line.strip()
        return (
            stripped.startswith('//') or
            stripped.startswith('#') or
            stripped.startswith('/*') or
            stripped.startswith('*') or
            stripped.startswith('<!--')
        )
    
    def _is_false_positive(self, rule_id: str, line: str, match: re.Match) -> bool:
        """Check for false positives based on context"""
        line_lower = line.lower()
        
        # Aadhaar false positives
        if rule_id == "PII_AADHAAR":
            matched_text = match.group()
            
            # Skip if it's in an array of zeros or repeated patterns
            if matched_text.replace(' ', '') in ['000000000000', '111111111111', '222222222222', 
                                                   '333333333333', '444444444444', '555555555555',
                                                   '666666666666', '777777777777', '888888888888', 
                                                   '999999999999']:
                return True
            
            # Skip if it's in a string of zeros (like JavaScript array)
            if "'0" in line or '"0' in line or "zeros" in line_lower:
                return True
            
            # Skip if it's a test/example value
            if any(keyword in line_lower for keyword in ['test', 'example', 'sample', 'dummy', 'mock', 'fake']):
                return True
            
            # Skip if it's in a comment
            if '//' in line[:line.index(matched_text)] or '#' in line[:line.index(matched_text)]:
                return True
            
            # Skip if all digits are the same
            digits_only = matched_text.replace(' ', '')
            if len(set(digits_only)) == 1:
                return True
            
            # Skip if it's a sequential pattern (123456789012, etc.)
            if self._is_sequential(digits_only):
                return True
            
            # Validate Aadhaar checksum (Verhoeff algorithm)
            if not self._validate_aadhaar_checksum(digits_only):
                return True
        
        # Email false positives
        if rule_id == "PII_EMAIL":
            # Skip example emails
            example_domains = ['example.com', 'test.com', 'domain.com', 'email.com']
            if any(domain in match.group().lower() for domain in example_domains):
                return True
            # Skip variable names
            if 'email' in line_lower and '=' in line_lower and '@' not in line_lower[:line_lower.index('=')]:
                return True
        
        # Password false positives
        if rule_id == "SECRET_PASSWORD":
            # Skip placeholder passwords
            password_value = match.group(2) if len(match.groups()) > 1 else ""
            placeholders = ['password', 'your_password', 'changeme', 'example', 'test', '***']
            if password_value.lower() in placeholders:
                return True
        
        # Phone number false positives
        if rule_id == "PII_PHONE":
            # Skip if it's a port number or other numeric value
            if 'port' in line_lower or 'timeout' in line_lower:
                return True
        
        return False
    
    def _is_sequential(self, digits: str) -> bool:
        """Check if digits form a sequential pattern"""
        if len(digits) < 4:
            return False
        
        # Check ascending sequence
        is_ascending = all(int(digits[i]) == (int(digits[i-1]) + 1) % 10 for i in range(1, len(digits)))
        
        # Check descending sequence
        is_descending = all(int(digits[i]) == (int(digits[i-1]) - 1) % 10 for i in range(1, len(digits)))
        
        return is_ascending or is_descending
    
    def _validate_aadhaar_checksum(self, aadhaar: str) -> bool:
        """
        Validate Aadhaar number using Verhoeff algorithm
        This reduces false positives significantly
        """
        if len(aadhaar) != 12:
            return False
        
        # Verhoeff algorithm multiplication table
        d = [
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
            [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
            [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
            [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
            [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
            [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
            [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
            [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
            [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
        ]
        
        # Permutation table
        p = [
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
            [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
            [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
            [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
            [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
            [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
            [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
        ]
        
        # Inverse table
        inv = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]
        
        try:
            c = 0
            for i, digit in enumerate(reversed(aadhaar)):
                c = d[c][p[(i % 8)][int(digit)]]
            
            return c == 0
        except (ValueError, IndexError):
            return False
    
    def _mask_sensitive(self, text: str, rule_id: str) -> str:
        """Mask sensitive parts of detected secrets"""
        if len(text) <= 8:
            return "***"
        
        # Show first 4 and last 4 characters
        return f"{text[:4]}...{text[-4:]}"
    
    def _check_base64_secrets(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Check for base64-encoded secrets"""
        violations = []
        
        # Look for base64 patterns (at least 40 chars)
        base64_pattern = r'[A-Za-z0-9+/]{40,}={0,2}'
        matches = re.finditer(base64_pattern, content)
        
        for match in matches:
            try:
                decoded = base64.b64decode(match.group())
                # Check if decoded content looks like a secret
                if self._looks_like_secret(decoded):
                    violations.append({
                        "rule_id": "SECRET_BASE64",
                        "file_path": file_path,
                        "line_number": content[:match.start()].count('\n') + 1,
                        "matched_text": f"{match.group()[:10]}...",
                        "category": "secrets",
                        "severity": "HIGH",
                        "description": "Potential base64-encoded secret detected",
                        "suggestion": "Review base64-encoded data for sensitive information"
                    })
            except Exception:
                # Not valid base64, skip
                pass
        
        return violations
    
    def _looks_like_secret(self, decoded: bytes) -> bool:
        """Check if decoded base64 looks like a secret"""
        try:
            text = decoded.decode('utf-8', errors='ignore')
            # Check for secret-like patterns
            secret_indicators = ['key', 'secret', 'token', 'password', 'api', 'auth']
            return any(indicator in text.lower() for indicator in secret_indicators)
        except Exception:
            return False
