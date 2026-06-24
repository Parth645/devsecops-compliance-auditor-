"""
Test script to verify scan storage and retrieval
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Import the storage functions
from main import store_scan, get_scans, get_scan_by_id
import time

# Create a test scan with compliance_issues
test_scan = {
    "scan_id": f"test-scan-{int(time.time())}",
    "repository_name": "test-repo",
    "repo_url": "https://github.com/test/repo",
    "branch": "main",
    "scan_date": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "scan_duration": 25.5,
    "total_files": 176,
    "total_findings": 2,
    "critical_count": 0,
    "high_count": 2,
    "medium_count": 0,
    "low_count": 0,
    "status": "completed",
    "findings": [
        {
            "title": "Hardcoded Secret Detected",
            "severity": "high",
            "file_path": "config/database.js",
            "line_number": 15,
            "message": "Database password hardcoded in source code",
            "rule_id": "DPDPA-SEC-001",
            "compliance_framework": "DPDPA 2023"
        },
        {
            "title": "Unencrypted Data Transmission",
            "severity": "high",
            "file_path": "api/payment.js",
            "line_number": 42,
            "message": "Payment data transmitted without encryption",
            "rule_id": "RBI-SEC-002",
            "compliance_framework": "RBI Guidelines"
        }
    ],
    "analysis_summary": {
        "total_violations": 2,
        "severity_breakdown": {
            "critical": 0,
            "high": 2,
            "medium": 0,
            "low": 0
        },
        "scan_method": "AI-driven semantic analysis (Groq)"
    }
}

print("=" * 60)
print("TESTING SCAN STORAGE")
print("=" * 60)

# Store the scan
print("\n1. Storing test scan...")
stored = store_scan(test_scan)
print(f"   ✓ Stored scan: {stored['scan_id']}")
print(f"   ✓ Findings count: {len(stored.get('findings', []))}")

# Retrieve all scans
print("\n2. Retrieving all scans...")
all_scans = get_scans(limit=10)
print(f"   ✓ Retrieved {len(all_scans)} scans")

if all_scans:
    latest = all_scans[0]
    print(f"   ✓ Latest scan ID: {latest.get('scan_id')}")
    print(f"   ✓ Total findings: {latest.get('total_findings')}")
    print(f"   ✓ Findings array length: {len(latest.get('findings', []))}")
    print(f"   ✓ High count: {latest.get('high_count')}")
    
    # Check all possible field names
    print("\n3. Checking field names in stored scan:")
    for field in ['findings', 'violations', 'compliance_issues']:
        value = latest.get(field)
        if value:
            print(f"   ✓ {field}: {len(value)} items")
        else:
            print(f"   ✗ {field}: Not found or empty")

# Retrieve by ID
print(f"\n4. Retrieving scan by ID: {test_scan['scan_id']}")
scan_by_id = get_scan_by_id(test_scan['scan_id'])
if scan_by_id:
    print(f"   ✓ Found scan: {scan_by_id['scan_id']}")
    print(f"   ✓ Findings: {len(scan_by_id.get('findings', []))}")
    
    # Print first finding details
    if scan_by_id.get('findings'):
        print("\n5. First finding details:")
        finding = scan_by_id['findings'][0]
        print(f"   Title: {finding.get('title')}")
        print(f"   Severity: {finding.get('severity')}")
        print(f"   File: {finding.get('file_path')}")
        print(f"   Message: {finding.get('message')}")
else:
    print("   ✗ Scan not found!")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
