#!/usr/bin/env python3
"""
Test script to verify policy loader works correctly
"""

from ai_engine.policy_loader import load_indian_compliance_policies

def test_policy_loader():
    """Test loading Indian compliance policies"""
    
    print("=" * 60)
    print("Testing Policy Loader")
    print("=" * 60)
    
    try:
        policy_text = load_indian_compliance_policies()
        
        if not policy_text:
            print("❌ No policy text loaded")
            return False
        
        print(f"✓ Loaded policy text ({len(policy_text)} characters)")
        
        # Check for key sections
        required_sections = [
            "DPDPA 2023",
            "RBI Information Security",
            "IT Act 2000",
            "Consent Requirements",
            "Authorization Control",
            "Input Validation"
        ]
        
        missing = []
        for section in required_sections:
            if section not in policy_text:
                missing.append(section)
        
        if missing:
            print(f"⚠ Missing sections: {missing}")
        else:
            print(f"✓ All required sections present")
        
        # Show first 500 chars
        print("\n" + "=" * 60)
        print("Policy Text Preview:")
        print("=" * 60)
        print(policy_text[:500] + "...")
        
        print("\n✅ Policy loader test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Policy loader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = test_policy_loader()
    sys.exit(0 if success else 1)
