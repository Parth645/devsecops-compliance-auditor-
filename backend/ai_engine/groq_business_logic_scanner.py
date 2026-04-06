"""
Groq Business Logic Scanner - AI-Driven Compliance Violation Detection
Analyzes code for business logic issues that directly map to policy violations
NOT just keyword matching - understands semantic vulnerabilities

Specifically designed for:
- DPDPA 2023 (Personal Data Protection)
- IT Act 2000 + SPDI Rules
- RBI Guidelines
- CERT-In Standards
"""

import logging
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from groq import Groq

logger = logging.getLogger(__name__)


class GroqBusinessLogicScanner:
    """
    AI-Driven Business Logic Scanner
    Detects compliance violations through semantic code analysis
    NOT through simple keyword matching
    
    Enhanced with Indian Compliance Rules (18 rules):
    - DPDPA 2023 (5 rules)
    - RBI Guidelines (5 rules)
    - IT Act 2000 + SPDI (3 rules)
    - SEBI Regulations (2 rules)
    - ISO 8000 (1 rule)
    - General Security (2 rules)
    """
    
    def __init__(self, api_key: str, rules_manager: Optional['IndianComplianceRulesManager'] = None, scan_raw_files: bool = True):
        """
        Initialize business logic scanner
        
        Args:
            api_key: Groq API key
            rules_manager: Optional IndianComplianceRulesManager for enhanced scanning
            scan_raw_files: Whether to scan raw files directly (default: True)
                           Set to False to only use Semgrep results verification
        """
        self.client = Groq(api_key=api_key)
        self.models = ["llama-3.1-8b-instant", "mixtral-8x7b-32768", "llama-3.3-70b-versatile"]
        self.model = self.models[0]  # Start with cheapest
        self.rules_manager = rules_manager
        self.scan_raw_files = scan_raw_files  # NEW: Control raw file scanning
        
        if not self.scan_raw_files:
            logger.info("✓ GroqBusinessLogicScanner initialized (raw file scanning DISABLED)")
        
        # Load rules manager if not provided
        if not self.rules_manager:
            try:
                from .indian_rules_manager import IndianComplianceRulesManager
                self.rules_manager = IndianComplianceRulesManager()
            except Exception as e:
                logger.warning(f"Could not load Indian rules manager: {e}")
                self.rules_manager = None
        
        # Compliance policy mappings
        self.compliance_mapping = {
            "DPDPA": {
                "consent_violation": {
                    "title": "Missing Consent Validation",
                    "severity": "critical",
                    "section": "Section 7 - Consent Requirement",
                    "requirement": "Explicit consent must be obtained before processing personal data"
                },
                "purpose_limitation": {
                    "title": "Purpose Limitation Breach",
                    "severity": "critical",
                    "section": "Purpose Limitation Principle",
                    "requirement": "Data cannot be used for purposes other than disclosed consent"
                },
                "data_minimization": {
                    "title": "Excessive Data Processing",
                    "severity": "high",
                    "section": "Data Minimization Principle",
                    "requirement": "Only necessary personal data should be processed"
                },
                "breach_notification": {
                    "title": "No Breach Detection/Notification",
                    "severity": "critical",
                    "section": "Section 8 - Data Breach Notification",
                    "requirement": "Notification required within 72 hours of discovering breach"
                },
                "retention_policy": {
                    "title": "No Retention/Deletion Policy",
                    "severity": "high",
                    "section": "Data Storage & Deletion",
                    "requirement": "Personal data must be deleted after purpose is fulfilled"
                },
                "user_rights": {
                    "title": "User Data Rights Not Implemented",
                    "severity": "critical",
                    "section": "Sections 16-18 - User Rights",
                    "requirement": "Users must be able to access, correct, and delete personal data"
                }
            },
            "RBI": {
                "authorization_bypass": {
                    "title": "Authorization Logic Vulnerability",
                    "severity": "critical",
                    "guideline": "RBI Information Security Guidelines",
                    "requirement": "Access control must not be bypassable or using client-controlled data"
                },
                "race_condition": {
                    "title": "Race Condition in Financial Transaction",
                    "severity": "critical",
                    "guideline": "Payment System Security",
                    "requirement": "Financial transactions must be atomic - no double-charging or race conditions"
                },
                "encryption_enforcement": {
                    "title": "Sensitive Data Not Encrypted",
                    "severity": "high",
                    "guideline": "Data Protection Standards",
                    "requirement": "All financial/customer data must be encrypted in transit and at rest"
                },
                "audit_trail": {
                    "title": "Insufficient Audit Logging",
                    "severity": "high",
                    "guideline": "Audit Trail Requirements",
                    "requirement": "All financial transactions must have immutable audit trail (3-year retention)"
                },
                "rate_limiting": {
                    "title": "Missing Rate Limiting",
                    "severity": "medium",
                    "guideline": "Security Hardening",
                    "requirement": "Must implement rate limiting to prevent brute force and DDoS"
                }
            },
            "IT_ACT": {
                "unauthorized_access": {
                    "title": "Unauthorized Data Access Risk",
                    "severity": "critical",
                    "rule": "SPDI Rules Section 4",
                    "requirement": "Only authorized users can access sensitive personal data"
                },
                "input_validation": {
                    "title": "Input Validation Missing",
                    "severity": "high",
                    "rule": "SPDI Rules Section 4.6",
                    "requirement": "All inputs must be validated to prevent injection attacks"
                },
                "pia_violation": {
                    "title": "Privacy Impact Assessment Not Evident",
                    "severity": "high",
                    "rule": "SPDI Rules",
                    "requirement": "PIA required for systems processing sensitive data"
                },
                "data_leakage": {
                    "title": "Potential Data Leakage",
                    "severity": "high",
                    "rule": "SPDI Rules - Data Protection",
                    "requirement": "Sensitive data exposure through logs, improper channels, or APIs"
                }
            }
        }
    
    async def scan_code_for_business_logic_issues(self, code_content: str, file_path: str, repo_context: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Scan code for business logic vulnerabilities that map to compliance violations
        
        Args:
            code_content: Source code to analyze
            file_path: Path to the file
            repo_context: Optional repository context (tech stack, framework, etc.)
            
        Returns:
            List of compliance-mapped violations
        """
        logger.info(f"[BUSINESS LOGIC SCAN] Analyzing {Path(file_path).name} for compliance violations...")
        
        # Build analysis prompt
        prompt = self._build_analysis_prompt(code_content, file_path, repo_context)
        
        # Call Groq for semantic analysis
        violations = await self._analyze_with_groq(prompt, file_path)
        
        logger.info(f"  ✓ Found {len(violations)} compliance-related business logic issues")
        
        return violations
    
    def _build_analysis_prompt(self, code_content: str, file_path: str, repo_context: Optional[Dict]) -> str:
        """Build detailed analysis prompt for Groq"""
        
        file_name = Path(file_path).name
        file_type = Path(file_path).suffix
        
        context_info = ""
        if repo_context:
            context_info = f"""
REPOSITORY CONTEXT:
- Tech Stack: {repo_context.get('tech_stack', 'unknown')}
- Framework: {repo_context.get('framework', 'unknown')}
- Application Type: {repo_context.get('app_type', 'unknown')}
- Previous Compliance Issues: {repo_context.get('compliance_history', 'none')}\n"""
        
        prompt = f"""You are a compliance and security expert analyzing code for POLICY VIOLATIONS.

FILE: {file_name} (Type: {file_type})
{context_info}

COMPLIANCE FRAMEWORKS TO CHECK:
1. DPDPA 2023 - Consent, Purpose Limitation, Data Minimization, Breach Notification
2. RBI Guidelines - Authorization, Transaction Integrity, Audit Trails, Encryption
3. IT Act 2000 + SPDI Rules - Access Control, Input Validation, Data Protection

ANALYZE THIS CODE FOR BUSINESS LOGIC VULNERABILITIES:
```
{code_content[:3000]}
```

For EACH compliance violation found, identify:
1. TYPE: What business logic issue exists?
   - Authorization bypass? (Client-controlled role checks)
   - Race condition? (Non-atomic operations on state)
   - Data leakage? (Sensitive data in wrong channels)
   - Consent gap? (Data processing without validation)
   - Retention gap? (No deletion mechanism)
   - Purpose violation? (Data used beyond intended scope)

2. COMPLIANCE MAPPING: Which policy does it violate?
   - DPDPA Section/Principle
   - RBI Guideline
   - IT Act / SPDI Rule

3. SEVERITY: Critical, High, Medium, Low

4. IMPACT: Specific compliance consequence

5. REMEDIATION: Exact code fix required

Respond with ONLY valid JSON array. No markdown, no explanations.
[
  {{
    "vulnerability_type": "authorization_bypass|race_condition|data_leakage|consent_gap|purpose_violation|retention_gap|input_validation|other",
    "business_logic_issue": "Detailed description of what's wrong",
    "code_evidence": "Actual problematic code snippet",
    "compliance_framework": "DPDPA|RBI|IT_ACT",
    "compliance_violation": "Specific section/principle violated",
    "severity": "critical|high|medium|low",
    "impact": "What compliance consequence occurs?",
    "remediation": "Exact fix or implementation required",
    "line_range": {{"start": 0, "end": 0}},
    "cwe": "CWE-639|CWE-362|CWE-200|CWE-213",
    "policy_section": "e.g., DPDPA Section 7, RBI Information Security Guidelines"
  }}
]"""
        
        return prompt
    
    async def _analyze_with_groq(self, prompt: str, file_path: str) -> List[Dict[str, Any]]:
        """Call Groq for semantic analysis"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert compliance auditor and security analyst.
Your task: Find REAL compliance violations in code through business logic analysis (not keywords).
Return ONLY valid JSON. No markdown, no code blocks, no explanations.
Focus on: Authorization, State Management, Data Flow, Compliance Requirements.
"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Low temperature for consistency
                max_tokens=3000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Strip markdown if present
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            violations = json.loads(result_text)
            if not isinstance(violations, list):
                violations = [violations]
            
            # Enrich with compliance metadata
            enriched_violations = []
            for violation in violations:
                enriched = self._enrich_with_compliance_policy(violation, file_path)
                enriched_violations.append(enriched)
            
            return enriched_violations
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Groq response: {e}")
            logger.debug(f"Response: {result_text[:500]}")
            return []
        except Exception as e:
            logger.error(f"Business logic scan failed: {e}")
            return []
    
    def _enrich_with_compliance_policy(self, violation: Dict[str, Any], file_path: str) -> Dict[str, Any]:
        """Enrich violation with detailed compliance policy information"""
        
        framework = violation.get("compliance_framework", "UNKNOWN")
        violation_type = violation.get("compliance_violation", "unknown")
        
        # Look up compliance policy
        policy_details = self.compliance_mapping.get(framework, {}).get(violation_type, {})
        
        enriched = {
            **violation,
            "file_path": str(file_path),
            "detector": "groq_business_logic_scanner",
            "analysis_type": "semantic_business_logic",
            "compliance_policy": {
                "framework": framework,
                "violation_type": violation_type,
                "title": policy_details.get("title", "Compliance Violation"),
                "requirement": policy_details.get("requirement", ""),
                "section": policy_details.get("section") or policy_details.get("guideline") or policy_details.get("rule", ""),
                "severity": violation.get("severity", "medium")
            },
            "evidence_chain": {
                "detector": "groq_business_logic_scanner",
                "analysis_method": "semantic_business_logic_analysis",
                "confidence": 0.85,
                "file_path": str(file_path)
            }
        }
        
        return enriched
    
    async def scan_codebase_for_policy_violations(self, repo_path: str, code_files: List[str], max_files: int = 20) -> List[Dict[str, Any]]:
        """
        Scan entire codebase for business logic compliance violations
        
        Args:
            repo_path: Repository root path
            code_files: List of all code files
            max_files: Max files to analyze (for performance)
            
        Returns:
            All compliance violations found via business logic analysis
        """
        # Check if raw file scanning is disabled
        if not self.scan_raw_files:
            logger.info("[CODEBASE SCAN] Raw file scanning is DISABLED - skipping")
            return []
        
        logger.info(f"[CODEBASE SCAN] Analyzing {min(len(code_files), max_files)} files for policy violations...")
        
        all_violations = []
        files_to_scan = code_files[:max_files]
        
        # Scan files by priority (auth > data > payment > other)
        priority_files = self._prioritize_files(files_to_scan)
        
        for i, file_path in enumerate(priority_files):
            logger.info(f"  [{i+1}/{len(priority_files)}] Scanning {Path(file_path).name}...")
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    code_content = f.read()
                
                if len(code_content) < 100:  # Skip tiny files
                    continue
                
                violations = await self.scan_code_for_business_logic_issues(
                    code_content,
                    file_path,
                    {"app_type": "backend_service"}
                )
                
                all_violations.extend(violations)
                
            except Exception as e:
                logger.debug(f"Error scanning {file_path}: {e}")
                continue
        
        logger.info(f"  ✓ Found {len(all_violations)} policy violations via business logic analysis")
        
        return all_violations
    
    def _prioritize_files(self, files: List[str]) -> List[str]:
        """Prioritize files by compliance risk (auth > data > payment > other)"""
        
        auth_files = []
        data_files = []
        payment_files = []
        other_files = []
        
        for file_path in files:
            name_lower = Path(file_path).name.lower()
            
            if any(x in name_lower for x in ["auth", "login", "permission", "role", "access"]):
                auth_files.append(file_path)
            elif any(x in name_lower for x in ["payment", "transaction", "billing", "charge", "refund"]):
                payment_files.append(file_path)
            elif any(x in name_lower for x in ["data", "db", "user", "profile", "personal"]):
                data_files.append(file_path)
            else:
                other_files.append(file_path)
        
        # Return in priority order
        return auth_files + payment_files + data_files + other_files
    
    def get_compliance_summary(self, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate compliance summary from violations"""
        
        by_framework = {}
        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        by_type = {}
        
        for violation in violations:
            # By framework
            framework = violation.get("compliance_framework", "unknown")
            by_framework[framework] = by_framework.get(framework, 0) + 1
            
            # By severity
            severity = violation.get("compliance_policy", {}).get("severity", "medium").lower()
            if severity in by_severity:
                by_severity[severity] += 1
            
            # By type
            v_type = violation.get("vulnerability_type", "unknown")
            by_type[v_type] = by_type.get(v_type, 0) + 1
        
        return {
            "total_violations": len(violations),
            "by_framework": by_framework,
            "by_severity": by_severity,
            "by_vulnerability_type": by_type,
            "compliance_risk_score": self._calculate_risk_score(by_severity)
        }
    
    def _calculate_risk_score(self, severity_breakdown: Dict[str, int]) -> float:
        """Calculate overall compliance risk score (0-100)"""
        
        critical_weight = severity_breakdown.get("critical", 0) * 30
        high_weight = severity_breakdown.get("high", 0) * 10
        medium_weight = severity_breakdown.get("medium", 0) * 3
        low_weight = severity_breakdown.get("low", 0) * 1
        
        total_weight = critical_weight + high_weight + medium_weight + low_weight
        risk_score = min(100, int(total_weight / 5))  # Normalize to 0-100
        
        return risk_score
