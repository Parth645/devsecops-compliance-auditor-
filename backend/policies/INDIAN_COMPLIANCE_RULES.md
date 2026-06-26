# Indian Compliance Rules Documentation

## Overview

This document describes the comprehensive set of Indian compliance rules implemented for the DevSecOps Compliance Auditor. These rules cover major Indian regulatory frameworks and international standards applicable to Indian organizations.

## Frameworks Covered

### 1. Digital Personal Data Protection Act 2023 (DPDPA)
**Total Rules: 7 (4 Critical, 3 High)**

India's comprehensive data protection law that regulates the processing of digital personal data.

#### Rules:
- **DPDPA-001**: Consent Management (Critical)
- **DPDPA-002**: Purpose Limitation (High)
- **DPDPA-003**: Data Minimization (High)
- **DPDPA-004**: Breach Notification (Critical)
- **DPDPA-005**: User Rights Implementation (High)
- **DPDPA-006**: Data Localization (High)
- **DPDPA-007**: Children's Data Protection (Critical)

### 2. Information Technology Act 2000 (IT Act)
**Total Rules: 6 (3 Critical, 3 High)**

India's primary law for cybersecurity, electronic commerce, and digital crimes.

#### Rules:
- **ITA-001**: Unauthorized Access Prevention (Critical)
- **ITA-002**: Data Protection and Privacy (Critical)
- **ITA-003**: Secure Communication (High)
- **ITA-004**: Input Validation (High)
- **ITA-005**: Audit Trail Requirements (High)
- **ITA-006**: Password Security (Critical)

### 3. Reserve Bank of India Guidelines (RBI)
**Total Rules: 7 (4 Critical, 3 High)**

RBI's cybersecurity and digital payment security guidelines for financial institutions.

#### Rules:
- **RBI-001**: Strong Authentication (Critical)
- **RBI-002**: Transaction Atomicity (Critical)
- **RBI-003**: Encryption Standards (Critical)
- **RBI-004**: Payment Data Security (Critical)
- **RBI-005**: Rate Limiting (High)
- **RBI-006**: Session Management (High)
- **RBI-007**: Transaction Monitoring (High)

### 4. Securities and Exchange Board of India (SEBI)
**Total Rules: 3 (2 Critical, 1 High)**

SEBI's cybersecurity guidelines for financial market participants.

#### Rules:
- **SEBI-001**: Market Data Protection (Critical)
- **SEBI-002**: Trading System Security (Critical)
- **SEBI-003**: Audit and Compliance Logging (High)

### 5. ISO 27001 Information Security
**Total Rules: 4 (0 Critical, 4 High)**

International standard for information security management systems.

#### Rules:
- **ISO-001**: Access Control Policy (High)
- **ISO-002**: Cryptographic Controls (High)
- **ISO-003**: Secure Development (High)
- **ISO-004**: Incident Management (High)

### 6. CERT-In Guidelines
**Total Rules: 3 (1 Critical, 2 High)**

Indian Computer Emergency Response Team cybersecurity guidelines.

#### Rules:
- **CERTIN-001**: Vulnerability Management (High)
- **CERTIN-002**: Incident Reporting (Critical)
- **CERTIN-003**: Log Retention (High)

## Rule Structure

Each rule contains the following fields:

```json
{
  "id": "DPDPA-001",
  "name": "Consent Management",
  "severity": "critical",
  "description": "Ensure explicit user consent is obtained before processing personal data",
  "category": "data-protection",
  "cwe": ["CWE-359"],
  "owasp": ["A01:2021"],
  "patterns": [
    "Missing consent validation before data collection",
    "No consent tracking mechanism",
    "Implicit consent without user action"
  ],
  "remediation": "Implement explicit consent mechanism with clear opt-in/opt-out options and maintain consent records"
}
```

### Field Descriptions:

- **id**: Unique identifier for the rule
- **name**: Short, descriptive name
- **severity**: critical, high, medium, or low
- **description**: Detailed explanation of the requirement
- **category**: Classification (data-protection, authentication, cryptography, etc.)
- **cwe**: Common Weakness Enumeration IDs
- **owasp**: OWASP Top 10 mappings
- **patterns**: List of violation patterns to detect
- **remediation**: Recommended fix/solution

## Severity Levels

### Critical (13 rules)
Issues that pose immediate security risks or severe compliance violations:
- Data breaches
- Unauthorized access
- Missing encryption
- Authentication failures
- Payment security issues

### High (17 rules)
Significant security or compliance issues that should be addressed promptly:
- Input validation
- Session management
- Audit logging
- Access controls
- Data minimization

## Usage

### Loading Rules in Python

```python
from ai_engine.indian_rules_manager import IndianComplianceRulesManager

# Initialize manager
manager = IndianComplianceRulesManager()

# Get all frameworks
frameworks = manager.get_frameworks()

# Get rules by framework
dpdpa_rules = manager.get_rules_by_framework("Digital Personal Data Protection Act 2023")

# Get critical rules
critical_rules = manager.get_critical_rules()

# Get specific rule
rule = manager.get_rule("DPDPA-001")

# Find matching rules by keywords
matching = manager.find_matching_rules(["consent", "data", "collection"])
```

### Integration with Semgrep

The rules are also available in Semgrep YAML format at:
`backend/policies/indian_compliance_rules_complete.yaml`

This allows for static code analysis using Semgrep's pattern matching engine.

## Compliance Mapping

### CWE (Common Weakness Enumeration)
Rules are mapped to relevant CWE IDs for standardized vulnerability classification:
- CWE-284: Improper Access Control
- CWE-287: Improper Authentication
- CWE-311: Missing Encryption
- CWE-359: Exposure of Private Information
- CWE-778: Insufficient Logging
- And more...

### OWASP Top 10 (2021)
Rules are mapped to OWASP Top 10 categories:
- A01:2021 - Broken Access Control
- A02:2021 - Cryptographic Failures
- A03:2021 - Injection
- A04:2021 - Insecure Design
- A07:2021 - Identification and Authentication Failures
- A09:2021 - Security Logging and Monitoring Failures

## Supported Languages

The rules are designed to work with multiple programming languages:
- Python
- JavaScript/Node.js
- Java
- Go
- Ruby
- PHP

## Testing

Run the test script to verify rules are loaded correctly:

```bash
cd backend
python test_indian_rules.py
```

Expected output:
```
✓ Rules file found
✓ JSON loaded successfully
✓ Found 6 frameworks
✓ Total Rules: 30
✓ Critical: 13
✓ High: 17
✅ All tests passed!
```

## Updates and Maintenance

### Version History
- **v1.0.0** (2024-01-15): Initial release with 30 rules across 6 frameworks

### Adding New Rules

To add a new rule:

1. Edit `backend/policies/indian_compliance_rules.json`
2. Add the rule to the appropriate framework
3. Follow the existing structure
4. Run `python test_indian_rules.py` to validate
5. Update the Semgrep YAML if needed

### Rule Categories

Available categories:
- `data-protection`: Data privacy and protection
- `access-control`: Authentication and authorization
- `cryptography`: Encryption and key management
- `input-validation`: Input sanitization and validation
- `logging`: Audit trails and monitoring
- `session-management`: Session handling
- `transaction-security`: Financial transaction security
- `incident-response`: Incident detection and response
- `vulnerability-management`: Vulnerability scanning and patching
- `secure-development`: SDLC security practices
- `system-security`: Infrastructure and system security
- `monitoring`: Real-time monitoring and alerting

## References

### Official Documentation
- [DPDPA 2023](https://www.meity.gov.in/writereaddata/files/Digital%20Personal%20Data%20Protection%20Act%202023.pdf)
- [IT Act 2000](https://www.indiacode.nic.in/handle/123456789/1999)
- [RBI Cyber Security Framework](https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=10435)
- [SEBI Cyber Security Guidelines](https://www.sebi.gov.in/legal/circulars/apr-2018/cyber-security-and-cyber-resilience-framework-of-stock-exchanges-clearing-corporations-and-depositories_38623.html)
- [ISO 27001](https://www.iso.org/isoiec-27001-information-security.html)
- [CERT-In Directions](https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf)

### Additional Resources
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Database](https://cwe.mitre.org/)
- [Semgrep Rules](https://semgrep.dev/docs/writing-rules/overview/)

## Support

For questions or issues:
1. Check the test script output
2. Review the JSON structure
3. Verify file paths are correct
4. Check logs for detailed error messages

## License

These rules are provided for compliance auditing purposes. Organizations should consult with legal counsel to ensure full compliance with applicable regulations.
