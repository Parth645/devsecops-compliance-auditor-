"""Test to see actual Semgrep JSON output structure"""
import subprocess
import json
from pathlib import Path

# Run Semgrep on backend directory
cmd = [
    "semgrep",
    "--json",
    "--config", "policies/indian_compliance_rules_complete.yaml",
    "."
]

print("Running Semgrep...")
result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

if result.stdout:
    output = json.loads(result.stdout)
    results = output.get("results", [])
    
    print(f"\nFound {len(results)} results\n")
    
    # Show first 3 results in detail
    for i, r in enumerate(results[:3], 1):
        print(f"=== Result {i} ===")
        print(f"Rule ID: {r.get('check_id')}")
        print(f"File: {r.get('path')}")
        print(f"Line: {r.get('start', {}).get('line')}")
        print(f"Message: {r.get('extra', {}).get('message')}")
        print(f"\nExtra keys: {list(r.get('extra', {}).keys())}")
        print(f"\nFull extra:")
        print(json.dumps(r.get('extra', {}), indent=2))
        print("\n")
