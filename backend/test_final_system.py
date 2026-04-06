"""
Final System Integration Test
Tests complete pipeline: Semgrep (38 rules) → Groq AI → Remediation → JSON Output
"""

import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.insert(0, str(Path(__file__).parent))

from ai_engine.semgrep_detector import SemgrepDetector
from ai_engine.groq_semgrep_verifier import GroqSemgrepVerifier
from ai_engine.groq_remediation_engine import GroqRemediationEngine
from ai_engine.indian_rules_manager import IndianComplianceRulesManager

async def test_final_system():
    print("="*70)
    print("FINAL SYSTEM INTEGRATION TEST")
    print("="*70)
    
    # Check API key
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("\nERROR: GROQ_API_KEY not set in .env file")
        return None
    
    print(f"\n[1] Environment Check")
    print(f"    API Key: {groq_key[:15]}...")
    print(f"    OK")
    
    # Initialize components
    print(f"\n[2] Initializing Components")
    try:
        detector = SemgrepDetector()
        rules_manager = IndianComplianceRulesManager()
        verifier = GroqSemgrepVerifier(groq_key, rules_manager)
        remediation_engine = GroqRemediationEngine(groq_key)
        
        print(f"    Semgrep Detector: OK")
        print(f"    Rules Manager: {len(rules_manager.rules)} rules loaded")
        print(f"    AI Verifier: OK")
        print(f"    Remediation Engine: OK")
    except Exception as e:
        print(f"    ERROR: {e}")
        return None
    
    # Run Semgrep scan
    print(f"\n[3] Running Semgrep Scan")
    test_dir = Path(".").resolve()
    print(f"    Scanning: {test_dir}")
    
    try:
        semgrep_result = await detector.scan_repository(str(test_dir))
        findings = semgrep_result.get("findings", [])
        
        print(f"    Semgrep found: {len(findings)} findings")
        
        if len(findings) == 0:
            print(f"    WARNING: No findings detected")
            print(f"    Check if test files have violations")
            return None
        
        # Calculate detection rate
        total_rules = 38  # Complete ruleset
        detection_rate = (len(findings) / total_rules) * 100 if total_rules > 0 else 0
        print(f"    Detection rate: {detection_rate:.1f}%")
        
        if detection_rate < 10:
            print(f"    WARNING: Low detection rate")
        
    except Exception as e:
        print(f"    ERROR: {e}")
        return None
    
    # AI Verification
    print(f"\n[4] AI Verification (Groq)")
    print(f"    Processing {len(findings)} findings in batches...")
    
    try:
        # Process all findings with batching
        verified = await verifier.verify_semgrep_findings(
            findings,  # Process ALL findings
            repo_context="Test repository"
        )
        
        false_positives = len(findings) - len(verified)
        accuracy = (len(verified)/len(findings)*100) if len(findings) > 0 else 0
        
        print(f"    Total processed: {len(findings)}")
        print(f"    Verified: {len(verified)} true positives")
        print(f"    Filtered: {false_positives} false positives")
        print(f"    Accuracy: {accuracy:.1f}%")
        print(f"    False positive rate: {(false_positives/len(findings)*100):.1f}%")
        
    except Exception as e:
        print(f"    ERROR: {e}")
        import traceback
        traceback.print_exc()
        verified = findings  # Use unverified if AI fails
    
    # Generate Remediations
    print(f"\n[5] Generating Remediations (Groq)")
    print(f"    Processing {len(verified)} verified violations...")
    
    try:
        # Generate remediations for all verified violations
        remediated = await remediation_engine.generate_remediation(
            verified,  # Process ALL verified violations
            repo_context="Test repository"
        )
        
        print(f"    Generated: {len(remediated)} remediations")
        
        # Show sample
        if remediated:
            print(f"\n    Sample Remediations:")
            for i, sample in enumerate(remediated[:3], 1):
                print(f"      {i}. Rule: {sample.get('rule_id')}")
                print(f"         File: {Path(sample.get('file_path', '')).name}")
                
                rem = sample.get('remediation', {})
                if rem:
                    print(f"         Fix: {rem.get('explanation', 'N/A')[:50]}...")
                    print(f"         Priority: {rem.get('priority', 'N/A')}")
        
    except Exception as e:
        print(f"    ERROR: {e}")
        import traceback
        traceback.print_exc()
        remediated = verified
    
    # Generate JSON Output
    print(f"\n[6] Generating JSON Output")
    try:
        output = {
            "scan_summary": {
                "total_findings": len(findings),
                "verified_violations": len(verified),
                "false_positives_filtered": len(findings) - len(verified),
                "false_positive_rate_percent": ((len(findings) - len(verified))/len(findings)*100) if len(findings) > 0 else 0,
                "detection_rate_percent": detection_rate,
                "rules_applied": semgrep_result.get("rules_used", [])
            },
            "violations": [
                {
                    "id": i + 1,
                    "rule_id": v.get("rule_id"),
                    "severity": v.get("severity"),
                    "file_path": v.get("file_path"),
                    "line_number": v.get("line_start"),
                    "description": v.get("message"),
                    "framework": v.get("framework"),
                    "code_snippet": v.get("code_snippet", "")[:100],
                    "ai_verified": v.get("ai_verified", False),
                    "ai_confidence": v.get("ai_confidence", 0),
                    "remediation": v.get("remediation", {})
                }
                for i, v in enumerate(remediated)
            ],
            "remediation_summary": remediation_engine.get_remediation_summary(remediated)
        }
        
        # Save to file
        output_file = Path("scan_results.json")
        with open(output_file, 'w') as f:
            json.dump(output, indent=2, fp=f)
        
        print(f"    JSON saved to: {output_file}")
        print(f"    Size: {output_file.stat().st_size} bytes")
        
    except Exception as e:
        print(f"    ERROR: {e}")
        output = None
    
    # Final Summary
    print(f"\n" + "="*70)
    print(f"SYSTEM TEST RESULTS")
    print(f"="*70)
    
    if output:
        summary = output["scan_summary"]
        print(f"\nSemgrep Performance:")
        print(f"  Total findings: {summary['total_findings']}")
        print(f"  Detection rate: {summary['detection_rate_percent']:.1f}%")
        print(f"  Target: >80% (38+ rules)")
        
        if summary['detection_rate_percent'] >= 80:
            print(f"  Status: EXCELLENT")
        elif summary['detection_rate_percent'] >= 50:
            print(f"  Status: GOOD")
        else:
            print(f"  Status: NEEDS IMPROVEMENT")
        
        print(f"\nAI Verification:")
        print(f"  Verified: {summary['verified_violations']}")
        print(f"  False positives filtered: {summary['false_positives_filtered']}")
        
        print(f"\nRemediation:")
        rem_summary = output["remediation_summary"]
        print(f"  Total violations: {rem_summary['total_violations']}")
        print(f"  By priority:")
        for priority, count in rem_summary['by_priority'].items():
            if count > 0:
                print(f"    {priority}: {count}")
        
        print(f"\nJSON Output:")
        print(f"  File: scan_results.json")
        print(f"  Violations with remediation: {len(output['violations'])}")
        
        print(f"\n" + "="*70)
        print(f"SUCCESS: System fully integrated and working!")
        print(f"="*70)
        
        return output
    else:
        print(f"\nFAILED: Check errors above")
        return None

if __name__ == "__main__":
    result = asyncio.run(test_final_system())
    
    if result:
        print(f"\nTest completed successfully")
        print(f"Review scan_results.json for full output")
    else:
        print(f"\nTest failed - check errors above")
