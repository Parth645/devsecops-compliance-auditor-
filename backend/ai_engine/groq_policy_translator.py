"""
Groq Policy Translator (Step 2: Dynamic Semgrep YAML Generator)
Converts company policy text to Semgrep rules using Groq LLM
Generates compositional patterns with taint analysis
"""

import logging
import json
import yaml
from typing import Dict, List, Any
from pathlib import Path
from groq import Groq

logger = logging.getLogger(__name__)


class GroqPolicyTranslator:
    """
    Translates natural language policy into executable Semgrep rules
    Uses llama-3.1-8b-instant (10x cheaper) with temperature=0.1 for consistency
    """
    
    def __init__(self, api_key: str, output_dir: str = "policies/generated_rules"):
        """Initialize policy translator"""
        self.client = Groq(api_key=api_key)
        self.models = ["llama-3.1-8b-instant", "mixtral-8x7b-32768", "llama-3.3-70b-versatile"]
        self.model = self.models[0]  # Start with cheapest
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def translate_policy_to_semgrep_rules(self, policy_text: str, policy_name: str = "custom_policy") -> Dict[str, Any]:
        """
        Convert policy text to Semgrep YAML rules
        
        Args:
            policy_text: Natural language compliance policy
            policy_name: Identifier for the policy
            
        Returns:
            Dictionary with generated rules and metadata
        """
        logger.info(f"[AI STAGE 2] Translating policy '{policy_name}' to Semgrep rules...")
        
        # Generate rule proposals using Groq
        rule_proposals = await self._generate_rule_proposals(policy_text, policy_name)
        
        # Validate and compile rules
        compiled_rules = self._compile_rules_to_yaml(rule_proposals, policy_name)
        
        # Save rules to disk
        rules_file = self.output_dir / f"{policy_name}_rules.yaml"
        with open(rules_file, 'w') as f:
            f.write(compiled_rules)
        
        logger.info(f"  ✓ Generated {len(rule_proposals.get('rules', []))} Semgrep rules")
        logger.info(f"  ✓ Saved to: {rules_file}")
        
        return {
            "status": "success",
            "policy_name": policy_name,
            "rules_generated": len(rule_proposals.get('rules', [])),
            "output_file": str(rules_file),
            "rule_proposals": rule_proposals,
            "yaml_output": compiled_rules
        }
    
    async def _generate_rule_proposals(self, policy_text: str, policy_name: str) -> Dict[str, Any]:
        """Use Groq to generate rule proposals from policy"""
        
        prompt = f"""You are a Semgrep rule expert. Convert this comprehensive compliance policy into executable Semgrep rules.

COMPANY POLICY:
{policy_text}

REQUIREMENTS:
1. Generate AT LEAST 18 rules (minimum 5 per framework: DPDPA, RBI, IT Act + 2 SEBI + 3 ISO)
2. For EACH compliance framework mentioned, create rules that detect violations
3. Use compositional operators: pattern, pattern-not, pattern-inside, pattern-not-inside
4. For data flow rules: use mode: taint with pattern-sources and pattern-sinks  
5. Look for ABSENCE of security features (anti-patterns) - e.g., "missing consent check"
6. Focus on practical, detectable patterns
7. Generate one rule per violation type - do NOT combine multiple rules into one

FRAMEWORKS TO COVER:
- DPDPA 2023: Rules for consent, purpose limitation, data minimization, breach notification, user rights
- RBI Guidelines: Rules for authorization, transaction atomicity, encryption, audit trails, rate limiting
- IT Act 2000: Rules for authentication, input validation, unauthorized access prevention
- SEBI: Rules for fair trading practices, transparency
- ISO 8000: Rules for data quality, data accuracy

Respond with ONLY a valid JSON object (no markdown):
{{
  "policy_summary": "brief policy summary",
  "rules": [
    {{
      "rule_id": "custom.policy.rule001",
      "title": "Rule title",
      "description": "What this rule detects",
      "severity": "ERROR|WARNING",
      "pattern_type": "pattern|taint|regex",
      "languages": ["javascript", "typescript"],
      "patterns": {{
        "pattern": "code pattern to match",
        "pattern-not": "negative pattern (optional)",
        "pattern-inside": "parent context (optional)",
        "pattern-sources": ["source1", "source2"],
        "pattern-sinks": ["sink1", "sink2"]
      }},
      "message": "Error message when matched",
      "fix": "Suggested remediation (optional)"
    }}
  ]
}}"""
        
        try:
            # Try models in order until one works
            for model in self.models:
                try:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {
                                "role": "system",
                                "content": """You are a security expert who writes Semgrep rules. 
Generate ONLY valid JSON responses. No markdown, no code blocks, no explanations.
Ensure all JSON is properly formatted and valid.
Generate AT LEAST 18 rules covering all compliance frameworks (DPDPA, RBI, IT Act, SEBI, ISO 8000)."""
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.1,  # Low temperature for consistency
                        max_tokens=6000  # Increased from 3000 to allow full rule generation (all 18+ rules)
                    )
                    
                    result_text = response.choices[0].message.content.strip()
                    
                    # Strip markdown if present
                    if result_text.startswith("```"):
                        result_text = result_text.split("```")[1]
                        if result_text.startswith("json"):
                            result_text = result_text[4:]
                    
                    rule_proposals = json.loads(result_text)
                    self.model = model  # Update to working model
                    logger.info(f"  Generated {len(rule_proposals.get('rules', []))} rule proposals")
                    
                    return rule_proposals
                    
                except Exception as e:
                    if "429" in str(e) or "rate_limit" in str(e).lower():
                        logger.debug(f"  Rate limit on {model}, trying next...")
                        continue
                    elif "400" in str(e):
                        logger.debug(f"  Bad request on {model}, trying next...")
                        continue
                    else:
                        if "json" in str(type(e)):
                            continue
                        raise
            
            # If all models fail, return empty rules
            logger.error("All models failed for policy translation")
            return {"rules": [], "error": "all_models_failed"}
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Groq rule proposals: {e}")
            return {"rules": [], "error": "json_parse_error"}
        except Exception as e:
            logger.error(f"Policy translation failed: {e}")
            return {"rules": [], "error": str(e)}
    
    def _compile_rules_to_yaml(self, rule_proposals: Dict[str, Any], policy_name: str) -> str:
        """Compile rule proposals into valid Semgrep YAML"""
        
        semgrep_rules = []
        
        for rule_proposal in rule_proposals.get('rules', []):
            semgrep_rule = self._build_semgrep_rule(rule_proposal)
            if semgrep_rule:
                semgrep_rules.append(semgrep_rule)
        
        # Build complete YAML structure
        yaml_output = {
            "rules": semgrep_rules
        }
        
        # Convert to YAML
        yaml_str = yaml.dump(yaml_output, default_flow_style=False, sort_keys=False)
        
        return yaml_str
    
    def _build_semgrep_rule(self, rule_proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Build a valid Semgrep rule from proposal"""
        
        try:
            pattern_type = rule_proposal.get('pattern_type', 'pattern')
            patterns = rule_proposal.get('patterns', {})
            
            rule = {
                "id": rule_proposal.get('rule_id', 'custom.rule'),
                "pattern": patterns.get('pattern') if pattern_type == 'pattern' else None,
                "pattern-not": patterns.get('pattern-not'),
                "pattern-inside": patterns.get('pattern-inside'),
                "message": rule_proposal.get('message', 'Security issue detected'),
                "languages": rule_proposal.get('languages', ['javascript']),
                "severity": rule_proposal.get('severity', 'WARNING').upper(),
                "metadata": {
                    "source": "groq_policy_translator",
                    "policy": rule_proposal.get('policy', 'custom'),
                    "fix": rule_proposal.get('fix')
                }
            }
            
            # Handle taint analysis rules
            if pattern_type == 'taint':
                rule['mode'] = 'taint'
                rule['pattern-sources'] = patterns.get('pattern-sources', [])
                rule['pattern-sinks'] = patterns.get('pattern-sinks', [])
                rule['pattern-sanitizers'] = patterns.get('pattern-sanitizers', [])
            
            # Remove None values
            rule = {k: v for k, v in rule.items() if v is not None}
            
            return rule
            
        except Exception as e:
            logger.error(f"Failed to build rule: {e}")
            return None
    
    async def generate_custom_rules_from_file(self, policy_file_path: str) -> Dict[str, Any]:
        """Load policy from file and generate rules"""
        
        try:
            with open(policy_file_path, 'r') as f:
                policy_text = f.read()
            
            policy_name = Path(policy_file_path).stem
            
            return await self.translate_policy_to_semgrep_rules(policy_text, policy_name)
            
        except Exception as e:
            logger.error(f"Failed to load policy file: {e}")
            return {"error": str(e), "status": "failed"}
