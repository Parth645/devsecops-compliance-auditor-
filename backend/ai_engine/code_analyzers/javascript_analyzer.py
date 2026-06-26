"""
JavaScript/Node.js Code Analyzer
Analyzes JavaScript and TypeScript code for compliance
"""

import re
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class JavaScriptAnalyzer:
    """Analyzes JavaScript/Node.js code for compliance"""
    
    def __init__(self):
        pass
    
    def extract_api_endpoints(self, content: str) -> List[Dict[str, Any]]:
        """Extract Express/Node.js API endpoints"""
        endpoints = []
        
        # Express route patterns
        route_patterns = [
            r'(?:app|router)\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            r'\.route\(["\']([^"\']+)["\']',
        ]
        
        for pattern in route_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                if len(match.groups()) == 2:
                    method = match.group(1)
                    path = match.group(2)
                else:
                    method = 'unknown'
                    path = match.group(1)
                
                endpoints.append({
                    'method': method,
                    'path': path,
                    'has_auth': self._check_auth_middleware(content, match.start())
                })
        
        return endpoints
    
    def check_encryption_usage(self, content: str) -> Dict[str, Any]:
        """Check encryption practices in JavaScript"""
        result = {
            'weak_algorithms': [],
            'strong_algorithms': [],
            'no_encryption': False
        }
        
        # Weak algorithms
        weak_patterns = [
            (r'crypto\.createHash\(["\']md5["\']', 'MD5'),
            (r'crypto\.createHash\(["\']sha1["\']', 'SHA1'),
            (r'CryptoJS\.MD5', 'MD5'),
            (r'CryptoJS\.SHA1', 'SHA1'),
        ]
        
        for pattern, algo in weak_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                result['weak_algorithms'].append(algo)
        
        # Strong algorithms
        strong_patterns = [
            (r'crypto\.createHash\(["\']sha256["\']', 'SHA256'),
            (r'crypto\.createHash\(["\']sha512["\']', 'SHA512'),
            (r'bcrypt\.', 'bcrypt'),
            (r'crypto\.createCipheriv\(["\']aes', 'AES'),
        ]
        
        for pattern, algo in strong_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                result['strong_algorithms'].append(algo)
        
        return result
    
    def check_logging_practices(self, content: str) -> List[Dict[str, Any]]:
        """Check logging practices"""
        issues = []
        
        # Check for sensitive data in console.log
        log_patterns = [
            r'console\.log\([^)]*(?:password|secret|token|api_key)',
            r'logger\.(?:info|debug|warn|error)\([^)]*(?:password|secret|token|api_key)',
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
    
    def check_database_connections(self, content: str) -> List[Dict[str, Any]]:
        """Check database connection configurations"""
        connections = []
        
        # MongoDB connections
        mongo_pattern = r'mongoose\.connect\(["\']([^"\']+)["\']'
        matches = re.finditer(mongo_pattern, content)
        for match in matches:
            conn_string = match.group(1)
            connections.append({
                'type': 'mongodb',
                'connection_string': conn_string,
                'uses_env': 'process.env' in conn_string
            })
        
        # PostgreSQL/MySQL connections
        sql_patterns = [
            r'new\s+Pool\(\{[^}]*host:\s*["\']([^"\']+)["\']',
            r'createConnection\(\{[^}]*host:\s*["\']([^"\']+)["\']',
        ]
        
        for pattern in sql_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                host = match.group(1)
                connections.append({
                    'type': 'sql',
                    'host': host,
                    'is_localhost': 'localhost' in host or '127.0.0.1' in host
                })
        
        return connections
    
    def check_jwt_security(self, content: str) -> Dict[str, Any]:
        """Check JWT implementation security"""
        result = {
            'uses_jwt': False,
            'secret_hardcoded': False,
            'weak_algorithm': False
        }
        
        # Check if JWT is used
        if re.search(r'jwt\.sign|jsonwebtoken', content, re.IGNORECASE):
            result['uses_jwt'] = True
            
            # Check for hardcoded secrets
            secret_pattern = r'jwt\.sign\([^,]+,\s*["\']([^"\']{8,})["\']'
            if re.search(secret_pattern, content):
                result['secret_hardcoded'] = True
            
            # Check for weak algorithms
            if re.search(r'algorithm:\s*["\']HS256["\']', content):
                result['weak_algorithm'] = True
        
        return result
    
    def check_cors_configuration(self, content: str) -> Dict[str, Any]:
        """Check CORS configuration"""
        result = {
            'has_cors': False,
            'allows_all_origins': False,
            'allows_credentials': False
        }
        
        if re.search(r'cors\(', content):
            result['has_cors'] = True
            
            # Check for permissive CORS
            if re.search(r'origin:\s*["\*]', content):
                result['allows_all_origins'] = True
            
            if re.search(r'credentials:\s*true', content):
                result['allows_credentials'] = True
        
        return result
    
    def _check_auth_middleware(self, content: str, position: int) -> bool:
        """Check if endpoint has authentication middleware"""
        # Look at the route definition line
        line_start = content.rfind('\n', 0, position) + 1
        line_end = content.find('\n', position)
        line = content[line_start:line_end]
        
        # Common auth middleware patterns
        auth_patterns = [
            r'authenticate',
            r'isAuth',
            r'requireAuth',
            r'verifyToken',
            r'checkAuth',
        ]
        
        for pattern in auth_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        
        return False
