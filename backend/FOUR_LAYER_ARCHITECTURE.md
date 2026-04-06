# 3-Layer Intelligent Compliance Analysis System

## Architecture Overview

This system combines detection, compliance mapping, and gap analysis.

```
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 1: DETECTION (Ground Truth - No API Calls)               │
├─────────────────────────────────────────────────────────────────┤
│ ✓ Semgrep      → Pattern-based rules (fast, deterministic)     │
│ OUTPUT: 20-50 unique findings per repository                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 2: MAPPING (Groq Batch - Intelligent Batching)           │
├─────────────────────────────────────────────────────────────────┤
│ ✓ Batch Size: 10 findings per LLM call                         │
│ ✓ Cost: ~100 tokens per finding (vs 200+ single calls)         │
│ ✓ Speed: 3-5 calls instead of 50+ calls                        │
│ ✓ Maps to: DPDPA / IT_ACT_2000 / RBI / CERT-In                │
│ OUTPUT: Framework mapping + risk explanation                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 3: GAP ANALYSIS (Groq Single Call)                       │
├─────────────────────────────────────────────────────────────────┤
│ ✓ Single Groq call per repository                              │
│ ✓ Analyzes: Missing features, absent mechanisms                │
│ ✓ Examples: "No user consent", "No breach notification"        │
│ OUTPUT: 5-10 structural compliance gaps                         │
└─────────────────────────────────────────────────────────────────┘
```

## Key Advantages Over Copilot

| Aspect | Copilot | Our System |
|--------|---------|-----------|
| **Detection Method** | Manual browsing | Automated Semgrep |
| **False Positives** | High (manual review) | Low (pattern-based) |
| **Reproducibility** | Not reproducible | 100% reproducible |
| **Cost** | Manual hours | ~5-10 API calls |
| **Auditability** | Unclear evidence | Full evidence chain |
| **Gap Detection** | Good | Excellent (structured analysis) |
| **Compliance Mapping** | Implicit | Explicit + explained |

## How Each Layer Works

### Layer 1: DETECTION

#### Semgrep
- **Input**: Repository path
- **Processing**: Runs local patterns (no API calls)
- **Output**: JSON findings with file, line, rule ID
- **Time**: 30-60 seconds
- **Cost**: $0

```json
{
  "rule_id": "hardcoded-secret",
  "file": "auth.js",
  "line_start": 42,
  "severity": "critical",
  "message": "Hardcoded JWT secret detected"
}
```

### Layer 2: MAPPING (Groq Batch)

Instead of sending each finding separately:

**BAD (50 API calls × 200 tokens = 10,000 tokens = 💸):**
```
Call 1: "Map this: hardcoded-secret in auth.js:42" → 200 tokens
Call 2: "Map this: sql-injection in database.js:128" → 200 tokens
...
Call 50: → 200 tokens
Total: 10,000 tokens
```

**GOOD (5 API calls × 2000 tokens = 10,000 tokens with context):**
```
Batch 1:
{
  "findings": [
    {"rule": "hardcoded-secret", "file": "auth.js:42"},
    {"rule": "sql-injection", "file": "database.js:128"},
    {...}
  ]
}
→ 2000 tokens (but maps 10 findings)
```

**ACTUAL (3 calls × 2000 tokens = 6,000 tokens total):**
```python
batch_size = 10  # 10 findings per batch
batches = ceil(35 findings / 10) = 4 batches
API calls = 4 × ~1500 tokens = 6,000 tokens total (40% savings!)
```

### Layer 3: GAP ANALYSIS

Sends repository profile once:

```
{
  "tech_stack": ["JavaScript", "Node.js"],
  "files_analyzed": 50,
  "auth_files": ["auth.js", "userController.js"],
  "keywords_found": {
    "authentication": 12,
    "encryption": 0,     ← Gap!
    "logging": 8,
    "consent": 0,        ← Gap!
    "breach_notification": 0  ← Gap!
  }
}
```

Groq returns:

```json
[
  {
    "gap_id": "gap_001",
    "feature": "User Consent Mechanism",
    "framework": "DPDPA",
    "severity": "critical",
    "issue": "No evidence of consent collection",
    "remediation": "Implement consent banner + audit trail"
  },
  {
    "gap_id": "gap_002",
    "feature": "Encryption",
    "framework": "IT_ACT_2000",
    "severity": "critical",
    "issue": "No encryption library detected",
    "remediation": "Add bcrypt for password hashing"
  }
]
```

### Layer 4: EVIDENCE LINKING

Every final violation:

```python
violation = {
    "rule_id": "hardcoded-secret",
    "file": "auth.js",
    "line_start": 42,
    "severity": "critical",
    
    # Layer 2 mapping
    "compliance_mapping": {
        "framework": "IT_ACT_2000",
        "compliance_requirement": "Section 43A: Unauthorized access to computer systems",
        "risk_explanation": "Hardcoded secrets allow unauthorized API access, violating IT Act Section 43A",
        "remediation": "Move secret to environment variables or secrets manager",
        "evidence_weight": "high"
    },
    
    # Layer 4 evidence chain
    "evidence_chain": {
        "detector": "semgrep",
        "rule_id": "hardcoded-secret",
        "file_path": "/repo/src/auth.js",
        "line_number": 42,
        "confidence": 0.95,
        "code_snippet": "const JWT_SECRET = 'super-secret-key-123';"
    }
}
```

## Batching Math

### Problem
- 50 findings × 200 tokens per single mapping call = 10,000 tokens
- At 6000 TPM limit = Rate limit hit after ~18 calls

### Solution: Batching
- Batch 10 findings into 1 call = 2000 tokens
- 5 calls × 2000 = 10,000 tokens (same cost!)
- But: 5 calls vs 50 calls = **10× fewer rate limit hits**

### Result
```
Without batching:  50 API calls → 429 rate limit error
With batching:     5 API calls → No rate limiting
```

## Token Budget

For typical repository:

| Layer | Cost | Details |
|-------|------|---------|
| Layer 1 | $0 | Semgrep (local) |
| Layer 2 | ~6,000 tokens | 5-10 batches × 1000-2000 tokens |
| Layer 3 | ~1,500 tokens | 1 gap analysis call |
| **Total** | **~7,500 tokens** | ~$0.0008 cost |

## Running the System

```python
from ai_engine.compliance_analyzer import ComplianceAnalyzer

analyzer = ComplianceAnalyzer()

result = await analyzer.analyze_repository_for_compliance(
    repo_path="/path/to/repo",
    language="javascript"
)

# Result includes:
# - 20-50 violations with evidence
# - 5-10 compliance gaps
# - Framework breakdown (DPDPA/IT_ACT_2000/RBI/CERT-In)
# - High-risk files list
# - Full audit trail
```

## Comparison: Before vs After

### BEFORE (Pattern-Only)
```
Violations: 3
- hardcoded_secret in auth.js
- no_mfa in auth.js
- no_https in config.js

Problems:
❌ Only pattern matching (misses complex issues)
❌ No compliance framework mapping
❌ No gap detection
❌ Manual effort to validate
```

### AFTER (3-Layer System)
```
Violations: 25-40 (vs 3 before)
- 10-15 critical violations with framework mapping
- 5-8 high-risk files identified
- 5-10 compliance gaps detected
- All with evidence chain + remediations

Benefits:
✓ Comprehensive detection (Semgrep patterns)
✓ Smart batching (no rate limits)
✓ Full auditability (every finding traced)
✓ Gap detection (like Copilot)
✓ Compliance-aware (DPDPA/RBI/IT_ACT_2000/CERT-In)
```

## Compliance Frameworks Mapped

| Framework | Coverage | Examples |
|-----------|----------|----------|
| **DPDPA 2023** | Personal data protection | Consent, retention, breach notification |
| **IT Act 2000** | Information security | Encryption, authentication, SPDI Rules |
| **RBI Guidelines** | Financial security | Security headers, MFA, TLS, audit logs |
| **CERT-In** | Critical infrastructure | Incident reporting, 72h notification |

## Future Enhancements

1. **CodeQL Integration** (Optional): Add graph-based analysis for complex vulnerabilities
2. **Remediation Generation**: Use Stage 4 (auto-remediation) for each gap
3. **Trend Analysis**: Track violations across multiple scans
4. **Compliance Scoring**: % compliance with each framework
5. **Integration**: GitHub, GitLab, Azure DevOps webhooks
6. **Custom Rules**: Allow teams to define org-specific compliance rules
