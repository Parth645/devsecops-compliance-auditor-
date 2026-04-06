"""
Model-Based Compliance Analyzer
Uses Groq AI to analyze specific business logic compliance by examining
route-model pairs rather than raw files
Implements targeted RAG (Retrieval-Augmented Generation) for token efficiency
"""

import logging
from typing import Dict, List, Any, Optional
import json
from groq import Groq

logger = logging.getLogger(__name__)


class ModelBasedComplianceAnalyzer:
    """
    Analyzes data models and routes for compliance violations
    Focuses on business logic rather than syntax
    Token-efficient by analyzing extracted data flows only
    """
    
    def __init__(self, api_key: str):
        """Initialize model-based analyzer with Groq"""
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"  # Powerful model for reasoning
        logger.info("✓ Model-Based Compliance Analyzer initialized")
    
    async def analyze_data_flows(self, flows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze extracted data flows for compliance violations
        
        Args:
            flows: List of data flow objects from DataFlowExtractor
            
        Returns:
            List of compliance violations found
        """
        violations = []
        
        if not flows:
            logger.info("[MODEL ANALYZER] No flows to analyze")
            return violations
        
        logger.info(f"[MODEL ANALYZER] Analyzing {len(flows)} data flows for compliance violations")
        
        for i, flow in enumerate(flows):
            logger.debug(f"[MODEL ANALYZER] Flow {i+1}/{len(flows)}: {flow}")
            result = await self._analyze_single_flow(flow)
            if result:
                logger.info(f"[MODEL ANALYZER] Found {len(result)} violations in flow {i+1}")
            violations.extend(result)
        
        logger.info(f"[MODEL ANALYZER] Total violations found: {len(violations)}")
        return violations
    
    async def _analyze_single_flow(self, flow: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze a single route → model data flow"""
        violations = []
        
        route_path = flow.get('route', '') or flow.get('route_path', '')
        model_name = flow.get('model', '') or flow.get('model_name', '')
        pii_fields = flow.get('pii_fields', [])
        
        # Skip if insufficient data
        if not pii_fields or not route_path or not model_name:
            logger.debug(f"Skipping flow analysis: route={route_path}, model={model_name}, pii_fields={pii_fields}")
            return violations
        
        logger.debug(f"Analyzing flow: {route_path} → {model_name} (PII: {pii_fields})")
        
        # Build prompt for Groq analysis
        prompt = self._build_compliance_prompt(route_path, model_name, pii_fields)
        
        if not prompt:
            logger.warning(f"Empty prompt generated for {route_path}")
            return violations
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an Indian compliance expert specializing in DPDPA 2023, RBI guidelines, and IT Act 2000. Analyze business logic for compliance violations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Deterministic responses
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content
            logger.debug(f"[MODEL ANALYZER] Groq response for {route_path}: {response_text[:100]}...")
            
            # Parse violations from response
            violations = self._parse_violations(response_text, route_path, model_name)
            
        except Exception as e:
            logger.error(f"Error analyzing flow {route_path}: {e}")
        
        return violations
    
    def _build_compliance_prompt(self, route_path: str, model_name: str, pii_fields: List[str]) -> str:
        """Build targeted compliance analysis prompt"""
        

        return f"""
COMPLIANCE ANALYSIS: Data Flow Assessment

**Context:**
- API Endpoint: {route_path} (likely POST/PUT to create/update {model_name})
- Database Model: {model_name}
- Personal Data Fields: {', '.join(pii_fields)}

**Your Task:**
Analyze this data flow against DPDPA 2023, RBI Guidelines, and IT Act 2000. 
For EACH compliance concern below, respond with either "PASS" or "VIOLATION: [explanation]"

**DPDPA 2023 Compliance Checks:**
1. CONSENT MANAGEMENT: Is there a mechanism to verify explicit user consent before processing {', '.join(pii_fields)}?
   - Look for: consent checks, opt-in fields, consent timestamp
   
2. PURPOSE LIMITATION: Are {', '.join(pii_fields)} collected for a single, specific purpose, or is there over-collection?
   - Flag: If endpoint accepts entire request body instead of specific fields
   
3. DATA MINIMIZATION: Is the {model_name} model collecting ONLY necessary fields, or are there unnecessary sensitive fields?
   - Example unnecessary fields: SSN, AADHAAR when not required for transaction
   
4. BREACH NOTIFICATION: Is access to {', '.join(pii_fields)} logged and auditable?
   - Look for: audit logs, timestamps, user tracking
   
5. USER RIGHTS: Can a user request deletion of their {', '.join(pii_fields)} via the API?
   - Check: Is there a DELETE endpoint for {route_path}?

**RBI Guidelines Checks (for financial data):**
1. AUTHORIZATION: Is the user verified via server-side session/token, NOT client-provided headers?
2. ENCRYPTION: Are {', '.join(pii_fields)} encrypted at rest in the database?
3. TRANSACTION ATOMICITY: If this is a transaction endpoint, is it atomic (no race conditions)?
4. AUDIT TRAIL: Are all {model_name} writes logged with timestamp and user ID?

**IT Act 2000 + SPDI Checks:**
1. INPUT VALIDATION: Are all input fields validated before storage?
2. UNAUTHORIZED ACCESS: Is there proper authorization check to prevent users accessing other users' {', '.join(pii_fields)}?

**Response Format:**
Return ONLY a JSON array with this structure:
[
  {{
    "rule": "dpdpa_consent_management",
    "status": "VIOLATION",
    "severity": "critical",
    "message": "No consent verification found in endpoint. Endpoint accepts {pii_fields} but no consent check exists.",
    "remediation": "Add consent verification before database write. Example: if (!user.consentGiven) throw Error('Consent required')"
  }}
]

If PASS for all checks, return empty array: []
"""
    
    def _parse_violations(self, response_text: str, route_path: str, model_name: str) -> List[Dict[str, Any]]:
        """Parse JSON violations from Groq response"""
        violations = []
        
        try:
            logger.debug(f"[MODEL ANALYZER] Raw Groq response (first 200 chars): {response_text[:200]}")
            
            # Strip markdown code blocks if present (Groq often wraps JSON in ```json ... ```)
            clean_text = response_text
            if "```json" in clean_text:
                clean_text = clean_text.replace("```json", "").replace("```", "")
            elif "```" in clean_text:
                clean_text = clean_text.split("```")[1]
            clean_text = clean_text.strip()
            
            logger.debug(f"[MODEL ANALYZER] After markdown stripping (first 200 chars): {clean_text[:200]}")
            
            # Extract JSON from response
            json_start = clean_text.find('[')
            json_end = clean_text.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = clean_text[json_start:json_end]
                logger.debug(f"[MODEL ANALYZER] Extracted JSON string: {json_str[:150]}")
                parsed = json.loads(json_str)
                logger.debug(f"[MODEL ANALYZER] Parsed {len(parsed)} violation objects from JSON")
                
                for violation in parsed:
                    violations.append({
                        'rule': violation.get('rule', 'unknown'),
                        'file': f'data_flow:{route_path}',
                        'line': 0,
                        'severity': violation.get('severity', 'medium'),
                        'framework': self._get_framework(violation.get('rule', '')),
                        'message': violation.get('message', ''),
                        'remediation': violation.get('remediation', ''),
                        'type': 'business_logic'
                    })
            else:
                logger.warning(f"[MODEL ANALYZER] No JSON array found in Groq response for {route_path}")
        
        except json.JSONDecodeError as e:
            logger.warning(f"[MODEL ANALYZER] JSON parse error for {route_path}: {e}")
            logger.debug(f"[MODEL ANALYZER] Response text that failed to parse: {clean_text[:300]}")
        except Exception as e:
            logger.error(f"[MODEL ANALYZER] Unexpected error parsing violations for {route_path}: {e}", exc_info=True)
        
        return violations
    
    @staticmethod
    def _get_framework(rule: str) -> str:
        """Get compliance framework from rule name"""
        if 'dpdpa' in rule.lower():
            return 'DPDPA'
        elif 'rbi' in rule.lower():
            return 'RBI'
        elif 'it_act' in rule.lower() or 'spdi' in rule.lower():
            return 'IT Act 2000'
        elif 'sebi' in rule.lower():
            return 'SEBI'
        else:
            return 'General'


class ComplianceRuleExtractor:
    """
    Extracts compliance requirements from data flows
    Creates targeted prompts for specific compliance rules
    """
    
    COMPLIANCE_RULES = {
        'dpdpa_consent': {
            'framework': 'DPDPA',
            'section': 'Section 7',
            'requirement': 'Explicit consent required before processing personal data',
            'indicators': ['consent', 'permission', 'opt-in', 'agree', 'accept']
        },
        'dpdpa_purpose': {
            'framework': 'DPDPA',
            'section': 'Purpose Limitation',
            'requirement': 'Data cannot be used for purposes other than disclosed',
            'indicators': ['purpose', 'scope', 'use_case', 'disclosure']
        },
        'dpdpa_minimization': {
            'framework': 'DPDPA',
            'section': 'Data Minimization',
            'requirement': 'Only necessary personal data should be processed',
            'indicators': ['minimize', 'necessary', 'required', 'essential']
        },
        'dpdpa_breach': {
            'framework': 'DPDPA',
            'section': 'Section 8',
            'requirement': 'Data breach notification required within 72 hours',
            'indicators': ['breach', 'incident', 'unauthorized_access', 'exposure']
        },
        'dpdpa_retention': {
            'framework': 'DPDPA',
            'section': 'Data Storage & Deletion',
            'requirement': 'Personal data must be deleted after purpose fulfilled',
            'indicators': ['delete', 'retention', 'expiry', 'purge', 'archive']
        },
        'dpdpa_rights': {
            'framework': 'DPDPA',
            'section': 'Sections 16-18',
            'requirement': 'Users must access, correct, and delete personal data',
            'indicators': ['access', 'correction', 'deletion', 'portability', 'export']
        },
        'rbi_authorization': {
            'framework': 'RBI',
            'guideline': 'Information Security Guidelines',
            'requirement': 'Access control must be robust, server-side verified',
            'indicators': ['authorization', 'access_control', 'authentication', 'privilege']
        },
        'rbi_atomicity': {
            'framework': 'RBI',
            'guideline': 'Payment System Security',
            'requirement': 'Financial transactions must be atomic',
            'indicators': ['transaction', 'transfer', 'payment', 'debit', 'credit']
        },
        'rbi_encryption': {
            'framework': 'RBI',
            'guideline': 'Data Protection Standards',
            'requirement': 'All sensitive data must be encrypted',
            'indicators': ['encrypt', 'cipher', 'secure', 'tls', 'ssl']
        },
        'rbi_audit': {
            'framework': 'RBI',
            'guideline': 'Audit Trail Requirements',
            'requirement': 'All financial transactions logged (3-year retention)',
            'indicators': ['audit', 'log', 'trace', 'record', 'history']
        },
        'it_act_input': {
            'framework': 'IT Act 2000',
            'rule': 'SPDI Rules Section 4.6',
            'requirement': 'All inputs must be validated',
            'indicators': ['validate', 'sanitize', 'escape', 'filter', 'check']
        },
        'it_act_access': {
            'framework': 'IT Act 2000',
            'rule': 'SPDI Rules Section 4',
            'requirement': 'Only authorized users can access sensitive data',
            'indicators': ['access_control', 'permission', 'role', 'privilege']
        }
    }
    
    @classmethod
    def extract_relevant_rules(cls, pii_fields: List[str], route_method: str) -> List[str]:
        """Extract relevant compliance rules based on data flow"""
        relevant = []
        
        # All routes with PII should have DPDPA consent
        relevant.append('dpdpa_consent')
        relevant.append('dpdpa_minimization')
        
        # If endpoint is POST/PUT, check retention and deletion
        if route_method in ['POST', 'PUT', 'PATCH']:
            relevant.append('dpdpa_retention')
            relevant.append('dpdpa_rights')
        
        # Financial data → RBI rules
        financial_keywords = ['payment', 'transaction', 'account', 'transfer', 'card']
        if any(kw in ' '.join(pii_fields).lower() for kw in financial_keywords):
            relevant.append('rbi_authorization')
            relevant.append('rbi_atomicity')
            relevant.append('rbi_audit')
        
        # All data → encryption and input validation
        relevant.append('rbi_encryption')
        relevant.append('it_act_input')
        relevant.append('it_act_access')
        
        return relevant
