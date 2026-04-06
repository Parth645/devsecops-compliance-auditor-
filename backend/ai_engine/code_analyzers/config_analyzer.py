"""
Configuration File Analyzer
Analyzes YAML, JSON, and other config files
"""

import re
import json
import yaml
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigAnalyzer:
    """Analyzes configuration files for compliance"""
    
    def __init__(self):
        pass
    
    def parse_yaml(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse YAML content"""
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse YAML: {e}")
            return None
    
    def parse_json(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse JSON content"""
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}")
            return None
    
    def extract_database_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract database settings from config"""
        db_settings = {}
        
        # Common database config keys
        db_keys = ['database', 'db', 'databases', 'datasource', 'mongodb', 'postgres', 'mysql']
        
        for key in db_keys:
            if key in config:
                db_settings[key] = config[key]
        
        # Check nested structures
        if 'spring' in config and 'datasource' in config['spring']:
            db_settings['spring_datasource'] = config['spring']['datasource']
        
        return db_settings
    
    def check_log_retention(self, config: Dict[str, Any]) -> Optional[int]:
        """Check log retention settings"""
        # Common log retention keys
        retention_keys = [
            'log_retention_days',
            'retention_days',
            'log_retention',
            'retention_period',
            'max_age_days'
        ]
        
        for key in retention_keys:
            if key in config:
                try:
                    return int(config[key])
                except (ValueError, TypeError):
                    pass
        
        # Check nested logging config
        if 'logging' in config:
            logging_config = config['logging']
            for key in retention_keys:
                if key in logging_config:
                    try:
                        return int(logging_config[key])
                    except (ValueError, TypeError):
                        pass
        
        return None
    
    def check_encryption_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check encryption configuration"""
        result = {
            'encryption_enabled': False,
            'encryption_algorithm': None,
            'tls_enabled': False,
            'tls_version': None
        }
        
        # Check for encryption settings
        encryption_keys = ['encryption', 'encrypt', 'ssl', 'tls']
        for key in encryption_keys:
            if key in config:
                result['encryption_enabled'] = True
                if isinstance(config[key], dict):
                    if 'algorithm' in config[key]:
                        result['encryption_algorithm'] = config[key]['algorithm']
                    if 'version' in config[key]:
                        result['tls_version'] = config[key]['version']
        
        # Check database encryption
        db_settings = self.extract_database_settings(config)
        for db_key, db_config in db_settings.items():
            if isinstance(db_config, dict):
                if 'ssl' in db_config or 'tls' in db_config:
                    result['tls_enabled'] = True
        
        return result
    
    def check_security_headers(self, config: Dict[str, Any]) -> List[str]:
        """Check security headers configuration"""
        missing_headers = []
        
        recommended_headers = [
            'X-Frame-Options',
            'X-Content-Type-Options',
            'Strict-Transport-Security',
            'Content-Security-Policy',
            'X-XSS-Protection'
        ]
        
        # Check if headers are configured
        headers_config = config.get('headers', {})
        if not isinstance(headers_config, dict):
            return recommended_headers
        
        for header in recommended_headers:
            if header not in headers_config and header.lower() not in headers_config:
                missing_headers.append(header)
        
        return missing_headers
    
    def extract_environment_variables(self, content: str) -> List[str]:
        """Extract environment variable references"""
        env_vars = []
        
        # Common patterns for env vars
        patterns = [
            r'\$\{([A-Z_][A-Z0-9_]*)\}',  # ${VAR_NAME}
            r'\$([A-Z_][A-Z0-9_]*)',  # $VAR_NAME
            r'process\.env\.([A-Z_][A-Z0-9_]*)',  # process.env.VAR_NAME
            r'os\.environ\[["\']([A-Z_][A-Z0-9_]*)["\']\]',  # os.environ['VAR_NAME']
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                env_vars.append(match.group(1))
        
        return list(set(env_vars))
    
    def check_hardcoded_secrets(self, content: str) -> List[Dict[str, Any]]:
        """Check for hardcoded secrets in config files"""
        secrets = []
        
        # Patterns for potential secrets
        secret_patterns = [
            (r'password\s*[:=]\s*["\']([^"\']{8,})["\']', 'password'),
            (r'api_key\s*[:=]\s*["\']([^"\']{20,})["\']', 'api_key'),
            (r'secret\s*[:=]\s*["\']([^"\']{20,})["\']', 'secret'),
            (r'token\s*[:=]\s*["\']([^"\']{20,})["\']', 'token'),
            (r'private_key\s*[:=]\s*["\']([^"\']{20,})["\']', 'private_key'),
        ]
        
        for pattern, secret_type in secret_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                value = match.group(1)
                # Skip obvious placeholders
                placeholders = ['your_password', 'your_api_key', 'changeme', 'example', 'test']
                if not any(placeholder in value.lower() for placeholder in placeholders):
                    secrets.append({
                        'type': secret_type,
                        'value': value[:10] + '...',  # Truncate for safety
                        'line': content[:match.start()].count('\n') + 1
                    })
        
        return secrets
    
    def check_cors_settings(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check CORS configuration"""
        result = {
            'cors_enabled': False,
            'allows_all_origins': False,
            'allowed_origins': []
        }
        
        cors_keys = ['cors', 'allowed_origins', 'allowedOrigins']
        for key in cors_keys:
            if key in config:
                result['cors_enabled'] = True
                cors_config = config[key]
                
                if isinstance(cors_config, list):
                    result['allowed_origins'] = cors_config
                    if '*' in cors_config:
                        result['allows_all_origins'] = True
                elif isinstance(cors_config, dict):
                    origins = cors_config.get('origins', cors_config.get('allowed_origins', []))
                    result['allowed_origins'] = origins
                    if '*' in origins:
                        result['allows_all_origins'] = True
        
        return result
