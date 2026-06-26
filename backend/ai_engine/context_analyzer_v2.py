"""
Enhanced Context-Aware AI Judge v2
Deep multi-layered analysis with confidence scoring
"""

import re
import json
import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def load_knowledge_base(kb_path: str = "backend/knowledge/safe_patterns.json") -> Dict[str, Any]:
    """Load the dynamic knowledge base from JSON file"""
    try:
        possible_paths = [
            kb_path,
            os.path.join(os.path.dirname(__file__), "..", "knowledge", "safe_patterns.json"),
            os.path.join(os.path.dirname(__file__), "knowledge", "safe_patterns.json"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    kb = json.load(f)
                    logger.info(f"✓ Loaded knowledge base from {path}")
                    return kb
        
        logger.warning(f"Knowledge base not found, using defaults")
        return _get_default_knowledge_base()
        
    except Exception as e:
        logger.error(f"Failed to load knowledge base: {e}")
        return _get_default_knowledge_base()


def _get_default_knowledge_base() -> Dict[str, Any]:
    """Return default knowledge base"""
    return {
        "safe_libs": ["crypto-js", "web3", "ethers", "bcrypt", "argon2", "truffle-contract"],
        "safe_patterns": ["000000000000", "dummy", "mock", "example.com"],
        "test_indicators": ["describe", "it", "test", "mock", "setup", "teardown"],
        "hashing_algorithms": ["sha256", "sha3", "keccak", "blake2"],
        "safe_crypto_operations": ["hash", "digest", "verify", "sign"]
    }


async def ai_verify_violation_v2(
    code_snippet: str,
    rule_id: str,
    file_path: str,
    knowledge_base: Optional[Dict[str, Any]] = None,
    surrounding_lines: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """
    ENHANCED: Deep Context-Aware AI Judge with 9-layer analysis
    
    Scans library files but intelligently filters false positives
    using multi-layered context understanding and confidence scoring.
    """
    if knowledge_base is None:
        knowledge_base = load_knowledge_base()
    
    safe_libs = knowledge_base.get("safe_libs", [])
    safe_patterns = knowledge_base.get("safe_patterns", [])
    test_indicators = knowledge_base.get("test_indicators", [])
    hashing_algorithms = knowledge_base.get("hashing_algorithms", [])
    safe_crypto_ops = knowledge_base.get("safe_crypto_operations", [])
    
    thought_process = []
    confidence_score = 0.5  # Start neutral
    
    code_lower = code_snippet.lower()
    file_lower = file_path.lower()
    
    # LAYER 1: File Context
    is_library = any(lib in file_lower for lib in ['truffle-contract', 'web3.min', 'jquery', 'bootstrap'])
    is_minified = '.min.' in file_lower
    
    if is_library or is_minified:
        thought_process.append(f"📚 Library file: {os.path.basename(file_path)}")
        confidence_score -= 0.3
    
    # LAYER 2: Test Data Patterns
    for pattern in safe_patterns:
        if pattern.lower() in code_lower:
            thought_process.append(f"✓ Test pattern: '{pattern}'")
            confidence_score -= 0.4
            
            if (is_library or is_minified) and pattern in ['000000000000', '111111111111']:
                thought_process.append("✓ Test pattern in library - FALSE POSITIVE")
                return None
    
    # LAYER 3: Library Usage
    for lib in safe_libs:
        if lib.lower() in code_lower:
            if any(kw in code_lower for kw in ['import', 'require', 'from', 'include']):
                thought_process.append(f"✓ Importing: '{lib}'")
                return None
            
            if any(api in code_lower for api in ['.', '(', 'new ']):
                thought_process.append(f"✓ Using API: '{lib}'")
                confidence_score -= 0.2
    
    # LAYER 4: Crypto Context
    if rule_id in ["SECRET_CRYPTO", "CRYPTO_WEAK", "rule_2", "rule_3"]:
        for algo in hashing_algorithms:
            if algo.lower() in code_lower:
                for op in safe_crypto_ops:
                    if op.lower() in code_lower:
                        thought_process.append(f"✓ Safe crypto: {algo}.{op}")
                        
                        if is_library or is_minified:
                            thought_process.append("✓ Crypto in library - expected")
                            return None
                        
                        confidence_score -= 0.3
    
    # LAYER 5: Comments/Docs
    stripped = code_snippet.strip()
    if any(stripped.startswith(c) for c in ['//', '#', '/*', '*', '<!--', '"""', "'''"]):
        thought_process.append("✓ Comment")
        return None
    
    if any(doc in code_lower for doc in ['@example', '@param', '@returns', 'example:', 'usage:']):
        thought_process.append("✓ Documentation")
        return None
    
    # LAYER 6: Test Files
    test_indicators_file = ['test', 'spec', '__tests__', 'mock', 'fixture', '.test.', '.spec.']
    if any(ind in file_lower for ind in test_indicators_file):
        thought_process.append("✓ Test file")
        
        for indicator in test_indicators:
            if indicator.lower() in code_lower:
                thought_process.append(f"✓ Test keyword: '{indicator}'")
                return None
    
    # LAYER 7: Surrounding Context
    if surrounding_lines:
        context = '\n'.join(surrounding_lines).lower()
        
        test_blocks = ['describe(', 'it(', 'test(', 'def test_', 'function test']
        if any(block in context for block in test_blocks):
            thought_process.append("✓ Test block")
            return None
        
        if 'example' in context or 'demo' in context or 'sample' in context:
            thought_process.append("✓ Example code")
            confidence_score -= 0.3
        
        if is_library and any(init in context for init in ['module.exports', 'export default', 'define(', 'window.']):
            thought_process.append("✓ Library init")
            confidence_score -= 0.2
    
    # LAYER 8: PII-Specific
    if "PII" in rule_id:
        if any(meta in code_lower for meta in ['_npmuser', 'author', 'maintainer', 'contributor']):
            thought_process.append("✓ NPM metadata")
            return None
        
        example_domains = ['example.com', 'test.com', 'domain.com', 'localhost']
        if any(domain in code_lower for domain in example_domains):
            thought_process.append("✓ Example domain")
            return None
        
        if rule_id == "PII_AADHAAR":
            digits = re.sub(r'\D', '', code_snippet)
            
            if len(digits) == 12:
                if len(set(digits)) == 1:
                    thought_process.append(f"✓ Constant Aadhaar (all {digits[0]}s)")
                    return None
                
                try:
                    is_seq = all(int(digits[i]) == (int(digits[i-1]) + 1) % 10 for i in range(1, len(digits)))
                    if is_seq:
                        thought_process.append("✓ Sequential Aadhaar")
                        return None
                except:
                    pass
    
    # LAYER 9: Final Decision
    if confidence_score < 0.2:
        thought_process.append(f"✓ Low confidence ({confidence_score:.2f}) - FALSE POSITIVE")
        return None
    
    if (is_library or is_minified) and confidence_score < 0.5:
        thought_process.append(f"✓ Library + low confidence ({confidence_score:.2f}) - FALSE POSITIVE")
        return None
    
    # TRUE POSITIVE
    thought_process.append(f"⚠ Confidence: {confidence_score:.2f} - TRUE POSITIVE")
    
    severity = "MEDIUM"
    if "SECRET" in rule_id or "PASSWORD" in rule_id:
        severity = "HIGH"
    elif "PII" in rule_id and "AADHAAR" in rule_id:
        severity = "HIGH"
    elif "CRYPTO_WEAK" in rule_id:
        severity = "HIGH"
    elif confidence_score > 0.7:
        severity = "HIGH"
    
    return {
        "thought_process": " | ".join(thought_process),
        "is_true_positive": True,
        "severity": severity,
        "confidence": max(0.5, confidence_score),
        "recommendation": _get_remediation(rule_id),
        "file_context": "library" if (is_library or is_minified) else "production"
    }


def _get_remediation(rule_id: str) -> str:
    """Get remediation recommendation"""
    remediation_map = {
        "SECRET_": "Move secrets to environment variables or secure vault",
        "PII_AADHAAR": "Implement data masking and encryption for Aadhaar (DPDP Act)",
        "PII_EMAIL": "Implement data masking for email addresses (DPDP Act)",
        "PII_PHONE": "Implement data masking for phone numbers (DPDP Act)",
        "CRYPTO_WEAK": "Use approved cryptographic algorithms (AES-256, RSA-2048+)",
        "PASSWORD": "Use secure password hashing (bcrypt, argon2)",
    }
    
    for key, value in remediation_map.items():
        if key in rule_id:
            return value
    
    return "Review and remediate according to security best practices"


# Backward compatible wrapper
class ContextAnalyzer:
    """Context Analyzer with Enhanced Judge v2"""
    
    def __init__(self, project_profile=None):
        self.project_profile = project_profile
        self.knowledge_base = load_knowledge_base()
        logger.info("✓ Enhanced Context Analyzer v2 initialized")
    
    def analyze_detection(self, matched_text: str, line: str, file_path: str, 
                         rule_id: str, surrounding_lines: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze detection using Enhanced Judge v2"""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            ai_verify_violation_v2(
                code_snippet=line,
                rule_id=rule_id,
                file_path=file_path,
                knowledge_base=self.knowledge_base,
                surrounding_lines=surrounding_lines
            )
        )
        
        if result is None:
            return {
                "is_false_positive": True,
                "confidence": 0.9,
                "file_context": "safe",
                "data_type": "filtered",
                "reasons": ["Filtered by Enhanced Judge v2"],
                "recommendation": "Safe to ignore"
            }
        else:
            return {
                "is_false_positive": False,
                "confidence": result.get("confidence", 0.85),
                "file_context": result.get("file_context", "production"),
                "data_type": "real_data",
                "reasons": [result.get("thought_process", "")],
                "recommendation": result.get("recommendation", "Review required")
            }


__all__ = ['ContextAnalyzer', 'load_knowledge_base', 'ai_verify_violation_v2']
