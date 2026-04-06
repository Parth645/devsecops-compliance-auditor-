import sys
import os
import logging

# Set up logging to see what's being blocked
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

sys.path.append(os.path.join(os.path.dirname(__file__), 'ai engine'))

from enhanced_repository_scanner import EnhancedRepositoryScanner

# Initialize scanner with Semgrep (if available) and AI Judge
print('Initializing Enhanced Scanner...')
print('  - Semgrep: Enabled (will auto-detect)')
print('  - AI Judge: Enabled')
print('  - Context Analysis: Enabled')
scanner = EnhancedRepositoryScanner(
    enable_context_analysis=True,
    use_semgrep=True  # Will use Semgrep if installed, otherwise fallback to regex
)

# Get the correct path to repo folder (one level up from backend)
repo_path = os.path.join(os.path.dirname(__file__), '..', 'repo')
repo_path = os.path.abspath(repo_path)

print(f'\nRepo path: {repo_path}')

# Scan the repo folder
print('\nScanning repository...')
print('='*70)

results = scanner.scan_repository(repo_path, file_extensions=['.js', '.sol', '.py'])

print(f'\n📊 SCAN RESULTS:')
print(f'='*70)
print(f'Scanner used: {results.get("scanner_used", "unknown").upper()}')
print(f'Files scanned: {results.get("scan_summary", {}).get("total_files_scanned", 0)}')
print(f'Files with violations: {results.get("scan_summary", {}).get("files_with_violations", 0)}')
print(f'Total violations found: {results.get("scan_summary", {}).get("total_violations", 0)}')
print(f'False positives filtered by AI: {results.get("false_positives_filtered", 0)}')
print(f'True positives (final): {len(results.get("violations", []))}')
print(f'Compliance score: {results.get("compliance_score", 0):.1%}')
print(f'Scan duration: {results.get("scan_duration", 0):.2f}s')

# Show severity breakdown
severity_breakdown = results.get("scan_summary", {}).get("severity_breakdown", {})
if severity_breakdown:
    print(f'\n📈 Severity Breakdown:')
    for severity, count in severity_breakdown.items():
        if count > 0:
            print(f'  {severity}: {count}')

# Show category breakdown
category_breakdown = results.get("scan_summary", {}).get("category_breakdown", {})
if category_breakdown:
    print(f'\n📂 Category Breakdown:')
    for category, count in sorted(category_breakdown.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f'  {category}: {count}')

# Show violations
violations = results.get('violations', [])
if violations:
    print(f'\n⚠️  TRUE POSITIVE VIOLATIONS ({len(violations)}):')
    print('='*70)
    for i, v in enumerate(violations[:20], 1):
        print(f'\n{i}. {v.get("file_path", "unknown")}:{v.get("line_number", "?")}')
        print(f'   Severity: {v.get("severity", "UNKNOWN")}')
        print(f'   Rule: {v.get("rule_id", "unknown")}')
        print(f'   Category: {v.get("category", "unknown")}')
        print(f'   Description: {v.get("description", "")}')
        if v.get("ai_verified"):
            print(f'   ✓ AI Verified (confidence: {v.get("ai_confidence", 0):.2f})')
    
    if len(violations) > 20:
        print(f'\n... and {len(violations) - 20} more violations')
else:
    print(f'\n✅ No violations found!')
    print('Either the code is compliant or all issues were filtered as false positives.')

print(f'\n{'='*70}')
if results.get("scanner_used") == "semgrep":
    print('✨ Scan complete using Semgrep + AI Judge!')
else:
    print('✨ Scan complete using Regex Checkers + AI Judge!')
    print('\n💡 Tip: Install Semgrep for better accuracy:')
    print('   pip install semgrep')
print('='*70)
