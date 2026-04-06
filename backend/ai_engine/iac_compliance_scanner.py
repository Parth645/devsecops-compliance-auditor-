"""
Infrastructure-as-Code (IaC) Compliance Scanner
Scans Terraform, Kubernetes, Docker, and CloudFormation for compliance violations
Enforces data localization, encryption, and retention policies
"""

import logging
import json
import yaml
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class IaCComplianceScanner:
    """
    Scans Infrastructure-as-Code files for compliance violations
    Focus areas:
    - Data localization (servers in Indian region)
    - Log retention (CERT-In: 180 days minimum)
    - Encryption enforcement (in-transit and at-rest)
    - Backup and disaster recovery
    """
    
    def __init__(self):
        """Initialize IaC scanner"""
        self.violations = []
        self.rules = self._init_rules()
        logger.info("✓ IaC Compliance Scanner initialized")
    
    def _init_rules(self) -> Dict[str, Dict]:
        """Initialize compliance rules for IaC"""
        return {
            "data_localization": {
                "severity": "critical",
                "framework": "DPDPA",
                "description": "Data must be stored in India (ap-south-1, ap-south-2 regions)"
            },
            "log_retention": {
                "severity": "high",
                "framework": "CERT-In",
                "description": "Logs must be retained for minimum 180 days"
            },
            "encryption_at_rest": {
                "severity": "critical",
                "framework": "RBI",
                "description": "All persistent data must be encrypted at rest"
            },
            "encryption_in_transit": {
                "severity": "high",
                "framework": "RBI",
                "description": "All data in transit must use TLS 1.2+ (no TLS 1.0/1.1)"
            },
            "backup_retention": {
                "severity": "high",
                "framework": "RBI",
                "description": "Backups must be retained for minimum 180 days"
            },
            "network_isolation": {
                "severity": "high",
                "framework": "IT Act",
                "description": "Sensitive data must be in isolated VPCs with restricted access"
            }
        }
    
    def scan_iac_file(self, file_path: str, file_content: str) -> List[Dict[str, Any]]:
        """
        Scan a single IaC file for compliance violations
        
        Args:
            file_path: Path to IaC file
            file_content: Content of the file
            
        Returns:
            List of violations found
        """
        violations = []
        file_lower = file_path.lower()
        
        if file_lower.endswith('.tf'):
            violations.extend(self._scan_terraform(file_path, file_content))
        elif file_lower.endswith(('.yaml', '.yml')):
            violations.extend(self._scan_kubernetes_or_compose(file_path, file_content))
        elif file_lower.endswith(('dockerfile', 'docker-compose.yml')):
            violations.extend(self._scan_docker(file_path, file_content))
        elif 'cloudformation' in file_lower or file_lower.endswith(('.json', '.yaml')):
            violations.extend(self._scan_cloudformation(file_path, file_content))
        
        return violations
    
    def _scan_terraform(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Scan Terraform files for compliance"""
        violations = []
        
        # Check 1: AWS region must be ap-south-1 or ap-south-2 (India)
        region_pattern = r'region\s*=\s*["\']([^"\']+)["\']'
        regions = re.findall(region_pattern, content)
        
        for match in re.finditer(region_pattern, content):
            region = match.group(1)
            if region not in ['ap-south-1', 'ap-south-2']:
                line_num = content[:match.start()].count('\n') + 1
                violations.append({
                    'rule': 'data_localization',
                    'file': file_path,
                    'line': line_num,
                    'severity': 'critical',
                    'message': f'DPDPA VIOLATION: Data stored in region "{region}" instead of India (ap-south-1). Data must remain in Indian servers',
                    'finding': f'region = "{region}"',
                    'remediation': 'Change region to "ap-south-1" or "ap-south-2"'
                })
        
        # Check 2: RDS encryption at rest
        if 'aws_db_instance' in content:
            for match in re.finditer(r'storage_encrypted\s*=\s*(false|False)', content):
                line_num = content[:match.start()].count('\n') + 1
                violations.append({
                    'rule': 'encryption_at_rest',
                    'file': file_path,
                    'line': line_num,
                    'severity': 'critical',
                    'message': 'RBI VIOLATION: RDS database encryption disabled. All customer data must be encrypted at rest',
                    'finding': 'storage_encrypted = false',
                    'remediation': 'Set storage_encrypted = true and use KMS key for encryption'
                })
        
        # Check 3: CloudWatch Logs retention
        if 'aws_cloudwatch_log_group' in content:
            # Check for missing retention_in_days
            if 'retention_in_days' not in content:
                violations.append({
                    'rule': 'log_retention',
                    'file': file_path,
                    'line': 0,
                    'severity': 'high',
                    'message': 'CERT-In VIOLATION: Log retention period not set. Must be minimum 180 days',
                    'finding': 'Missing retention_in_days in aws_cloudwatch_log_group',
                    'remediation': 'Add: retention_in_days = 180'
                })
            else:
                for match in re.finditer(r'retention_in_days\s*=\s*(\d+)', content):
                    retention = int(match.group(1))
                    if retention < 180:
                        line_num = content[:match.start()].count('\n') + 1
                        violations.append({
                            'rule': 'log_retention',
                            'file': file_path,
                            'line': line_num,
                            'severity': 'high',
                            'message': f'CERT-In VIOLATION: Log retention is {retention} days, minimum required is 180',
                            'finding': f'retention_in_days = {retention}',
                            'remediation': 'Set retention_in_days = 180 or higher'
                        })
        
        # Check 4: ElastiCache encryption
        if 'aws_elasticache_cluster' in content:
            if 'at_rest_encryption_enabled' not in content:
                violations.append({
                    'rule': 'encryption_at_rest',
                    'file': file_path,
                    'line': 0,
                    'severity': 'high',
                    'message': 'RBI VIOLATION: ElastiCache encryption not enabled. Cache must be encrypted',
                    'finding': 'Missing at_rest_encryption_enabled',
                    'remediation': 'Add: at_rest_encryption_enabled = true'
                })
        
        # Check 5: Security Group - ensure not open to 0.0.0.0
        if 'aws_security_group' in content:
            for match in re.finditer(r'from_port\s*=\s*(\d+).*?cidr_blocks\s*=\s*\["0\.0\.0\.0/0"\]', 
                                    content, re.DOTALL):
                port = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                if port in ['443', '80', '3306', '5432']:
                    violations.append({
                        'rule': 'network_isolation',
                        'file': file_path,
                        'line': line_num,
                        'severity': 'high',
                        'message': f'IT Act VIOLATION: Security group open to 0.0.0.0/0 on port {port}. Restrict access',
                        'finding': f'Port {port} accessible from 0.0.0.0/0',
                        'remediation': 'Restrict CIDR blocks to specific IP ranges or VPC'
                    })
        
        return violations
    
    def _scan_kubernetes_or_compose(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Scan Kubernetes or Docker Compose files"""
        violations = []
        
        try:
            # Try to parse as YAML
            data = yaml.safe_load(content)
            if not data:
                return violations
            
            # Check for Kubernetes resources
            if isinstance(data, dict):
                spec = data.get('spec', {})
                kind = data.get('kind', '')
                
                # Check 1: Secrets stored as base64 only (not truly encrypted)
                if kind == 'Secret' and data.get('type') == 'Opaque':
                    violations.append({
                        'rule': 'encryption_at_rest',
                        'file': file_path,
                        'line': 0,
                        'severity': 'critical',
                        'message': 'RBI VIOLATION: Secret stored as base64 (not encrypted). Use etcd encryption or external secret manager',
                        'finding': 'Kind: Secret with type: Opaque',
                        'remediation': 'Use: encrypted: true in etcd or integrate Vault/AWS Secrets Manager'
                    })
                
                # Check 2: Pod without resource limits (security risk)
                if kind == 'Pod' or kind == 'Deployment':
                    containers = spec.get('template', {}).get('spec', {}).get('containers', [])
                    for i, container in enumerate(containers):
                        if 'resources' not in container or 'limits' not in container.get('resources', {}):
                            violations.append({
                                'rule': 'encryption_in_transit',
                                'file': file_path,
                                'line': 0,
                                'severity': 'medium',
                                'message': 'IT Act VIOLATION: Container without resource limits. Could be abused for data exfiltration',
                                'finding': f'Container {container.get("name")} missing resource limits',
                                'remediation': 'Add resource limits: cpu, memory'
                            })
        except yaml.YAMLError:
            # Not valid YAML, check for plain text patterns
            if container not in content:
                pass
        
        return violations
    
    def _scan_cloudformation(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Scan AWS CloudFormation templates"""
        violations = []
        
        try:
            if file_path.endswith('.json'):
                data = json.loads(content)
            else:
                data = yaml.safe_load(content)
            
            if not data:
                return violations
            
            resources = data.get('Resources', {})
            
            # Check RDS encryption
            for logical_id, resource in resources.items():
                if resource.get('Type') == 'AWS::RDS::DBInstance':
                    props = resource.get('Properties', {})
                    if props.get('StorageEncrypted') is False:
                        violations.append({
                            'rule': 'encryption_at_rest',
                            'file': file_path,
                            'line': 0,
                            'severity': 'critical',
                            'message': f'RBI VIOLATION: RDS instance {logical_id} not encrypted',
                            'finding': 'StorageEncrypted: false',
                            'remediation': 'Set StorageEncrypted: true'
                        })
        except (json.JSONDecodeError, yaml.YAMLError):
            pass
        
        return violations
    
    def _scan_docker(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Scan Dockerfile and docker-compose.yml"""
        violations = []
        
        # Check for secrets hardcoded in Dockerfile
        if 'dockerfile' in file_path.lower():
            for match in re.finditer(r'(password|secret|key|token|api_key)\s*=\s*["\']([^"\']+)["\']', 
                                    content, re.IGNORECASE):
                line_num = content[:match.start()].count('\n') + 1
                violations.append({
                    'rule': 'encryption_at_rest',
                    'file': file_path,
                    'line': line_num,
                    'severity': 'critical',
                    'message': 'IT Act VIOLATION: Secret hardcoded in Dockerfile. Use environment variables or secret management',
                    'finding': match.group(0),
                    'remediation': 'Use ARG or pass via environment variables'
                })
        
        # Check for non-HTTPS registries
        for match in re.finditer(r'FROM\s+(.+?)\n', content):
            image = match.group(1)
            if image.startswith('http://'):
                line_num = content[:match.start()].count('\n') + 1
                violations.append({
                    'rule': 'encryption_in_transit',
                    'file': file_path,
                    'line': line_num,
                    'severity': 'high',
                    'message': 'RBI VIOLATION: Docker image pulled over HTTP. Use HTTPS registry',
                    'finding': f'FROM {image}',
                    'remediation': 'Use HTTPS registry URL'
                })
        
        return violations
    
    def get_violations(self) -> List[Dict[str, Any]]:
        """Get all violations found"""
        return self.violations


def identify_iac_files(repo_path: str) -> List[str]:
    """
    Identify all Infrastructure-as-Code files in repository
    
    Args:
        repo_path: Path to repository
        
    Returns:
        List of IaC file paths
    """
    iac_patterns = [
        '**/*.tf',                          # Terraform
        '**/*.tfvars',                      # Terraform variables
        '**/docker-compose.yml',            # Docker Compose
        '**/Dockerfile',                    # Dockerfile
        '**/Dockerfile.*',                  # Dockerfile variants
        '**/*.yaml',                        # Kubernetes manifests
        '**/*.yml',                         # Kubernetes manifests
        '**/k8s/**/*.yaml',                 # Kubernetes in k8s folder
        '**/kubernetes/**/*.yaml',          # Kubernetes in kubernetes folder
        '**/cloudformation/**/*.json',      # CloudFormation
        '**/cloudformation/**/*.yaml',      # CloudFormation
        '**/infrastructure/**/*.tf',        # Infrastructure folder Terraform
        '**/infra/**/*.tf',                 # Infra folder Terraform
    ]
    
    iac_files = []
    path = Path(repo_path)
    
    for pattern in iac_patterns:
        iac_files.extend([str(f) for f in path.glob(pattern)])
    
    return list(set(iac_files))  # Remove duplicates
