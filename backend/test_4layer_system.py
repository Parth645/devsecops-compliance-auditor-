"""
Test 3-Layer Intelligent Compliance System
Demonstrates Semgrep + Groq Batch Mapping + Gap Analysis
"""

import asyncio
import logging
from ai_engine.compliance_analyzer import ComplianceAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_three_layer_system():
    """Test complete 3-layer system"""
    
    print("\n" + "="*80)
    print("3-LAYER INTELLIGENT COMPLIANCE ANALYSIS SYSTEM")
    print("="*80)
    print("""
This system combines:
✓ Layer 1: Semgrep detection (ground truth findings)
✓ Layer 2: Groq batch mapping (compliance framework mapping)
✓ Layer 3: Gap analysis (missing compliance features)

Expected benefits:
- NO rate limiting (intelligent batching: 5-20 findings per call)
- Comprehensive detection (Semgrep patterns)
- Copilot-level gap detection (identifies missing mechanisms)
- Full auditability (every violation has evidence chain)
    """)
    
    # Initialize analyzer
    analyzer = ComplianceAnalyzer()
    
    # Test repository (using same as before)
    repo_url = "https://github.com/Haru65/ashebackend"
    repo_path = "/tmp/test_repo"  # Would be cloned here
    
    print(f"\nRepository: {repo_url}")
    print(f"Local path: {repo_path}")
    
    print("\n" + "-"*80)
    print("SCANNING WITH 4-LAYER SYSTEM...")
    print("-"*80)
    
    # Run analysis
    result = await analyzer.analyze_repository_for_compliance(repo_path)
    
    # Display results
    if result.get("status") == "completed":
        print(f"\n✓ SCAN COMPLETED in {result.get('scan_duration_seconds', 0):.1f}s\n")
        
        # Layer 1 results
        print("LAYER 1: DETECTION")
        print("-" * 40)
        pipeline = result.get("pipeline", {})
        print(f"  Semgrep findings: {pipeline.get('layer_1_detection', 0)}")
        
        # Layer 2 results
        print(f"\nLAYER 2: MAPPING (Groq Batching)")
        print("-" * 40)
        print(f"  Findings mapped:  {pipeline.get('layer_2_mapping', 0)}")
        
        # Layer 3 results
        print(f"\nLAYER 3: GAP ANALYSIS")
        print("-" * 40)
        print(f"  Compliance gaps:  {pipeline.get('layer_3_gaps', 0)}")
        
        # Summary
        print(f"\nSUMMARY")
        print("-" * 40)
        severity = result.get("severity_breakdown", {})
        print(f"  Total violations:  {result.get('total_violations', 0)}")
        print(f"  Critical:          {severity.get('critical', 0)}")
        print(f"  High:              {severity.get('high', 0)}")
        print(f"  Medium:            {severity.get('medium', 0)}")
        
        framework = result.get("framework_breakdown", {})
        print(f"\n  By Framework:")
        for fw, count in framework.items():
            print(f"    - {fw}: {count}")
        
        print(f"\n  High-Risk Files:")
        for file_info in result.get("high_risk_files", [])[:5]:
            print(f"    - {file_info.get('file')}: {file_info.get('critical', 0)} critical, {file_info.get('high', 0)} high")
        
        # Sample violation with evidence
        print(f"\nSAMPLE VIOLATION WITH EVIDENCE:")
        print("-" * 40)
        if result.get("violations"):
            violation = result["violations"][0]
            print(f"  Rule: {violation.get('rule_id', 'unknown')}")
            print(f"  File: {violation.get('file_path', 'unknown')}:{violation.get('line_start', '?')}")
            print(f"  Framework: {violation.get('framework', 'unknown')}")
            print(f"  Severity: {violation.get('severity', 'unknown')}")
            print(f"  Message: {violation.get('message', 'unknown')}")
            
            if violation.get("compliance_mapping"):
                mapping = violation["compliance_mapping"]
                print(f"  Compliance Requirement: {mapping.get('compliance_requirement', '')}")
                print(f"  Risk: {mapping.get('risk_explanation', '')}")
                print(f"  Remediation: {mapping.get('remediation', '')}")
    else:
        print(f"\n✗ SCAN FAILED: {result.get('error', 'unknown error')}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(test_three_layer_system())
