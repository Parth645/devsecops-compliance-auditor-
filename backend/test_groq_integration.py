"""
Test Groq Integration with Compliance Pipeline
Simple test without unicode characters for Windows compatibility
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from ai_engine.compliance_analyzer import ComplianceAnalyzer

async def test_groq():
    print("="*70)
    print("GROQ INTEGRATION TEST")
    print("="*70)
    
    # Check API key
    print("\n[1] Checking GROQ_API_KEY...")
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        print(f"   OK - API Key found: {groq_key[:15]}...")
    else:
        print("   ERROR - GROQ_API_KEY not set!")
        print("   Set it in backend/.env file")
        return
    
    # Initialize analyzer
    print("\n[2] Initializing analyzer with Groq...")
    try:
        analyzer = ComplianceAnalyzer(groq_api_key=groq_key)
        print("   OK - Analyzer initialized")
        print(f"   - Semgrep: {'Yes' if analyzer.semgrep_detector else 'No'}")
        print(f"   - AI Verifier: {'Yes' if analyzer.semgrep_verifier else 'No'}")
        print(f"   - Business Logic: {'Yes' if analyzer.business_logic_scanner else 'No'}")
        print(f"   - Batch Mapper: {'Yes' if analyzer.batch_mapper else 'No'}")
    except Exception as e:
        print(f"   ERROR - {e}")
        return
    
    # Run scan on test file
    print("\n[3] Running scan on test_file.js...")
    test_file_dir = Path(".").resolve()
    
    try:
        result = await analyzer.analyze_repository_for_compliance(
            repo_path=str(test_file_dir),
            custom_policy_text=None
        )
        
        print("\n[4] Results:")
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Duration: {result.get('scan_duration', 0):.1f}s")
        print(f"   Violations: {len(result.get('violations', []))}")
        
        violations = result.get('violations', [])
        if violations:
            print(f"\n[5] Sample violations:")
            for i, v in enumerate(violations[:3], 1):
                print(f"   {i}. {v.get('rule_id')}")
                print(f"      File: {Path(v.get('file_path', '')).name}")
                print(f"      Severity: {v.get('severity')}")
                if v.get('ai_verified'):
                    print(f"      AI Verified: Yes")
        
        # Check which stages ran
        print(f"\n[6] Pipeline stages:")
        print(f"   Semgrep scan: {'Yes' if result.get('semgrep_findings', 0) > 0 else 'No'}")
        print(f"   AI verification: {'Yes' if result.get('verified_findings', 0) > 0 else 'No'}")
        print(f"   Business logic: {'Yes' if result.get('business_logic_violations', 0) > 0 else 'No'}")
        
        print("\n" + "="*70)
        if len(violations) > 0:
            print("SUCCESS - Groq integration working!")
            print(f"Found {len(violations)} violations with AI verification")
        else:
            print("WARNING - No violations found")
            print("Semgrep is working but no violations detected")
        print("="*70)
        
        return result
        
    except Exception as e:
        print(f"\n   ERROR - Scan failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_groq())
    
    if result:
        print(f"\nFinal: {len(result.get('violations', []))} violations")
    else:
        print("\nTest failed - check errors above")
