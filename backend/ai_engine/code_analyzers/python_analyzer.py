"""
Python Code Analyzer
Analyzes Python code for compliance issues
"""

import re
import ast
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PythonAnalyzer:
    """Analyzes Python code for compliance"""
    
    def __init__(self):
        self.tree = None
        
    def parse(self, content: str) -> bool:
        """Parse Python code into AST"""
        try:
            self.tree = ast.parse(content)
            return True
        except SyntaxError as e:
            logger.warning(f"Failed to parse Python code: {e}")
            return False
    
    def extract_database_connections(self, content: str) -> List[Dict[str, Any]]:
        """Extract database connection strings"""
        connections = []
        
        # Common database connection patterns
        patterns = [
            r'(?:DATABASE_URL|DB_URL|SQLALCHEMY_DATABASE_URI)\s*=\s*["\']([^"\']+)["\']',
            r'(?:host|hostname)\s*=\s*["\']([^"\']+)["\']',
            r'psycopg2\.connect\([^)]*host\s*=\s*["\']([^"\']+)["\']',
            r'pymongo\.MongoClient\(["\']([^"\']+)["\']',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                conn_string = match.group(1)
                connections.append({
                    'connection_string': conn_string,
                    'host': self._extract_host(conn_string),
                    'is_localhost': 'localhost' in conn_string or '127.0.0.1' in conn_string
                })
        
        return connections
    
    def extract_api_endpoints(self, content: str) -> List[Dict[str, Any]]:
        """Extract API endpoint definitions"""
        endpoints = []
        
        # Flask/FastAPI route patterns
        route_patterns = [
            r'@app\.route\(["\']([^"\']+)["\']',
            r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            r'@api\.route\(["\']([^"\']+)["\']',
        ]
        
        for pattern in route_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                endpoint = match.group(1) if len(match.groups()) == 1 else match.group(2)
                endpoints.append({
                    'path': endpoint,
                    'has_auth': self._check_auth_decorator(content, match.start())
                })
        
        return endpoints
    
    def check_encryption_usage(self, content: str) -> Dict[str, Any]:
        """Check encryption algorithm usage"""
        result = {
            'weak_algorithms': [],
            'strong_algorithms': [],
            'no_encryption': False
        }
        
        # Weak algorithms
        weak_patterns = [
            (r'hashlib\.md5\(', 'MD5'),
            (r'hashlib\.sha1\(', 'SHA1'),
            (r'DES\.new\(', 'DES'),
            (r'RC4\.new\(', 'RC4'),
        ]
        
        for pattern, algo in weak_patterns:
            if re.search(pattern, content):
                result['weak_algorithms'].append(algo)
        
        # Strong algorithms
        strong_patterns = [
            (r'hashlib\.sha256\(', 'SHA256'),
            (r'hashlib\.sha512\(', 'SHA512'),
            (r'AES\.new\(', 'AES'),
            (r'bcrypt\.', 'bcrypt'),
            (r'argon2\.', 'Argon2'),
        ]
        
        for pattern, algo in strong_patterns:
            if re.search(pattern, content):
                result['strong_algorithms'].append(algo)
        
        # Check if handling sensitive data without encryption
        sensitive_keywords = ['password', 'secret', 'token', 'api_key', 'private_key']
        has_sensitive = any(keyword in content.lower() for keyword in sensitive_keywords)
        has_encryption = bool(result['strong_algorithms'])
        
        result['no_encryption'] = has_sensitive and not has_encryption
        
        return result
    
    def check_logging_practices(self, content: str) -> List[Dict[str, Any]]:
        """Check logging practices"""
        issues = []
        
        # Check for sensitive data in logs
        log_patterns = [
            r'log(?:ger)?\.(?:info|debug|warning|error)\([^)]*(?:password|secret|token|api_key)',
            r'print\([^)]*(?:password|secret|token|api_key)',
        ]
        
        for pattern in log_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                issues.append({
                    'type': 'sensitive_data_in_logs',
                    'line': content[:match.start()].count('\n') + 1,
                    'snippet': match.group(0)
                })
        
        return issues
    
    def check_consent_logging(self, content: str) -> Dict[str, bool]:
        """Check if consent is being logged properly"""
        result = {
            'has_consent_field': False,
            'has_timestamp': False,
            'has_purpose': False
        }
        
        # Check for consent-related fields
        consent_patterns = [
            r'consent',
            r'user_consent',
            r'consent_given',
            r'consent_timestamp',
            r'consent_purpose'
        ]
        
        for pattern in consent_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                result['has_consent_field'] = True
                if 'timestamp' in pattern:
                    result['has_timestamp'] = True
                if 'purpose' in pattern:
                    result['has_purpose'] = True
        
        return result
    
    def _extract_host(self, connection_string: str) -> Optional[str]:
        """Extract host from connection string"""
        # PostgreSQL: postgresql://user:pass@host:port/db
        # MySQL: mysql://user:pass@host:port/db
        # MongoDB: mongodb://host:port/db
        
        host_match = re.search(r'@([^:/@]+)', connection_string)
        if host_match:
            return host_match.group(1)
        
        # Simple host:port format
        host_match = re.search(r'^([^:/@]+)', connection_string)
        if host_match:
            return host_match.group(1)
        
        return None
    
    def _check_auth_decorator(self, content: str, position: int) -> bool:
        """Check if endpoint has authentication decorator"""
        # Look backwards from position for auth decorators
        before_content = content[:position]
        lines = before_content.split('\n')[-10:]  # Check last 10 lines
        
        auth_patterns = [
            r'@login_required',
            r'@auth_required',
            r'@requires_auth',
            r'@jwt_required',
            r'@token_required',
        ]
        
        for line in lines:
            for pattern in auth_patterns:
                if re.search(pattern, line):
                    return True
        
        return False
