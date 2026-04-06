"""
Quick Groq Test - Just test Semgrep + AI verification on one file
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.insert(0, str(Path(__file__).parent))

from ai_engine.semgrep_detector import SemgrepDetector
from ai_engine.groq_semgrep_verifier import GroqSemgrepVerifier
from ai_engine.indian_rules_manager import IndianComplianceRulesManager

async def test():
    print("Quick Groq + Semgrep Test")
    print("="*50)
    
    # Check API key
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("ERROR: GROQ_API_KEY not set")
        return
    
    print(f"1. API Key: {groq_key[:15]}...")
    
    # Initialize components
    print("\n2. Initializing components...")
    detector = SemgrepDetector()
    rules_manager = IndianComplianceRulesManager()
    verifier = GroqSemgrepVerifier(groq_key, rules_manager)
    
    print(f"   Semgrep: OK")
    print(f"   Rules: {len(rules_manager.rules)} loaded")
    print(f"   AI Verifier: OK")
    
    # Create test directory with just test_file.js
    test_dir = Path(".").resolve()
    print(f"\n3. Scanning: {test_dir}")
    
    # Run Semgrep
    print("\n4. Running Semgrep...")
    semgrep_result = await detector.scan_repository(str(test_dir))
    
    findings = semgrep_result.get("findings", [])
    print(f"   Semgrep found: {len(findings)} findings")
    
    if len(findings) == 0:
        print("   No findings - test may need actual violations")
        return
    
    # Show findings
    print("\n5. Semgrep findings:")
    for i, f in enumerate(findings[:5], 1):
        print(f"   {i}. {f.get('rule_id')}")
        print(f"      File: {Path(f.get('file_path', '')).name}")
        print(f"      Line: {f.get('line_start')}")
    
    # AI Verification
    print(f"\n6. Running AI verification on {len(findings)} findings...")
    try:
        verified = await verifier.verify_semgrep_findings(
            findings,
            repo_context="Test repository"
        )
        
        print(f"   Verified: {len(verified)} true positives")
        print(f"   Filtered: {len(findings) - len(verified)} false positives")
        
        if verified:
            print("\n7. Verified violations:")
            for i, v in enumerate(verified[:3], 1):
                print(f"   {i}. {v.get('rule_id')}")
                print(f"      Confidence: {v.get('ai_confidence', 0):.2f}")
        
        print("\n" + "="*50)
        print(f"SUCCESS: Groq AI verification working!")
        print(f"Filtered {len(findings) - len(verified)} false positives")
        print("="*50)
        
    except Exception as e:
        print(f"   ERROR in AI verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
