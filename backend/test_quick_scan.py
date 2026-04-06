"""Quick scan test on small test file"""
import subprocess
import json
from pathlib import Path

print("Quick Semgrep Test on test_file.js")
print("="*50)

rules_path = Path("policies/indian_compliance_rules.yaml").resolve()
test_file = Path("test_file.js").resolve()

cmd = [
    "semgrep",
    "--config", str(rules_path),
    "--json",
    str(test_file)
]

print(f"Running: {' '.join(cmd)}\n")

result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, shell=True)

if result.stdout:
    output = json.loads(result.stdout)
    findings = output.get("results", [])
    
    print(f"✓ Found {len(findings)} findings:\n")
    
    for i, f in enumerate(findings, 1):
        print(f"{i}. {f.get('check_id')}")
        print(f"   Line {f.get('start', {}).get('line')}: {f.get('extra', {}).get('message')}")
        print()
    
    print(f"✅ Semgrep is working correctly!")
else:
    print(f"✗ No output")
