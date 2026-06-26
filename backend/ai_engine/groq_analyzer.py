"""
Groq AI Analyzer for Indian Compliance
Handles DPDP Act, RBI regulations, and other Indian compliance requirements
Uses Groq API for fast LLM-powered analysis
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
from groq import Groq

logger = logging.getLogger(__name__)

class GroqIndianComplianceAnalyzer:
    """
    Groq-powered analyzer for Indian compliance frameworks
    - DPDP (Digital Personal Data Protection) Act
    - RBI (Reserve Bank of India) Regulations
    - Company Law and IT Act
    - Data localization requirements
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "mixtral-8x7b-32768"):
        """
        Initialize Groq analyzer for Indian compliance
        
        Args:
            api_key: Groq API key (falls back to env variable)
            model: Groq model to use
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = Groq(api_key=self.api_key)
        self.model = model
        self.org_region = "india"
        
        # Indian compliance frameworks
        self.frameworks = {
            "dpdp": {
                "name": "Digital Personal Data Protection Act 2023",
                "key_areas": [
                    "Personal data processing consent",
                    "Data fiduciary and data processor responsibilities",
                    "Data breach notification (72 hours)",
                    "Processing of sensitive personal data",
                    "Cross-border data transfers",
                    "User rights and grievance redressal"
                ],
                "penalties": {
                    "minor": "Up to ₹2 crore or 2% annual turnover",
                    "major": "Up to ₹5 crore or 5% annual turnover"
                }
            },
            "rbi": {
                "name": "Reserve Bank of India Regulations",
                "key_areas": [
                    "Data localization for financial data",
                    "Cybersecurity framework",
                    "Payment system compliance",
                    "Third-party service provider management",
                    "Data residency requirements",
                    "Audit and reporting requirements"
                ],
                "penalties": {
                    "minor": "₹1-5 lakh",
                    "major": "₹5+ lakh and action against license"
                }
            },
            "it_act": {
                "name": "Information Technology Act 2000",
                "key_areas": [
                    "Data security measures (Section 43A)",
                    "Personal data protection",
                    "Intermediary guidelines",
                    "Cybersecurity obligations",
                    "Data breach reporting"
                ],
                "penalties": {
                    "minor": "Up to ₹2 lakh",
                    "major": "Up to ₹5 lakh"
                }
            }
        }
        
        logger.info(f"✓ Groq Analyzer initialized with model: {self.model}")
        logger.info(f"✓ Compliance frameworks loaded: {list(self.frameworks.keys())}")
    
    async def analyze_code_for_compliance(
        self, 
        code_snippet: str, 
        file_type: str = "python",
        frameworks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze code for Indian compliance violations
        
        Args:
            code_snippet: Code to analyze
            file_type: Type of code (python, javascript, java, etc.)
            frameworks: List of frameworks to check (default: all)
            
        Returns:
            Compliance analysis results
        """
        if frameworks is None:
            frameworks = list(self.frameworks.keys())
        
        logger.info(f"Analyzing {file_type} code for {len(frameworks)} compliance frameworks")
        
        prompt = self._build_analysis_prompt(code_snippet, file_type, frameworks)
        
        try:
            response = await self._call_groq_api(prompt)
            analysis = self._parse_analysis_response(response, frameworks)
            
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "file_type": file_type,
                "frameworks_checked": frameworks,
                "analysis": analysis,
                "severity_summary": self._calculate_severity_summary(analysis)
            }
        except Exception as e:
            logger.error(f"Groq analysis failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _build_analysis_prompt(
        self, 
        code: str, 
        file_type: str, 
        frameworks: List[str]
    ) -> str:
        """Build analysis prompt for Groq"""
        frameworks_info = "\n".join([
            f"- {self.frameworks[f]['name']}: {', '.join(self.frameworks[f]['key_areas'][:3])}"
            for f in frameworks if f in self.frameworks
        ])
        
        prompt = f"""You are an expert Indian compliance analyst specializing in data protection and financial regulations.

Analyze the following {file_type} code for compliance violations with Indian regulations:

FRAMEWORKS TO CHECK:
{frameworks_info}

CODE TO ANALYZE:
```{file_type}
{code}
```

Provide analysis in the following JSON format:
{{
    "violations": [
        {{
            "framework": "framework_name",
            "violation": "description of violation",
            "severity": "critical|high|medium|low",
            "impact": "business impact description",
            "requirement": "specific regulation requirement",
            "remediation": "how to fix this"
        }}
    ],
    "compliance_score": 0-100,
    "data_handling_assessment": {{
        "data_collection": "assessment",
        "data_storage": "assessment",
        "data_transfer": "assessment",
        "user_consent": "assessment"
    }},
    "recommendations": ["recommendation1", "recommendation2"],
    "risk_level": "critical|high|medium|low"
}}

Be specific and cite the exact regulation requiring changes."""
        
        return prompt
    
    async def _call_groq_api(self, prompt: str, max_tokens: int = 2000) -> str:
        """Call Groq API"""
        try:
            message = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=max_tokens,
                top_p=0.9,
            )
            return message.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise
    
    def _parse_analysis_response(
        self, 
        response: str, 
        frameworks: List[str]
    ) -> Dict[str, Any]:
        """Parse Groq response"""
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            analysis = json.loads(json_str)
            
            # Validate and enhance analysis
            if "violations" not in analysis:
                analysis["violations"] = []
            if "compliance_score" not in analysis:
                analysis["compliance_score"] = 50
            if "risk_level" not in analysis:
                analysis["risk_level"] = "medium"
            
            return analysis
        except Exception as e:
            logger.warning(f"Failed to parse Groq response: {e}")
            return {
                "violations": [],
                "compliance_score": 50,
                "risk_level": "medium",
                "raw_response": response[:500]
            }
    
    def _calculate_severity_summary(self, analysis: Dict) -> Dict[str, int]:
        """Calculate severity summary from violations"""
        summary = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "total": 0
        }
        
        for violation in analysis.get("violations", []):
            severity = violation.get("severity", "low").lower()
            if severity in summary:
                summary[severity] += 1
            summary["total"] += 1
        
        return summary
    
    async def analyze_data_handling(
        self, 
        code: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Specific analysis for data handling in code (DPDP compliance)
        
        Args:
            code: Code to analyze
            context: Additional context about data being handled
            
        Returns:
            Data handling assessment
        """
        logger.info("Analyzing data handling practices for DPDP compliance")
        
        context_str = json.dumps(context) if context else ""
        
        prompt = f"""Analyze this code for DPDP (Digital Personal Data Protection Act) compliance issues related to data handling.

Additional Context: {context_str}

CODE:
```
{code}
```

Check for:
1. Explicit user consent for data collection
2. Data minimization principles
3. Purpose limitation
4. Secure data storage (encryption)
5. Data retention policies
6. User rights implementation (access, deletion, portability)
7. Data breach notification readiness
8. Processing agreement with vendors

Return JSON with format:
{{
    "dpdp_compliance_status": "compliant|partial|non_compliant",
    "consent_management": {{"status": "", "issues": []}},
    "data_security": {{"status": "", "issues": []}},
    "user_rights": {{"status": "", "issues": []}},
    "critical_issues": [],
    "recommendations": [],
    "overall_assessment": ""
}}"""

        try:
            response = await self._call_groq_api(prompt, max_tokens=1500)
            return self._parse_analysis_response({"raw": response}, ["dpdp"])
        except Exception as e:
            logger.error(f"Data handling analysis failed: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def check_rbi_compliance(
        self, 
        code: str, 
        system_type: str = "payment_system"
    ) -> Dict[str, Any]:
        """
        Check RBI compliance for financial systems
        
        Args:
            code: Code to analyze
            system_type: Type of system (payment_system, data_processor, etc.)
            
        Returns:
            RBI compliance assessment
        """
        logger.info(f"Checking RBI compliance for {system_type}")
        
        prompt = f"""Check this code for RBI (Reserve Bank of India) compliance requirements.

System Type: {system_type}

CODE:
```
{code}
```

RBI Compliance Areas:
1. Data localization (India-based storage for financial transactions)
2. Cybersecurity framework implementation
3. Third-party service provider security controls
4. Encryption standards (AES-256 minimum)
5. Audit trail and logging
6. Disaster recovery and business continuity
7. Incident response procedures
8. Regulatory reporting capabilities

Return JSON:
{{
    "rbi_compliant": true|false,
    "data_localization": {{"compliant": "", "details": ""}},
    "cybersecurity": {{"compliant": "", "details": ""}},
    "audit_capabilities": {{"compliant": "", "details": ""}},
    "critical_gaps": [],
    "remediation_plan": [],
    "timeline_for_compliance": ""
}}"""

        try:
            response = await self._call_groq_api(prompt, max_tokens=1500)
            return self._parse_analysis_response({"raw": response}, ["rbi"])
        except Exception as e:
            logger.error(f"RBI compliance check failed: {e}")
            return {"error": str(e), "rbi_compliant": False}
    
    async def generate_remediation_steps(
        self, 
        violation: Dict[str, Any],
        code: str
    ) -> Dict[str, Any]:
        """
        Generate specific remediation steps for a violation
        
        Args:
            violation: The compliance violation
            code: The problematic code
            
        Returns:
            Detailed remediation steps
        """
        logger.info(f"Generating remediation for {violation.get('framework')} violation")
        
        prompt = f"""Generate specific, actionable remediation steps for this Indian compliance violation.

VIOLATION:
Framework: {violation.get('framework')}
Issue: {violation.get('violation')}
Requirement: {violation.get('requirement')}

PROBLEMATIC CODE:
```
{code}
```

Provide step-by-step remediation with:
1. Code examples showing the fix
2. Configuration changes needed
3. Dependencies to add
4. Security best practices
5. Testing approach
6. Timeline for implementation

Return JSON:
{{
    "remediation_steps": [
        {{"step": 1, "description": "", "code_example": "", "effort": "high|medium|low"}}
    ],
    "dependencies": [],
    "security_implications": "",
    "estimated_effort": "",
    "compliance_impact": ""
}}"""

        try:
            response = await self._call_groq_api(prompt, max_tokens=2000)
            return self._parse_analysis_response({"raw": response}, [violation.get("framework")])
        except Exception as e:
            logger.error(f"Remediation generation failed: {e}")
            return {"error": str(e)}
    
    def get_compliance_status_report(self) -> Dict[str, Any]:
        """Get system compliance status report"""
        return {
            "analyzer": "Groq",
            "region": "India",
            "frameworks": list(self.frameworks.keys()),
            "model": self.model,
            "capabilities": [
                "DPDP Act compliance checking",
                "RBI regulation verification",
                "Data handling assessment",
                "Remediation suggestions",
                "Risk scoring",
                "Compliance reporting"
            ],
            "last_updated": datetime.now().isoformat()
        }
