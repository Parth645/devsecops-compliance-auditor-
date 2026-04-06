"""
Test Semgrep Integration
Quick test to verify Semgrep is working
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai engine'))

from semgrep_scanner import SemgrepScanner, create_indian_compliance_rules

print("="*70)
print("SEMGREP INTEGRATION TEST")
print("="*70)

# Check if Semgrep is installed
scanner = SemgrepScanner()

if not scanner.semgrep_available:
    print("\n❌ Semgrep is NOT installed")
    print("\nTo install Semgrep:")
    print("  pip install semgrep")
    print("\nOr using Homebrew (macOS):")
    print("  brew install semgrep")
    sys.exit(1)

print("\n✅ Semgrep is installed and ready!")

# Show available rulesets
print("\n📋 Available Semgrep Rulesets:")
for ruleset in scanner.get_available_rulesets():
    print(f"  - {ruleset}")

# Create custom Indian compliance rules
print("\n🇮🇳 Creating Indian Compliance Rules...")
try:
    rules_file = create_indian_compliance_rules()
    print(f"✅ Created: {rules_file}")
except Exception as e:
    print(f"❌ Failed to create rules: {e}")

# Test scan on sample repo
print("\n🔍 Testing Scan on Sample Repository...")
repo_path = os.path.join(os.path.dirname(__file__), '..', 'repo')
repo_path = os.path.abspath(repo_path)

if os.path.exists(repo_path):
    print(f"Scanning: {repo_path}")
    
    try:
        results = scanner.scan_repository(repo_path)
        
        if results.get("status") == "success":
            violations = results.get("violations", [])
            print(f"\n✅ Scan completed successfully!")
            print(f"   Found {len(violations)} potential violations")
            
            if violations:
                print(f"\n📊 Sample Violations:")
                for i, v in enumerate(violations[:5], 1):
                    print(f"\n{i}. {v.get('file_path')}:{v.get('line_number')}")
                    print(f"   Rule: {v.get('rule_id')}")
                    print(f"   Severity: {v.get('severity')}")
                    print(f"   Description: {v.get('description')[:80]}...")
                
                if len(violations) > 5:
                    print(f"\n... and {len(violations) - 5} more violations")
        else:
            print(f"\n❌ Scan failed: {results.get('message')}")
    
    except Exception as e:
        print(f"\n❌ Scan error: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"❌ Repository not found: {repo_path}")

print("\n" + "="*70)
print("Test complete!")
print("="*70)
