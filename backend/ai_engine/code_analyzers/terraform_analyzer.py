"""
Terraform/IaC Analyzer
Parses and analyzes Terraform and CloudFormation files
"""

import re
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TerraformAnalyzer:
    """Analyzes Terraform and Infrastructure-as-Code files"""
    
    # Indian cloud regions
    INDIAN_REGIONS = {
        'aws': ['ap-south-1', 'ap-south-2'],  # Mumbai
        'azure': ['centralindia', 'southindia', 'westindia'],
        'gcp': ['asia-south1', 'asia-south2']  # Mumbai, Delhi
    }
    
    def __init__(self):
        self.resources = []
        
    def extract_aws_resources(self, content: str) -> List[Dict[str, Any]]:
        """Extract AWS resources from Terraform"""
        resources = []
        
        # Pattern: resource "aws_*" "name" { ... }
        resource_pattern = r'resource\s+"(aws_\w+)"\s+"(\w+)"\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        
        matches = re.finditer(resource_pattern, content, re.MULTILINE | re.DOTALL)
        for match in matches:
            resource_type = match.group(1)
            resource_name = match.group(2)
            resource_body = match.group(3)
            
            # Extract region
            region = self._extract_region(resource_body)
            
            resources.append({
                'type': resource_type,
                'name': resource_name,
                'region': region,
                'body': resource_body,
                'is_in_india': region in self.INDIAN_REGIONS['aws'] if region else None
            })
        
        return resources
    
    def extract_regions(self, content: str) -> List[str]:
        """Extract all regions mentioned in file"""
        regions = []
        
        # Look for region specifications
        region_patterns = [
            r'region\s*=\s*"([^"]+)"',
            r'location\s*=\s*"([^"]+)"',
            r'--region\s+(\S+)',
        ]
        
        for pattern in region_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                regions.append(match.group(1))
        
        return list(set(regions))
    
    def extract_database_configs(self, content: str) -> List[Dict[str, Any]]:
        """Extract database configurations"""
        databases = []
        
        # RDS instances
        rds_pattern = r'resource\s+"aws_db_instance"\s+"(\w+)"\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        matches = re.finditer(rds_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            db_name = match.group(1)
            db_body = match.group(2)
            
            databases.append({
                'type': 'rds',
                'name': db_name,
                'region': self._extract_region(db_body),
                'encrypted': 'storage_encrypted' in db_body,
                'multi_az': 'multi_az' in db_body
            })
        
        return databases
    
    def check_data_localization(self, content: str) -> List[Dict[str, Any]]:
        """Check if resources are in Indian regions"""
        violations = []
        
        # Check AWS resources
        aws_resources = self.extract_aws_resources(content)
        for resource in aws_resources:
            if resource['region'] and not resource['is_in_india']:
                violations.append({
                    'resource_type': resource['type'],
                    'resource_name': resource['name'],
                    'region': resource['region'],
                    'issue': f"Resource in non-Indian region: {resource['region']}",
                    'suggestion': f"Use Indian region: {', '.join(self.INDIAN_REGIONS['aws'])}"
                })
        
        return violations
    
    def check_encryption(self, content: str) -> List[Dict[str, Any]]:
        """Check encryption settings"""
        violations = []
        
        # Check S3 buckets
        s3_pattern = r'resource\s+"aws_s3_bucket"\s+"(\w+)"\s*\{([^}]*)\}'
        matches = re.finditer(s3_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            bucket_name = match.group(1)
            bucket_body = match.group(2)
            
            if 'server_side_encryption_configuration' not in bucket_body:
                violations.append({
                    'resource_type': 'aws_s3_bucket',
                    'resource_name': bucket_name,
                    'issue': 'S3 bucket encryption not configured',
                    'suggestion': 'Add server_side_encryption_configuration block'
                })
        
        # Check RDS encryption
        databases = self.extract_database_configs(content)
        for db in databases:
            if not db['encrypted']:
                violations.append({
                    'resource_type': 'aws_db_instance',
                    'resource_name': db['name'],
                    'issue': 'RDS instance not encrypted',
                    'suggestion': 'Set storage_encrypted = true'
                })
        
        return violations
    
    def _extract_region(self, content: str) -> Optional[str]:
        """Extract region from resource body"""
        region_match = re.search(r'region\s*=\s*"([^"]+)"', content)
        if region_match:
            return region_match.group(1)
        
        # Check for availability_zone (can infer region)
        az_match = re.search(r'availability_zone\s*=\s*"([^"]+)"', content)
        if az_match:
            az = az_match.group(1)
            # Extract region from AZ (e.g., ap-south-1a -> ap-south-1)
            return az[:-1] if az else None
        
        return None
