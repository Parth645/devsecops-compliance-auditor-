"""
Indian Compliance Rules Manager
Loads and manages the 18 Indian compliance rules from JSON
Provides rule lookup, pattern matching, and severity filtering
"""

import logging
import json
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class IndianComplianceRulesManager:
    """Manages Indian compliance rules for scanning and analysis"""
    
    def __init__(self, rules_file: str = "policies/indian_compliance_rules.json"):
        """
        Initialize rules manager
        
        Args:
            rules_file: Path to indian_compliance_rules.json
        """
        self.rules_file = Path(rules_file)
        self.rules = {}
        self.rules_by_framework = {}
        self.rules_by_severity = {}
        self.all_keywords = set()
        
        # Load rules
        self._load_rules()
    
    def _load_rules(self):
        """Load rules from JSON file"""
        
        try:
            if not self.rules_file.exists():
                logger.warning(f"Rules file not found: {self.rules_file}")
                return
            
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract rules from frameworks structure
            all_rules = []
            for framework in data.get('frameworks', []):
                framework_id = framework.get('id')
                framework_name = framework.get('name')
                
                for rule in framework.get('rules', []):
                    # Add framework info to each rule
                    rule['framework'] = framework_name
                    rule['framework_id'] = framework_id
                    all_rules.append(rule)
            
            # Build indexes
            self.rules = {rule['id']: rule for rule in all_rules}
            
            # Index by framework
            for rule in all_rules:
                framework = rule.get('framework')
                if framework not in self.rules_by_framework:
                    self.rules_by_framework[framework] = []
                self.rules_by_framework[framework].append(rule)
            
            # Index by severity
            for rule in all_rules:
                severity = rule.get('severity')
                if severity not in self.rules_by_severity:
                    self.rules_by_severity[severity] = []
                self.rules_by_severity[severity].append(rule)
            
            # Collect all keywords from patterns
            for rule in all_rules:
                for pattern in rule.get('patterns', []):
                    # Extract keywords from patterns
                    words = pattern.lower().split()
                    self.all_keywords.update(words)
            
            logger.info(f"✓ Loaded {len(self.rules)} Indian compliance rules")
            logger.info(f"  Frameworks: {', '.join(self.rules_by_framework.keys())}")
            logger.info(f"  CRITICAL: {len(self.rules_by_severity.get('critical', []))} rules")
            logger.info(f"  HIGH: {len(self.rules_by_severity.get('high', []))} rules")
            
        except Exception as e:
            logger.error(f"Failed to load rules: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Get specific rule by ID"""
        return self.rules.get(rule_id)
    
    def get_rules_by_framework(self, framework: str) -> List[Dict[str, Any]]:
        """Get all rules for a framework"""
        return self.rules_by_framework.get(framework, [])
    
    def get_rules_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """Get all rules with given severity"""
        return self.rules_by_severity.get(severity, [])
    
    def get_critical_rules(self) -> List[Dict[str, Any]]:
        """Get all critical rules"""
        return self.rules_by_severity.get('critical', [])
    
    def get_frameworks(self) -> List[str]:
        """Get list of all frameworks"""
        return list(self.rules_by_framework.keys())
    
    def find_matching_rules(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Find rules matching given keywords
        
        Args:
            keywords: List of keywords to search
            
        Returns:
            List of matching rules
        """
        matching = []
        keywords_lower = [k.lower() for k in keywords]
        
        for rule in self.rules.values():
            # Check patterns
            patterns = [p.lower() for p in rule.get('patterns', [])]
            
            # Check if any keywords match patterns or rule name/description
            rule_text = f"{rule.get('name', '')} {rule.get('description', '')}".lower()
            
            for keyword in keywords_lower:
                if keyword in rule_text or any(keyword in p for p in patterns):
                    matching.append(rule)
                    break
        
        return matching
    
    def get_rule_summary_for_framework(self, framework: str) -> Dict[str, Any]:
        """Get summary of rules for a framework"""
        rules = self.get_rules_by_framework(framework)
        
        return {
            "framework": framework,
            "total_rules": len(rules),
            "critical": len([r for r in rules if r.get('severity') == 'critical']),
            "high": len([r for r in rules if r.get('severity') == 'high']),
            "rules": [{
                "id": r.get('id'),
                "name": r.get('name'),
                "severity": r.get('severity')
            } for r in rules]
        }
    
    def get_all_summaries(self) -> Dict[str, Any]:
        """Get summary for all frameworks"""
        return {
            framework: self.get_rule_summary_for_framework(framework)
            for framework in self.get_frameworks()
        }
    
    def convert_rule_to_groq_prompt(self, rule: Dict[str, Any]) -> str:
        """Convert rule to Groq prompt for semantic analysis"""
        
        patterns = "\n  - ".join(rule.get('patterns', []))
        
        prompt = f"""
Rule: {rule.get('name')}
Framework: {rule.get('framework')}
Severity: {rule.get('severity')}
Category: {rule.get('category')}

Description: {rule.get('description')}

Violation Patterns to Detect:
  - {patterns}

Remediation: {rule.get('remediation')}

Provide a semantic code analysis to detect if this violation exists in the provided code.
"""
        return prompt.strip()
    
    def get_patterns_for_framework(self, framework: str) -> Dict[str, List[str]]:
        """Get all patterns for a framework"""
        rules = self.get_rules_by_framework(framework)
        patterns_dict = {}
        
        for rule in rules:
            patterns_dict[rule.get('id')] = rule.get('patterns', [])
        
        return patterns_dict
    
    def get_keywords_for_framework(self, framework: str) -> List[str]:
        """Get all keywords for a framework"""
        rules = self.get_rules_by_framework(framework)
        keywords = set()
        
        for rule in rules:
            # Extract keywords from patterns
            for pattern in rule.get('patterns', []):
                words = pattern.lower().split()
                keywords.update(words)
        
        return list(keywords)


def get_rules_manager() -> IndianComplianceRulesManager:
    """Singleton getter for rules manager"""
    global _rules_manager
    if '_rules_manager' not in globals():
        _rules_manager = IndianComplianceRulesManager()
    return _rules_manager
