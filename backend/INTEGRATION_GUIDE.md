# Integration Guide - Compliance Checkers with Existing System

## Overview

This guide shows how to integrate the new intelligent compliance checkers with your existing DevSecOps Compliance Auditor system.

## Option 1: Replace Existing Scanner (Recommended)

### Step 1: Update main.py

```python
# In backend/main.py

# OLD:
# from ai_engine.repository_scanner import RepositoryScanner

# NEW:
from ai_engine.enhanced_repository_scanner import EnhancedRepositoryScanner

# Update initialization
compliance_analyzer = ComplianceAnalyzer()
# OLD: scanner = RepositoryScanner(policy_processor)
# NEW:
scanner = EnhancedRepositoryScanner(policy_processor)
```

### Step