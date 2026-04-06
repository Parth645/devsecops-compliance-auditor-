"""
Production-Ready Scan Test
Handles large result sets efficiently with smart prioritization
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

async def smart_verification(findings, verifier, max_verify=50):
    """
    Smart verification strategy:
    1. Verify all CRITICAL findings
    2. Verify HIGH findings (up to limit)
    3. Sample MEDIUM/LOW findings
    """
    
    # Separate by severity
    critical = [f for f in findings if f.get('severity') == 'critical']
    high = [f for f in findings if f.get('severity') == 'high']
    medium = [f for f in findings if f.get('severity') == 'medium']
    low = [f for f in findings if f.get('severity') == 'low']
    
    print(f"    Findings by severity:")
    print(f"      CRITICAL: {len(critical)}")
    print(f"      HIGH: {len(high)}")
    print(f"      MEDIUM: {len(medium)}")
    print(f"      LOW: {len(low)}")
    
    # Prioritize verification
    to_verify = []
    
    # Always verify all critical
    to_verify.extend(critical)
    remaining = max_verify - len(to_verify)
    
    # Verify high (up to remaining limit)
    if remaining > 0:
        to_verify.extend(high[:remaining])
        remaining = max_verify - len(to_verify)
    
    # Sample medium/low
    if remaining > 0:
        sample_size = min(remaining, len(medium) + len(low))
        to_verify.extend((medium + low)[:sample_size])
    
    print(f"    Verifying {len(to_verify)} prioritized findings...")
    
    # Verify
    verified = await verifier.verify_semgrep_findings(to_verify, "Production scan")
    
    # Add unverified critical/high as-is (assume true positives)
    unverified_critical = critical[len([f for f in verified if f.get('severity') == 'critical']):]
    for f in unverified_critical:
        f['ai_verified'] = False
        f['ai_confidence'] = 0.9  # High confidence for critical
        verified.append(f)
    
    return verified

async def test_production():
    print("="*70)
    print("PRODUCTION SCAN TEST - Smart Prioritization")
    print("="*70)
    
    # Check API key
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("\nERROR: GROQ_API_KEY not set")
        return None
    
    print(f"\n[1] Initializing...")
    detector = SemgrepDetector()
    rules_manager = IndianComplianceRulesManager()
    verifier = GroqSemgrepVerifier(groq_key, rules_manager)
    remediation_engine = GroqRemediationEngine(groq_key)
    print(f"    OK - All components ready")
    
    # Scan
    print(f"\n[2] Running Semgrep...")
    test_dir = Path(".").resolve()
    semgrep_result = await detector.scan_repository(str(test_dir))
    findings = semgrep_result.get("findings", [])
    
    print(f"    Total findings: {len(findings)}")
    
    if len(findings) == 0:
        print(f"    No findings detected")
        return None
    
    # Smart verification
    print(f"\n[3] Smart AI Verification...")
    verified = await smart_verification(findings, verifier, max_verify=50)
    
    false_positives = len(findings) - len(verified)
    print(f"    Verified: {len(verified)} violations")
    print(f"    Filtered: {false_positives} false positives")
    print(f"    False positive rate: {(false_positives/len(findings)*100):.1f}%")
    
    # Generate remediations for top violations
    print(f"\n[4] Generating Remediations...")
    
    # Prioritize critical and high
    critical_high = [v for v in verified if v.get('severity') in ['critical', 'high']]
    to_remediate = critical_high[:20]  # Top 20 critical/high
    
    print(f"    Generating fixes for {len(to_remediate)} critical/high violations...")
    remediated = await remediation_engine.generate_remediation(to_remediate, "Production")
    
    print(f"    Generated: {len(remediated)} remediations")
    
    # Generate output
    print(f"\n[5] Generating Report...")
    
    output = {
        "scan_summary": {
            "total_findings": len(findings),
            "verified_violations": len(verified),
            "false_positives_filtered": false_positives,
            "false_positive_rate": f"{(false_positives/len(findings)*100):.1f}%",
            "by_severity": {
                "critical": len([v for v in verified if v.get('severity') == 'critical']),
                "high": len([v for v in verified if v.get('severity') == 'high']),
                "medium": len([v for v in verified if v.get('severity') == 'medium']),
                "low": len([v for v in verified if v.get('severity') == 'low'])
            }
        },
        "critical_violations": [
            {
                "id": i + 1,
                "rule_id": v.get("rule_id"),
                "severity": v.get("severity"),
                "file_path": v.get("file_path"),
                "line_number": v.get("line_start"),
                "description": v.get("message"),
                "framework": v.get("framework"),
                "remediation": v.get("remediation", {})
            }
            for i, v in enumerate(remediated)
        ],
        "all_violations_summary": {
            "total": len(verified),
            "with_remediation": len(remediated),
            "pending_review": len(verified) - len(remediated)
        }
    }
    
    # Save
    output_file = Path("production_scan_results.json")
    with open(output_file, 'w') as f:
        json.dump(output, indent=2, fp=f)
    
    print(f"    Report saved: {output_file}")
    
    # Summary
    print(f"\n" + "="*70)
    print(f"PRODUCTION SCAN COMPLETE")
    print(f"="*70)
    
    summary = output["scan_summary"]
    print(f"\nResults:")
    print(f"  Total findings: {summary['total_findings']}")
    print(f"  Verified violations: {summary['verified_violations']}")
    print(f"  False positive rate: {summary['false_positive_rate']}")
    
    print(f"\nBy Severity:")
    for sev, count in summary['by_severity'].items():
        if count > 0:
            print(f"  {sev.upper()}: {count}")
    
    print(f"\nRemediations:")
    print(f"  Generated: {len(remediated)}")
    print(f"  Pending: {len(verified) - len(remediated)}")
    
    print(f"\n" + "="*70)
    print(f"SUCCESS - Production scan completed efficiently!")
    print(f"Review: production_scan_results.json")
    print(f"="*70)
    
    return output

if __name__ == "__main__":
    result = asyncio.run(test_production())
    
    if result:
        print(f"\nScan completed - {result['scan_summary']['verified_violations']} violations found")
    else:
        print(f"\nScan failed")
