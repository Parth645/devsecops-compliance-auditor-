"""
AI-Driven Repository Profiler (Step 1: Fast Triage)
Replaces keyword-based analysis with Groq API intelligence
Analyzes repository structure, routing, and compliance features
"""

import logging
import json
from typing import Dict, List, Any
from pathlib import Path
from groq import Groq

logger = logging.getLogger(__name__)


class GroqRepoProfiler:
    """
    AI-Driven Fast Triage
    - Analyzes repository file tree and routing
    - Identifies where compliance features are implemented
    - Single Groq API call (llama-3.1-8b-instant - 10x cheaper)
    """
    
    def __init__(self, api_key: str):
        """Initialize repo profiler with Groq client"""
        self.client = Groq(api_key=api_key)
        self.models = ["llama-3.1-8b-instant", "mixtral-8x7b-32768", "llama-3.3-70b-versatile"]
        self.model = self.models[0]  # Start with cheapest
    
    async def profile_repository(self, repo_path: str, files: List[str]) -> Dict[str, Any]:
        """
        Build intelligent repository profile
        
        Args:
            repo_path: Root path of repository
            files: List of all files in repository
            
        Returns:
            Dictionary with profile data and compliance feature locations
        """
        logger.info("[AI STAGE 1] Profiling repository with Groq...")
        
        # Extract file tree structure
        file_tree = self._build_file_tree(files)
        
        # Extract routing/endpoint patterns
        routes = self._extract_routes(repo_path, files)
        
        # Build context for Groq
        context = self._build_groq_context(file_tree, routes, files)
        
        # Call Groq for intelligent analysis
        profile = await self._analyze_with_groq(context)
        
        logger.info(f"  ✓ Repository profiled: {profile.get('tech_stack', 'unknown')} tech stack")
        
        return profile
    
    def _build_file_tree(self, files: List[str]) -> str:
        """Convert file list into readable tree structure"""
        dirs = {}
        
        for file_path in files[:100]:  # Analyze first 100 files for performance
            parts = Path(file_path).parts
            current = dirs
            
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            current[Path(file_path).name] = "FILE"
        
        return self._format_tree(dirs, "", max_depth=3)
    
    def _format_tree(self, tree: Dict, prefix: str = "", max_depth: int = 3, depth: int = 0) -> str:
        """Format tree as readable text"""
        if depth >= max_depth:
            return ""
        
        lines = []
        items = list(tree.items())[:20]  # Limit output
        
        for i, (name, subtree) in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            lines.append(prefix + current_prefix + name)
            
            if isinstance(subtree, dict) and subtree:
                next_prefix = prefix + ("    " if is_last else "│   ")
                lines.append(self._format_tree(subtree, next_prefix, max_depth, depth + 1))
        
        return "\n".join(filter(None, lines))
    
    def _extract_routes(self, repo_path: str, files: List[str]) -> List[str]:
        """Extract API routes and endpoints"""
        routes = []
        
        for file_path in files:
            if any(x in file_path.lower() for x in ["route", "controller", "handler", "api"]):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # Extract route patterns (Express, FastAPI, Django patterns)
                        for line in content.split('\n'):
                            if any(x in line for x in ["@app.", "@router.", "app.post", "app.get", "router.get", "router.post"]):
                                # Clean up to show endpoint
                                endpoint = line.strip()[:100]
                                if endpoint and endpoint not in routes:
                                    routes.append(endpoint)
                except:
                    pass
        
        return routes[:30]  # Top 30 routes
    
    def _build_groq_context(self, file_tree: str, routes: List[str], files: List[str]) -> str:
        """Build context for Groq analysis"""
        
        # File type breakdown
        extensions = {}
        for file_path in files:
            ext = Path(file_path).suffix or "no_ext"
            extensions[ext] = extensions.get(ext, 0) + 1
        
        # Identify framework by patterns
        framework_clues = []
        content_sample = ""
        
        for file_path in files[:20]:
            if file_path.endswith(('.js', '.ts', '.json')):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        sample = f.read()[:500]
                        if "express" in sample:
                            framework_clues.append("Express.js")
                        if "fastapi" in sample or "from fastapi" in sample:
                            framework_clues.append("FastAPI")
                        if "django" in sample:
                            framework_clues.append("Django")
                        if "fastify" in sample:
                            framework_clues.append("Fastify")
                except:
                    pass
        
        context = f"""REPOSITORY STRUCTURE:
{file_tree}

FILE TYPE DISTRIBUTION:
{json.dumps(extensions, indent=2)}

DETECTED FRAMEWORK HINTS:
{', '.join(set(framework_clues)) if framework_clues else "Unknown/Custom"}

TOP ROUTES/ENDPOINTS:
{chr(10).join(routes) if routes else "No routes found"}

TOTAL FILES: {len(files)}
"""
        
        return context
    
    async def _analyze_with_groq(self, context: str) -> Dict[str, Any]:
        """Use Groq to analyze repository structure and identify compliance features"""
        
        prompt = f"""You are a code auditor analyzing a repository for compliance features.

REPOSITORY CONTEXT:
{context}

Based on the file structure, routes, and framework patterns, identify:

1. **Architecture Overview**: What is this application's purpose and architecture?
2. **Compliance Features Present**: Where are these implemented (if found)?
   - Authentication/Authorization (files: __)
   - Data Encryption (files: __)
   - Audit Logging (files: __)
   - User Consent (files: __)
   - Data Retention/Deletion (files: __)
   - Breach Notification (files: __)
   - API Rate Limiting (files: __)
   - Input Validation (files: __)
   - Security Headers (files: __)
   
3. **Critical Gaps**: What compliance features are NOTICEABLY ABSENT?

Respond with ONLY a valid JSON object (no markdown, no code blocks):
{{
  "application_purpose": "brief description",
  "tech_stack": "detected technologies",
  "architecture": "brief architecture description",
  "framework": "identified framework",
  "entry_points": ["list of main entry files"],
  "compliance_features": {{
    "authentication": {{"present": true/false, "files": ["file1", "file2"]}},
    "encryption": {{"present": true/false, "files": []}},
    "audit_logging": {{"present": true/false, "files": []}},
    "user_consent": {{"present": true/false, "files": []}},
    "data_retention": {{"present": true/false, "files": []}},
    "breach_notification": {{"present": true/false, "files": []}},
    "rate_limiting": {{"present": true/false, "files": []}},
    "input_validation": {{"present": true/false, "files": []}},
    "security_headers": {{"present": true/false, "files": []}}
  }},
  "critical_gaps": ["gap1", "gap2"],
  "confidence_score": 0.85
}}"""
        
        try:
            # Try models in order until one works
            for model in self.models:
                try:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an expert compliance auditor. Respond ONLY with valid JSON. No markdown, no explanations."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.15,
                        max_tokens=2000
                    )
                    
                    result_text = response.choices[0].message.content.strip()
                    
                    # Strip markdown if present
                    if result_text.startswith("```"):
                        result_text = result_text.split("```")[1]
                        if result_text.startswith("json"):
                            result_text = result_text[4:]
                    
                    profile = json.loads(result_text)
                    self.model = model  # Update to working model
                    logger.info(f"  ✓ Groq profiled repository: {profile.get('application_purpose', 'unknown')}")
                    
                    return profile
                    
                except Exception as e:
                    if "429" in str(e) or "rate_limit" in str(e).lower():
                        logger.debug(f"  Rate limit on {model}, trying next...")
                        continue
                    elif "400" in str(e):
                        logger.debug(f"  Bad request on {model}, trying next...")
                        continue
                    else:
                        raise
            
            # If all models fail, return unknown profile
            logger.error("All models failed for repo profiling, returning default profile")
            return {
                "application_purpose": "unknown",
                "tech_stack": "unknown",
                "architecture": "unknown",
                "framework": "unknown",
                "compliance_features": {},
                "critical_gaps": []
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Groq response: {e}")
            logger.debug(f"Response was: {result_text[:200]}")
            return {"error": "json_parse_error", "fallback": True}
        except Exception as e:
            logger.error(f"Repo profiling failed: {e}")
            return {"error": str(e), "fallback": True}
