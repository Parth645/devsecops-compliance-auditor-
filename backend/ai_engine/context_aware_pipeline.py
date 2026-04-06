"""
Context-Aware Compliance Pipeline
Integrates The Bouncer (file filter) and The Judge (finding validator)
to reduce false positives in compliance scanning.
"""

import os
from typing import List, Dict, Tuple
from pathlib import Path

from file_bouncer import FileBouncer
from finding_judge import FindingJudge, Finding, JudgmentResult


class ContextAwarePipeline:
    """
    Main pipeline that orchestrates context-aware compliance scanning.
    
    Pipeline Stages:
    1. File Discovery - Find all files in repository
    2. The Bouncer - Filter out vendor/library files
    3. Code Analysis - Scan allowed files for issues
    4. The Judge - Validate findings to remove false positives
    5. Report Generation - Create final compliance report
    """
    
    def __init__(self, knowledge_base_path: str = "backend/knowledge/safe_patterns.json"):
        """
        Initialize the context-aware pipeline.
        
        Args:
            knowledge_base_path: Path to knowledge base JSON
        """
        self.bouncer = FileBouncer(knowledge_base_path)
        self.judge = FindingJudge(knowledge_base_path)
        
        self.stats = {
            'total_files_discovered': 0,
            'files_blocked_by_bouncer': 0,
            'files_scanned': 0,
            'raw_findings': 0,
            'true_positives': 0,
            'false_positives_filtered': 0,
        }
    
    def filter_files(self, file_paths: List[str]) -> Tuple[List[str], List[str]]:
        """
        Stage 2: Apply The Bouncer to filter files.
        
        Args:
            file_paths: List of all discovered files
            
        Returns:
            Tuple of (allowed_files, blocked_files)
        """
        self.stats['total_files_discovered'] = len(file_paths)
        
        allowed, blocked = self.bouncer.filter_files(file_paths)
        
        self.stats['files_blocked_by_bouncer'] = len(blocked)
        self.stats['files_scanned'] = len(allowed)
        
        return allowed, blocked
    
    def validate_findings(self, findings: List[Finding], 
                         file_contents: Dict[str, str] = None) -> Tuple[List[Finding], List[Finding]]:
        """
        Stage 4: Apply The Judge to validate findings.
        
        Args:
            findings: List of raw findings from code analysis
            file_contents: Optional dict of file_path -> content for context
            
        Returns:
            Tuple of (true_positives, false_positives)
        """
        self.stats['raw_findings'] = len(findings)
        
        # Judge all findings
        judgments = self.judge.batch_judge(findings, file_contents)
        
        # Separate true positives from false positives
        true_positives = []
        false_positives = []
        
        for judgment in judgments:
            if judgment.is_true_positive:
                true_positives.append(judgment.original_finding)
            else:
                false_positives.append(judgment.original_finding)
        
        self.stats['true_positives'] = len(true_positives)
        self.stats['false_positives_filtered'] = len(false_positives)
        
        return true_positives, false_positives
    
    def get_pipeline_stats(self) -> Dict:
        """Get statistics about the pipeline execution."""
        if self.stats['total_files_discovered'] > 0:
            block_rate = (self.stats['files_blocked_by_bouncer'] / 
                         self.stats['total_files_discovered'] * 100)
        else:
            block_rate = 0
        
        if self.stats['raw_findings'] > 0:
            fp_reduction = (self.stats['false_positives_filtered'] / 
                           self.stats['raw_findings'] * 100)
        else:
            fp_reduction = 0
        
        return {
            **self.stats,
            'bouncer_block_rate': f"{block_rate:.1f}%",
            'false_positive_reduction': f"{fp_reduction:.1f}%",
        }
    
    def generate_report(self, true_positives: List[Finding], 
                       false_positives: List[Finding],
                       blocked_files: List[str]) -> Dict:
        """
        Stage 5: Generate comprehensive compliance report.
        
        Args:
            true_positives: Validated findings
            false_positives: Filtered out findings
            blocked_files: Files blocked by bouncer
            
        Returns:
            Report dictionary
        """
        # Group findings by severity
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for finding in true_positives:
            severity = finding.severity.lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Group by finding type
        type_counts = {}
        for finding in true_positives:
            type_counts[finding.finding_type] = type_counts.get(finding.finding_type, 0) + 1
        
        report = {
            'summary': {
                'total_true_positives': len(true_positives),
                'total_false_positives_filtered': len(false_positives),
                'files_scanned': self.stats['files_scanned'],
                'files_blocked': self.stats['files_blocked_by_bouncer'],
                'severity_breakdown': severity_counts,
                'finding_types': type_counts,
            },
            'pipeline_performance': self.get_pipeline_stats(),
            'true_positives': [f.to_dict() for f in true_positives],
            'false_positives_sample': [f.to_dict() for f in false_positives[:5]],
            'blocked_files_sample': blocked_files[:10],
        }
        
        return report


def create_sample_findings() -> List[Finding]:
    """Create sample findings for testing."""
    return [
        Finding(
            file_path="backend/main.py",
            line_number=45,
            finding_type="hardcoded_secret",
            severity="critical",
            description="Hardcoded database password detected",
            code_snippet="DATABASE_URL = 'postgresql://user:MyP@ssw0rd@localhost/db'",
            rule_id="DPDP-SEC-001"
        ),
        Finding(
            file_path="repo/src/js/web3.min.js",
            line_number=1,
            finding_type="hardcoded_secret",
            severity="high",
            description="Potential API key in minified library",
            code_snippet="const addr='0x0000000000000000000000000000000000000000'",
            rule_id="DPDP-SEC-001"
        ),
        Finding(
            file_path="tests/test_auth.py",
            line_number=15,
            finding_type="hardcoded_secret",
            severity="high",
            description="Hardcoded test credential",
            code_snippet="test_token = 'dummy_test_token_12345'",
            rule_id="DPDP-SEC-001"
        ),
        Finding(
            file_path="backend/api/users.py",
            line_number=78,
            finding_type="pii_exposure",
            severity="high",
            description="PII data logged without masking",
            code_snippet="logger.info(f'User email: {user.email}')",
            rule_id="DPDP-PII-002"
        ),
        Finding(
            file_path="docs/api_examples.md",
            line_number=23,
            finding_type="pii_exposure",
            severity="medium",
            description="Email in documentation",
            code_snippet="// Example: contact@example.com",
            rule_id="DPDP-PII-002"
        ),
    ]


if __name__ == "__main__":
    print("Context-Aware Compliance Pipeline Demo")
    print("=" * 70)
    
    # Initialize pipeline
    pipeline = ContextAwarePipeline()
    
    # Stage 1: File Discovery (simulated)
    all_files = [
        "backend/main.py",
        "backend/api/users.py",
        "tests/test_auth.py",
        "node_modules/web3/index.js",
        "repo/src/js/web3.min.js",
        "venv/lib/site-packages/requests/__init__.py",
        "docs/api_examples.md",
        "package-lock.json",
        "frontend/src/App.js",
    ]
    
    print(f"\n📁 Stage 1: File Discovery")
    print(f"   Discovered {len(all_files)} files")
    
    # Stage 2: The Bouncer
    print(f"\n🚪 Stage 2: The Bouncer (File Filtering)")
    allowed_files, blocked_files = pipeline.filter_files(all_files)
    print(f"   ✅ Allowed: {len(allowed_files)} files")
    print(f"   🚫 Blocked: {len(blocked_files)} files")
    for blocked in blocked_files:
        print(f"      - {blocked}")
    
    # Stage 3: Code Analysis (simulated)
    print(f"\n🔍 Stage 3: Code Analysis")
    raw_findings = create_sample_findings()
    print(f"   Found {len(raw_findings)} potential issues")
    
    # Stage 4: The Judge
    print(f"\n⚖️  Stage 4: The Judge (Finding Validation)")
    true_positives, false_positives = pipeline.validate_findings(raw_findings)
    print(f"   ✅ True Positives: {len(true_positives)}")
    print(f"   ❌ False Positives Filtered: {len(false_positives)}")
    
    print(f"\n   False Positives Removed:")
    for fp in false_positives:
        print(f"      - {fp.file_path}:{fp.line_number} - {fp.description}")
    
    # Stage 5: Report Generation
    print(f"\n📊 Stage 5: Report Generation")
    report = pipeline.generate_report(true_positives, false_positives, blocked_files)
    
    print(f"\n{'='*70}")
    print(f"FINAL COMPLIANCE REPORT")
    print(f"{'='*70}")
    print(f"\n📈 Summary:")
    print(f"   Total Files Discovered: {report['pipeline_performance']['total_files_discovered']}")
    print(f"   Files Blocked by Bouncer: {report['pipeline_performance']['files_blocked_by_bouncer']} "
          f"({report['pipeline_performance']['bouncer_block_rate']})")
    print(f"   Files Scanned: {report['pipeline_performance']['files_scanned']}")
    print(f"   Raw Findings: {report['pipeline_performance']['raw_findings']}")
    print(f"   False Positives Filtered: {report['pipeline_performance']['false_positives_filtered']} "
          f"({report['pipeline_performance']['false_positive_reduction']})")
    print(f"   ⚠️  True Positives: {report['summary']['total_true_positives']}")
    
    print(f"\n🎯 Severity Breakdown:")
    for severity, count in report['summary']['severity_breakdown'].items():
        if count > 0:
            print(f"   {severity.upper()}: {count}")
    
    print(f"\n🔍 Finding Types:")
    for finding_type, count in report['summary']['finding_types'].items():
        print(f"   {finding_type}: {count}")
    
    print(f"\n✅ True Positive Findings:")
    for i, finding in enumerate(true_positives, 1):
        print(f"\n   {i}. [{finding.severity.upper()}] {finding.file_path}:{finding.line_number}")
        print(f"      Type: {finding.finding_type}")
        print(f"      Description: {finding.description}")
        print(f"      Code: {finding.code_snippet}")
    
    print(f"\n{'='*70}")
    print(f"✨ Pipeline successfully reduced false positives by "
          f"{report['pipeline_performance']['false_positive_reduction']}!")
