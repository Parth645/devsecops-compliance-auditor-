"""
Groq Batch Mapper Module
Layer 2: Maps findings to compliance frameworks using Groq
Uses intelligent batching (5-20 findings per request) to minimize API calls
"""

import logging
import json
from typing import Dict, List, Any
from groq import Groq

logger = logging.getLogger(__name__)


class GroqBatchMapper:
    """
    Maps security findings to compliance frameworks
    Uses batching to reduce API calls:
    - 5-20 findings per batch
    - Drastically reduces token usage
    - Prevents rate limiting
    """
    
    def __init__(self, api_key: str):
        """Initialize Groq batch mapper"""
        self.client = Groq(api_key=api_key)
        self.models = ["llama-3.1-8b-instant", "mixtral-8x7b-32768", "llama-3.3-70b-versatile"]
        self.model = self.models[0]  # Start with cheapest
        self.batch_size = 10  # 10 findings per batch
        
    async def map_findings_to_compliance(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Map findings to compliance frameworks in intelligent batches
        
        Args:
            findings: List of findings from Semgrep/CodeQL
            
        Returns:
            Findings with compliance mapping added
        """
        logger.info(f"[BATCH MAPPER] Mapping {len(findings)} findings to compliance frameworks...")
        
        mapped_findings = []
        
        # Split into batches
        batches = [
            findings[i:i+self.batch_size]
            for i in range(0, len(findings), self.batch_size)
        ]
        
        logger.info(f"  Processing {len(batches)} batches of {self.batch_size} findings...")
        
        for batch_num, batch in enumerate(batches, 1):
            try:
                logger.info(f"  Batch {batch_num}/{len(batches)}: {len(batch)} findings")
                batch_mapped = await self._map_batch(batch)
                mapped_findings.extend(batch_mapped)
            except Exception as e:
                logger.error(f"Batch {batch_num} mapping failed: {e}")
                # Return unmapped findings on error
                mapped_findings.extend(batch)
        
        logger.info(f"  ✓ Mapped {len(mapped_findings)} findings")
        return mapped_findings
    
    async def _map_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Map a single batch of findings
        Sends batch to Groq for compliance analysis
        """
        # Format findings for Groq
        findings_text = self._format_batch_for_llm(batch)
        
        prompt = f"""Analyze these {len(batch)} security findings and map them to Indian compliance frameworks.

FINDINGS:
{findings_text}

For EACH finding, provide a JSON object with:
1. rule_id: Original rule ID
2. framework: DPDPA, IT_ACT_2000, RBI, CERT-IN, or MULTIPLE
3. compliance_requirement: Specific requirement violated
4. risk_explanation: Business impact in 1-2 sentences
5. remediation: Concrete fix (1 sentence)
6. evidence_weight: "high" / "medium" / "low" (how obvious is the violation)

CRITICAL REQUIREMENTS:
- DPDPA 2023: Personal data protection, consent, retention, breach notification
- IT Act 2000 SPDI: Encryption, authentication, access control, audit logging
- RBI Guidelines: Security headers, MFA, rate limiting, TLS enforcement
- CERT-In: Incident reporting, 72-hour breach notification, audit trails

Return ONLY a JSON array of objects. No other text.
"""
        
        try:
            # Try models in order until one works
            for model in self.models:
                try:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a compliance expert mapping code vulnerabilities to Indian regulatory frameworks. Return ONLY valid JSON, no markdown or explanations."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.3,  # Low temperature for consistency
                        max_tokens=3000,  # Reasonable limit for batch
                        response_format={"type": "json_object"}
                    )
                    
                    # Parse response
                    result_text = response.choices[0].message.content
                    mappings = json.loads(result_text)
                    
                    # Ensure it's a list
                    if not isinstance(mappings, list):
                        mappings = [mappings]
                    
                    # Merge mappings back to findings
                    mapped_batch = self._merge_mappings(batch, mappings)
                    self.model = model  # Update to working model
                    return mapped_batch
                    
                except Exception as e:
                    if "429" in str(e) or "rate_limit" in str(e).lower():
                        logger.debug(f"  Rate limit on {model}, trying next...")
                        continue
                    elif "400" in str(e):
                        logger.debug(f"  Bad request on {model}, trying next...")
                        continue
                    elif isinstance(e, json.JSONDecodeError):
                        logger.debug(f"  JSON error on {model}, trying next...")
                        continue
                    else:
                        raise
            
            # If all models fail, return batch without mapping
            logger.error("All models failed for batch mapping")
            return batch
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error in batch mapper: {e}")
            # Return batch with basic mapping
            return batch
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return batch
    
    def _format_batch_for_llm(self, batch: List[Dict]) -> str:
        """Format findings for Groq prompt"""
        formatted = []
        for i, finding in enumerate(batch, 1):
            text = f"""
{i}. Rule: {finding.get('rule_id', 'unknown')}
   File: {finding.get('file', 'unknown')}:{finding.get('line_start', '?')}
   Message: {finding.get('message', '')}
   Severity: {finding.get('severity', 'unknown')}
"""
            formatted.append(text)
        
        return "\n".join(formatted)
    
    def _merge_mappings(self, batch: List[Dict], mappings: List[Dict]) -> List[Dict]:
        """Merge Groq mappings back to findings"""
        merged = []
        
        for finding in batch:
            rule_id = finding.get("rule_id", "")
            
            # Find matching mapping
            matching_mapping = next(
                (m for m in mappings if m.get("rule_id") == rule_id),
                None
            )
            
            if matching_mapping:
                # Merge mapping data
                merged_finding = {
                    **finding,
                    "compliance_mapping": {
                        "framework": matching_mapping.get("framework", "UNKNOWN"),
                        "compliance_requirement": matching_mapping.get("compliance_requirement", ""),
                        "risk_explanation": matching_mapping.get("risk_explanation", ""),
                        "remediation": matching_mapping.get("remediation", ""),
                        "evidence_weight": matching_mapping.get("evidence_weight", "medium")
                    }
                }
            else:
                # Default mapping if not found
                merged_finding = {
                    **finding,
                    "compliance_mapping": {
                        "framework": finding.get("framework", "IT_ACT_2000"),
                        "compliance_requirement": "Security best practice",
                        "risk_explanation": finding.get("message", ""),
                        "remediation": "Address the security issue",
                        "evidence_weight": "medium"
                    }
                }
            
            merged.append(merged_finding)
        
        return merged
    
    async def generate_summary_report(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate executive summary using Groq
        Single LLM call for entire report
        """
        logger.info("[SUMMARY GENERATOR] Creating executive summary...")
        
        # Build summary stats
        stats = self._calculate_stats(findings)
        
        prompt = f"""Create a brief executive summary of these compliance findings:

Total Findings: {len(findings)}
Critical: {stats['critical']} | High: {stats['high']} | Medium: {stats['medium']}

Top Issues by Framework:
{self._format_stats_summary(findings)}

Write a 150-word summary explaining:
1. Overall risk profile
2. Top compliance gaps
3. Recommended immediate actions
4. Long-term improvements

Be concise and actionable."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a compliance expert writing executive summaries."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=500
            )
            
            return {
                "summary": response.choices[0].message.content,
                "status": "generated"
            }
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return {"summary": "", "status": "failed"}
    
    def _calculate_stats(self, findings: List[Dict]) -> Dict[str, int]:
        """Calculate statistics"""
        return {
            "total": len(findings),
            "critical": len([f for f in findings if f.get("severity") == "critical"]),
            "high": len([f for f in findings if f.get("severity") == "high"]),
            "medium": len([f for f in findings if f.get("severity") == "medium"]),
            "low": len([f for f in findings if f.get("severity") == "low"])
        }
    
    def _format_stats_summary(self, findings: List[Dict]) -> str:
        """Format framework stats for summary"""
        frameworks = {}
        for f in findings:
            fw = f.get("framework", "UNKNOWN")
            frameworks[fw] = frameworks.get(fw, 0) + 1
        
        return "\n".join([f"- {fw}: {count}" for fw, count in sorted(frameworks.items(), key=lambda x: x[1], reverse=True)])
