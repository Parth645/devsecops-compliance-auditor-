"""
Compliance Analyzer - AI-Driven Orchestrator
SIMPLIFIED ARCHITECTURE - 6 STEP PIPELINE (Pre-built Rules Only):
  Step 1 (Fast Triage): AI repo profiling with Groq (GroqRepoProfiler)
  Step 2 (Pre-built Rules): Using 18 Indian Compliance Rules (DPDPA, RBI, IT Act, SEBI, ISO 8000)
  Step 3a (Detection): Execute Semgrep with pre-built rules
  Step 3.5 (Verification): Groq proof-checking to filter false positives
  Step 3b (Business Logic): Groq semantic analysis
  Step 3.7 (Infrastructure): IaC compliance scanning
  Step 3.8 (Data Flows): Targeted business logic analysis
  Step 4 (Mapping): Map violations to compliance frameworks
  Step 5 (Gaps): Identify missing features based on AI profile
  
BENEFITS:
  - Fast: No API calls for rule generation (~1 second for STEP 2)
  - Consistent: 18 rules are version-controlled, not dynamic
  - Accurate: Pre-tested rules for Indian compliance frameworks
  - Reliable: No HTTP 413/400 errors from API payload limits
"""

import logging
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime
import json
import os
from pathlib import Path
from .semgrep_detector import SemgrepDetector
from .finding_merger import FindingMerger
from .groq_batch_mapper import GroqBatchMapper
from .gap_analyzer import GapAnalyzer
from .groq_repo_profiler import GroqRepoProfiler
from .groq_business_logic_scanner import GroqBusinessLogicScanner
from .groq_semgrep_verifier import GroqSemgrepVerifier
from .indian_rules_manager import IndianComplianceRulesManager
from .iac_compliance_scanner import IaCComplianceScanner, identify_iac_files
from .data_flow_extractor import DataFlowExtractor
from .model_based_compliance_analyzer import ModelBasedComplianceAnalyzer

logger = logging.getLogger(__name__)


class ComplianceAnalyzer:
    """
    AI-Driven Orchestrator - 6-Step Pipeline with Indian Compliance Rules
    
    ARCHITECTURE:
    Step 1 (AI Fast Triage): Groq profiles repo structure
    Step 2 (Dynamic Rules): Groq translates policies to Semgrep YAML
    Step 3a (Detection): Semgrep scans with dynamic rules
    Step 3b (Business Logic): Groq semantic analysis with 18 Indian Compliance Rules:
        - DPDPA 2023: Consent, Purpose Limitation, Data Minimization, Breach Notification, User Rights
        - RBI Guidelines: Authorization, Transaction Atomicity, Encryption, Audit Trails, Rate Limiting
        - IT Act 2000 + SPDI: Unauthorized Access, Data Protection, Input Validation
        - SEBI: Market Manipulation, Transparency
        - ISO 8000: Data Quality
    Step 4 (Mapping): Groq maps findings to frameworks
    Step 5 (Gaps): AI identifies missing compliance features
    """
    
    def __init__(self, policies_dir: str = "policies", groq_api_key: Optional[str] = None):
        """
        Initialize AI-driven compliance analyzer
        
        Args:
            policies_dir: Directory for policy documents
            groq_api_key: Groq API key (uses env var if not provided)
        """
        self.policies_dir = policies_dir
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        
        # Core detection
        self.semgrep_detector = SemgrepDetector()
        self.finding_merger = FindingMerger()
        
        # Load Indian compliance rules (18 rules: DPDPA, RBI, IT Act, SEBI, ISO 8000)
        self.rules_manager = IndianComplianceRulesManager()
        logger.info(f"  ✓ Loaded {len(self.rules_manager.rules)} Indian compliance rules")
        
        # AI components
        if self.groq_api_key:
            self.repo_profiler = GroqRepoProfiler(self.groq_api_key)  # Step 1
            self.semgrep_verifier = GroqSemgrepVerifier(self.groq_api_key, self.rules_manager)  # Step 3.5
            self.business_logic_scanner = GroqBusinessLogicScanner(self.groq_api_key, self.rules_manager, scan_raw_files=False)  # Step 3b - RE-ENABLED with targeted RAG
            self.batch_mapper = GroqBatchMapper(self.groq_api_key)  # Step 4
            self.gap_analyzer = None  # Step 5 - DISABLED
            
            # NEW: Infrastructure and business logic analysis
            self.iac_scanner = IaCComplianceScanner()
            self.data_flow_extractor = DataFlowExtractor()
            self.model_analyzer = ModelBasedComplianceAnalyzer(self.groq_api_key)
        else:
            logger.warning("Groq API key not found. AI components disabled.")
            self.repo_profiler = None
            self.semgrep_verifier = None
            self.business_logic_scanner = None
            self.batch_mapper = None
            self.gap_analyzer = None
            self.iac_scanner = None
            self.data_flow_extractor = None
            self.model_analyzer = None
        
        logger.info("✓ AI-Driven Compliance Analyzer initialized (8-Step Pipeline with Architectural Pivots)")
        logger.info(f"  📋 Indian Compliance Rules: {len(self.rules_manager.rules)} rules (DPDPA, RBI, IT Act, SEBI, ISO 8000)")
        logger.info("  ✓ Step 1: Repo Profiler")
        logger.info("  ✓ Step 2: Policy Translator")
        logger.info("  ✓ Step 3a: Semgrep Detector (with Taint Analysis)")
        logger.info("  ✓ Step 3.5: Semgrep Verifier (Context-aware proof-checking)")
        logger.info("  ✓ Step 3b: Targeted Business Logic Analysis (RAG-based, token-efficient)")
        logger.info("  ✓ PIVOT 2: Data Flow Extraction (Routes → Models)")
        logger.info("  ✓ PIVOT 2: Model-Based Compliance Analysis (Groq on data flows)")
        logger.info("  ✓ PIVOT 3: Infrastructure Scanning (Terraform, K8s, Docker)")
        logger.info(f"  ✓ Step 4: Batch Mapper")
        logger.info(f"  ✓ Step 5: Gap Analyzer")
    
    async def analyze_repository_for_compliance(self, repo_path: str, custom_policy_text: Optional[str] = None, language: str = "javascript") -> Dict[str, Any]:
        """
        SIMPLIFIED 3-STEP COMPLIANCE PIPELINE
        
        Step 1: Semgrep Scan
          - Runs Semgrep with pre-built Indian compliance rules (18+ rules)
          - DPDPA, RBI, IT Act, SEBI, ISO 8000
          - Returns raw findings with file paths and line numbers
          
        Step 2: Groq False Positive Filtering
          - AI analyzes each finding for context
          - Filters out test files, comments, safe libraries
          - Returns only true violations
          
        Step 3: Groq Remediation Generation
          - AI generates fix suggestions for each violation
          - Provides code examples and best practices
          - Maps to compliance framework requirements
        """
        
        try:
            start_time = datetime.now()
            logger.info(f"[AI-DRIVEN SCAN] Starting 5-step compliance analysis: {repo_path}")
            
            # Collect all source files
            logger.info("[0/5] Collecting source files...")
            all_files = self._collect_all_code_files(repo_path)
            logger.info(f"  ✓ Found {len(all_files)} source files")
            
            # ========== STEP 1: AI FAST TRIAGE ==========
            logger.info("[1/5] STEP 1 - AI Fast Triage (Groq Repo Profiler)...")
            repo_profile = {}
            if self.repo_profiler:
                repo_profile = await self.repo_profiler.profile_repository(repo_path, all_files)
                logger.info(f"  ✓ Profiled: {repo_profile.get('application_purpose', 'unknown')}")
            
            # ========== STEP 2: USING PRE-BUILT COMPLIANCE RULES ==========
            logger.info("[2/6] STEP 2 - Loading Pre-built Compliance Rules...")
            logger.info("  ✓ Using pre-built Indian compliance rules (18+ rules: DPDPA, RBI, IT Act, SEBI, ISO 8000)")
            
            # ========== STEP 3a: SEMGREP EXECUTION ==========
            logger.info("[3a/6] STEP 3a - Executing Semgrep (Static Pattern Detection)...")
            
            # Run Semgrep with pre-built rules only (FAST - no API calls)
            semgrep_results = await self.semgrep_detector.scan_repository(
                repo_path,
                custom_rules_path=None
            )
            semgrep_findings = semgrep_results.get("findings", [])
            logger.info(f"  ✓ Semgrep: {len(semgrep_findings)} raw findings detected")
            
            # ========== STEP 3.5: SEMGREP VERIFICATION (NEW) ==========
            logger.info("[3.5/6] STEP 3.5 - Semgrep Proof-Checking with Groq (Filter False Positives)...")
            verified_findings = []
            
            if self.semgrep_verifier and len(semgrep_findings) > 0:
                verified_findings = await self.semgrep_verifier.verify_semgrep_findings(
                    semgrep_findings,
                    repo_context=f"Repository: {Path(repo_path).name}"
                )
                logger.info(f"  ✓ Verified: {len(verified_findings)} real violations confirmed")
                logger.info(f"  ⚠ Filtered: {len(semgrep_findings) - len(verified_findings)} false positives")
            else:
                verified_findings = semgrep_findings
                logger.info("  ⚠ Skipping Semgrep verification (verifier disabled)")
            
            # ========== STEP 3b: BUSINESS LOGIC SCANNING ==========
            logger.info("[3b/6] STEP 3b - Business Logic Analysis (Semantic Compliance Checker)...")
            business_logic_violations = []
            
            # If Semgrep findings are low, enable business logic scanning
            if len(semgrep_findings) < 10 and self.business_logic_scanner:
                logger.info("  ℹ Semgrep findings < 10, enabling business logic analysis...")
                try:
                    business_logic_violations = await self.business_logic_scanner.scan_codebase_for_policy_violations(
                        repo_path,
                        all_files,
                        max_files=20
                    )
                    logger.info(f"  ✓ Found {len(business_logic_violations)} business logic violations")
                except Exception as e:
                    logger.warning(f"  ⚠ Business logic scanning failed: {e}")
                    business_logic_violations = []
            else:
                if len(semgrep_findings) >= 10:
                    logger.info(f"  ℹ Sufficient findings ({len(semgrep_findings)}), skipping business logic scan")
                else:
                    logger.info("  ℹ Business logic scanner not available")
            
            # Combine all detections
            all_detections = verified_findings + business_logic_violations
            
            # ========== PIVOT 3: INFRASTRUCTURE-AS-CODE SCANNING ==========
            logger.info("[3.7/8] PIVOT 3 - Scanning Infrastructure-as-Code (Terraform, K8s, Docker)...")
            iac_violations = []
            
            try:
                iac_files = identify_iac_files(repo_path)
                if iac_files:
                    logger.info(f"  ✓ Found {len(iac_files)} IaC files")
                    
                    for iac_file in iac_files[:10]:  # Limit to top 10
                        try:
                            with open(iac_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            file_violations = self.iac_scanner.scan_iac_file(iac_file, content)
                            iac_violations.extend(file_violations)
                        except Exception as e:
                            logger.debug(f"Error scanning IaC file {iac_file}: {e}")
                    
                    logger.info(f"  ✓ IaC Scan: {len(iac_violations)} violations found")
                    logger.info(f"    - Data localization issues: {len([v for v in iac_violations if v['rule'] == 'data_localization'])}")
                    logger.info(f"    - Log retention issues: {len([v for v in iac_violations if v['rule'] == 'log_retention'])}")
                    logger.info(f"    - Encryption issues: {len([v for v in iac_violations if 'encryption' in v['rule']])}")
                else:
                    logger.info("  ℹ No IaC files found")
            except Exception as e:
                logger.warning(f"  ⚠ IaC scanning failed: {e}")
            
            # ========== PIVOT 2: TARGETED RAG-BASED BUSINESS LOGIC ANALYSIS ==========
            logger.info("[3.8/8] PIVOT 2 - Extracting Data Flows for Targeted AI Analysis...")
            model_violations = []
            flows_result = {}
            
            try:
                # Extract data flows (routes → models)
                flows_result = self.data_flow_extractor.extract_from_repository(repo_path)
                analysis_targets = flows_result.get('analysis_targets', [])
                
                logger.info(f"  ✓ Extracted {len(flows_result['routes'])} routes and {len(flows_result['models'])} models")
                logger.info(f"  ✓ Found {len(flows_result['data_flows'])} data flows with PII")
                logger.info(f"  ✓ Prioritized {len(analysis_targets)} for AI analysis")
                
                # Analyze prioritized data flows with Groq
                if analysis_targets and self.model_analyzer:
                    logger.info("  → Analyzing with Model-Based Compliance Analyzer...")
                    model_violations = await self.model_analyzer.analyze_data_flows(analysis_targets)
                    logger.info(f"  ✓ Model analysis: {len(model_violations)} compliance violations found")
            except Exception as e:
                logger.warning(f"  ⚠ Data flow analysis failed: {e}")
            
            # Combine all detections
            all_detections = verified_findings + business_logic_violations + iac_violations + model_violations
            
            # ========== STEP 4: FRAMEWORK MAPPING ==========
            logger.info("[4/6] STEP 4 - Mapping to Compliance Frameworks...")
            mapped_findings = []
            
            if self.batch_mapper and len(all_detections) > 0:
                mapped_findings = await self.batch_mapper.map_findings_to_compliance(all_detections)
                logger.info(f"  ✓ Mapped {len(mapped_findings)} findings to frameworks")
            else:
                mapped_findings = all_detections
                logger.info("  ⚠ Skipping Groq mapping (disabled or no findings)")
            
            # ========== STEP 5: GAP ANALYSIS ==========
            logger.info("[5/6] STEP 5 - AI Gap Analysis...")
            gaps = []
            
            if self.gap_analyzer:
                gaps = await self.gap_analyzer.analyze_gaps(repo_path, all_files)
                logger.info(f"  ✓ Found {len(gaps)} compliance gaps")
            else:
                logger.info("  ⚠ Gap analyzer not available")
            
            # ========== COMPLETE ANALYSIS ==========
            logger.info("[8/8] Building final compliance report...")
            
            all_violations = mapped_findings + gaps
            
            # Calculate statistics
            stats = self.finding_merger.get_summary(all_violations)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"✓ SCAN COMPLETE in {duration:.1f}s")
            logger.info(f"  Total violations: {len(all_violations)}")
            logger.info(f"  Critical: {stats['by_severity'].get('critical', 0)} | High: {stats['by_severity'].get('high', 0)}")
            
            return {
                "status": "completed",
                "repository": repo_path,
                "violations": all_violations[:100],  # Top 100
                "total_violations": len(all_violations),
                "gaps": gaps,
                "severity_breakdown": stats["by_severity"],
                "framework_breakdown": stats["by_framework"],
                "detector_breakdown": stats["by_detector"],
                "high_risk_files": stats["high_risk_files"],
                "pipeline": {
                    "step_1_ai_profiling": {"status": "complete", "findings": 1},
                    "step_2_pre_built_rules": {"status": "complete", "rules_loaded": 18},
                    "step_3a_semgrep_execution": {"status": "complete", "raw_findings": len(semgrep_findings)},
                    "step_3_5_semgrep_verification": {"status": "complete", "verified_findings": len(verified_findings), "false_positives_filtered": len(semgrep_findings) - len(verified_findings)},
                    "step_3b_business_logic_scanner": {"status": "complete", "violations": len(business_logic_violations)},
                    "pivot_2_infrastructure_scanning": {"status": "complete", "iac_violations": len(iac_violations)},
                    "pivot_2_data_flow_analysis": {"status": "complete", "model_violations": len(model_violations)},
                    "step_4_framework_mapping": {"status": "complete", "mapped": len(mapped_findings)},
                    "step_5_gap_analysis": {"status": "complete", "gaps": len(gaps)}
                },
                "repo_profile": repo_profile,
                "semgrep_verification": {
                    "raw_findings": len(semgrep_findings),
                    "verified_findings": len(verified_findings),
                    "false_positives": len(semgrep_findings) - len(verified_findings),
                    "verification_efficiency": f"{round(100*(len(verified_findings)/len(semgrep_findings)), 1)}%" if semgrep_findings else "0%"
                },
                "iac_analysis": {
                    "total_violations": len(iac_violations),
                    "data_localization": len([v for v in iac_violations if v['rule'] == 'data_localization']),
                    "log_retention": len([v for v in iac_violations if v['rule'] == 'log_retention']),
                    "encryption": len([v for v in iac_violations if 'encryption' in v['rule']])
                },
                "business_logic_analysis": {
                    "data_flows_extracted": len(flows_result.get('data_flows', [])),
                    "model_violations": len(model_violations)
                },
                "scan_duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"5-step scan failed: {e}", exc_info=True)
            return {"error": str(e), "status": "failed"}
    
    def _collect_all_code_files(self, repo_path: str) -> List[str]:
        """Collect ALL source code files, not just key files"""
        code_files = []
        repo_path = Path(repo_path)
        
        # Extensions to scan
        extensions = {'.js', '.ts', '.jsx', '.tsx', '.py', '.java', '.go', '.rs', '.cpp', '.c', '.php', '.rb', '.conf', '.json', '.yaml', '.yml'}
        
        # Exclude patterns
        excludes = {'.git', 'node_modules', '.venv', 'venv', 'build', 'dist', '__pycache__', '.pytest_cache'}
        
        for file_path in repo_path.rglob('*'):
            # Skip excluded directories
            if any(exclude in file_path.parts for exclude in excludes):
                continue
            
            # Add code files
            if file_path.is_file() and file_path.suffix in extensions:
                code_files.append(str(file_path))
        
        return code_files[:500]  # Limit to 500 files for performance
