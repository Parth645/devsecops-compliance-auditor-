"""
Policy Manager - Custom Company Policy Ingestion & Storage
Handles uploading, parsing, and storing company-specific compliance policies
"""

import logging
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

class PolicyManager:
    """
    Manages custom company compliance policies
    - Upload and parse policy documents
    - Generate Semgrep rules from policies
    - Store policy versions
    - Track policy coverage
    """
    
    def __init__(self, policies_dir: str = "policies"):
        """Initialize policy manager"""
        self.policies_dir = Path(policies_dir)
        self.policies_dir.mkdir(exist_ok=True)
        
        self.metadata_file = self.policies_dir / "policy_metadata.json"
        self.rules_file = self.policies_dir / "generated_rules.json"
        
        self.policies = self._load_policies()
        self.rules = self._load_rules()
        
        logger.info(f"✓ PolicyManager initialized: {self.policies_dir}")
    
    # ========================================================================
    # POLICY INGESTION
    # ========================================================================
    
    def ingest_policy(
        self,
        policy_name: str,
        policy_text: str,
        policy_type: str = "custom",
        version: str = "1.0",
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ingest a new company policy document
        
        Args:
            policy_name: Unique identifier for policy (e.g., "data_handling_2026")
            policy_text: Full text of the policy
            policy_type: Type of policy (custom, dpdp, rbi, it_act, etc.)
            version: Version number
            description: Human-readable description
            metadata: Additional metadata
            
        Returns:
            Policy record with ID, hash, and metadata
        """
        logger.info(f"Ingesting policy: {policy_name}")
        
        # Generate policy ID
        policy_hash = hashlib.sha256(policy_text.encode()).hexdigest()[:12]
        policy_id = f"{policy_name}_v{version}_{policy_hash}"
        
        # Create policy record
        policy_record = {
            "id": policy_id,
            "name": policy_name,
            "type": policy_type,
            "version": version,
            "description": description,
            "hash": policy_hash,
            "text_length": len(policy_text),
            "ingested_at": datetime.now().isoformat(),
            "text": policy_text,
            "metadata": metadata or {}
        }
        
        # Store policy
        policy_file = self.policies_dir / f"{policy_id}.json"
        with open(policy_file, "w") as f:
            json.dump(policy_record, f, indent=2)
        
        # Update policies index
        self.policies[policy_id] = policy_record
        self._save_policies()
        
        logger.info(f"✓ Policy ingested: {policy_id}")
        return policy_record
    
    def list_policies(self, policy_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all policies, optionally filtered by type"""
        policies = list(self.policies.values())
        
        if policy_type:
            policies = [p for p in policies if p.get("type") == policy_type]
        
        return sorted(policies, key=lambda p: p.get("ingested_at"), reverse=True)
    
    def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific policy by ID"""
        return self.policies.get(policy_id)
    
    # ========================================================================
    # RULE GENERATION & MANAGEMENT
    # ========================================================================
    
    def store_generated_rules(
        self,
        policy_id: str,
        rules: List[Dict[str, Any]],
        coverage_percentage: float = 0.0
    ) -> Dict[str, Any]:
        """
        Store rules generated from a policy
        
        Args:
            policy_id: ID of the source policy
            rules: List of Semgrep-compatible rules
            coverage_percentage: Estimated policy coverage percentage
            
        Returns:
            Rule record with ID and statistics
        """
        logger.info(f"Storing {len(rules)} rules for policy {policy_id}")
        
        rule_record = {
            "policy_id": policy_id,
            "generated_at": datetime.now().isoformat(),
            "rule_count": len(rules),
            "coverage": coverage_percentage,
            "rules": rules
        }
        
        if policy_id not in self.rules:
            self.rules[policy_id] = []
        
        self.rules[policy_id].append(rule_record)
        self._save_rules()
        
        logger.info(f"✓ Stored rule set with {len(rules)} rules")
        return rule_record
    
    def get_latest_rules(self, policy_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get the latest generated rules for a policy"""
        if policy_id in self.rules and self.rules[policy_id]:
            return self.rules[policy_id][-1].get("rules", [])
        return None
    
    def export_rules_for_semgrep(self, policy_id: str) -> str:
        """
        Export rules in Semgrep YAML format
        
        Args:
            policy_id: ID of the policy
            
        Returns:
            YAML-formatted string ready for Semgrep
        """
        rules = self.get_latest_rules(policy_id)
        if not rules:
            return ""
        
        yaml_output = "rules:\n"
        for rule in rules:
            yaml_output += f"""  - id: {rule.get('id', 'unknown')}
    pattern: {rule.get('pattern', '')}
    message: {rule.get('message', '')}
    languages: {rule.get('languages', ['python', 'javascript'])}
    severity: {rule.get('severity', 'WARNING')}

"""
        
        return yaml_output
    
    # ========================================================================
    # POLICY COVERAGE & ANALYTICS
    # ========================================================================
    
    def analyze_policy_coverage(self, policy_id: str, violation_types: List[str]) -> Dict[str, Any]:
        """
        Analyze how well the generated rules cover the policy requirements
        
        Args:
            policy_id: ID of the policy
            violation_types: Types of violations detected
            
        Returns:
            Coverage analysis with gaps
        """
        policy = self.get_policy(policy_id)
        if not policy:
            return {"error": "Policy not found"}
        
        rules = self.get_latest_rules(policy_id)
        if not rules:
            return {"error": "No rules generated yet"}
        
        policy_keywords = self._extract_keywords(policy.get("text", ""))
        rule_keywords = set()
        for rule in rules:
            rule_keywords.update(self._extract_keywords(
                rule.get("message", "") + " " + rule.get("pattern", "")
            ))
        
        coverage = len(rule_keywords & policy_keywords) / len(policy_keywords) if policy_keywords else 0
        
        return {
            "policy_id": policy_id,
            "policy_keywords": len(policy_keywords),
            "rule_coverage": len(rule_keywords),
            "coverage_percentage": coverage * 100,
            "gaps": list(policy_keywords - rule_keywords)[:10]  # Top 10 gaps
        }
    
    def get_policy_statistics(self) -> Dict[str, Any]:
        """Get overall policy management statistics"""
        total_policies = len(self.policies)
        total_rules = sum(len(v) for v in self.rules.values())
        
        policy_types = {}
        for policy in self.policies.values():
            pt = policy.get("type", "unknown")
            policy_types[pt] = policy_types.get(pt, 0) + 1
        
        return {
            "total_policies": total_policies,
            "total_rule_sets": total_rules,
            "policies_by_type": policy_types,
            "total_text_length": sum(p.get("text_length", 0) for p in self.policies.values())
        }
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def _extract_keywords(self, text: str) -> set:
        """Extract keywords from policy text"""
        # Simple keyword extraction - could be enhanced
        words = text.lower().split()
        # Filter out common stop words
        stop_words = {"the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "is"}
        return {w for w in words if len(w) > 3 and w not in stop_words}
    
    def _load_policies(self) -> Dict[str, Dict[str, Any]]:
        """Load all policies from disk"""
        policies = {}
        for policy_file in self.policies_dir.glob("*.json"):
            if policy_file.name != "policy_metadata.json":
                try:
                    with open(policy_file) as f:
                        policy = json.load(f)
                        policies[policy.get("id", policy_file.stem)] = policy
                except Exception as e:
                    logger.warning(f"Failed to load policy {policy_file}: {e}")
        return policies
    
    def _save_policies(self):
        """Save policies index"""
        try:
            with open(self.metadata_file, "w") as f:
                metadata = {
                    "version": "1.0",
                    "updated_at": datetime.now().isoformat(),
                    "policies": list(self.policies.keys())
                }
                json.dump(metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save policies metadata: {e}")
    
    def _load_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load all generated rules from disk"""
        rules = {}
        rules_file = self.policies_dir / "generated_rules.json"
        
        if rules_file.exists():
            try:
                with open(rules_file) as f:
                    all_rules = json.load(f)
                    for policy_id, rule_sets in all_rules.items():
                        rules[policy_id] = rule_sets
            except Exception as e:
                logger.warning(f"Failed to load rules: {e}")
        
        return rules
    
    def _save_rules(self):
        """Save all generated rules to disk"""
        try:
            with open(self.rules_file, "w") as f:
                json.dump(self.rules, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save rules: {e}")


# Convenience function for quick policy access
def create_sample_policies() -> Dict[str, str]:
    """Create sample company policies for testing"""
    return {
        "data_handling": """
COMPANY DATA HANDLING POLICY

1. Personal Data Processing
   - All personal data collection requires explicit user consent
   - Users must be informed of data usage before collection
   - Data retention must not exceed 3 years without justification

2. Database Security
   - All database queries must use parameterized statements
   - No hardcoded database credentials in source code
   - Database connections must use encrypted protocols (TLS 1.2+)

3. Authentication & Authorization
   - All user authentication must support multi-factor authentication (MFA)
   - Session timeouts must not exceed 30 minutes
   - Passwords must meet complexity requirements (minimum 12 characters)

4. API Security
   - All API endpoints must require authentication
   - Rate limiting must prevent brute force attacks
   - API logs must not contain sensitive data (passwords, tokens, PII)

5. Data Classification
   - Sensitive data must be encrypted at rest and in transit
   - Audit logs must track all access to sensitive data
   - Data deletion must be verifiable and permanent
        """,
        
        "financial_compliance": """
FINANCIAL COMPLIANCE POLICY

1. Transaction Logging
   - All financial transactions must be logged with timestamp and user ID
   - Logs must be immutable and retained for 7 years
   - Access to transaction logs requires audit trail

2. Encryption Standards
   - Financial data must use AES-256 encryption
   - All transmission must use TLS 1.3
   - Key management must follow industry standards

3. Access Control
   - Financial data access must be logged and monitored
   - Dual-approval required for high-value transactions
   - Admin accounts must have time-limited access tokens

4. Compliance Reporting
   - Monthly compliance reports must be generated automatically
   - Violations must be reported within 24 hours
   - Remediation plans must be documented and tracked
        """,
        
        "api_security": """
API SECURITY POLICY

1. Authentication
   - All API requests must include valid authentication tokens
   - Tokens must expire within 1 hour
   - Token refresh must require user re-authentication

2. Rate Limiting
   - API endpoints must implement rate limiting (100 req/minute per user)
   - Suspicious activity beyond thresholds must trigger alerts
   - DDoS protection must be enabled

3. Data Validation
   - All user inputs must be validated and sanitized
   - SQL injection attempts must be logged and blocked
   - Response payloads must never include stack traces or debug info

4. Versioning & Deprecation
   - API versions must be supported for minimum 2 major releases
   - Breaking changes require 6-month deprecation notice
   - Clients must upgrade to latest secure version
        """
    }
