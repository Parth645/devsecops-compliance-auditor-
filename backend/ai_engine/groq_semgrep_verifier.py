"""
Groq Semgrep Verifier - Step 3.5: Verify Semgrep Findings with AI
Takes Semgrep JSON output, extracts code_snippet and message, sends to Groq for proof-checking
"""

import logging
import json
from typing import Dict, List, Any, Optional
from groq import Groq

logger = logging.getLogger(__name__)


class GroqSemgrepVerifier:
    """
    Proof-checking layer: Takes Semgrep findings and verifies them with Groq LLM
    
    Flow:
    1. Semgrep finds potential violations (pattern-based)
    2. Extract code_snippet and message from Semgrep JSON
    3. Send to Groq for semantic verification
    4. Groq confirms if it's a real violation or false positive
    5. Return verified findings with confidence scores
    """
    
    def __init__(self, api_key: str, rules_manager=None):
        """Initialize Groq verifier with model fallback strategy"""
        self.client = Groq(api_key=api_key)
        # Priority: Strong reasoning model first for accurate verification
        # Fallback to cheaper models if rate limited
        self.models = [
            "llama-3.3-70b-versatile",    # Primary: Best reasoning for auditing
            "mixtral-8x7b-32768",         # Fallback: Balanced speed/quality
            "qwen/qwen3-32b",             # Fallback: Good reasoning capability
            "llama-3.1-8b-instant"        # Last resort: Fast but less rigorous
        ]
        self.model = self.models[0]  # Start with strongest model
        self.rules_manager = rules_manager
        logger.info(f"✓ GroqSemgrepVerifier initialized (using model: {self.model})")
    
    async def verify_semgrep_findings(self, semgrep_findings: List[Dict], repo_context: str = "") -> List[Dict]:
        """
        Verify Semgrep findings using Groq
        
        Args:
            semgrep_findings: List of findings from Semgrep
            repo_context: Additional context about the repository
            
        Returns:
            List of verified findings with confidence scores
        """
        if not semgrep_findings:
            logger.info("  ℹ No Semgrep findings to verify")
            return []
        
        logger.info(f"[VERIFY] Proof-checking {len(semgrep_findings)} Semgrep findings with Groq...")
        
        verified_findings = []
        batch_size = 10  # Increased from 5 to 10 for better throughput
        max_findings = min(len(semgrep_findings), 50)  # Process up to 50 findings
        
        logger.info(f"  Processing {max_findings} findings in batches of {batch_size}")
        
        for i in range(0, max_findings, batch_size):
            batch = semgrep_findings[i:i+batch_size]
            logger.info(f"  Batch {i//batch_size + 1}/{(max_findings-1)//batch_size + 1}: Verifying {len(batch)} findings...")
            
            try:
                batch_verified = await self._verify_batch(batch, repo_context)
                verified_findings.extend(batch_verified)
                logger.info(f"    ✓ Verified {len(batch_verified)}/{len(batch)} in this batch")
            except Exception as e:
                logger.error(f"    ✗ Batch verification failed: {e}")
                # Continue with next batch instead of failing completely
                continue
        
        logger.info(f"  ✓ Total verified: {len(verified_findings)} findings")
        
        # Report on false positives filtered out
        false_positives = max_findings - len(verified_findings)
        if false_positives > 0:
            logger.info(f"  ⚠ Filtered {false_positives} false positives ({(false_positives/max_findings*100):.1f}%)")
        
        return verified_findings
    
    async def _verify_batch(self, findings: List[Dict], repo_context: str) -> List[Dict]:
        """Verify a batch of findings - optimized for speed"""
        verified = []
        
        # Process findings in parallel-like manner (sequential but fast)
        for i, finding in enumerate(findings, 1):
            try:
                verified_finding = await self._verify_single_finding(finding, repo_context)
                if verified_finding:  # Only include if confidence > threshold
                    verified.append(verified_finding)
            except Exception as e:
                logger.debug(f"    Finding {i}/{len(findings)} verification failed: {e}")
                # Continue with next finding
                continue
        
        return verified
    
    async def _verify_single_finding(self, finding: Dict, repo_context: str) -> Optional[Dict]:
        """Verify a single Semgrep finding with model fallback"""
        
        # Extract code snippet and message
        code_snippet = finding.get("code_snippet", "")
        message = finding.get("message", "")
        rule_id = finding.get("rule_id", "")
        file_path = finding.get("file_path", "")
        
        if not code_snippet:
            logger.debug(f"  ⚠ Skipping finding {rule_id}: no code snippet")
            return None
        
        # Build verification prompt
        prompt = self._build_verification_prompt(
            code_snippet,
            message,
            rule_id,
            file_path,
            repo_context
        )
        
        # Try models in order until one works
        for model in self.models:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": """You are a STRICT Indian Regulatory Auditor specializing in DPDPA 2023, RBI Guidelines, and IT Act 2000. 
Your job is to VALIDATE compliance violations, not dismiss them.

PRINCIPLE: Code is GUILTY until proven SAFE. You must find reasons to confirm violations, not reasons to dismiss them.

For each finding, respond ONLY with JSON:
{\"is_violation\": true/false, \"confidence\": 0.0-1.0, \"reason\": \"explicit justification\"}

IMPORTANT: 
- If you cannot PROVE the code is safe, it IS a violation.
- Default to YES for missing security checks.
- Missing validation = VIOLATION
- Missing consent = VIOLATION
- Missing encryption = VIOLATION
- Missing audit logs = VIOLATION

Be STRICT, not lenient. Compliance costs companies fines of up to 4% of revenue per the DPDPA."""
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,  # Lower for stricter, more deterministic responses
                    max_tokens=500
                )
                
                result_text = response.choices[0].message.content.strip()
                self.model = model  # Update to working model
                
                # Parse JSON response
                if result_text.startswith("```"):
                    result_text = result_text.split("```")[1]
                    if result_text.startswith("json"):
                        result_text = result_text[4:]
                
                verification = json.loads(result_text)
                
                # Lower threshold to 0.3 since we're now using strict auditor mindset
                # Trust Semgrep's pattern detection, use verifier to confirm violations
                if verification.get("is_violation", False) and verification.get("confidence", 0) > 0.3:
                    return {
                        **finding,
                        "verified": True,
                        "confidence": verification.get("confidence", 0.4),
                        "verification_reason": verification.get("reason", ""),
                        "detector": "semgrep+groq"
                    }
                else:
                    logger.debug(f"  ✗ False positive: {rule_id} (confidence: {verification.get('confidence', 0)})")
                    return None
                    
            except json.JSONDecodeError as e:
                logger.debug(f"Failed to parse response from {model}: {e}")
                continue
            except Exception as e:
                # Check for rate limit error
                if "429" in str(e) or "rate_limit" in str(e).lower():
                    logger.warning(f"  Rate limit on {model}, trying next...")
                    continue
                else:
                    logger.debug(f"  Error with {model}: {e}")
                    continue
        
        # If all models fail, return finding as-is with lower confidence
        logger.warning(f"  All models failed for {rule_id}, including as unverified")
        return {**finding, "verified": False, "confidence": 0.3}
    
    def _build_verification_prompt(self, code_snippet: str, message: str, rule_id: str, 
                                   file_path: str, repo_context: str) -> str:
        """Build verification prompt for Groq"""
        
        prompt = f"""Review this code finding from Semgrep.

RULE ID: {rule_id}
FILE: {file_path}
SEMGREP DETECTION: {message}

CODE SNIPPET:
```
{code_snippet}
```

REVIEW QUESTIONS:
1. Does this code represent a real security/compliance issue?
2. Is this a legitimate match for the Semgrep rule (or a false positive)?
3. What's the risk level if this is a violation?

IMPORTANT: Semgrep already did the pattern matching. Your job is to confirm:
- YES: This matches the pattern AND represents a real issue
- NO: This is a false positive (pattern matches but not a real issue)

For compliance violations (DPDPA, RBI, IT Act):
- Authorization bypasses = YES
- Missing encryption = YES
- Missing rate limiting = YES
- Missing audit logs = YES
- Missing user consent = YES
- Hardcoded credentials = YES
- Test/demo code = MAYBE (check context)
- Configuration warnings = MAYBE (check if actually used)

Your confidence score should reflect how certain you are this is a genuine issue:
- 0.9-1.0: Definite security issue
- 0.7-0.8: Likely issue, needs attention
- 0.5-0.6: Possible issue, review needed
- 0.3-0.4: Uncertain, but matches pattern
- <0.3: Probably false positive
"""
        
        if repo_context:
            prompt += f"\nREPO CONTEXT:\n{repo_context}\n"
        
        prompt += "\nRESPOND WITH JSON: {\"is_violation\": true/false, \"confidence\": 0.0-1.0, \"reason\": \"brief explanation\"}"
        
        return prompt
    
    def get_verification_summary(self, verified_findings: List[Dict]) -> Dict[str, Any]:
        """Get summary of verification results"""
        
        critical = sum(1 for f in verified_findings if f.get("severity") == "critical")
        high = sum(1 for f in verified_findings if f.get("severity") == "high")
        medium = sum(1 for f in verified_findings if f.get("severity") == "medium")
        
        avg_confidence = sum(f.get("confidence", 0.6) for f in verified_findings) / len(verified_findings) if verified_findings else 0
        
        return {
            "total_verified": len(verified_findings),
            "critical": critical,
            "high": high,
            "medium": medium,
            "average_confidence": round(avg_confidence, 2),
            "verified_findings": verified_findings
        }
