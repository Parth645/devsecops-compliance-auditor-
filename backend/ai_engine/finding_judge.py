"""
The Judge - Stage 4 Validator
AI agent that 'thinks' and verifies if a finding is a True Positive.
Reduces false positives by analyzing context and intent.
"""

import json
import os
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class Finding:
    """Represents a security/compliance finding."""
    file_path: str
    line_number: int
    finding_type: str  # e.g., "hardcoded_secret", "pii_exposure"
    severity: str  # "critical", "high", "medium", "low"
    description: str
    code_snippet: str
    rule_id: str
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class JudgmentResult:
    """Result of The Judge's analysis."""
    is_true_positive: bool
    confidence: float  # 0.0 to 1.0
    reasoning: str
    recommended_action: str
    original_finding: Finding
    
    def to_dict(self) -> dict:
        result = asdict(self)
        result['original_finding'] = self.original_finding.to_dict()
        return result


class FindingJudge:
    """
    AI agent that analyzes findings to determine if they are true positives.
    Uses context-aware heuristics and pattern matching.
    """
    
    def __init__(self, knowledge_base_path: str = "backend/knowledge/safe_patterns.json"):
        """
        Initialize The Judge with knowledge base.
        
        Args:
            knowledge_base_path: Path to safe patterns JSON
        """
        self.safe_libs: List[str] = []
        self.test_indicators: List[str] = []
        self._load_knowledge_base(knowledge_base_path)
        
        # Patterns for different types of false positives
        self.false_positive_patterns = {
            'test_data': [
                r'000+',  # All zeros
                r'111+',  # All ones
                r'dummy',
                r'example',
                r'sample',
                r'placeholder',
                r'0x0+',  # Ethereum zero address
            ],
            'comments': [
                r'^\s*//',  # Single line comment
                r'^\s*/\*',  # Multi-line comment start
                r'^\s*\*',  # Multi-line comment middle
                r'^\s*#',  # Python/shell comment
            ],
            'documentation': [
                r'@example',
                r'@param',
                r'@returns',
                r'TODO',
                r'FIXME',
                r'NOTE',
            ]
        }
    
    def _load_knowledge_base(self, kb_path: str) -> None:
        """Load safe patterns from knowledge base."""
        try:
            if os.path.exists(kb_path):
                with open(kb_path, 'r', encoding='utf-8') as f:
                    kb = json.load(f)
                    self.safe_libs = kb.get('safe_libs', [])
                    self.test_indicators = kb.get('test_indicators', [])
        except Exception as e:
            print(f"Warning: Could not load knowledge base: {e}")
            self._set_defaults()
    
    def _set_defaults(self) -> None:
        """Set default patterns if knowledge base unavailable."""
        self.safe_libs = ['crypto-js', 'web3', 'ethers', 'bcrypt']
        self.test_indicators = ['describe', 'it', 'mock', 'stub', '000000', 'dummy']
    
    def judge(self, finding: Finding, file_content: Optional[str] = None) -> JudgmentResult:
        """
        Analyze a finding to determine if it's a true positive.
        
        Args:
            finding: The security/compliance finding to analyze
            file_content: Optional full file content for context analysis
            
        Returns:
            JudgmentResult with verdict and reasoning
        """
        # Run multiple checks
        checks = [
            self._check_test_data(finding),
            self._check_safe_library(finding),
            self._check_comment_or_doc(finding),
            self._check_test_file(finding),
            self._check_context(finding, file_content),
        ]
        
        # Aggregate results
        false_positive_votes = sum(1 for check in checks if not check['is_true_positive'])
        total_checks = len(checks)
        
        # Collect reasoning from all checks
        reasoning_parts = [check['reasoning'] for check in checks if check['reasoning']]
        
        # Determine verdict - if majority of checks say false positive, it's false positive
        is_true_positive = false_positive_votes <= (total_checks / 2)
        
        # Calculate confidence based on vote margin
        vote_margin = abs(false_positive_votes - (total_checks - false_positive_votes))
        confidence = vote_margin / total_checks
        
        # Override: If 2+ checks indicate false positive, mark as false positive
        if false_positive_votes >= 2:
            is_true_positive = False
            confidence = min(0.9, confidence + 0.2)  # Boost confidence
        
        # Generate recommendation
        if is_true_positive:
            recommended_action = self._get_remediation_action(finding)
        else:
            recommended_action = "Mark as false positive and suppress"
        
        return JudgmentResult(
            is_true_positive=is_true_positive,
            confidence=confidence,
            reasoning=" | ".join(reasoning_parts) if reasoning_parts else "Standard analysis",
            recommended_action=recommended_action,
            original_finding=finding
        )
    
    def _check_test_data(self, finding: Finding) -> Dict:
        """Check if finding is in test data."""
        code = finding.code_snippet.lower()
        
        # Check for test indicators
        for indicator in self.test_indicators:
            if indicator.lower() in code:
                return {
                    'is_true_positive': False,
                    'reasoning': f"Contains test indicator: '{indicator}'"
                }
        
        # Check for test data patterns
        for pattern in self.false_positive_patterns['test_data']:
            if re.search(pattern, code, re.IGNORECASE):
                return {
                    'is_true_positive': False,
                    'reasoning': f"Matches test data pattern: {pattern}"
                }
        
        return {'is_true_positive': True, 'reasoning': ''}
    
    def _check_safe_library(self, finding: Finding) -> Dict:
        """Check if finding is from a safe library usage."""
        code = finding.code_snippet.lower()
        file_path = finding.file_path.lower()
        
        # Check if it's importing/using a safe library
        for lib in self.safe_libs:
            lib_lower = lib.lower()
            if lib_lower in code or lib_lower in file_path:
                # Check if it's an import statement
                if any(keyword in code for keyword in ['import', 'require', 'from']):
                    return {
                        'is_true_positive': False,
                        'reasoning': f"Safe library usage: '{lib}'"
                    }
        
        return {'is_true_positive': True, 'reasoning': ''}
    
    def _check_comment_or_doc(self, finding: Finding) -> Dict:
        """Check if finding is in a comment or documentation."""
        code = finding.code_snippet.strip()
        
        # Check comment patterns
        for pattern in self.false_positive_patterns['comments']:
            if re.match(pattern, code):
                return {
                    'is_true_positive': False,
                    'reasoning': "Finding is in a comment"
                }
        
        # Check documentation patterns
        for pattern in self.false_positive_patterns['documentation']:
            if re.search(pattern, code, re.IGNORECASE):
                return {
                    'is_true_positive': False,
                    'reasoning': "Finding is in documentation"
                }
        
        return {'is_true_positive': True, 'reasoning': ''}
    
    def _check_test_file(self, finding: Finding) -> Dict:
        """Check if finding is in a test file."""
        file_path = finding.file_path.lower()
        
        test_indicators = [
            'test', 'spec', '__tests__', 'tests/',
            'test_', '_test.', '.test.', '.spec.'
        ]
        
        for indicator in test_indicators:
            if indicator in file_path:
                return {
                    'is_true_positive': False,
                    'reasoning': f"File is a test file: contains '{indicator}'"
                }
        
        return {'is_true_positive': True, 'reasoning': ''}
    
    def _check_context(self, finding: Finding, file_content: Optional[str]) -> Dict:
        """
        Analyze surrounding context if file content is available.
        """
        if not file_content:
            return {'is_true_positive': True, 'reasoning': ''}
        
        # Get lines around the finding
        lines = file_content.split('\n')
        line_idx = finding.line_number - 1
        
        if line_idx < 0 or line_idx >= len(lines):
            return {'is_true_positive': True, 'reasoning': ''}
        
        # Check 3 lines before and after for context
        start = max(0, line_idx - 3)
        end = min(len(lines), line_idx + 4)
        context = '\n'.join(lines[start:end]).lower()
        
        # Context-based checks
        if 'example' in context or 'demo' in context:
            return {
                'is_true_positive': False,
                'reasoning': "Surrounding context indicates example/demo code"
            }
        
        if 'test' in context or 'mock' in context:
            return {
                'is_true_positive': False,
                'reasoning': "Surrounding context indicates test code"
            }
        
        return {'is_true_positive': True, 'reasoning': ''}
    
    def _get_remediation_action(self, finding: Finding) -> str:
        """Generate remediation recommendation based on finding type."""
        remediation_map = {
            'hardcoded_secret': "Move secret to environment variables or secure vault",
            'pii_exposure': "Implement data masking and encryption",
            'insecure_crypto': "Use approved cryptographic algorithms (AES-256, RSA-2048+)",
            'sql_injection': "Use parameterized queries or ORM",
            'xss_vulnerability': "Implement input validation and output encoding",
            'weak_password': "Enforce strong password policy (min 12 chars, complexity)",
            'missing_encryption': "Enable encryption for data at rest and in transit",
        }
        
        return remediation_map.get(
            finding.finding_type,
            "Review and remediate according to security best practices"
        )
    
    def batch_judge(self, findings: List[Finding], 
                   file_contents: Optional[Dict[str, str]] = None) -> List[JudgmentResult]:
        """
        Judge multiple findings in batch.
        
        Args:
            findings: List of findings to judge
            file_contents: Optional dict mapping file_path to file content
            
        Returns:
            List of judgment results
        """
        results = []
        
        for finding in findings:
            file_content = None
            if file_contents and finding.file_path in file_contents:
                file_content = file_contents[finding.file_path]
            
            result = self.judge(finding, file_content)
            results.append(result)
        
        return results
    
    def get_judgment_stats(self, results: List[JudgmentResult]) -> Dict:
        """Get statistics from judgment results."""
        if not results:
            return {
                'total': 0,
                'true_positives': 0,
                'false_positives': 0,
                'avg_confidence': 0.0,
                'false_positive_rate': '0%'
            }
        
        true_positives = sum(1 for r in results if r.is_true_positive)
        false_positives = len(results) - true_positives
        avg_confidence = sum(r.confidence for r in results) / len(results)
        
        return {
            'total': len(results),
            'true_positives': true_positives,
            'false_positives': false_positives,
            'avg_confidence': f"{avg_confidence:.2f}",
            'false_positive_rate': f"{(false_positives / len(results) * 100):.1f}%"
        }


if __name__ == "__main__":
    # Test The Judge
    judge = FindingJudge()
    
    # Create test findings
    test_findings = [
        Finding(
            file_path="repo/src/js/web3.min.js",
            line_number=1,
            finding_type="hardcoded_secret",
            severity="high",
            description="Potential hardcoded API key",
            code_snippet="const key = '0x0000000000000000000000000000000000000000';",
            rule_id="SEC001"
        ),
        Finding(
            file_path="backend/main.py",
            line_number=45,
            finding_type="hardcoded_secret",
            severity="critical",
            description="Hardcoded database password",
            code_snippet="db_password = 'MySecretP@ssw0rd123'",
            rule_id="SEC001"
        ),
        Finding(
            file_path="tests/test_auth.py",
            line_number=10,
            finding_type="hardcoded_secret",
            severity="high",
            description="Hardcoded test credential",
            code_snippet="mock_token = 'dummy_token_12345'",
            rule_id="SEC001"
        ),
        Finding(
            file_path="src/utils.js",
            line_number=23,
            finding_type="pii_exposure",
            severity="medium",
            description="Email address in code",
            code_snippet="// Example: user@example.com",
            rule_id="PII002"
        ),
    ]
    
    print("Testing The Judge\n" + "="*70)
    
    results = judge.batch_judge(test_findings)
    
    for i, result in enumerate(results, 1):
        print(f"\nFinding #{i}: {result.original_finding.file_path}")
        print(f"Type: {result.original_finding.finding_type}")
        print(f"Code: {result.original_finding.code_snippet}")
        print(f"Verdict: {'✅ TRUE POSITIVE' if result.is_true_positive else '❌ FALSE POSITIVE'}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Reasoning: {result.reasoning}")
        print(f"Action: {result.recommended_action}")
        print("-" * 70)
    
    # Print statistics
    stats = judge.get_judgment_stats(results)
    print(f"\nJudgment Statistics:")
    print(f"Total Findings: {stats['total']}")
    print(f"True Positives: {stats['true_positives']}")
    print(f"False Positives: {stats['false_positives']}")
    print(f"False Positive Rate: {stats['false_positive_rate']}")
    print(f"Average Confidence: {stats['avg_confidence']}")
