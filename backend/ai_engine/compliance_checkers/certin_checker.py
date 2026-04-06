"""
CERT-In Directions 2022 Compliance Checkers
Cybersecurity incident reporting and logging compliance
"""

from typing import List, Dict, Any
import re
from .base_checker import BaseComplianceChecker, Violation
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from code_analyzers import ConfigAnalyzer
import logging

logger = logging.getLogger(__name__)


class CERTInIncidentReportingChecker(BaseComplianceChecker):
    """
    CERT-In: 6-Hour Incident Reporting
    Verifies incident detection and reporting mechanisms
    """
    
    def __init__(self):
        super().__init__("CERT-In Directions 2022 - Incident Reporting", "CERT-In")
    
    def check(self, file_path: str, content: str, file_type: str, context: Dict[str, Any]) -> List[Violation]:
        """Check incident reporting compliance"""
        self.clear_violations()
        
        has_incident_detection = self._check_incident_detection(content)
        has_reporting_function = self._check_reporting_function(content)
        has_timeline = self._check_timeline_requirement(content)
        
        if not has_incident_detection:
            self.add_violation(
                rule_id='CERTIN_IR_001',
                severity='HIGH',
                category='incident_reporting',
                description="No incident detection mechanism found",
                file_path=file_path,
                fix_suggestion="Implement security incident detection and monitoring"
            )
        
        if has_incident_detection and not has_reporting_function:
            self.add_violation(
                rule_id='CERTIN_IR_002',
                severity='HIGH',
                category='incident_reporting',
                description="Incident detection without reporting function",
                file_path=file_path,
                fix_suggestion="Implement incident reporting function to CERT-In"
            )
        
        if has_reporting_function and not has_timeline:
            self.add_violation(
                rule_id='CERTIN_IR_003',
                severity='MEDIUM',
                category='incident_reporting',
                description="Incident reporting without 6-hour timeline documentation",
                file_path=file_path,
                fix_suggestion="Document and implement 6-hour reporting requirement"
            )
        
        return self.get_violations()
    
    def _check_incident_detection(self, content: str) -> bool:
        """Check for incident detection"""
        patterns = [
            r'incident.*detect',
            r'security.*event',
            r'intrusion.*detect',
            r'threat.*detect',
            r'anomaly.*detect',
            r'security.*monitor',
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)
    
    def _check_reporting_function(self, content: str) -> bool:
        """Check for reporting functions"""
        patterns = [
            r'report.*incident',
            r'notify.*cert',
            r'alert.*security',
            r'incident.*report',
            r'security.*report',
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)
    
    def _check_timeline_requirement(self, content: str) -> bool:
        """Check for 6-hour timeline"""
        patterns = [
            r'6.*hour',
            r'six.*hour',
            r'within.*6',
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)


class CERTInLogRetentionChecker(BaseComplianceChecker):
    """
    CERT-In: 180-Day Log Retention
    Verifies log retention configuration
    """
    
    def __init__(self):
        super().__init__("CERT-In Directions 2022 - Log Retention", "CERT-In")
        self.config_analyzer = ConfigAnalyzer()
    
    def check(self, file_path: str, content: str, file_type: str, context: Dict[str, Any]) -> List[Violation]:
        """Check log retention compliance"""
        self.clear_violations()
        
        if file_type in ['yaml', 'yml']:
            config = self.config_analyzer.parse_yaml(content)
        elif file_type == 'json':
            config = self.config_analyzer.parse_json(content)
        else:
            config = None
        
        if config:
            retention_days = self.config_analyzer.check_log_retention(config)
            
            if retention_days is None:
                self.add_violation(
                    rule_id='CERTIN_LR_001',
                    severity='HIGH',
                    category='log_retention',
                    description="Log retention period not configured",
                    file_path=file_path,
                    fix_suggestion="Configure log retention to at least 180 days"
                )
            elif retention_days < 180:
                self.add_violation(
                    rule_id='CERTIN_LR_002',
                    severity='HIGH',
                    category='log_retention',
                    description=f"Log retention period ({retention_days} days) is less than required 180 days",
                    file_path=file_path,
                    fix_suggestion="Increase log retention to at least 180 days"
                )
        else:
            # Check in code
            retention_days = self._extract_retention_from_code(content)
            if retention_days and retention_days < 180:
                self.add_violation(
                    rule_id='CERTIN_LR_003',
                    severity='HIGH',
                    category='log_retention',
                    description=f"Log retention ({retention_days} days) is less than required 180 days",
                    file_path=file_path,
                    fix_suggestion="Increase log retention to at least 180 days"
                )
        
        return self.get_violations()
    
    def _extract_retention_from_code(self, content: str) -> int:
        """Extract retention days from code"""
        patterns = [
            r'retention.*=\s*(\d+)',
            r'log.*retention.*=\s*(\d+)',
            r'max.*age.*=\s*(\d+)',
            r'keep.*days.*=\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    pass
        
        return None


class CERTInSecurityLoggingChecker(BaseComplianceChecker):
    """
    CERT-In: Security Event Logging
    Verifies comprehensive security logging
    """
    
    def __init__(self):
        super().__init__("CERT-In Directions 2022 - Security Logging", "CERT-In")
    
    def check(self, file_path: str, content: str, file_type: str, context: Dict[str, Any]) -> List[Violation]:
        """Check security logging compliance"""
        self.clear_violations()
        
        has_auth_logging = self._check_authentication_logging(content)
        has_access_logging = self._check_access_logging(content)
        has_audit_trail = self._check_audit_trail(content)
        has_error_logging = self._check_error_logging(content)
        
        if not has_auth_logging:
            self.add_violation(
                rule_id='CERTIN_SL_001',
                severity='HIGH',
                category='security_logging',
                description="Authentication events not being logged",
                file_path=file_path,
                fix_suggestion="Implement logging for all authentication attempts (success and failure)"
            )
        
        if not has_access_logging:
            self.add_violation(
                rule_id='CERTIN_SL_002',
                severity='MEDIUM',
                category='security_logging',
                description="Access control events not being logged",
                file_path=file_path,
                fix_suggestion="Implement logging for authorization and access control decisions"
            )
        
        if not has_audit_trail:
            self.add_violation(
                rule_id='CERTIN_SL_003',
                severity='MEDIUM',
                category='security_logging',
                description="No audit trail implementation found",
                file_path=file_path,
                fix_suggestion="Implement comprehensive audit trail for security-relevant actions"
            )
        
        if not has_error_logging:
            self.add_violation(
                rule_id='CERTIN_SL_004',
                severity='LOW',
                category='security_logging',
                description="Security errors may not be logged",
                file_path=file_path,
                fix_suggestion="Ensure all security-related errors are logged"
            )
        
        return self.get_violations()
    
    def _check_authentication_logging(self, content: str) -> bool:
        """Check for authentication logging"""
        patterns = [
            r'log.*login',
            r'log.*auth',
            r'log.*signin',
            r'logger.*auth',
            r'audit.*login',
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)
    
    def _check_access_logging(self, content: str) -> bool:
        """Check for access logging"""
        patterns = [
            r'log.*access',
            r'log.*permission',
            r'log.*authorization',
            r'audit.*access',
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)
    
    def _check_audit_trail(self, content: str) -> bool:
        """Check for audit trail"""
        patterns = [
            r'audit.*trail',
            r'audit.*log',
            r'activity.*log',
            r'user.*activity',
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)
    
    def _check_error_logging(self, content: str) -> bool:
        """Check for error logging"""
        patterns = [
            r'log.*error',
            r'logger\.error',
            r'console\.error',
            r'except.*log',
            r'catch.*log',
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)
