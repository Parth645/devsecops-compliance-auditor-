"""
Base Compliance Checker
Foundation class for all compliance checkers
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Violation:
    """Represents a compliance violation"""
    rule_id: str
    regulation: str
    severity: str  # HIGH, MEDIUM, LOW
    category: str
    description: str
    file_path: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    fix_suggestion: Optional[str] = None
    confidence: float = 1.0
    matched_text: Optional[str] = None  # Text that matched the pattern (for context analysis)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert violation to dictionary"""
        return {
            'rule_id': self.rule_id,
            'regulation': self.regulation,
            'severity': self.severity,
            'category': self.category,
            'description': self.description,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'code_snippet': self.code_snippet,
            'fix_suggestion': self.fix_suggestion,
            'confidence': self.confidence,
            'matched_text': self.matched_text,
            'detected_at': datetime.now().isoformat()
        }


class BaseComplianceChecker:
    """Base class for all compliance checkers"""
    
    def __init__(self, regulation_name: str, regulation_code: str):
        """
        Initialize compliance checker
        
        Args:
            regulation_name: Full name of regulation (e.g., "DPDP Act 2023")
            regulation_code: Short code (e.g., "DPDP")
        """
        self.regulation_name = regulation_name
        self.regulation_code = regulation_code
        self.violations: List[Violation] = []
        
    def check(self, file_path: str, content: str, file_type: str, context: Dict[str, Any]) -> List[Violation]:
        """
        Main check method - to be overridden by subclasses
        
        Args:
            file_path: Path to file being checked
            content: File content
            file_type: Type of file (py, js, tf, yaml, etc.)
            context: Additional context (repo info, other files, etc.)
            
        Returns:
            List of violations found
        """
        raise NotImplementedError("Subclasses must implement check() method")
    
    def add_violation(self, rule_id: str, severity: str, category: str, 
                     description: str, file_path: str, line_number: Optional[int] = None,
                     code_snippet: Optional[str] = None, fix_suggestion: Optional[str] = None,
                     confidence: float = 1.0, matched_text: Optional[str] = None) -> Violation:
        """
        Helper method to create and add a violation
        
        Args:
            rule_id: Unique rule identifier
            severity: HIGH, MEDIUM, or LOW
            category: Category of violation
            description: Human-readable description
            file_path: Path to file with violation
            line_number: Line number (optional)
            code_snippet: Code snippet (optional)
            fix_suggestion: How to fix (optional)
            confidence: Confidence score 0-1 (optional)
            matched_text: Text that matched the pattern (optional)
            
        Returns:
            Created violation
        """
        violation = Violation(
            rule_id=rule_id,
            regulation=self.regulation_name,
            severity=severity,
            category=category,
            description=description,
            file_path=file_path,
            line_number=line_number,
            code_snippet=code_snippet,
            fix_suggestion=fix_suggestion,
            confidence=confidence,
            matched_text=matched_text
        )
        self.violations.append(violation)
        return violation
    
    def clear_violations(self):
        """Clear all violations"""
        self.violations = []
    
    def get_violations(self) -> List[Violation]:
        """Get all violations"""
        return self.violations
    
    def get_violations_dict(self) -> List[Dict[str, Any]]:
        """Get violations as dictionaries"""
        return [v.to_dict() for v in self.violations]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of violations"""
        severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        category_counts = {}
        
        for violation in self.violations:
            severity_counts[violation.severity] = severity_counts.get(violation.severity, 0) + 1
            category_counts[violation.category] = category_counts.get(violation.category, 0) + 1
        
        return {
            'regulation': self.regulation_name,
            'total_violations': len(self.violations),
            'severity_breakdown': severity_counts,
            'category_breakdown': category_counts
        }
