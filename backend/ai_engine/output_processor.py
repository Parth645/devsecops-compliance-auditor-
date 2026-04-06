"""
Output Processor - Aggregates and deduplicates scan results
Transforms raw violations into demo-ready grouped format
"""

import hashlib
from typing import Dict, List, Any
from pathlib import Path
import re


class OutputProcessor:
    """Process and aggregate scan results for clean output"""
    
    def __init__(self):
        self.grouped_violations = {}
        self.total_lines_scanned = 0
    
    def process_scan_results(self, raw_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw scan results into aggregated format
        
        Args:
            raw_results: Raw scan results with individual violations
            
        Returns:
            Processed results with grouped violations and risk score
        """
        violations = raw_results.get("violations", [])
        scanned_files = raw_results.get("scanned_files", [])
        
        # Calculate total lines scanned
        self.total_lines_scanned = sum(
            file_data.get("line_count", 0) 
            for file_data in scanned_files
        )
        
        # Group violations by rule + issue
        grouped = self._group_violations(violations)
        
        # Calculate risk score
        risk_score, risk_calc = self._calculate_risk_score(grouped, self.total_lines_scanned)
        
        # Get priority fixes
        priority_fixes = self._get_priority_fixes(grouped)
        
        # Clean paths in grouped violations
        for group in grouped:
            group["files"] = [self._clean_path(f) for f in group["files"]]
        
        return {
            "status": "success",
            "repository_path": self._clean_path(raw_results.get("repository_path", "")),
            "scan_timestamp": raw_results.get("scan_timestamp"),
            "grouped_issues": grouped,
            "total_unique_issues": len(grouped),
            "total_violations": len(violations),
            "analysis_summary": {
                "risk_score": risk_score,
                "risk_calculation": risk_calc,
                "priority_fixes": priority_fixes,
                "total_lines_scanned": self.total_lines_scanned,
                "files_scanned": len(scanned_files),
                "severity_breakdown": self._get_severity_breakdown(grouped),
                "category_breakdown": self._get_category_breakdown(grouped)
            },
            "compliance_score": raw_results.get("compliance_score", 0.0),
            "scan_duration": raw_results.get("scan_duration", 0)
        }
    
    def _group_violations(self, violations: List[Dict]) -> List[Dict[str, Any]]:
        """Group identical violations across files"""
        groups = {}
        
        for violation in violations:
            # Create unique key for grouping
            rule_id = violation.get("rule_id", "unknown")
            description = violation.get("description", "")
            category = violation.get("category", "unknown")
            severity = violation.get("severity", "MEDIUM")
            
            # Create hash of issue content for grouping
            issue_hash = hashlib.md5(
                f"{rule_id}:{description}:{category}".encode()
            ).hexdigest()[:8]
            
            group_key = f"{rule_id}_{issue_hash}"
            
            if group_key not in groups:
                groups[group_key] = {
                    "rule_id": rule_id,
                    "issue": description,
                    "severity": severity,
                    "category": category,
                    "count": 0,
                    "files": [],
                    "suggestion": violation.get("suggestion", "Review and fix this issue")
                }
            
            # Add file location
            file_path = violation.get("file_path", "unknown")
            line_number = violation.get("line_number", 0)
            groups[group_key]["files"].append(f"{file_path}:{line_number}")
            groups[group_key]["count"] += 1
        
        # Convert to list and sort by severity and count
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        grouped_list = sorted(
            groups.values(),
            key=lambda x: (severity_order.get(x["severity"], 4), -x["count"])
        )
        
        return grouped_list
    
    def _calculate_risk_score(self, grouped_violations: List[Dict], total_lines: int) -> tuple:
        """
        Calculate risk score (0-100, higher = more risky)
        
        Formula: (critical*15 + high*8 + med*3 + low*1) / total_lines * 100
        Capped at 100
        """
        if total_lines == 0:
            return 0, "No code scanned"
        
        severity_weights = {
            "CRITICAL": 15,
            "HIGH": 8,
            "MEDIUM": 3,
            "LOW": 1
        }
        
        weighted_sum = 0
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        
        for group in grouped_violations:
            severity = group.get("severity", "LOW")
            count = group.get("count", 1)
            weight = severity_weights.get(severity, 1)
            
            weighted_sum += weight * count
            severity_counts[severity] += count
        
        # Calculate risk score (normalize to 0-100)
        # Assume 1 violation per 100 lines is 100% risk
        risk_score = min(100, int((weighted_sum / (total_lines / 100)) * 100))
        
        # Create calculation explanation
        risk_calc = (
            f"(critical*15 + high*8 + med*3 + low*1) / total_lines * 100 = "
            f"({severity_counts['CRITICAL']}*15 + {severity_counts['HIGH']}*8 + "
            f"{severity_counts['MEDIUM']}*3 + {severity_counts['LOW']}*1) / {total_lines} * 100 = {risk_score}"
        )
        
        return risk_score, risk_calc
    
    def _get_priority_fixes(self, grouped_violations: List[Dict]) -> List[str]:
        """Get top priority fixes based on severity and count"""
        priority_fixes = []
        
        # Get top 5 issues by severity and count
        top_issues = sorted(
            grouped_violations,
            key=lambda x: (
                {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(x["severity"], 4),
                -x["count"]
            )
        )[:5]
        
        for issue in top_issues:
            count = issue["count"]
            description = issue["issue"][:80]  # Truncate long descriptions
            files_text = f"{count} file{'s' if count > 1 else ''}"
            
            priority_fixes.append(f"{description} ({files_text})")
        
        return priority_fixes
    
    def _get_severity_breakdown(self, grouped_violations: List[Dict]) -> Dict[str, int]:
        """Get count of violations by severity"""
        breakdown = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        
        for group in grouped_violations:
            severity = group.get("severity", "LOW")
            count = group.get("count", 1)
            breakdown[severity] = breakdown.get(severity, 0) + count
        
        return breakdown
    
    def _get_category_breakdown(self, grouped_violations: List[Dict]) -> Dict[str, int]:
        """Get count of violations by category"""
        breakdown = {}
        
        for group in grouped_violations:
            category = group.get("category", "unknown")
            count = group.get("count", 1)
            breakdown[category] = breakdown.get(category, 0) + count
        
        return breakdown
    
    def _clean_path(self, file_path: str) -> str:
        """
        Clean Windows paths to relative paths
        
        C:\\Users\\haru\\...\\repo\\src\\js\\file.js → src/js/file.js
        """
        if not file_path:
            return ""
        
        # Convert to Path object
        path = Path(file_path)
        
        # Try to find 'repo' in path and take everything after it
        parts = path.parts
        
        # Look for common repository indicators
        repo_indicators = ['repo', 'repository', 'project', 'src', 'app']
        
        for i, part in enumerate(parts):
            if any(indicator in part.lower() for indicator in repo_indicators):
                # Take from this point onwards
                relative_parts = parts[i:]
                return str(Path(*relative_parts)).replace('\\', '/')
        
        # If no indicator found, just return the filename and parent
        if len(parts) >= 2:
            return str(Path(*parts[-2:])).replace('\\', '/')
        
        return path.name
