"""
Enhanced Repository Scanner with Indian Compliance Checkers
Integrates intelligent compliance checkers for DPDP, CERT-In, and RBI
Now with Context-Aware False Positive Filtering and Agentic Judge
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import sys
import os
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(__file__))

from compliance_checkers.utils import get_all_checkers, aggregate_violations, generate_compliance_report
from compliance_checkers import Violation

# Try to import Semgrep scanner
try:
    from semgrep_scanner import SemgrepScanner
    SEMGREP_AVAILABLE = True
except ImportError:
    SEMGREP_AVAILABLE = False
    SemgrepScanner = None

logger = logging.getLogger(__name__)


def is_vendor_or_generated(file_path: str) -> bool:
    """
    STEP 2: The Bouncer - Strictly filter vendor/library/generated files
    
    This function implements strict filtering rules to prevent scanning
    of third-party libraries, generated code, and build artifacts.
    
    Args:
        file_path: Path to the file (relative or absolute)
        
    Returns:
        True if file should be BLOCKED (not scanned), False if allowed
    """
    # Normalize path for consistent checking
    normalized_path = file_path.replace('\\', '/').lower()
    path_parts = normalized_path.split('/')
    filename = os.path.basename(normalized_path)
    
    # RULE 1: Block specific directories (STRICT)
    blocked_dirs = {
        'node_modules', 'dist', 'build', 'venv', '.venv', 'bin', '.git',
        'contracts/lib', 'vendor', '__pycache__', 'lib', 'libs',
        'bower_components', 'jspm_packages', 'packages', 'target',
        'out', '.next', '.nuxt', 'coverage', '.pytest_cache', '.mypy_cache',
        'migrations', 'alembic'
    }
    
    for part in path_parts:
        if part in blocked_dirs:
            return True
        # Also check for partial matches
        if any(blocked in part for blocked in ['node_modules', 'vendor', 'dist', 'build']):
            return True
    
    # RULE 2: Block specific file extensions (STRICT)
    blocked_extensions = {
        '.min.js', '.min.css', '.map', '.lock', '.svg',
        '.png', '.jpg', '.jpeg', '.gif', '.ico', '.woff', '.woff2',
        '.ttf', '.eot', '.pyc', '.pyo', '.so', '.dll', '.dylib',
        '.wasm', '.class', '.jar', '.war', '.ear'
    }
    
    for ext in blocked_extensions:
        if filename.endswith(ext):
            return True
    
    # RULE 3: Block specific filenames (STRICT)
    blocked_filenames = {
        'package-lock.json', 'yarn.lock', 'poetry.lock', 'pipfile.lock',
        'composer.lock', 'gemfile.lock', 'web3.min.js', 'truffle-contract.js',
        'jquery.min.js', 'bootstrap.min.js', 'bootstrap.min.css'
    }
    
    if filename in blocked_filenames:
        return True
    
    # RULE 4: Heuristic - Deeply nested files (>5 levels) without 'src'
    depth = len(path_parts)
    if depth > 5 and 'src' not in path_parts:
        # Likely a deeply nested dependency or generated file
        return True
    
    # RULE 5: Heuristic - Files with hash patterns (webpack bundles)
    # e.g., main.a1b2c3d4.js or bundle.12345678.js
    if '.' in filename:
        parts = filename.split('.')
        if len(parts) >= 3:
            # Check if middle part looks like a hash (8+ alphanumeric)
            middle = parts[-2]
            if len(middle) >= 8 and middle.isalnum() and not middle.isalpha():
                return True
    
    # RULE 6: Heuristic - Generated/compiled indicators in path
    generated_indicators = ['generated', 'compiled', 'bundled', 'minified', 'auto-generated']
    if any(indicator in normalized_path for indicator in generated_indicators):
        return True
    
    # File is allowed to be scanned
    return False


def is_infrastructure_as_code(file_path: str) -> bool:
    """
    PIVOT 3: Identify Infrastructure-as-Code files for compliance scanning
    
    IaC files contain critical compliance info:
    - Data localization (AWS region for DPDPA/RBI)
    - Log retention (CERT-In requirements)
    - Encryption settings (RBI encryption mandates)
    
    Args:
        file_path: Path to file
        
    Returns:
        True if file is IaC, False otherwise
    """
    file_lower = file_path.lower()
    
    # Terraform files
    if file_lower.endswith(('.tf', '.tfvars')):
        return True
    
    # Docker and docker-compose
    if 'dockerfile' in file_lower or 'docker-compose' in file_lower:
        return True
    
    # Kubernetes manifests
    if (file_lower.endswith(('.yaml', '.yml')) and 
        any(x in file_lower for x in ['/k8s/', '/kubernetes/', '/manifests/', 'kube'])):
        return True
    
    # CloudFormation
    if ('cloudformation' in file_lower or 'cfn' in file_lower):
        return True
    
    # Infrastructure directories
    if any(x in file_lower for x in ['/terraform/', '/infra/', '/infrastructure/', '/iac/']):
        return True
    
    return False


class EnhancedRepositoryScanner:
    """
    Enhanced repository scanner with intelligent Indian compliance checking
    Now includes context-aware false positive filtering
    """
    
    def __init__(self, policy_processor=None, enable_context_analysis=True, use_semgrep=True):
        """
        Initialize enhanced repository scanner
        
        Args:
            policy_processor: PolicyProcessor instance (optional)
            enable_context_analysis: Enable context-aware false positive filtering
            use_semgrep: Use Semgrep for enhanced code scanning (default: True)
        """
        self.policy_processor = policy_processor
        self.compliance_checkers = get_all_checkers()
        self.scan_results = {}
        self.enable_context_analysis = enable_context_analysis
        self.use_semgrep = use_semgrep and SEMGREP_AVAILABLE
        
        # Initialize Semgrep scanner
        self.semgrep_scanner = None
        if self.use_semgrep:
            try:
                self.semgrep_scanner = SemgrepScanner()
                if self.semgrep_scanner.semgrep_available:
                    logger.info("✓ Semgrep scanner enabled")
                else:
                    self.use_semgrep = False
                    logger.warning("Semgrep not available, falling back to regex checkers")
            except Exception as e:
                logger.warning(f"Failed to initialize Semgrep: {e}")
                self.use_semgrep = False
        
        # Initialize context analyzer and project profiler
        self.context_analyzer = None
        self.project_profiler = None
        self.project_profile = None
        
        if enable_context_analysis:
            try:
                from context_analyzer_v2 import ContextAnalyzer
                from project_profiler import ProjectProfiler
                
                self.project_profiler = ProjectProfiler()
                logger.info("✓ Context-aware analysis enabled (Enhanced Judge v2)")
            except ImportError as e:
                logger.warning(f"Context analyzer v2 not available: {e}")
                self.enable_context_analysis = False
        
        # Library/vendor exclusion patterns
        self.exclude_patterns = [
            'node_modules/',
            'vendor/',
            'dist/',
            'build/',
            'venv/',
            '.venv/',
            '__pycache__/',
            '.git/',
            'coverage/',
            '.next/',
            '.nuxt/',
            'out/',
            'target/',
            'bin/',
            'obj/',
        ]
        
        # File patterns to exclude
        self.exclude_file_patterns = [
            '.min.js',
            '.min.css',
            '.bundle.js',
            '.chunk.js',
            'truffle-contract.js',
            'web3.min.js',
            'web3.js',
            '-lock.json',
            'package-lock.json',
            'yarn.lock',
            'Gemfile.lock',
        ]
        
        logger.info(f"Initialized {len(self.compliance_checkers)} compliance checkers")
    
    def scan_repository(self, repo_path: str, file_extensions: List[str] = None) -> Dict[str, Any]:
        """
        Scan repository for compliance violations with context-aware filtering
        
        Args:
            repo_path: Path to repository root
            file_extensions: File extensions to scan
            
        Returns:
            Comprehensive scan results with violations (false positives filtered)
        """
        scan_start = datetime.now()
        
        if file_extensions is None:
            file_extensions = [
                '.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go',
                '.tf', '.yaml', '.yml', '.json', '.xml'
            ]
        
        results = {
            "repository_path": repo_path,
            "scan_timestamp": scan_start.isoformat(),
            "scan_summary": {},
            "violations": [],
            "compliance_score": 0.0,
            "scanned_files": [],
            "checkers_applied": len(self.compliance_checkers),
            "scan_duration": 0,
            "context_analysis_enabled": self.enable_context_analysis,
            "false_positives_filtered": 0,
            "project_profile": {}
        }
        
        try:
            repo_path = Path(repo_path)
            if not repo_path.exists():
                raise FileNotFoundError(f"Repository path not found: {repo_path}")
            
            # Profile the project first for context-aware analysis
            if self.enable_context_analysis and self.project_profiler:
                logger.info("Profiling repository for context-aware analysis...")
                self.project_profile = self.project_profiler.profile_repository(str(repo_path))
                
                # Initialize context analyzer with project profile
                from context_analyzer_v2 import ContextAnalyzer
                self.context_analyzer = ContextAnalyzer(self.project_profile)
                
                results["project_profile"] = self.project_profiler.get_context_summary()
                logger.info(f"Project type: {self.project_profile.project_type}, Maturity: {self.project_profile.project_maturity}")
            
            # Find all code files (excluding libraries)
            code_files = []
            for ext in file_extensions:
                all_files = repo_path.rglob(f'*{ext}')
                # Filter out excluded paths
                filtered_files = [f for f in all_files if self._should_scan_file(f, repo_path)]
                code_files.extend(filtered_files)
            
            logger.info(f"Scanning {len(code_files)} files in {repo_path} (libraries excluded)")
            
            # OPTION 1: Use Semgrep for faster, more accurate scanning
            if self.use_semgrep and self.semgrep_scanner:
                logger.info("Using Semgrep for code scanning...")
                semgrep_results = self.semgrep_scanner.scan_repository(str(repo_path))
                
                if semgrep_results.get("status") == "success":
                    # Semgrep found violations - add them to results
                    raw_violations = semgrep_results.get("violations", [])
                    raw_violations_count = len(raw_violations)
                    
                    logger.info(f"Semgrep found {raw_violations_count} potential violations")
                    
                    # Apply context-aware filtering to Semgrep results
                    if self.enable_context_analysis and self.context_analyzer:
                        for violation in raw_violations:
                            file_path = repo_path / violation.get("file_path", "")
                            filtered = self._filter_false_positives([violation], file_path, repo_path)
                            results["violations"].extend(filtered)
                    else:
                        results["violations"].extend(raw_violations)
                    
                    # Track files scanned
                    scanned_files_set = set(v.get("file_path") for v in raw_violations)
                    for file_path in scanned_files_set:
                        results["scanned_files"].append({
                            "file_path": file_path,
                            "violations": [v for v in raw_violations if v.get("file_path") == file_path]
                        })
                else:
                    logger.warning(f"Semgrep scan failed: {semgrep_results.get('message')}")
                    # Fall back to regex checkers
                    self.use_semgrep = False
            
            # OPTION 2: Use regex-based compliance checkers (fallback or supplement)
            if not self.use_semgrep:
                logger.info("Using regex-based compliance checkers...")
                raw_violations_count = 0
                for file_path in code_files:
                    try:
                        file_results = self._scan_file(file_path, repo_path)
                        if file_results:
                            results["scanned_files"].append(file_results)
                            
                            # Track raw violations before filtering
                            raw_violations = file_results.get("violations", [])
                            raw_violations_count += len(raw_violations)
                            
                            # Log raw violations for debugging
                            if raw_violations:
                                logger.info(f"Found {len(raw_violations)} raw violations in {file_path.name}")
                            
                            # Apply context-aware filtering
                            if self.enable_context_analysis and self.context_analyzer:
                                filtered_violations = self._filter_false_positives(
                                    raw_violations, 
                                    file_path, 
                                    repo_path
                                )
                                results["violations"].extend(filtered_violations)
                                
                                # Log filtering results
                                filtered_count = len(raw_violations) - len(filtered_violations)
                                if filtered_count > 0:
                                    logger.info(f"  ✓ AI Judge filtered {filtered_count} false positives, kept {len(filtered_violations)} true positives")
                            else:
                                results["violations"].extend(raw_violations)
                            
                    except Exception as e:
                        logger.error(f"Failed to scan file {file_path}: {e}")
            
            # Calculate false positives filtered
            if self.use_semgrep:
                results["false_positives_filtered"] = raw_violations_count - len(results["violations"])
                results["scanner_used"] = "semgrep"
            else:
                results["false_positives_filtered"] = raw_violations_count - len(results["violations"])
                results["scanner_used"] = "regex"
            
            if results["false_positives_filtered"] > 0:
                logger.info(f"✓ Filtered {results['false_positives_filtered']} false positives using context analysis")
            
            # Calculate compliance metrics
            results["scan_summary"] = self._calculate_scan_summary(results)
            results["compliance_score"] = self._calculate_compliance_score(results)
            
            # Calculate scan duration
            scan_end = datetime.now()
            results["scan_duration"] = (scan_end - scan_start).total_seconds()
            
            logger.info(f"Repository scan completed: {len(results['violations'])} violations found")
            return results
            
        except Exception as e:
            logger.error(f"Repository scan failed: {e}")
            return {
                "repository_path": str(repo_path),
                "scan_timestamp": scan_start.isoformat(),
                "error": str(e),
                "scan_duration": (datetime.now() - scan_start).total_seconds()
            }
    
    def _scan_file(self, file_path: Path, repo_root: Path) -> Optional[Dict[str, Any]]:
        """
        Scan individual file with all compliance checkers
        
        Args:
            file_path: Path to file to scan
            repo_root: Repository root path
            
        Returns:
            File scan results
        """
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Determine file type
            file_type = self._get_file_type(file_path)
            
            # Relative path for reporting
            relative_path = str(file_path.relative_to(repo_root))
            
            file_results = {
                "file_path": relative_path,
                "file_type": file_type,
                "file_size": len(content),
                "line_count": len(content.split('\n')),
                "violations": [],
                "compliance_checks": []
            }
            
            # Build context
            context = {
                "repo_root": str(repo_root),
                "file_path": relative_path,
                "file_type": file_type
            }
            
            # Apply each compliance checker
            for checker in self.compliance_checkers:
                try:
                    violations = checker.check(relative_path, content, file_type, context)
                    
                    # Convert violations to dict format and add matched_text for context analysis
                    for violation in violations:
                        violation_dict = violation.to_dict()
                        
                        # Extract matched text from the line for context analysis
                        if "line_number" in violation_dict and violation_dict["line_number"] is not None and violation_dict["line_number"] > 0:
                            try:
                                lines = content.split('\n')
                                line_idx = violation_dict["line_number"] - 1
                                if 0 <= line_idx < len(lines):
                                    # Store the matched text (or the whole line if not available)
                                    violation_dict["matched_text"] = violation_dict.get("matched_text", lines[line_idx].strip())
                            except Exception:
                                pass
                        
                        file_results["violations"].append(violation_dict)
                    
                    # Record compliance check
                    file_results["compliance_checks"].append({
                        "checker": checker.regulation_name,
                        "violations_found": len(violations)
                    })
                    
                except Exception as e:
                    logger.error(f"Checker {checker.regulation_name} failed on {relative_path}: {e}")
            
            return file_results
            
        except Exception as e:
            logger.error(f"File scan failed for {file_path}: {e}")
            return None
    
    def _should_scan_file(self, file_path: Path, repo_root: Path) -> bool:
        """
        Determine if a file should be scanned - LESS AGGRESSIVE FILTERING
        
        Only block truly irrelevant files (binaries, locks, generated artifacts)
        Let The Judge handle false positives from libraries
        
        Args:
            file_path: Path to file
            repo_root: Repository root path
            
        Returns:
            True if file should be scanned, False if it should be excluded
        """
        try:
            relative_path = str(file_path.relative_to(repo_root))
            filename = file_path.name.lower()
            
            # ONLY block these specific cases:
            
            # 1. Lock files (no code)
            if filename.endswith(('.lock', '-lock.json', 'package-lock.json', 'yarn.lock')):
                logger.debug(f"🚫 Bouncer blocked (lock file): {relative_path}")
                return False
            
            # 2. Binary/compiled files
            binary_extensions = {'.pyc', '.pyo', '.so', '.dll', '.dylib', '.class', '.jar', '.exe'}
            if any(filename.endswith(ext) for ext in binary_extensions):
                logger.debug(f"🚫 Bouncer blocked (binary): {relative_path}")
                return False
            
            # 3. Source maps (generated)
            if filename.endswith('.map'):
                logger.debug(f"🚫 Bouncer blocked (source map): {relative_path}")
                return False
            
            # 4. node_modules, venv, .venv, .git (dependencies/system)
            # Check both forward and backward slashes for Windows compatibility
            blocked_dirs = {'node_modules', 'venv', '.venv', '__pycache__', '.git', 'build', 'dist'}
            path_parts = relative_path.replace('\\', '/').lower().split('/')
            
            # Check if ANY part of the path contains a blocked directory
            for part in path_parts:
                if part in blocked_dirs:
                    logger.debug(f"🚫 Bouncer blocked (dependency dir '{part}'): {relative_path}")
                    return False
            
            # Also check the absolute path to catch cases where relative path calculation fails
            abs_path_str = str(file_path).replace('\\', '/').lower()
            for blocked_dir in blocked_dirs:
                if f'/{blocked_dir}/' in abs_path_str or abs_path_str.endswith(f'/{blocked_dir}'):
                    logger.debug(f"🚫 Bouncer blocked (dependency dir '{blocked_dir}'): {file_path}")
                    return False
            
            # ALLOW EVERYTHING ELSE - including minified files, libraries, etc.
            # Let The Judge determine if findings are false positives
            return True
            
        except Exception as e:
            logger.warning(f"Error checking file {file_path}: {e}")
            return True  # Default to scanning if check fails
    
    def _filter_false_positives(
        self, 
        violations: List[Dict[str, Any]], 
        file_path: Path, 
        repo_root: Path
    ) -> List[Dict[str, Any]]:
        """
        STEP 4: Filter false positives using The Agentic Judge
        
        This integrates the AI verification into the scanning pipeline:
        1. For each violation candidate
        2. Call ai_verify_violation() with context
        3. Only keep violations confirmed as true positives
        
        Args:
            violations: List of detected violations
            file_path: Path to file being scanned
            repo_root: Repository root path
            
        Returns:
            Filtered list of violations (false positives removed)
        """
        if not self.context_analyzer:
            return violations
        
        filtered_violations = []
        relative_path = str(file_path.relative_to(repo_root))
        
        # Read file content for context analysis
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                file_lines = f.readlines()
        except Exception as e:
            logger.warning(f"Could not read file for context analysis: {e}")
            return violations
        
        # Import the async verification function
        import asyncio
        from context_analyzer_v2 import ai_verify_violation_v2
        
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        for violation in violations:
            try:
                line_number = violation.get("line_number", 0)
                matched_text = violation.get("matched_text", "")
                rule_id = violation.get("rule_id", "")
                
                # Get the line and surrounding context
                if 0 < line_number <= len(file_lines):
                    line = file_lines[line_number - 1]
                    
                    # Get surrounding lines for context (3 before, 2 after)
                    start_idx = max(0, line_number - 3)
                    end_idx = min(len(file_lines), line_number + 2)
                    surrounding_lines = [file_lines[i].rstrip() for i in range(start_idx, end_idx)]
                    
                    # CALL THE AGENTIC JUDGE V2
                    ai_result = loop.run_until_complete(
                        ai_verify_violation_v2(
                            code_snippet=line,
                            rule_id=rule_id,
                            file_path=relative_path,
                            knowledge_base=self.context_analyzer.knowledge_base,
                            surrounding_lines=surrounding_lines
                        )
                    )
                    
                    # Only keep if AI Judge confirms it's a TRUE POSITIVE
                    if ai_result is not None and ai_result.get("is_true_positive", False):
                        # Enhance violation with AI insights
                        violation["ai_verified"] = True
                        violation["ai_confidence"] = ai_result.get("confidence", 0.85)
                        violation["ai_reasoning"] = ai_result.get("thought_process", "")
                        violation["severity"] = ai_result.get("severity", violation.get("severity", "MEDIUM"))
                        
                        filtered_violations.append(violation)
                        logger.debug(
                            f"✓ AI Judge confirmed TRUE POSITIVE: {relative_path}:{line_number} "
                            f"(confidence: {ai_result.get('confidence', 0.85):.2f})"
                        )
                    else:
                        # AI Judge says it's a FALSE POSITIVE - filter it out
                        logger.debug(
                            f"✗ AI Judge filtered FALSE POSITIVE: {relative_path}:{line_number} "
                            f"(rule: {rule_id})"
                        )
                else:
                    # If we can't get the line, keep the violation to be safe
                    filtered_violations.append(violation)
                    
            except Exception as e:
                logger.warning(f"AI verification failed for violation: {e}")
                # Keep violation if AI verification fails (fail-safe)
                filtered_violations.append(violation)
        
        return filtered_violations
    
    def _get_file_type(self, file_path: Path) -> str:
        """Determine file type from extension"""
        ext = file_path.suffix.lower()
        
        type_mapping = {
            '.py': 'py',
            '.js': 'js',
            '.ts': 'ts',
            '.jsx': 'js',
            '.tsx': 'ts',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'cs',
            '.php': 'php',
            '.rb': 'rb',
            '.go': 'go',
            '.tf': 'tf',
            '.terraform': 'terraform',
            '.yaml': 'yaml',
            '.yml': 'yml',
            '.json': 'json',
            '.xml': 'xml',
        }
        
        return type_mapping.get(ext, 'unknown')
    
    def _calculate_scan_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics for scan results"""
        violations = results.get("violations", [])
        
        # Count by severity
        severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for violation in violations:
            severity = violation.get("severity", "LOW")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Count by regulation
        regulation_counts = {}
        for violation in violations:
            regulation = violation.get("regulation", "unknown")
            regulation_counts[regulation] = regulation_counts.get(regulation, 0) + 1
        
        # Count by category
        category_counts = {}
        for violation in violations:
            category = violation.get("category", "unknown")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Files with violations
        files_with_violations = len(set(v.get("file_path") for v in violations))
        total_files_scanned = len(results.get("scanned_files", []))
        
        return {
            "total_violations": len(violations),
            "severity_breakdown": severity_counts,
            "regulation_breakdown": regulation_counts,
            "category_breakdown": category_counts,
            "files_with_violations": files_with_violations,
            "total_files_scanned": total_files_scanned,
            "violation_rate": files_with_violations / max(total_files_scanned, 1)
        }
    
    def _calculate_compliance_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall compliance score (0-1)"""
        violations = results.get("violations", [])
        total_files = len(results.get("scanned_files", []))
        
        if total_files == 0:
            return 1.0
        
        # Weight violations by severity
        severity_weights = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        weighted_violations = sum(
            severity_weights.get(v.get("severity", "LOW"), 1) 
            for v in violations
        )
        
        # Calculate score (higher violations = lower score)
        max_possible_violations = total_files * 5  # Assume max 5 violations per file
        compliance_score = max(0.0, 1.0 - (weighted_violations / max_possible_violations))
        
        return round(compliance_score, 3)
    
    def get_scan_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable scan report"""
        report = []
        
        report.append("=" * 80)
        report.append("INDIAN COMPLIANCE SCAN REPORT")
        report.append("=" * 80)
        
        # Summary
        summary = results.get("scan_summary", {})
        report.append(f"Repository: {results.get('repository_path', 'Unknown')}")
        report.append(f"Scan Date: {results.get('scan_timestamp', 'Unknown')}")
        report.append(f"Compliance Score: {results.get('compliance_score', 0.0):.1%}")
        report.append(f"Total Violations: {summary.get('total_violations', 0)}")
        report.append(f"Files Scanned: {summary.get('total_files_scanned', 0)}")
        report.append(f"Checkers Applied: {results.get('checkers_applied', 0)}")
        report.append("")
        
        # Severity breakdown
        severity_breakdown = summary.get("severity_breakdown", {})
        report.append("VIOLATIONS BY SEVERITY:")
        for severity in ["HIGH", "MEDIUM", "LOW"]:
            count = severity_breakdown.get(severity, 0)
            report.append(f"  {severity}: {count}")
        report.append("")
        
        # Regulation breakdown
        regulation_breakdown = summary.get("regulation_breakdown", {})
        if regulation_breakdown:
            report.append("VIOLATIONS BY REGULATION:")
            for regulation, count in regulation_breakdown.items():
                report.append(f"  {regulation}: {count}")
            report.append("")
        
        # Category breakdown
        category_breakdown = summary.get("category_breakdown", {})
        if category_breakdown:
            report.append("VIOLATIONS BY CATEGORY:")
            for category, count in category_breakdown.items():
                report.append(f"  {category}: {count}")
            report.append("")
        
        # Top violations
        violations = results.get("violations", [])
        high_violations = [v for v in violations if v.get("severity") == "HIGH"]
        
        if high_violations:
            report.append("HIGH SEVERITY VIOLATIONS:")
            for i, violation in enumerate(high_violations[:10], 1):
                report.append(f"\n{i}. {violation.get('description', 'Unknown')}")
                report.append(f"   File: {violation.get('file_path', 'Unknown')}")
                report.append(f"   Rule: {violation.get('rule_id', 'Unknown')}")
                report.append(f"   Regulation: {violation.get('regulation', 'Unknown')}")
                report.append(f"   Fix: {violation.get('fix_suggestion', 'Review required')}")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
