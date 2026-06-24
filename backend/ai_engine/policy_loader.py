"""
Policy Loader - Load Indian compliance rules as policy text
Converts JSON rules to policy format for Semgrep rule generation
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_indian_compliance_policies() -> str:
    """
    Load Indian compliance rules from JSON file
    Convert to policy text format for Semgrep rule generation
    
    Returns:
        Policy text combining DPDPA, RBI, IT Act, SEBI rules
    """
    try:
        rules_file = Path(__file__).parent.parent / "policies" / "indian_compliance_rules.json"
        
        if not rules_file.exists():
            logger.warning(f"Indian compliance rules file not found: {rules_file}")
            return ""
        
        with open(rules_file, 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        # Extract frameworks and rules (frameworks is a list in new structure)
        frameworks = rules_data.get("frameworks", [])
        
        # Build policy text from all frameworks
        policy_text = """# Indian Compliance Policy Requirements

## DPDPA 2023 (Digital Personal Data Protection Act)
All applications handling personal data must comply with:

### Consent Requirements (Section 7)
- Explicit consent must be obtained before processing personal data
- Users must understand what data is being collected and why
- Consent must be specific, informed, and freely given.

### Purpose Limitation
- Personal data can only be used for the disclosed and consented purposes
- Secondary uses require new consent
- Examples: Data collected for "power monitoring" cannot be used for "behavioral profiling"

### Data Minimization
- Only necessary personal data should be collected
- Data collected must be relevant to the stated purpose
- Remove: SSN, DOB, address unless absolutely required

### Data Breach Notification
- Notify affected users within 72 hours of discovering breach
- Maintain breach detection and notification mechanisms
- Keep breach logs for compliance audits

### User Rights Implementation
- Right to Access: Users can request and view their personal data
- Right to Correction: Users can request correction of inaccurate data
- Right to Erasure: Users can request deletion of their data ("right to be forgotten")
- Right to Portability: Users can export their data in standard formats

## RBI Information Security Guidelines
Financial institutions and payment processors must:

### Authorization Control
- All authorization checks must be server-side
- Authorization state must be fetched from authenticated session/JWT
- NEVER trust client-provided role or permission data
- Example: const role = req.body.role ❌ WRONG
- Example: const role = extractFromJWT(req.headers.authorization) ✓ CORRECT

### Transaction Atomicity
- Financial transactions must be all-or-nothing (atomic)
- Implement database transactions for multi-step operations
- Prevent race conditions that could lead to double-charging
- Use pessimistic locks: SELECT ... FOR UPDATE

### Encryption Standards
- TLS 1.2 or higher for all data in transit
- AES-256 for sensitive data at rest
- Never transmit passwords or sensitive data over HTTP

### Audit Trails and Logging
- Maintain immutable audit logs for all transactions
- Log at least 3 years of transaction history
- Include: timestamp, user_id, action, amount, status, authorization
- Use append-only database, not modifiable logs

### Rate Limiting
- Implement rate limiting on authentication endpoints
- Limit login attempts to prevent brute force attacks
- Limit payment requests to prevent abuse
- Example: Max 5 login attempts per IP per 15 minutes

## IT Act 2000 & SPDI (Sensitive Personal Data/Information) Rules
All systems handling sensitive personal data must:

### Access Control
- Implement strong authentication (passwords, MFA)
- Enforce authorization checks before allowing access
- Log all access to sensitive data
- Prevent SQL injection and unauthorized queries

### Input Validation
- Validate and sanitize ALL user inputs
- Use parameterized queries to prevent SQL injection
- Prevent XSS through output encoding
- Validate data types, lengths, and formats

### Privacy Impact Assessment  
- Document how personal data flows through system
- Identify risks in data processing
- Implement controls for identified risks

### Data Leakage Prevention
- Never log personal data (email, phone, SSN)
- Remove sensitive data from API responses when not needed
- Use encrypted channels for data transmission
- Clean up logs after retention period expires

## SEBI Regulations (For Financial Systems)
### Market Manipulation Prevention
- No insider trading or front-running
- Equal access to market information
- Transparent pricing without hidden charges

### Transparency
- Disclose all charges and fees before transaction
- No selective disclosure of information to certain users
- All users receive information at the same time

## ISO 8000 Data Quality Standards
- Verify data accuracy before storage
- Maintain data integrity with checksums
- Regular data quality audits
- Handle data validation at entry and processing

## Implementation Checklist
"""
        
        # Add framework-specific requirements from new JSON structure
        for framework_data in frameworks:
            framework_name = framework_data.get("name", "Unknown Framework")
            framework_desc = framework_data.get("description", "")
            
            policy_text += f"\n### {framework_name}\n"
            if framework_desc:
                policy_text += f"{framework_desc}\n\n"
            
            rules = framework_data.get("rules", [])
            for rule in rules:
                rule_name = rule.get("name", "")
                description = rule.get("description", "")
                patterns = rule.get("patterns", [])
                remediation = rule.get("remediation", "")
                
                policy_text += f"\n#### {rule_name}\n"
                policy_text += f"{description}\n"
                
                if patterns:
                    policy_text += "Violations detected:\n"
                    for pattern in patterns[:3]:  # First 3 patterns
                        policy_text += f"  - {pattern}\n"
                
                if remediation:
                    policy_text += f"Remediation: {remediation}\n"
        
        logger.info(f"✓ Loaded Indian compliance policies ({len(policy_text)} chars)")
        return policy_text
        
    except Exception as e:
        logger.error(f"Failed to load Indian compliance policies: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return ""


def get_policy_by_framework(framework: str) -> str:
    """Get policy text for a specific framework"""
    policies = {
        "DPDPA": """
# DPDPA 2023 Compliance Requirements

## Consent Requirements (Section 7)
- Explicit consent before processing personal data
- Specific, informed, freely given consent required

## Purpose Limitation  
- Data only for disclosed purposes
- New consent needed for secondary uses

## Data Minimization
- Only necessary data collection
- Remove excessive fields (SSN, DOB, address)

## Breach Notification
- Notify within 72 hours
- Maintain detection mechanisms

## User Rights
- Right to access, correct, delete, export data
- Implement all user rights endpoints
""",
        "RBI": """
# RBI Information Security Guidelines

## Authorization Control
- Server-side authorization checks only
- Never trust client role/permission data
- Use JWT or session-based role validation

## Transaction Atomicity  
- All-or-nothing transactions
- Database-level locking for concurrency
- Prevent race conditions

## Encryption
- TLS 1.2+ for transit
- AES-256 at rest
- HTTPS only

## Audit Trails
- 3-year minimum retention
- Immutable append-only logs
- Log all transactions

## Rate Limiting
- Brute force protection
- API abuse prevention
- Account takeover protection
""",
        "IT_ACT": """
# IT Act 2000 & SPDI Rules

## Access Control
- Strong authentication required
- Authorization enforcement
- Access logging for sensitive data

## Input Validation
- Validate all sources
- Parameterized queries
- XSS and injection prevention

## PIA Requirements  
- Document data flows
- Risk identification
- Control implementation

## Data Leakage Prevention
- Never log PII
- Sanitize API responses
- Use encryption for transmission
"""
    }
    
    return policies.get(framework, "")
