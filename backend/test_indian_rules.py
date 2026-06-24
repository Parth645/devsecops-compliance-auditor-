#!/usr/bin/env python3
"""
Test script to verify Indian compliance rules JSON loading
"""

import json
import sys
from pathlib import Path

def test_indian_rules():
    """Test loading and validating Indian compliance rules"""
    
    rules_file = Path("policies/indian_compliance_rules.json")
    
    print("=" * 60)
    print("Testing Indian Compliance Rules JSON")
    print("=" * 60)
    
    # Check file exists
    if not rules_file.exists():
        print(f"❌ Rules file not found: {rules_file}")
        return False
    
    print(f"✓ Rules file found: {rules_file}")
    
    # Load JSON
    try:
        with open(rules_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("✓ JSON loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load JSON: {e}")
        return False
    
    # Validate structure
    if 'frameworks' not in data:
        print("❌ Missing 'frameworks' key")
        return False
    
    print(f"✓ Found {len(data['frameworks'])} frameworks")
    
    # Count rules
    total_rules = 0
    severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    
    for framework in data['frameworks']:
        framework_name = framework.get('name', 'Unknown')
        rules = framework.get('rules', [])
        total_rules += len(rules)
        
        print(f"\n📋 {framework_name}")
        print(f"   ID: {framework.get('id')}")
        print(f"   Rules: {len(rules)}")
        
        for rule in rules:
            severity = rule.get('severity', 'unknown')
            if severity in severity_counts:
                severity_counts[severity] += 1
            
            # Validate rule structure
            required_fields = ['id', 'name', 'severity', 'description', 'category', 'patterns', 'remediation']
            missing = [f for f in required_fields if f not in rule]
            
            if missing:
                print(f"   ⚠ Rule {rule.get('id')} missing fields: {missing}")
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total Rules: {total_rules}")
    print(f"Critical: {severity_counts['critical']}")
    print(f"High: {severity_counts['high']}")
    print(f"Medium: {severity_counts['medium']}")
    print(f"Low: {severity_counts['low']}")
    
    # Test with IndianComplianceRulesManager
    print("\n" + "=" * 60)
    print("Testing IndianComplianceRulesManager")
    print("=" * 60)
    
    try:
        from ai_engine.indian_rules_manager import IndianComplianceRulesManager
        
        manager = IndianComplianceRulesManager()
        
        print(f"✓ Manager initialized")
        print(f"✓ Loaded {len(manager.rules)} rules")
        print(f"✓ Frameworks: {', '.join(manager.get_frameworks())}")
        
        # Test getting rules by framework
        for framework in manager.get_frameworks():
            rules = manager.get_rules_by_framework(framework)
            print(f"   {framework}: {len(rules)} rules")
        
        # Test getting critical rules
        critical = manager.get_critical_rules()
        print(f"\n✓ Critical rules: {len(critical)}")
        for rule in critical[:3]:  # Show first 3
            print(f"   - {rule['id']}: {rule['name']}")
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_indian_rules()
    sys.exit(0 if success else 1)
