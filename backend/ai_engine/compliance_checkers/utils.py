"""
Utility functions for compliance checkers
"""

from typing import List, Dict, Any
from .base_checker import Violation
import logging

logger = logging.getLogger(__name__)


def get_all_checkers():
    """Get instances of all compliance checkers"""
    from .dpdp_checker import (
        DPDPDataLocalizationChecker,
        DPDPConsentChecker,
        DPDPBreachNotificationChecker,
        DPDPDataRetentionChecker
    )
    from .certin_checker import (
        CERTInIncidentReportingChecker,
        CERTInLogRetentionChecker,
        CERTInSecurityLoggingChecker
    )
    from .rbi_checker import (
        RBIEncryptionChecker,
        RBIAccessControlChecker,
        RBIAuditTrailChecker
    )
    
    return [
        # DPDP Checkers
        DPDPDataLocalizationChecker(),
        DPDPConsentChecker(),
        DPDPBreachNotificationChecker(),
        DPDPDataRetentionChecker(),
        # CERT-In Checkers
        CERTInIncidentReportingChecker(),
        CERTInLogRetentionChecker(),
        CERTInSecurityLoggingChecker(),
        # RBI Checkers
        RBIEncryptionChecker(),
        RBIAccessControlChecker(),
        RBIAuditTrailChecker(),
    ]


def aggregate_violations(checkers: List) -> Dict[str, Any]:
    """Aggregate violations from multiple checkers"""
    all_violations = []
    
    for checker in checkers:
        all_violations.extend(checker.get_violations())
    
    # Group by severity
    severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    for violation in all_violations:
        severity_counts[violation.severity] = severity_counts.get(violation.severity, 0) + 1
    
    # Group by regulation
    regulation_counts = {}
    for violation in all_violations:
        reg = violation.regulation
        regulation_counts[reg] = regulation_counts.get(reg, 0) + 1
    
    # Group by category
    category_counts = {}
    for violation in all_violations:
        cat = violation.category
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    return {
        'total_violations': len(all_violations),
        'violations': [v.to_dict() for v in all_violations],
        'severity_breakdown': severity_counts,
        'regulation_breakdown': regulation_counts,
        'category_breakdown': category_counts
    }


def filter_violations_by_severity(violations: List[Violation], min_severity: str = 'LOW') -> List[Violation]:
    """Filter violations by minimum severity"""
    severity_order = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
    min_level = severity_order.get(min_severity, 0)
    
    return [v for v in violations if severity_order.get(v.severity, 0) >= min_level]


def filter_violations_by_regulation(violations: List[Violation], regulation: str) -> List[Violation]:
    """Filter violations by regulation"""
    return [v for v in violations if regulation.lower() in v.regulation.lower()]


def generate_compliance_report(checkers: List) -> str:
    """Generate human-readable compliance report"""
    report = []
    report.append("=" * 80)
    report.append("INDIAN COMPLIANCE AUDIT REPORT")
    report.append("=" * 80)
    report.append("")
    
    aggregated = aggregate_violations(checkers)
    
    report.append(f"Total Violations: {aggregated['total_violations']}")
    report.append("")
    
    report.append("SEVERITY BREAKDOWN:")
    for severity, count in aggregated['severity_breakdown'].items():
        report.append(f"  {severity}: {count}")
    report.append("")
    
    report.append("REGULATION BREAKDOWN:")
    for regulation, count in aggregated['regulation_breakdown'].items():
        report.append(f"  {regulation}: {count}")
    report.append("")
    
    report.append("CATEGORY BREAKDOWN:")
    for category, count in aggregated['category_breakdown'].items():
        report.append(f"  {category}: {count}")
    report.append("")
    
    # High severity violations
    high_violations = [v for v in aggregated['violations'] if v['severity'] == 'HIGH']
    if high_violations:
        report.append("HIGH SEVERITY VIOLATIONS:")
        for i, violation in enumerate(high_violations[:10], 1):
            report.append(f"\n{i}. {violation['description']}")
            report.append(f"   File: {violation['file_path']}")
            report.append(f"   Rule: {violation['rule_id']}")
            report.append(f"   Fix: {violation['fix_suggestion']}")
    
    report.append("")
    report.append("=" * 80)
    
    return "\n".join(report)
