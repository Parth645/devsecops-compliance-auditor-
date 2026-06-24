"""
RBI Cybersecurity Guidelines Compliance Checkers
Reserve Bank of India cybersecurity compliance verification
"""

from typing import List, Dict, Any
import re
from .base_checker import BaseComplianceChecker, Violation
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from code_analyzers import PythonAnalyzer, JavaScriptAnalyzer, ConfigAnalyzer
import logging

logger = logging.getLogger(__name__)


class RBIEncryptionChecker(BaseComplianceChecker):
    """
    RBI: Encryption Standards
    Verifies AES-256 for data at rest, TLS 1.2+ for transit
    """
    
    def __init__(self):
        super().__init__("RBI Cybersecurity Guidelines - Encryption", "RBI")
        self.py_analyzer = PythonAnalyzer()
        self.js_analyzer = JavaScriptAnalyzer()
        self.config_analyzer = ConfigAnalyzer()
    
    def check(self, file_path: str, content: str, file_type: str, context: Dict[str, Any]) -> List[Violation]:
        """Check encryption standards compliance"""
        self.clear_violations()
        
        if file_type == 'py':
            self._check_python_encryption(file_path, content)
        elif file_type in ['js', 'ts']:
            self._check_javascript_encryption(file_path, content)
        elif file_type in ['yaml', 'yml', 'json']:
            self._check_config_encryption(file_path, content, file_type)
        
        return self.get_violations()
    
    def _check_python_encryption(self, file_path: str, content: str):
        """Check Python encryption usage"""
        encryption_info = self.py_analyzer.check_encryption_usage(content)
        
        # Flag weak algorithms
        for weak_algo in encryption_info['weak_algorithms']:
            self.add_violation(
                rule_id='RBI_ENC_001',
                severity='HIGH',
                category='encryption',
                description=f"Weak encryption algorithm detected: {weak_algo}",
                file_path=file_path,
                fix_suggestion=f"Replace {weak_algo} with SHA-256, SHA-512, or bcrypt"
            )
        
        # Check for no encryption when handling sensitive data
        if encryption_info['no_encryption']:
            self.add_violation(
                rule_id='RBI_ENC_002',
                severity='HIGH',
                category='encryption',
                description="Sensitive data handling without encryption",
                file_path=file_path,
                fix_suggestion="Implement encryption for sensitive data using AES-256 or bcrypt"
            )
    
    def _check_javascript_encryption(self, file_path: str, content: str):
        """Check JavaScript encryption usage"""
        encryption_info = self.js_analyzer.check_encryption_usage(content)
        
        # Flag weak algorithms
        for weak_algo in encryption_info['weak_algorithms']:
            self.add_violation(
                rule_id='RBI_ENC_003',
                severity='HIGH',
                category='encryption',
                description=f"Weak encryption algorithm detected: {weak_algo}",
                file_path=file_path,
                fix_suggestion=f"Replace {weak_algo} with SHA-256, SHA-512, or bcrypt"
            )
    
    def _check_config_encryption(self, file_path: str, content: str, file_type: str):
        """Check config file encryption settings"""
        if file_type in ['yaml', 'yml']:
            config = self.config_analyzer.parse_yaml(content)
        else:
            config = self.config_analyzer.parse_json(content)
        
        if not config:
            return
        
        encryption_settings = self.config_analyzer.check_encryption_settings(config)
        
        # Check TLS version
        if encryption_settings['tls_version']:
            tls_version = encryption_settings['tls_version']
            if isinstance(tls_version, str):
                # Extract version number
                version_match = re.search(r'(\d+\.?\d*)', tls_version)
                if version_match:
                    version = float(version_match.group(1))
                    if version < 1.2:
                        self.add_violation(
                            rule_id='RBI_ENC_004',
                            severity='HIGH',
                            category='encryption',
                            description=f"TLS version {tls_version} is below required 1.2",
                            file_path=file_path,
                            fix_suggestion="Upgrade to TLS 1.2 or higher"
                        )


class RBIAccessControlChecker(BaseComplianceChecker):
    """
    RBI: Access Controls
    Verifies MFA, RBAC, and session management
    """
    
    def __init__(self):
        super().__init__("RBI Cybersecurity Guidelines - Access Control", "RBI")
        self.js_analyzer = JavaScriptAnalyzer()
    
    def check(self, file_path: str, content: str, file_type: str, context: Dict[str, Any]) -> List[Violation]:
        """Check access control compliance"""
        self.clear_violations()
        
        has_mfa = self._check_mfa(content)
        has_rbac = self._check_rbac(content)
        has_session_mgmt = self._check_session_management(content)
        
        if not has_mfa:
            self.add_violation(
                rule_id='RBI_AC_001',
                severity='HIGH',
                category='access_control',
                description="Multi-factor authentication not implemented",
                file_path=file_path,
                fix_suggestion="Implement MFA for critical system access"
            )
        
        if not has_rbac:
            self.add_violation(
                rule_id='RBI_AC_002',
                severity='MEDIUM',
                category='access_control',
                description="Role-based access control not found",
                file_path=file_path,
                fix_suggestion="Implement RBAC to enforce least privilege principle"
            )
        
        if not has_session_mgmt:
            self.add_violation(
                rule_id='RBI_AC_003',
                severity='MEDIUM',
                category='access_control',
                description="Session management not properly implemented",
                file_path=file_path,
                fix_suggestion="Implement secure session management with timeouts"
            )
        
        # Check JWT security if used
        if file_type in ['js', 'ts']:
            jwt_info = self.js_analyzer.check_jwt_security(content)
            if jwt_info['uses_jwt']:
                if jwt_info['secret_hardcoded']:
                    self.add_violation(
                        rule_id='RBI_AC_004',
                        severity='HIGH',
                        category='access_control',
                        description="JWT secret is hardcoded",
                        file_path=file_path,
                        fix_suggestion="Move JWT secret to environment variables"
                    )
        
        return self.get_violations()
    
    def _check_mfa(self, content: str) -> bool:
        """Check for MFA implementation"""
        patterns = [
            r'mfa',
            r'multi.*factor',
            r'two.*factor',
            r'2fa',
            r'otp',
            r'totp',
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)
    
    def _check_rbac(self, content: str) -> bool:
        """Check for RBAC implementation"""
        patterns = [
            r'role.*based',
            r'rbac',
            r'permission',
            r'authorize',
            r'check.*role',
            r'has.*permission',
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)
    
    def _check_session_management(self, content: str) -> bool:
        """Check for session management"""
        patterns = [
            r'session',
            r'token.*expir',
            r'session.*timeout',
            r'refresh.*token',
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)


class RBIAuditTrailChecker(BaseComplianceChecker):
    """
    RBI: Audit Trails
    Verifies comprehensive transaction and activity logging
    """
    
    def __init__(self):
        super().__init__("RBI Cybersecurity Guidelines - Audit Trail", "RBI")
    
    def check(self, file_path: str, content: str, file_type: str, context: Dict[str, Any]) -> List[Violation]:
        """Check audit trail compliance"""
        self.clear_violations()
        
        has_transaction_logging = self._check_transaction_logging(content)
        has_user_activity = self._check_user_activity_logging(content)
        has_immutable_logs = self._check_log_immutability(content)
        
        if not has_transaction_logging:
            self.add_violation(
                rule_id='RBI_AT_001',
                severity='HIGH',
                category='audit_trail',
                description="Transaction logging not implemented",
                file_path=file_path,
                fix_suggestion="Implement comprehensive logging for all financial transactions"
            )
        
        if not has_user_activity:
            self.add_violation(
                rule_id='RBI_AT_002',
                severity='MEDIUM',
                category='audit_trail',
                description="User activity logging not found",
                file_path=file_path,
                fix_suggestion="Implement logging for all user actions and activities"
            )
        
        if has_transaction_logging and not has_immutable_logs:
            self.add_violation(
                rule_id='RBI_AT_003',
                severity='MEDIUM',
                category='audit_trail',
                description="Log immutability not ensured",
                file_path=file_path,
                fix_suggestion="Implement write-once audit logs or use blockchain for immutability"
            )
        
        return self.get_violations()
    
    def _check_transaction_logging(self, content: str) -> bool:
        """Check for transaction logging"""
        patterns = [
            r'log.*transaction',
            r'audit.*transaction',
            r'transaction.*log',
            r'record.*transaction',
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)
    
    def _check_user_activity_logging(self, content: str) -> bool:
        """Check for user activity logging"""
        patterns = [
            r'log.*activity',
            r'user.*activity',
            r'audit.*user',
            r'track.*user',
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)
    
    def _check_log_immutability(self, content: str) -> bool:
        """Check for log immutability"""
        patterns = [
            r'immutable.*log',
            r'write.*once',
            r'append.*only',
            r'blockchain.*log',
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)
