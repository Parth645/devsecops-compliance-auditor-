"""
Test Full Compliance Pipeline with Groq AI
Tests: Semgrep → AI Verification → Results
"""

import asyncio
import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

sys.path.insert(0, str(Path(__file__).parent))

from ai_engine.compliance_analyzer import ComplianceAnalyzer

async def test_full_pipeline():
    print("="*70)
    print("FULL COMPLIANCE PIPELINE TEST")
    print("="*70)
    
    # Step 1: Check environment
    print("\n[STEP 1] Checking environment...")
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        print(f"  OK GROQ_API_KEY is set ({groq_key[:10]}...)")
    else:
        print(f"  WARNING GROQ_API_KEY not set - AI features will be limited")
    
    # Step 2: Check rules file
    print("\n[STEP 2] Checking Semgrep rules...")
    rules_path = Path("policies/indian_compliance_rules.yaml")
    if rules_path.exists():
        import yaml
        with open(rules_path) as f:
            rules = yaml.safe_load(f)
        rule_count = len(rules.get('rules', []))
        print(f"  ✓ Rules file: {rules_path}")
        print(f"  ✓ Rules count: {rule_count}")
    else:
        print(f"  ✗ Rules file not found!")
        return
    
    # Step 3: Initialize analyzer
    print("\n[STEP 3] Initializing ComplianceAnalyzer...")
    try:
        analyzer = ComplianceAnalyzer()
        print(f"  ✓ Analyzer initialized")
        print(f"  ✓ Semgrep detector: {'Available' if analyzer.semgrep_detector else 'Not available'}")
        print(f"  ✓ AI verifier: {'Available' if analyzer.semgrep_verifier else 'Not available'}")
        print(f"  ✓ Business logic scanner: {'Available' if analyzer.business_logic_scanner else 'Not available'}")
    except Exception as e:
        print(f"  ✗ Failed to initialize: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 4: Test on small directory
    print("\n[STEP 4] Running scan on test file...")
    test_dir = Path(".").resolve()
    print(f"  Scanning: {test_dir}")
    
    try:
        result = await analyzer.analyze_repository_for_compliance(
            repo_path=str(test_dir),
            custom_policy_text=None
        )
        
        print("\n[STEP 5] Pipeline Results:")
        print(f"  Status: {result.get('status', 'unknown')}")
        print(f"  Scan duration: {result.get('scan_duration', 0):.2f}s")
        
        # Semgrep results
        semgrep_findings = result.get('semgrep_findings', 0)
        print(f"\n  Semgrep Stage:")
        print(f"    Raw findings: {semgrep_findings}")
        
        # AI verification results
        verified_findings = result.get('verified_findings', 0)
        false_positives = semgrep_findings - verified_findings if semgrep_findings > 0 else 0
        print(f"\n  AI Verification Stage:")
        print(f"    Verified findings: {verified_findings}")
        print(f"    False positives filtered: {false_positives}")
        
        # Final violations
        violations = result.get('violations', [])
        print(f"\n  Final Results:")
        print(f"    Total violations: {len(violations)}")
        
        if violations:
            print(f"\n[STEP 6] Sample Violations:")
            
            # Group by severity
            by_severity = {}
            for v in violations:
                sev = v.get('severity', 'UNKNOWN')
                by_severity[sev] = by_severity.get(sev, 0) + 1
            
            print(f"  Severity breakdown:")
            for sev, count in sorted(by_severity.items(), key=lambda x: x[1], reverse=True):
                print(f"    {sev}: {count}")
            
            # Show first 5
            print(f"\n  Top violations:")
            for i, v in enumerate(violations[:5], 1):
                print(f"    {i}. {v.get('rule_id', 'unknown')}")
                print(f"       File: {v.get('file_path', 'unknown')}")
                print(f"       Line: {v.get('line_number', '?')}")
                print(f"       Severity: {v.get('severity', 'UNKNOWN')}")
                if v.get('ai_verified'):
                    print(f"       ✓ AI Verified")
        else:
            print(f"\n[STEP 6] No violations found")
            print(f"  This could mean:")
            print(f"    1. Code is compliant")
            print(f"    2. All findings were false positives")
            print(f"    3. Rules didn't match patterns")
        
        # Pipeline stages summary
        print(f"\n[STEP 7] Pipeline Stages Summary:")
        stages = [
            ("Repo Profiling", result.get('repo_profile_completed', False)),
            ("Semgrep Scan", result.get('semgrep_completed', False)),
            ("AI Verification", result.get('ai_verification_completed', False)),
            ("Business Logic", result.get('business_logic_completed', False)),
            ("Framework Mapping", result.get('framework_mapping_completed', False)),
        ]
        
        for stage_name, completed in stages:
            status = "✓" if completed else "⚠"
            print(f"    {status} {stage_name}")
        
        print("\n" + "="*70)
        print("PIPELINE TEST COMPLETE")
        print("="*70)
        
        # Final assessment
        if len(violations) > 0:
            print(f"\n✅ SUCCESS: Found {len(violations)} compliance violations")
            print(f"   Semgrep is working and AI verification is active")
        else:
            print(f"\n⚠ WARNING: No violations found")
            print(f"   Check if test files have actual violations")
        
        return result
        
    except Exception as e:
        print(f"\n✗ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_full_pipeline())
    
    if result:
        print(f"\n📊 Final Stats:")
        print(f"   Violations: {len(result.get('violations', []))}")
        print(f"   Scan time: {result.get('scan_duration', 0):.2f}s")
        print(f"   Compliance score: {result.get('compliance_score', 0):.1%}")
