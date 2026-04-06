"""
Finding Merger Module
Merges and deduplicates findings from Semgrep and CodeQL
"""

import logging
from typing import Dict, List, Any
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class FindingMerger:
    """
    Merges findings from multiple detectors (Semgrep, CodeQL)
    Deduplicates findings to avoid redundancy
    Ranks findings by severity and confidence
    """
    
    def __init__(self, dedup_similarity: float = 0.85):
        """
        Args:
            dedup_similarity: Similarity threshold for deduplication (0-1)
        """
        self.dedup_similarity = dedup_similarity
    
    async def merge(self, 
                   semgrep_results: Dict[str, Any],
                   codeql_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge findings from both detectors
        
        Returns:
            Merged findings with deduplication and ranking
        """
        all_findings = []
        
        # Collect from both detectors
        semgrep_findings = semgrep_results.get("findings", [])
        codeql_findings = codeql_results.get("findings", [])
        
        logger.info(f"[MERGER] Semgrep: {len(semgrep_findings)} findings")
        logger.info(f"[MERGER] CodeQL: {len(codeql_findings)} findings")
        
        # Add Semgrep findings
        for finding in semgrep_findings:
            all_findings.append({
                **finding,
                "detector": "semgrep",
                "confidence": 0.90  # Semgrep rules are reliable
            })
        
        # Deduplicate with CodeQL findings
        unique_findings = []
        for codeql_finding in codeql_findings:
            is_duplicate = False
            for existing in unique_findings:
                if self._is_duplicate(existing, codeql_finding):
                    # Merge evidence
                    is_duplicate = True
                    existing["detectors"] = list(set(existing.get("detectors", []) + ["codeql"]))
                    existing["confidence"] = max(existing.get("confidence", 0.8), 0.92)
                    break
            
            if not is_duplicate:
                codeql_finding["confidence"] = 0.92  # CodeQL graph-based analysis
                codeql_finding["detectors"] = ["codeql"]
                all_findings.append(codeql_finding)
                unique_findings.append(codeql_finding)
        
        # Sort by severity + confidence
        sorted_findings = self._rank_findings(all_findings)
        
        logger.info(f"[MERGER] After deduplication: {len(sorted_findings)} unique findings")
        logger.info(f"  Critical: {len([f for f in sorted_findings if f.get('severity') == 'critical'])}")
        logger.info(f"  High: {len([f for f in sorted_findings if f.get('severity') == 'high'])}")
        logger.info(f"  Medium: {len([f for f in sorted_findings if f.get('severity') == 'medium'])}")
        
        return {
            "merged_findings": sorted_findings,
            "total_unique": len(sorted_findings),
            "semgrep_count": len(semgrep_findings),
            "codeql_count": len(codeql_findings),
            "duplicates_removed": len(semgrep_findings) + len(codeql_findings) - len(sorted_findings),
            "status": "merged"
        }
    
    def _is_duplicate(self, finding1: Dict, finding2: Dict) -> bool:
        """
        Check if two findings are duplicates
        Considers: file, line number, message similarity
        """
        # Same file and similar line numbers
        if (finding1.get("file_path") == finding2.get("file_path")):
            line1 = finding1.get("line_start", 0)
            line2 = finding2.get("line_start", 0)
            
            # Same or adjacent lines
            if abs(line1 - line2) <= 2:
                # Check message similarity
                msg1 = finding1.get("message", "").lower()
                msg2 = finding2.get("message", "").lower()
                
                similarity = SequenceMatcher(None, msg1, msg2).ratio()
                return similarity > self.dedup_similarity
        
        return False
    
    def _rank_findings(self, findings: List[Dict]) -> List[Dict]:
        """Rank findings by severity + confidence"""
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        
        def sort_key(f):
            severity_score = severity_order.get(f.get("severity", "low"), 0)
            confidence = f.get("confidence", 0.5)
            return (severity_score, confidence)
        
        return sorted(findings, key=sort_key, reverse=True)
    
    def group_by_type(self, findings: List[Dict]) -> Dict[str, List[Dict]]:
        """Group findings by type/rule"""
        grouped = {}
        for finding in findings:
            rule_id = finding.get("rule_id", "unknown")
            if rule_id not in grouped:
                grouped[rule_id] = []
            grouped[rule_id].append(finding)
        
        return grouped
    
    def get_summary(self, findings: List[Dict]) -> Dict[str, Any]:
        """Generate summary statistics"""
        return {
            "total": len(findings),
            "by_severity": self._count_by_severity(findings),
            "by_framework": self._count_by_framework(findings),
            "by_detector": self._count_by_detector(findings),
            "high_risk_files": self._get_high_risk_files(findings)
        }
    
    def _count_by_severity(self, findings: List[Dict]) -> Dict[str, int]:
        """Count findings by severity"""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for finding in findings:
            severity = finding.get("severity", "low")
            if severity in counts:
                counts[severity] += 1
        return counts
    
    def _count_by_framework(self, findings: List[Dict]) -> Dict[str, int]:
        """Count findings by compliance framework"""
        counts = {}
        for finding in findings:
            framework = finding.get("framework", "UNKNOWN")
            counts[framework] = counts.get(framework, 0) + 1
        return counts
    
    def _count_by_detector(self, findings: List[Dict]) -> Dict[str, int]:
        """Count findings by detector"""
        counts = {}
        for finding in findings:
            detectors = finding.get("detectors", [finding.get("detector", "unknown")])
            for detector in detectors:
                counts[detector] = counts.get(detector, 0) + 1
        return counts
    
    def _get_high_risk_files(self, findings: List[Dict], top_n: int = 10) -> List[Dict]:
        """Get files with highest risk"""
        file_risks = {}
        for finding in findings:
            file_path = finding.get("file_path", "unknown")
            if file_path not in file_risks:
                file_risks[file_path] = {
                    "file": finding.get("file", ""),
                    "critical": 0,
                    "high": 0,
                    "total": 0
                }
            
            severity = finding.get("severity", "low")
            if severity == "critical":
                file_risks[file_path]["critical"] += 1
            elif severity == "high":
                file_risks[file_path]["high"] += 1
            
            file_risks[file_path]["total"] += 1
        
        # Sort by critical count, then high count
        sorted_files = sorted(
            file_risks.items(),
            key=lambda x: (x[1]["critical"], x[1]["high"]),
            reverse=True
        )
        
        return [
            {**v, "file_path": k}
            for k, v in sorted_files[:top_n]
        ]
