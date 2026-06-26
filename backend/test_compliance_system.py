#!/usr/bin/env python3
"""
Test script to verify the entire compliance system initialization
"""

import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

def test_compliance_system():
    """Test the complete compliance system"""
    
    print("=" * 60)
    print("Testing Complete Compliance System")
    print("=" * 60)
    
    try:
        # Test 1: Indian Rules Manager
        print("\n[1/3] Testing Indian Rules Manager...")
        from ai_engine.indian_rules_manager import IndianComplianceRulesManager
        
        rules_manager = IndianComplianceRulesManager()
        print(f"  ✓ Loaded {len(rules_manager.rules)} rules")
        print(f"  ✓ Frameworks: {len(rules_manager.get_frameworks())}")
        print(f"  ✓ Critical rules: {len(rules_manager.get_critical_rules())}")
        
        # Test 2: Policy Loader
        print("\n[2/3] Testing Policy Loader...")
        from ai_engine.policy_loader import load_indian_compliance_policies
        
        policy_text = load_indian_compliance_policies()
        print(f"  ✓ Policy text loaded ({len(policy_text)} chars)")
        
        # Test 3: Compliance Analyzer Initialization
        print("\n[3/3] Testing Compliance Analyzer...")
        from ai_engine.compliance_analyzer import ComplianceAnalyzer
        
        analyzer = ComplianceAnalyzer()
        print(f"  ✓ Compliance analyzer initialized")
        
        print("\n" + "=" * 60)
        print("✅ All systems operational!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ System test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_compliance_system()
    sys.exit(0 if success else 1)
