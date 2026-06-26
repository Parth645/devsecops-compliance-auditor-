"""
Groq Remediation Engine - Generates fixes for compliance violations
Optimized for token efficiency and proper JSON output
"""

import logging
import json
from typing import Dict, List, Any, Optional
from groq import Groq
import os

logger = logging.getLogger(__name__)


class GroqRemediationEngine:
    """
    Generates remediation suggestions for compliance violations
    - Token-efficient batching
    - Structured JSON output
    - Framework-specific fixes
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not set")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"  # Best for code generation
        
        # Token limits per batch
        self.max_tokens_per_request = 6000  # Conservative limit
        self.max_violations_per_batch = 5  # Process 5 at a time
        
        logger.info("✓ Groq Remediation Engine initialized")
    
    async def generate_remediation(
        self,
        violations: List[Dict[str, Any]],
        repo_context: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Generate remediation for violations with token management
        
        Args:
            violations: List of violations to fix
            repo_context: Repository context for better fixes
            
        Returns:
            Violations with added remediation field
        """
        if not violations:
            return []
        
        logger.info(f"[REMEDIATION] Generating fixes for {len(violations)} violations")
        
        # Process in batches to avoid token limits
        remediated = []
        for i in range(0, len(violations), self.max_violations_per_batch):
            batch = violations[i:i + self.max_violations_per_batch]
            logger.info(f"  Processing batch {i//self.max_violations_per_batch + 1}/{(len(violations)-1)//self.max_violations_per_batch + 1}")
            
            try:
                batch_remediated = await self._process_batch(batch, repo_context)
                remediated.extend(batch_remediated)
            except Exception as e:
                logger.error(f"  Batch remediation failed: {e}")
                # Return original violations without remediation
                remediated.extend(batch)
        
        logger.info(f"  ✓ Generated {len(remediated)} remediations")
        return remediated
    
    async def _process_batch(
        self,
        violations: List[Dict[str, Any]],
        repo_context: str
    ) -> List[Dict[str, Any]]:
        """Process a batch of violations"""
        
        # Build compact prompt
        prompt = self._build_remediation_prompt(violations, repo_context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a security remediation expert. Generate secure code fixes for compliance violations. Output ONLY valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Low for consistent fixes
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            # Merge remediations back into violations
            remediations = result.get("remediations", [])
            for i, violation in enumerate(violations):
                if i < len(remediations):
                    violation["remediation"] = remediations[i]
                else:
                    violation["remediation"] = self._get_default_remediation(violation)
            
            return violations
            
        except Exception as e:
            logger.error(f"Remediation generation failed: {e}")
            # Add default remediations
            for violation in violations:
                violation["remediation"] = self._get_default_remediation(violation)
            return violations
    
    def _build_remediation_prompt(
        self,
        violations: List[Dict[str, Any]],
        repo_context: str
    ) -> str:
        """Build token-efficient prompt"""
        
        violations_summary = []
        for i, v in enumerate(violations, 1):
            violations_summary.append({
                "id": i,
                "rule": v.get("rule_id", "unknown"),
                "file": v.get("file_path", "unknown").split("/")[-1],  # Just filename
                "line": v.get("line_number", 0),
                "code": v.get("code_snippet", "")[:200],  # Limit code snippet
                "framework": v.get("metadata", {}).get("framework", "GENERAL")
            })
        
        prompt = f"""Generate secure code fixes for these {len(violations)} compliance violations.

Violations:
{json.dumps(violations_summary, indent=2)}

For each violation, provide:
1. fixed_code: The corrected code snippet
2. explanation: Brief explanation (1-2 sentences)
3. steps: List of 2-3 implementation steps

Output JSON format:
{{
  "remediations": [
    {{
      "violation_id": 1,
      "fixed_code": "const apiKey = process.env.API_KEY;",
      "explanation": "Moved API key to environment variable for security.",
      "steps": [
        "Create .env file with API_KEY=your_key",
        "Install dotenv: npm install dotenv",
        "Load in code: require('dotenv').config()"
      ],
      "priority": "HIGH"
    }}
  ]
}}

Keep fixes concise and production-ready."""
        
        return prompt
    
    def _get_default_remediation(self, violation: Dict[str, Any]) -> Dict[str, Any]:
        """Get default remediation based on rule"""
        
        rule_id = violation.get("rule_id", "")
        metadata = violation.get("metadata", {})
        
        # Default remediations by rule type
        defaults = {
            "hardcoded-api-key": {
                "fixed_code": "const apiKey = process.env.API_KEY;",
                "explanation": "Use environment variables to store sensitive credentials.",
                "steps": [
                    "Create .env file with API_KEY=your_key",
                    "Install dotenv package",
                    "Load environment variables in your application"
                ],
                "priority": "CRITICAL"
            },
            "sql-injection": {
                "fixed_code": "db.query('SELECT * FROM users WHERE id = ?', [userId])",
                "explanation": "Use parameterized queries to prevent SQL injection.",
                "steps": [
                    "Replace string concatenation with parameterized query",
                    "Use ? placeholders for values",
                    "Pass values as array parameter"
                ],
                "priority": "CRITICAL"
            },
            "weak-hash-md5": {
                "fixed_code": "const hash = crypto.createHash('sha256').update(data).digest('hex');",
                "explanation": "Replace MD5 with SHA-256 or better.",
                "steps": [
                    "Import crypto module",
                    "Replace md5 with sha256",
                    "Update any hash verification logic"
                ],
                "priority": "HIGH"
            },
            "no-input-validation": {
                "fixed_code": "const userId = validateUserId(req.body.id);",
                "explanation": "Validate all user input before processing.",
                "steps": [
                    "Create validation function",
                    "Check input type and format",
                    "Return error for invalid input"
                ],
                "priority": "HIGH"
            }
        }
        
        # Find matching default
        for key, default in defaults.items():
            if key in rule_id:
                return default
        
        # Generic default
        return {
            "fixed_code": metadata.get("fix", "// Apply security best practices"),
            "explanation": f"Fix {rule_id} violation according to {metadata.get('framework', 'security')} guidelines.",
            "steps": [
                "Review the violation details",
                "Apply recommended fix from documentation",
                "Test the changes thoroughly"
            ],
            "priority": "MEDIUM"
        }
    
    def get_remediation_summary(self, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of remediations"""
        
        total = len(violations)
        by_priority = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        by_framework = {}
        
        for v in violations:
            remediation = v.get("remediation", {})
            priority = remediation.get("priority", "MEDIUM")
            by_priority[priority] = by_priority.get(priority, 0) + 1
            
            framework = v.get("metadata", {}).get("framework", "GENERAL")
            by_framework[framework] = by_framework.get(framework, 0) + 1
        
        return {
            "total_violations": total,
            "by_priority": by_priority,
            "by_framework": by_framework,
            "estimated_fix_time_hours": total * 0.5  # Estimate 30 min per fix
        }
