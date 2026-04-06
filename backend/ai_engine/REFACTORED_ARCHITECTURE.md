# DevSecOps Compliance Auditor - Refactored AI-Driven Architecture

## Overview

The compliance auditor has been refactored from a simple 3-layer system to a sophisticated **5-step AI-driven intelligence pipeline** that leverages Groq's LLM capabilities for dynamic rule generation and intelligent triage.

## Architecture: 5-Step Pipeline

### Step 1: AI Fast Triage (GroqRepoProfiler)
**Model:** `llama-3.3-70b-versatile` | **Temperature:** 0.15

Analyzes repository structure without relying on hardcoded keyword lists:
- Builds file tree from repository contents
- Extracts API routes and endpoints
- Identifies framework and tech stack
- **Intelligently determines where compliance features are implemented** (or absent)
- Returns structured JSON profile of repository compliance posture

**Output:** Repository profile with compliance feature locations

**Example Detection:**
```json
{
  "application_purpose": "IoT Telemetry Backend",
  "tech_stack": "Node.js/Express",
  "compliance_features": {
    "authentication": {"present": true, "files": ["auth.js", "middleware/jwt.js"]},
    "encryption": {"present": false, "files": []},
    "audit_logging": {"present": true, "files": ["logger.js"]},
    "breach_notification": {"present": false, "files": []},
    "rate_limiting": {"present": false, "files": []}
  },
  "critical_gaps": ["No encryption", "No breach notification", "No rate limiting"]
}
```

### Step 2: Dynamic Semgrep YAML Generator (GroqPolicyTranslator)
**Model:** `llama-3.3-70b-versatile` | **Temperature:** 0.1

Converts natural language compliance policies into executable Semgrep rules:
- Accepts custom company policy text
- Generates compositional Semgrep patterns using:
  - `pattern`, `pattern-not`, `pattern-inside`, `pattern-not-inside`
  - `mode: taint` for data flow analysis
  - `pattern-sources` and `pattern-sinks`
- Focuses on anti-patterns (absence of security features)
- **Strips markdown from Groq responses to output pure YAML**
- Saves rules to disk for Semgrep consumption

**Output:** Valid Semgrep YAML file with custom organizational policies

**Example Usage:**
```python
translator = GroqPolicyTranslator(api_key)
result = await translator.translate_policy_to_semgrep_rules(
    policy_text=company_policy,
    policy_name="acme_corp_policy"
)
# Generates: policies/generated_rules/acme_corp_policy_rules.yaml
```

**Generated Rule Example:**
```yaml
rules:
  - id: custom.policy.data_encryption
    pattern: |
      password = $VAR
      ...
      db.store($VAR)
    message: "Unencrypted password storage violates company policy"
    languages: [javascript, typescript]
    severity: ERROR
    metadata:
      source: groq_policy_translator
      policy: custom
```

### Step 3: Semgrep Execution (SemgrepDetector)
**Model:** Static analysis (no LLM)

Runs Semgrep with standard rules + dynamically generated rules:
- Scans repository with organizational policies
- Produces ground-truth findings
- Returns structured JSON with file paths, lines, severity

**Output:** List of violations detected by Semgrep

### Step 4: Framework Mapping (GroqBatchMapper)
**Model:** `llama-3.3-70b-versatile` | **Temperature:** 0.3 | **Batch Size:** 10 findings/call

Intelligent batching to avoid rate limits while mapping to compliance frameworks:
- Groups 10 violations per Groq API call
- Maps to Indian compliance frameworks:
  - **DPDPA 2023** (Personal Data Protection Act)
  - **IT Act 2000** (Information Technology Act & SPDI Rules)
  - **RBI Guidelines** (Reserve Bank of India)
  - **CERT-In** (Indian Computer Emergency Response Team)
- Provides risk explanations and remediation guidance

**Output:** Violations with framework mapping and compliance context

### Step 5: AI Gap Analysis (GapAnalyzer)
**Model:** `llama-3.3-70b-versatile` (uses GroqRepoProfiler output)

Uses AI profiling (NOT keyword matching) to identify missing compliance features:
- Analyzes repository profile from Step 1
- Identifies critical gaps:
  - Missing breach notification system → **DPDPA critical**
  - No security headers → **RBI requirement**
  - No input validation → **IT Act requirement**
  - Missing TLS/HTTPS → **RBI encrypted transmission**
  - No privacy policy → **IT Act SPDI requirement**
- Provides remediation effort estimates

**Output:** List of missing compliance features with impact analysis

## Key Improvements

| Aspect | Before | After |
|--------|--------|-------|
| Gap Detection | Hardcoded keyword arrays | AI-driven repo profiling |
| Policy Handling | Manual Semgrep rules | Dynamic YAML generation from policies |
| Scalability | Limited to predefined rules | Flexible, company-specific rules |
| Triage Speed | Slow (multiple LLM calls) | Fast (single call for profiling) |
| False Positives | High (keyword-based) | Low (semantic understanding) |
| Rate Limiting | Uncontrolled API calls | Intelligent batching (10/call) |

## Integration Points

### In compliance_analyzer.py:
```python
analyzer = ComplianceAnalyzer()

# Automatic 5-step flow:
result = await analyzer.analyze_repository_for_compliance(
    repo_path="/path/to/repo",
    custom_policy_text="Optional company policy..."  # Optional
)
```

### Output Structure:
```json
{
  "status": "completed",
  "violations": [...],  // Top 100 violations
  "total_violations": 42,
  "gaps": [...],  // Missing features from Step 5
  "severity_breakdown": {"critical": 3, "high": 8, "medium": 1, "low": 0},
  "framework_breakdown": {"DPDPA": 15, "IT_ACT_2000": 12, "RBI": 10, "CERT-In": 5},
  "pipeline": {
    "step_1_ai_profiling": {"status": "complete"},
    "step_2_policy_translation": {"status": "complete", "custom_rules": true},
    "step_3_semgrep_execution": {"status": "complete", "findings": 6},
    "step_4_framework_mapping": {"status": "complete", "mapped": 36},
    "step_5_gap_analysis": {"status": "complete", "gaps": 5}
  },
  "repo_profile": {...},  // From Step 1
  "scan_duration_seconds": 125.4
}
```

## Performance Characteristics

- **Repository Profiling (Step 1):** ~5-10 seconds (single Groq call)
- **Policy Translation (Step 2):** ~8-12 seconds (if custom policy provided)
- **Semgrep Execution (Step 3):** ~20-60 seconds (depends on repo size)
- **Batch Mapping (Step 4):** ~2-5 seconds for 10 findings
- **Gap Analysis (Step 5):** ~3-5 seconds (uses profile, no new scans)
- **Total:** ~50-120 seconds for typical repositories

## Advanced Features

### 1. Compositional Semgrep Patterns
Step 2 generates rules with advanced operators:
```semgrep
pattern-inside: |
  def $FUNC(...):
    ...
    password = $VAR
    ...
pattern-not-inside: |
  def $FUNC(...):
    ...
    bcrypt.hash($VAR)
    ...
```

### 2. Taint Analysis
For data flow violations:
```semgrep
mode: taint
pattern-sources:
  - pattern: request.body
  - pattern: request.query
pattern-sinks:
  - pattern: db.execute(...)
pattern-sanitizers:
  - pattern: sanitize(...)
```

### 3. Temperature Control
- **Low (0.1):** Policy translation (consistency, precision)
- **Medium (0.15):** Repository profiling (nuanced analysis)
- **High (0.3):** Batch mapping (flexibility, variety in explanations)

## Files Created/Modified

### New Files:
- `ai_engine/groq_repo_profiler.py` - Step 1 implementationimplementation
- `ai_engine/groq_policy_translator.py` - Step 2 implementation

### Modified Files:
- `ai_engine/compliance_analyzer.py` - Refactored orchestrator
- `ai_engine/gap_analyzer.py` - Now uses AI profiling instead of keywords

### Backward Compatibility:
- Old keyword-based files kept as `*_old.bak` for reference
- All previous APIs maintained for compatibility

## Usage Examples

### Basic Scan:
```python
analyzer = ComplianceAnalyzer()
result = await analyzer.analyze_repository_for_compliance(repo_path)
```

### With Custom Policy:
```python
policy_text = """
COMPANY SECURITY POLICY
1. All passwords must be 12+ characters
2. All APIs must use TLS 1.2+
3. Audit logs must be retained for 3 years
"""

result = await analyzer.analyze_repository_for_compliance(
    repo_path=repo,
    custom_policy_text=policy_text
)
# Groq translates policy to Semgrep rules automatically
```

### Direct Policy Translation:
```python
translator = GroqPolicyTranslator(api_key)
result = await translator.translate_policy_to_semgrep_rules(
    policy_text="Your policy",
    policy_name="org_policy"
)
# Returns: path to generated YAML, rule count, etc.
```

## Configuration

All components use:
- **Groq Model:** `llama-3.3-70b-versatile`
- **API Key:** From environment variable `GROQ_API_KEY`
- **Async:** Full async/await support throughout
- **Error Handling:** Graceful degradation if components fail

## Next Steps (Future Enhancements)

1. **Placeholder:** Step 3b - False positive validation with qwen/qwen3-32b
2. **Custom remediation generation** - Auto-fix code for common issues
3. **Incremental scanning** - Only scan changed files
4. **Multi-tenant policies** - Different policies per organization
5. **Real-time webhook integration** - Pre-commit scanning
6. **Dashboard & reporting** - Visual compliance trends

