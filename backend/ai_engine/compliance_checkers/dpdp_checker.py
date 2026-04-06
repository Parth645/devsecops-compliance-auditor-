"""
DPDP Act 2023 Compliance Checkers
Digital Personal Data Protection Act compliance verification
"""

from typing import List, Dict, Any
import re
from .base_checker import BaseComplianceChecker, Violation
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from code_analyzers import TerraformAnalyzer, PythonAnalyzer, JavaScriptAnalyzer, ConfigAnalyzer
import logging

logger = logging.getLogger(__name__)


class DPDPDataLocalizationChecker(BaseComplianceChecker):
    """
    DPDP Act Article 8: Data Localization
    Verifies that personal data is stored within India
    """
    
    def __init__(self):
        super().__init__("DPDP Act 2023 - Data Localization", "DPDP")
        self.tf_analyzer = TerraformAnalyzer()
        self.py_analyzer = PythonAnalyzer()
        self.js_analyzer = JavaScriptAnalyzer()
        self.config_analyzer = ConfigAnalyzer()
    
    def check(self, file_path: str, content: str, file_type: str, context: Dict[str, Any]) -> List[Violation]:
        """Check data localization compliance"""
        self.clear_violations()
        
        if file_type in ['tf', 'terraform']:
            self._check_terraform(file_path, content)
        elif file_type == 'py':
            self._check_python(file_path, content)
        elif file_type in ['js', 'ts']:
            self._check_javascript(file_path, content)
        elif file_type in ['yaml', 'yml', 'json']:
            self._check_config(file_path, content, file_type)
        
        return self.get_violations()
    
    def _check_terraform(self, file_path: str, content: str):
        """Check Terraform files for data localization"""
        violations = self.tf_analyzer.check_data_localization(content)
        
        for violation in violations:
            self.add_violation(
                rule_id='DPDP_DL_001',
                severity='HIGH',
                category='data_localization',
                description=f"{violation['resource_type']} '{violation['resource_name']}' is in non-Indian region: {violation['region']}",
                file_path=file_path,
                fix_suggestion=violation['suggestion']
            )
    
    def _check_python(self, file_path: str, content: str):
        """Check Python code for data localization"""
        connections = self.py_analyzer.extract_database_connections(content)
        
        for conn in connections:
            host = conn.get('host', '')
            if host and not self._is_indian_host(host) and not conn.get('is_localhost'):
                self.add_violation(
                    rule_id='DPDP_DL_002',
                    severity='HIGH',
                    category='data_localization',
                    description=f"Database connection to non-Indian host: {host}",
                    file_path=file_path,
                    fix_suggestion="Use database servers located in India or verify host location"
                )
    
    def _check_javascript(self, file_path: str, content: str):
        """Check JavaScript code for data localization"""
        connections = self.js_analyzer.check_database_connections(content)
        
        for conn in connections:
            host = conn.get('host', '')
            if host and not self._is_indian_host(host) and not conn.get('is_localhost'):
                self.add_violation(
                    rule_id='DPDP_DL_003',
                    severity='HIGH',
                    category='data_localization',
                    description=f"Database connection to non-Indian host: {host}",
                    file_path=file_path,
                    fix_suggestion="Use database servers located in India"
                )
    
    def _check_config(self, file_path: str, content: str, file_type: str):
        """Check config files for data localization"""
        if file_type in ['yaml', 'yml']:
            config = self.config_analyzer.parse_yaml(content)
        else:
            config = self.config_analyzer.parse_json(content)
        
        if not config:
            return
        
        db_settings = self.config_analyzer.extract_database_settings(config)
        for db_key, db_config in db_settings.items():
            if isinstance(db_config, dict):
                host = db_config.get('host', db_config.get('hostname', ''))
                if host and not self._is_indian_host(str(host)):
                    self.add_violation(
                        rule_id='DPDP_DL_004',
                        severity='HIGH',
                        category='data_localization',
                        description=f"Database host in config may be outside India: {host}",
                        file_path=file_path,
                        fix_suggestion="Configure database to use Indian data centers"
                    )
    
    def _is_indian_host(self, host: str) -> bool:
        """Check if host is in India"""
        indian_indicators = [
            '.in', 'india', 'mumbai', 'delhi', 'bangalore', 'chennai', 'hyderabad',
            'ap-south', 'centralindia', 'southindia', 'asia-south'
        ]
        return any(indicator in host.lower() for indicator in indian_indicators)


class DPDPConsentChecker(BaseComplianceChecker):
    """
    DPDP Act Article 6: Consent Management
    Verifies proper consent logging and management
    """
    
    def __init__(self):
        super().__init__("DPDP Act 2023 - Consent Management", "DPDP")
        self.py_analyzer = PythonAnalyzer()
    
    def check(self, file_path: str, content: str, file_type: str, context: Dict[str, Any]) -> List[Violation]:
        """Check consent management compliance"""
        self.clear_violations()
        
        if file_type == 'py':
            self._check_python_consent(file_path, content)
        elif file_type in ['js', 'ts']:
            self._check_javascript_consent(file_path, content)
        
        return self.get_violations()
    
    def _check_python_consent(self, file_path: str, content: str):
        """Check Python code for consent logging"""
        consent_info = self.py_analyzer.check_consent_logging(content)
        
        # Check if collecting personal data
        personal_data_patterns = [
            r'(?:email|phone|address|ssn|aadhar|pan)',
            r'personal_data',
            r'user_data',
        ]
        
        collects_personal_data = any(
            re.search(pattern, content, re.IGNORECASE) 
            for pattern in personal_data_patterns
        )
        
        if collects_personal_data:
            if not consent_info['has_consent_field']:
                self.add_violation(
                    rule_id='DPDP_CM_001',
                    severity='HIGH',
                    category='consent_management',
                    description="Personal data collection without consent logging",
                    file_path=file_path,
                    fix_suggestion="Add consent field to track user consent"
                )
            
            if consent_info['has_consent_field'] and not consent_info['has_timestamp']:
                self.add_violation(
                    rule_id='DPDP_CM_002',
                    severity='MEDIUM',
                    category='consent_management',
                    description="Consent logging without timestamp",
                    file_path=file_path,
                    fix_suggestion="Add consent_timestamp field to record when consent was given"
                )
            
            if consent_info['has_consent_field'] and not consent_info['has_purpose']:
                self.add_violation(
                    rule_id='DPDP_CM_003',
                    severity='MEDIUM',
                    category='consent_management',
                    description="Consent logging without purpose specification",
                    file_path=file_path,
                    fix_suggestion="Add consent_purpose field to record why data is collected"
                )
    
    def _check_javascript_consent(self, file_path: str, content: str):
        """Check JavaScript code for consent logging"""
        # Check for personal data collection
        personal_data_patterns = [
            r'email|phone|address',
            r'personalData',
            r'userData',
        ]
        
        collects_personal_data = any(
            re.search(pattern, content, re.IGNORECASE) 
            for pattern in personal_data_patterns
        )
        
        has_consent = re.search(r'consent', content, re.IGNORECASE)
        
        if collects_personal_data and not has_consent:
            self.add_violation(
                rule_id='DPDP_CM_004',
                severity='HIGH',
                category='consent_management',
                description="Personal data collection without consent mechanism",
                file_path=file_path,
                fix_suggestion="Implement consent collection and logging"
            )


class DPDPBreachNotificationChecker(BaseComplianceChecker):
    """
    DPDP Act Article 8: Breach Notification
    Verifies 72-hour breach notification mechanisms
    """
    
    def __init__(self):
        super().__init__("DPDP Act 2023 - Breach Notification", "DPDP")
    
    def check(self, file_path: str, content: str, file_type: str, context: Dict[str, Any]) -> List[Violation]:
        """Check breach notification compliance"""
        self.clear_violations()
        
        # Check for breach detection and notification mechanisms
        has_breach_detection = self._check_breach_detection(content)
        has_notification = self._check_notification_mechanism(content)
        has_timeline = self._check_timeline_requirement(content)
        
        if not has_breach_detection:
            self.add_violation(
                rule_id='DPDP_BN_001',
                severity='HIGH',
                category='breach_notification',
                description="No breach detection mechanism found",
                file_path=file_path,
                fix_suggestion="Implement security monitoring and breach detection"
            )
        
        if has_breach_detection and not has_notification:
            self.add_violation(
                rule_id='DPDP_BN_002',
                severity='HIGH',
                category='breach_notification',
                description="Breach detection without notification mechanism",
                file_path=file_path,
                fix_suggestion="Implement breach notification function"
            )
        
        if has_notification and not has_timeline:
            self.add_violation(
                rule_id='DPDP_BN_003',
                severity='MEDIUM',
                category='breach_notification',
                description="Breach notification without 72-hour timeline documentation",
                file_path=file_path,
                fix_suggestion="Document and implement 72-hour notification requirement"
            )
        
        return self.get_violations()
    
    def _check_breach_detection(self, content: str) -> bool:
        """Check for breach detection mechanisms"""
        patterns = [
            r'breach.*detect',
            r'security.*incident',
            r'intrusion.*detect',
            r'anomaly.*detect',
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)
    
    def _check_notification_mechanism(self, content: str) -> bool:
        """Check for notification mechanisms"""
        patterns = [
            r'notify.*breach',
            r'breach.*notification',
            r'alert.*breach',
            r'report.*breach',
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)
    
    def _check_timeline_requirement(self, content: str) -> bool:
        """Check for 72-hour timeline"""
        patterns = [
            r'72.*hour',
            r'three.*day',
            r'3.*day',
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)


class DPDPDataRetentionChecker(BaseComplianceChecker):
    """
    DPDP Act Article 10: Data Retention
    Verifies data retention policies and deletion mechanisms
    """
    
    def __init__(self):
        super().__init__("DPDP Act 2023 - Data Retention", "DPDP")
        self.config_analyzer = ConfigAnalyzer()
    
    def check(self, file_path: str, content: str, file_type: str, context: Dict[str, Any]) -> List[Violation]:
        """Check data retention compliance"""
        self.clear_violations()
        
        has_retention_policy = self._check_retention_policy(content)
        has_deletion_mechanism = self._check_deletion_mechanism(content)
        has_cleanup_automation = self._check_cleanup_automation(content)
        
        if not has_retention_policy:
            self.add_violation(
                rule_id='DPDP_DR_001',
                severity='MEDIUM',
                category='data_retention',
                description="No data retention policy defined",
                file_path=file_path,
                fix_suggestion="Define and document data retention periods"
            )
        
        if not has_deletion_mechanism:
            self.add_violation(
                rule_id='DPDP_DR_002',
                severity='HIGH',
                category='data_retention',
                description="No data deletion mechanism found",
                file_path=file_path,
                fix_suggestion="Implement data deletion functions for expired data"
            )
        
        if has_deletion_mechanism and not has_cleanup_automation:
            self.add_violation(
                rule_id='DPDP_DR_003',
                severity='MEDIUM',
                category='data_retention',
                description="Manual deletion only - no automated cleanup",
                file_path=file_path,
                fix_suggestion="Implement automated cleanup jobs for expired data"
            )
        
        return self.get_violations()
    
    def _check_retention_policy(self, content: str) -> bool:
        """Check for retention policy"""
        patterns = [
            r'retention.*period',
            r'retention.*policy',
            r'data.*retention',
            r'keep.*days',
            r'expire.*after',
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)
    
    def _check_deletion_mechanism(self, content: str) -> bool:
        """Check for deletion mechanisms"""
        patterns = [
            r'delete.*user.*data',
            r'remove.*personal.*data',
            r'purge.*data',
            r'def.*delete',
            r'function.*delete',
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)
    
    def _check_cleanup_automation(self, content: str) -> bool:
        """Check for automated cleanup"""
        patterns = [
            r'cron',
            r'schedule',
            r'automated.*cleanup',
            r'periodic.*delete',
            r'celery.*task',
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns)
