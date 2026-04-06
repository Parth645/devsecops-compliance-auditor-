"""
Groq Pipeline Orchestrator - 4-Stage AI Architecture
Implements intelligent model routing for cost-efficient compliance scanning

Stage 1: Project Profiling (llama-3.1-8b-instant)
Stage 2: Custom Policy Translation (llama-3.3-70b-versatile) 
Stage 3: Context Analysis & False-Positive Filtering (qwen/qwen3-32b)
Stage 4: Auto-Remediation & Reporting (llama-3.3-70b-versatile)
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import os
from groq import Groq

logger = logging.getLogger(__name__)

class GroqPipelineOrchestrator:
    """
    Routes tasks to specialized Groq models for optimal cost/performance/accuracy balance
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the pipeline with Groq API"""
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        
        self.client = Groq(api_key=self.api_key)
        
        # Model routing configuration
        self.models = {
            "stage_1_profiling": "llama-3.1-8b-instant",           # Fast, lightweight
            "stage_2_translator": "llama-3.3-70b-versatile",       # Powerful NLP
            "stage_3_validator": "qwen/qwen3-32b",                 # Reasoning
            "stage_4_remediation": "llama-3.3-70b-versatile"       # Code generation
        }
        
        # Temperature settings per stage
        self.temperatures = {
            "stage_1": 0.3,    # Low for deterministic profiling
            "stage_2": 0.2,    # Low for exact rule generation
            "stage_3": 0.1,    # Very low for precise validation
            "stage_4": 0.4     # Slightly higher for flexible fix generation
        }
        
        logger.info("✓ Groq Pipeline Orchestrator initialized")
        logger.info(f"  Stage 1: {self.models['stage_1_profiling']}")
        logger.info(f"  Stage 2: {self.models['stage_2_translator']}")
        logger.info(f"  Stage 3: {self.models['stage_3_validator']}")
        logger.info(f"  Stage 4: {self.models['stage_4_remediation']}")
    
    # ========================================================================
    # STAGE 1: PROJECT PROFILING (llama-3.1-8b-instant)
    # ========================================================================
    
    async def stage_1_project_profiling(
        self, 
        repo_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        HIGH-SPEED PROJECT TRIAGE ENGINE
        
        Analyzes repository structure to:
        - Identify tech stack and frameworks
        - Classify project type (web/backend/library/contract)
        - Determine data sensitivity level
        - Identify test vs production code
        
        Args:
            repo_path: Path to repository
            metadata: Additional repository metadata
            
        Returns:
            Project profile with classification and risk assessment
        """
        logger.info(f"[Stage 1] Profiling repository: {repo_path}")
        
        # Collect metadata
        profile_data = self._extract_project_metadata(repo_path, metadata)
        
        prompt = f"""Analyze this repository profile and provide a JSON classification:

Repository Path: {repo_path}
Files Found: {len(profile_data.get('files', []))}
Key Files: {json.dumps(profile_data.get('key_files', []))}
File Extensions: {json.dumps(profile_data.get('extensions', {}))}
Dependencies: {json.dumps(profile_data.get('dependencies', [])[:10])}  # Top 10

Provide JSON response:
{{
    "tech_stack": ["framework1", "framework2"],
    "project_type": "web|backend|library|blockchain|hybrid",
    "maturity_level": "early|stable|legacy",
    "data_sensitivity": "high|medium|low",
    "has_tests": boolean,
    "test_framework": "jest|pytest|mocha|etc",
    "identified_risks": ["risk1", "risk2"],
    "confidence_score": 0.0-1.0
}}"""

        try:
            response = await self._call_groq(
                prompt,
                model=self.models["stage_1_profiling"],
                temp=self.temperatures["stage_1"],
                max_tokens=1000
            )
            
            profile = self._parse_json_response(response)
            profile["repo_path"] = repo_path
            profile["profiled_at"] = datetime.now().isoformat()
            
            logger.info(f"[Stage 1] ✓ Profiled as {profile.get('project_type')} ({profile.get('tech_stack')})")
            return profile
            
        except Exception as e:
            logger.error(f"[Stage 1] ✗ Profiling failed: {e}")
            return {"error": str(e), "repo_path": repo_path}
    
    def _extract_project_metadata(self, repo_path: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Extract repository metadata for profiling"""
        if metadata:
            return metadata
        
        try:
            files = list(Path(repo_path).rglob("*"))[:100]  # Limit to first 100 files
            extensions = {}
            key_files = []
            
            for f in files:
                if f.is_file():
                    ext = f.suffix
                    extensions[ext] = extensions.get(ext, 0) + 1
                    
                    # Track key configuration files
                    if f.name in ["package.json", "requirements.txt", "pom.xml", "Cargo.toml", "go.mod"]:
                        key_files.append(f.name)
            
            return {
                "files": [str(f) for f in files[:20]],
                "key_files": key_files,
                "extensions": extensions,
                "dependencies": []  # Would be populated from key files
            }
        except Exception as e:
            logger.warning(f"Could not extract metadata: {e}")
            return {"files": [], "key_files": [], "extensions": {}, "dependencies": []}
    
    # ========================================================================
    # STAGE 2: CUSTOM POLICY TRANSLATION (llama-3.3-70b-versatile)
    # ========================================================================
    
    async def stage_2_policy_translation(
        self,
        policy_document: str,
        policy_id: str,
        project_type: str = "web"
    ) -> Dict[str, Any]:
        """
        CUSTOM POLICY TO SEMGREP RULES TRANSLATOR
        
        Converts human-readable company policy documents into executable Semgrep YAML rules.
        
        Examples:
        - Policy: "All database queries must use parameterized statements"
        - Output: Semgrep rule to flag direct string concatenation in SQL queries
        
        Args:
            policy_document: The company policy text (PDF extracted or plain text)
            policy_id: Unique identifier for the policy
            project_type: Type of project (web, backend, library, etc.)
            
        Returns:
            Structured policy rules ready for Semgrep execution
        """
        logger.info(f"[Stage 2] Translating policy: {policy_id}")
        
        prompt = f"""Convert this company policy into Semgrep YAML rules:

COMPANY POLICY:
{policy_document[:2000]}  # Limit to first 2000 chars

PROJECT TYPE: {project_type}

Generate JSON containing Semgrep rules:
{{
    "policy_id": "{policy_id}",
    "rules": [
        {{
            "id": "rule_id",
            "pattern": "pattern_string",
            "message": "Why this is a violation",
            "languages": ["python", "javascript"],
            "severity": "ERROR|WARNING"
        }}
    ],
    "policy_summary": "Brief summary of this policy",
    "coverage": "What code patterns this monitors"
}}"""

        try:
            response = await self._call_groq(
                prompt,
                model=self.models["stage_2_translator"],
                temp=self.temperatures["stage_2"],
                max_tokens=4000
            )
            
            rules = self._parse_json_response(response)
            rules["policy_id"] = policy_id
            rules["created_at"] = datetime.now().isoformat()
            
            logger.info(f"[Stage 2] ✓ Generated {len(rules.get('rules', []))} rules from policy")
            return rules
            
        except Exception as e:
            logger.error(f"[Stage 2] ✗ Translation failed: {e}")
            return {"error": str(e), "policy_id": policy_id}
    
    # ========================================================================
    # STAGE 3: CONTEXT ANALYSIS & FALSE-POSITIVE FILTERING (qwen/qwen3-32b)
    # ========================================================================
    
    async def stage_3_context_analysis(
        self,
        violation: Dict[str, Any],
        code_snippet: str,
        surrounding_context: str,
        project_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        AI FALSE-POSITIVE FILTER WITH STEP-BY-STEP REASONING
        
        Validates Semgrep findings using deep contextual reasoning:
        - Is this in test code? (Check file path and function names)
        - Is this a mock/dummy value? (Check naming patterns and test frameworks)
        - What's the data flow? (Trace if data is encrypted downstream)
        - Is this a real threat? (Assign confidence score)
        
        Args:
            violation: The flagged violation from Semgrep
            code_snippet: The exact code line that triggered the violation
            surrounding_context: Broader code context (surrounding 10-20 lines)
            project_profile: Optional project profile from Stage 1
            
        Returns:
            Validated violation with confidence score and reasoning
        """
        logger.info(f"[Stage 3] Validating violation: {violation.get('rule_id')}")
        
        prompt = f"""Analyze this code violation using step-by-step reasoning:

FLAGGED VIOLATION:
Rule: {violation.get('rule_id')}
Message: {violation.get('message')}
File: {violation.get('file_path')}

CODE SNIPPET:
```
{code_snippet}
```

SURROUNDING CONTEXT:
```
{surrounding_context}
```

PROJECT PROFILE: {json.dumps(project_profile) if project_profile else "Unknown"}

Use reasoning to determine:
1. Is this in test/mock code? (Check filenames like *test.js, *_test.py, __mocks__)
2. Is the value a placeholder? (dummy, mock, example, TODO)
3. What's the data sensitivity? (PII, secrets, financial, or internal?)
4. Is there downstream protection? (encryption, hashing, sanitization)
5. Is this a FALSE POSITIVE or TRUE POSITIVE?

Return JSON:
{{
    "is_false_positive": boolean,
    "confidence_score": 0.0-1.0,
    "reasoning": "Step-by-step analysis",
    "risk_assessment": "LOW|MEDIUM|HIGH|CRITICAL",
    "context_clues": ["clue1", "clue2"],
    "data_sensitivity": "HIGH|MEDIUM|LOW",
    "location_type": "test|production|generated"
}}"""

        try:
            response = await self._call_groq(
                prompt,
                model=self.models["stage_3_validator"],
                temp=self.temperatures["stage_3"],
                max_tokens=2000
            )
            
            analysis = self._parse_json_response(response)
            analysis["rule_id"] = violation.get("rule_id")
            analysis["analyzed_at"] = datetime.now().isoformat()
            
            status = "FILTERED (False Positive)" if analysis.get("is_false_positive") else "CONFIRMED"
            logger.info(f"[Stage 3] ✓ {status} - Confidence: {analysis.get('confidence_score', 0):.2%}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"[Stage 3] ✗ Analysis failed: {e}")
            return {
                "error": str(e),
                "is_false_positive": False,
                "confidence_score": 0.5,
                "rule_id": violation.get("rule_id")
            }
    
    # ========================================================================
    # STAGE 4: AUTO-REMEDIATION & REPORTING (llama-3.3-70b-versatile)
    # ========================================================================
    
    async def stage_4_auto_remediation(
        self,
        violation: Dict[str, Any],
        code_snippet: str,
        policy_context: str,
        language: str = "python"
    ) -> Dict[str, Any]:
        """
        AUTO-REMEDIATION ENGINE WITH SECURE CODE GENERATION
        
        Generates:
        - Secure, drop-in code replacements
        - Explanation of the fix
        - Links to policy compliance
        - Implementation difficulty estimate
        
        Args:
            violation: The confirmed violation
            code_snippet: The problematic code
            policy_context: Relevant policy text explaining the requirement
            language: Programming language of the code
            
        Returns:
            Remediation plan with secure code fix
        """
        logger.info(f"[Stage 4] Generating fix for: {violation.get('rule_id')}")
        
        prompt = f"""Generate a secure code fix for this compliance violation:

VIOLATION DETAILS:
Rule: {violation.get('rule_id')}
Message: {violation.get('message')}
File: {violation.get('file_path')}
Language: {language}

PROBLEMATIC CODE:
```{language}
{code_snippet}
```

POLICY REQUIREMENT:
{policy_context}

RISK LEVEL: {violation.get('risk_assessment', 'MEDIUM')}

Generate a JSON response with the secure fix:
{{
    "rule_id": "{violation.get('rule_id')}",
    "fixed_code": "Secure replacement code",
    "fix_explanation": "Why this fix resolves the violation",
    "policy_link": "Which policy requirement this addresses",
    "implementation_steps": ["step1", "step2"],
    "difficulty": "EASY|MEDIUM|HARD",
    "estimated_effort_hours": 0.5-8.0,
    "testing_recommendations": ["test1", "test2"],
    "common_mistakes": "What NOT to do"
}}"""

        try:
            response = await self._call_groq(
                prompt,
                model=self.models["stage_4_remediation"],
                temp=self.temperatures["stage_4"],
                max_tokens=2000
            )
            
            remediation = self._parse_json_response(response)
            remediation["rule_id"] = violation.get("rule_id")
            remediation["generated_at"] = datetime.now().isoformat()
            
            logger.info(f"[Stage 4] ✓ Fix generated - Difficulty: {remediation.get('difficulty')}")
            return remediation
            
        except Exception as e:
            logger.error(f"[Stage 4] ✗ Remediation generation failed: {e}")
            return {
                "error": str(e),
                "rule_id": violation.get("rule_id"),
                "fixed_code": "# Unable to auto-generate fix. Please review manually."
            }
    
    # ========================================================================
    # FULL PIPELINE ORCHESTRATION
    # ========================================================================
    
    async def run_full_pipeline(
        self,
        repo_path: str,
        policy_document: str,
        semgrep_findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute the complete 4-stage AI pipeline:
        
        1. Profile the project
        2. Translate custom policy to rules
        3. Filter false positives using context
        4. Generate auto-remediation for confirmed violations
        
        Args:
            repo_path: Path to code repository
            policy_document: Company policy text
            semgrep_findings: List of violations from Semgrep
            
        Returns:
            Complete analysis with confirmed violations and fixes
        """
        logger.info("=" * 70)
        logger.info("STARTING 4-STAGE AI PIPELINE")
        logger.info("=" * 70)
        
        start_time = datetime.now()
        results = {
            "pipeline_version": "4-stage",
            "started_at": start_time.isoformat(),
            "stages": {}
        }
        
        try:
            # Stage 1: Project Profiling
            logger.info("\n[STAGE 1] Project Profiling...")
            profile = await self.stage_1_project_profiling(repo_path)
            results["stages"]["stage_1"] = profile
            
            # Stage 2: Policy Translation
            logger.info("\n[STAGE 2] Policy Translation...")
            policy_rules = await self.stage_2_policy_translation(
                policy_document,
                policy_id="custom_policy_001",
                project_type=profile.get("project_type", "web")
            )
            results["stages"]["stage_2"] = policy_rules
            
            # Semgrep would run here (deterministic, not AI)
            logger.info("\n[SEMGREP] Running static analysis...")
            logger.info(f"  Found {len(semgrep_findings)} potential violations")
            
            # Stage 3: Context Analysis (filter false positives)
            logger.info("\n[STAGE 3] Context Analysis & Validation...")
            confirmed_violations = []
            
            for finding in semgrep_findings:
                analysis = await self.stage_3_context_analysis(
                    violation=finding,
                    code_snippet=finding.get("code_snippet", ""),
                    surrounding_context=finding.get("context", ""),
                    project_profile=profile
                )
                
                if not analysis.get("is_false_positive"):
                    confirmed_violations.append({
                        "finding": finding,
                        "analysis": analysis
                    })
            
            logger.info(f"  ✓ Validated: {len(confirmed_violations)} confirmed violations")
            logger.info(f"  ✗ Filtered: {len(semgrep_findings) - len(confirmed_violations)} false positives")
            results["stages"]["stage_3"] = {
                "total_findings": len(semgrep_findings),
                "confirmed": len(confirmed_violations),
                "filtered": len(semgrep_findings) - len(confirmed_violations)
            }
            
            # Stage 4: Auto-Remediation
            logger.info("\n[STAGE 4] Auto-Remediation Generation...")
            remediations = []
            
            for violation_data in confirmed_violations:
                fix = await self.stage_4_auto_remediation(
                    violation=violation_data["finding"],
                    code_snippet=violation_data["finding"].get("code_snippet", ""),
                    policy_context=policy_document[:500],  # Relevant policy excerpt
                    language=violation_data["finding"].get("language", "python")
                )
                remediations.append(fix)
            
            logger.info(f"  ✓ Generated {len(remediations)} remediation plans")
            results["stages"]["stage_4"] = {
                "remediations": remediations
            }
            
            # Summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            results["summary"] = {
                "total_violations": len(semgrep_findings),
                "true_positives": len(confirmed_violations),
                "false_positives": len(semgrep_findings) - len(confirmed_violations),
                "remediations_generated": len(remediations),
                "fp_elimination_rate": (len(semgrep_findings) - len(confirmed_violations)) / len(semgrep_findings) if semgrep_findings else 0,
                "duration_seconds": duration,
                "completed_at": end_time.isoformat()
            }
            
            logger.info("\n" + "=" * 70)
            logger.info("PIPELINE COMPLETE")
            logger.info(f"  Duration: {duration:.2f}s")
            logger.info(f"  False Positive Elimination: {results['summary']['fp_elimination_rate']:.1%}")
            logger.info("=" * 70)
            
            return results
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            results["error"] = str(e)
            return results
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    async def _call_groq(
        self,
        prompt: str,
        model: str,
        temp: float,
        max_tokens: int
    ) -> str:
        """Make async call to Groq API"""
        try:
            message = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                temperature=temp,
                max_tokens=max_tokens,
                top_p=0.9
            )
            return message.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Extract and parse JSON from Groq response"""
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            return {}
        except Exception as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return {}
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get pipeline configuration and status"""
        return {
            "status": "active",
            "version": "4-stage",
            "models": self.models,
            "temperatures": self.temperatures,
            "stages": {
                "stage_1": "Project Profiling (Fast Classification)",
                "stage_2": "Policy Translation (Generate Rules)",
                "stage_3": "Context Validation (Filter False Positives)",
                "stage_4": "Auto-Remediation (Generate Fixes)"
            }
        }
