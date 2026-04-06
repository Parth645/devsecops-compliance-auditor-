"""
Direct Semgrep Test - Minimal test to verify Semgrep works
"""

import subprocess
import json
from pathlib import Path

print("="*70)
print("DIRECT SEMGREP TEST")
print("="*70)

# Step 1: Check Semgrep installation
print("\n[STEP 1] Checking Semgrep installation...")
print("  Note: First run may be slow on Windows (30-60 seconds)...")
try:
    result = subprocess.run(["semgrep", "--version"], capture_output=True, text=True, timeout=60, shell=True)
    if result.returncode == 0:
        print(f"  ✓ Semgrep installed: {result.stdout.strip()}")
    else:
        print(f"  ✗ Semgrep check failed: {result.stderr}")
        print(f"  Continuing anyway - will test with actual scan...")
except subprocess.TimeoutExpired:
    print(f"  ⚠ Semgrep version check timed out (this is OK on Windows)")
    print(f"  Continuing with scan test...")
except Exception as e:
    print(f"  ⚠ Semgrep check warning: {e}")
    print(f"  Continuing anyway...")

# Step 2: Check rules file
print("\n[STEP 2] Checking rules file...")
rules_path = Path("policies/indian_compliance_rules.yaml")
print(f"  Path: {rules_path.resolve()}")
print(f"  Exists: {rules_path.exists()}")

if not rules_path.exists():
    print(f"  ✗ Rules file not found!")
    exit(1)

# Validate rules
import yaml
try:
    with open(rules_path) as f:
        rules = yaml.safe_load(f)
    rule_count = len(rules.get('rules', []))
    print(f"  ✓ Rules validated: {rule_count} rules")
except Exception as e:
    print(f"  ✗ Rules validation failed: {e}")
    exit(1)

# Step 3: Find test repository
print("\n[STEP 3] Finding test repository...")
test_repo = Path("../repo").resolve()
if not test_repo.exists():
    test_repo = Path(".").resolve()
    print(f"  Using current directory: {test_repo}")
else:
    print(f"  Using test repo: {test_repo}")

# Count files
code_files = list(test_repo.rglob("*.js")) + list(test_repo.rglob("*.py"))
print(f"  Code files: {len(code_files)}")

# Step 4: Run Semgrep directly
print("\n[STEP 4] Running Semgrep...")
cmd = [
    "semgrep",
    "--config", str(rules_path.resolve()),
    "--json",
    "--quiet",
    str(test_repo)
]

print(f"  Command: {' '.join(cmd)}")
print(f"  Running (may take 1-2 minutes on first run)...")

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, shell=True)
    
    print(f"\n[STEP 5] Semgrep Results:")
    print(f"  Exit code: {result.returncode}")
    print(f"  Stdout length: {len(result.stdout)} bytes")
    print(f"  Stderr length: {len(result.stderr)} bytes")
    
    if result.returncode >= 2:
        print(f"  ✗ Semgrep failed!")
        print(f"  Error: {result.stderr}")
        exit(1)
    
    if result.stdout:
        try:
            output = json.loads(result.stdout)
            findings = output.get("results", [])
            
            print(f"  ✓ Findings: {len(findings)}")
            
            if findings:
                print(f"\n[STEP 6] Sample Findings:")
                for i, finding in enumerate(findings[:5], 1):
                    print(f"    {i}. {finding.get('check_id')}")
                    print(f"       File: {finding.get('path')}")
                    print(f"       Line: {finding.get('start', {}).get('line')}")
            else:
                print(f"\n[STEP 6] No findings")
                print(f"  Possible reasons:")
                print(f"    1. Code is compliant")
                print(f"    2. Rules don't match patterns")
                print(f"    3. Files were filtered out")
                
        except json.JSONDecodeError as e:
            print(f"  ✗ Failed to parse JSON: {e}")
            print(f"  Raw output: {result.stdout[:500]}")
    else:
        print(f"  ⚠ No output from Semgrep")
        
except subprocess.TimeoutExpired:
    print(f"  ✗ Semgrep timed out (180s)")
except Exception as e:
    print(f"  ✗ Semgrep failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
