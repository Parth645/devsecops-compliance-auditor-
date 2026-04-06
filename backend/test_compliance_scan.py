"""
Test Compliance Scanning End-to-End
Verifies that Semgrep rules are loaded and scanning works
"""

import asyncio
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ai_engine.compliance_analyzer import ComplianceAnalyzer

async def test_scan():
    print("="*70)
    print("COMPLIANCE SCAN END-TO-END TEST")
    print("="*70)
    
    # Step 1: Check rules file
    print("\n[STEP 1] Checking rules file...")
    rules_path = Path("policies/indian_compliance_rules.yaml")
    print(f"  Path: {rules_path.resolve()}")
    print(f"  Exists: {rules_path.exists()}")
    
    if rules_path.exists():
        import yaml
        try:
            with open(rules_path) as f:
                rules = yaml.safe_load(f)
            rule_count = len(rules.get('rules', []))
            print(f"  ✓ Rules count: {rule_count}")
            
            # Show first 3 rule IDs
            rule_ids = [r.get('id') for r in rules.get('rules', [])[:3]]
            print(f"  Sample rules: {', '.join(rule_ids)}")
        except Exception as e:
            print(f"  ✗ Error reading rules: {e}")
            return
    else:
        print(f"  ✗ Rules file not found!")
        return
    
    # Step 2: Initialize analyzer
    print(f"\n[STEP 2] Initializing ComplianceAnalyzer...")
    try:
        analyzer = ComplianceAnalyzer()
        print(f"  ✓ Analyzer initialized")
    except Exception as e:
        print(f"  ✗ Failed to initialize: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Check test repository
    print(f"\n[STEP 3] Checking test repository...")
    test_repo = Path("../repo").resolve()
    print(f"  Path: {test_repo}")
    print(f"  Exists: {test_repo.exists()}")
    
    if not test_repo.exists():
        print(f"  ⚠ Test repo not found, using current directory")
        test_repo = Path(".").resolve()
    
    # Count files in repo
    code_files = list(test_repo.rglob("*.js")) + list(test_repo.rglob("*.py"))
    print(f"  Code files found: {len(code_files)}")
    
    # Step 4: Run scan
    print(f"\n[STEP 4] Running compliance scan...")
    print(f"  This may take 1-2 minutes...")
    
    try:
        result = await analyzer.analyze_repository_for_compliance(
            repo_path=str(test_repo),
            custom_policy_text=None
        )
        
        print(f"\n[STEP 5] Scan Results:")
        print(f"  Status: {result.get('status', 'unknown')}")
        print(f"  Violations found: {len(result.get('violations', []))}")
        print(f"  Scan duration: {result.get('scan_duration', 0):.2f}s")
        
        # Show violation breakdown
        violations = result.get('violations', [])
        if violations:
            print(f"\n[STEP 6] Violation Details:")
            
            # Group by severity
            by_severity = {}
            for v in violations:
                sev = v.get('severity', 'UNKNOWN')
                by_severity[sev] = by_severity.get(sev, 0) + 1
            
            print(f"  Severity breakdown:")
            for sev, count in sorted(by_severity.items()):
                print(f"    {sev}: {count}")
            
            # Show first 5 violations
            print(f"\n  Sample violations:")
            for i, v in enumerate(violations[:5], 1):
                print(f"    {i}. {v.get('rule_id', 'unknown')}")
                print(f"       File: {v.get('file_path', 'unknown')}")
                print(f"       Line: {v.get('line_number', '?')}")
                print(f"       Severity: {v.get('severity', 'UNKNOWN')}")
        else:
            print(f"\n[STEP 6] No violations found")
            print(f"  Possible reasons:")
            print(f"    1. Code is fully compliant")
            print(f"    2. Rules didn't match any patterns")
            print(f"    3. All findings were filtered as false positives")
        
        print(f"\n" + "="*70)
        print(f"TEST COMPLETE")
        print(f"="*70)
        
    except Exception as e:
        print(f"\n  ✗ Scan failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_scan())
