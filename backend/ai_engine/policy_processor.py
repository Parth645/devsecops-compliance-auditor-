"""
Policy Processor - AI Engine Component for Legal Policy Management
Converts legal policies to compliance rules using transformers
"""

import logging
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import asyncio

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    from transformers import AutoModelForQuestionAnswering, AutoTokenizer
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)

class PolicyProcessor:
    """
    Processes legal policies and converts them to compliance rules using AI
    """
    
    def __init__(self, policies_dir: str = "policies"):
        """
        Initialize policy processor
        
        Args:
            policies_dir: Directory containing policy documents
        """
        self.policies_dir = Path(policies_dir)
        self.policies_dir.mkdir(exist_ok=True)
        
        # Initialize transformers pipelines
        self.text_classifier = None
        self.qa_pipeline = None
        self.summarizer = None
        
        # Policy storage
        self.processed_policies = {}
        self.compliance_rules = {}
        
        self._initialize_transformers()
        self._load_existing_policies()
    
    def _initialize_transformers(self):
        """Initialize transformer models for policy processing"""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers not available, falling back to rule-based processing")
            return
        
        try:
            logger.info("Initializing lightweight transformer models for policy processing...")
            
            # Use lightweight models for better performance
            # Text classification - using a smaller, more appropriate model
            try:
                self.text_classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli"
                )
                logger.info("✓ Text classifier initialized")
            except Exception as e:
                logger.warning(f"Text classifier initialization failed: {e}")
                self.text_classifier = None
            
            # Question-answering for extracting specific requirements
            try:
                self.qa_pipeline = pipeline(
                    "question-answering",
                    model="distilbert-base-cased-distilled-squad"
                )
                logger.info("✓ QA pipeline initialized")
            except Exception as e:
                logger.warning(f"QA pipeline initialization failed: {e}")
                self.qa_pipeline = None
            
            # Summarization - using a lighter model
            try:
                self.summarizer = pipeline(
                    "summarization",
                    model="sshleifer/distilbart-cnn-6-6",
                    max_length=200,
                    min_length=50
                )
                logger.info("✓ Summarizer initialized")
            except Exception as e:
                logger.warning(f"Summarizer initialization failed: {e}")
                self.summarizer = None
            
            logger.info("Transformer models initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize transformers: {e}")
            self.text_classifier = None
            self.qa_pipeline = None
            self.summarizer = None
    
    def _load_existing_policies(self):
        """Load previously processed policies from JSON files"""
        try:
            policies_json_path = self.policies_dir / "processed_policies.json"
            rules_json_path = self.policies_dir / "compliance_rules.json"
            
            if policies_json_path.exists():
                with open(policies_json_path, 'r', encoding='utf-8') as f:
                    self.processed_policies = json.load(f)
                logger.info(f"Loaded {len(self.processed_policies)} existing policies")
            
            if rules_json_path.exists():
                with open(rules_json_path, 'r', encoding='utf-8') as f:
                    self.compliance_rules = json.load(f)
                logger.info(f"Loaded {len(self.compliance_rules)} existing compliance rules")
                
        except Exception as e:
            logger.error(f"Failed to load existing policies: {e}")
    
    def import_policy_folder(self, folder_path: str) -> Dict[str, Any]:
        """
        Import all policy documents from a folder
        
        Args:
            folder_path: Path to folder containing policy documents
            
        Returns:
            Import results with processing status
        """
        results = {
            "imported_count": 0,
            "processed_count": 0,
            "failed_count": 0,
            "policies": [],
            "errors": []
        }
        
        try:
            folder = Path(folder_path)
            if not folder.exists():
                raise FileNotFoundError(f"Policy folder not found: {folder_path}")
            
            # Supported file types
            supported_extensions = {'.txt', '.md', '.pdf', '.doc', '.docx'}
            
            for file_path in folder.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                    try:
                        policy_content = self._read_policy_file(file_path)
                        policy_id = self._generate_policy_id(file_path)
                        
                        # Process the policy
                        processed_policy = self.process_policy(
                            policy_id=policy_id,
                            content=policy_content,
                            file_path=str(file_path)
                        )
                        
                        results["policies"].append(processed_policy)
                        results["imported_count"] += 1
                        
                        if processed_policy.get("processing_status") == "success":
                            results["processed_count"] += 1
                        else:
                            results["failed_count"] += 1
                            
                    except Exception as e:
                        error_msg = f"Failed to process {file_path}: {str(e)}"
                        logger.error(error_msg)
                        results["errors"].append(error_msg)
                        results["failed_count"] += 1
            
            # Save updated policies
            self._save_policies()
            
            logger.info(f"Policy import completed: {results['processed_count']}/{results['imported_count']} successful")
            return results
            
        except Exception as e:
            logger.error(f"Policy folder import failed: {e}")
            results["errors"].append(str(e))
            return results
    
    def _read_policy_file(self, file_path: Path) -> str:
        """Read content from various file types"""
        try:
            if file_path.suffix.lower() in ['.txt', '.md']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif file_path.suffix.lower() == '.pdf':
                # For PDF files, you'd need PyPDF2 or similar
                logger.warning(f"PDF processing not implemented for {file_path}")
                return f"PDF file: {file_path.name} (content extraction not implemented)"
            
            elif file_path.suffix.lower() in ['.doc', '.docx']:
                # For Word files, you'd need python-docx
                logger.warning(f"Word document processing not implemented for {file_path}")
                return f"Word document: {file_path.name} (content extraction not implemented)"
            
            else:
                return f"Unsupported file type: {file_path.suffix}"
                
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return f"Error reading file: {str(e)}"
    
    def _generate_policy_id(self, file_path: Path) -> str:
        """Generate unique policy ID from file path"""
        return f"policy_{file_path.stem}_{hash(str(file_path)) % 10000}"
    
    def process_policy(self, policy_id: str, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Process a single policy document using AI
        
        Args:
            policy_id: Unique identifier for the policy
            content: Policy text content
            file_path: Original file path
            
        Returns:
            Processed policy with extracted compliance rules
        """
        processing_start = datetime.now()
        
        try:
            policy_data = {
                "policy_id": policy_id,
                "file_path": file_path,
                "content": content,
                "processed_at": processing_start.isoformat(),
                "processing_status": "processing",
                "metadata": {},
                "compliance_rules": [],
                "categories": [],
                "key_requirements": [],
                "enforcement_actions": []
            }
            
            # Extract metadata
            policy_data["metadata"] = self._extract_metadata(content)
            
            # Categorize policy using AI
            if self.text_classifier:
                policy_data["categories"] = self._categorize_policy(content)
            else:
                policy_data["categories"] = self._rule_based_categorization(content)
            
            # Extract key requirements using QA
            if self.qa_pipeline:
                policy_data["key_requirements"] = self._extract_requirements_ai(content)
            else:
                policy_data["key_requirements"] = self._extract_requirements_rules(content)
            
            # Generate compliance rules
            policy_data["compliance_rules"] = self._generate_compliance_rules(
                policy_data["key_requirements"],
                policy_data["categories"]
            )
            
            # Extract enforcement actions
            policy_data["enforcement_actions"] = self._extract_enforcement_actions(content)
            
            # Generate summary if possible
            if self.summarizer and len(content) > 500:
                try:
                    summary = self.summarizer(content[:1000])  # Limit input length
                    policy_data["summary"] = summary[0]["summary_text"]
                except Exception as e:
                    logger.warning(f"Summarization failed: {e}")
                    policy_data["summary"] = content[:200] + "..."
            else:
                policy_data["summary"] = content[:200] + "..."
            
            # Mark as successfully processed
            policy_data["processing_status"] = "success"
            policy_data["processing_duration"] = (datetime.now() - processing_start).total_seconds()
            
            # Store processed policy
            self.processed_policies[policy_id] = policy_data
            
            # Store compliance rules
            for rule in policy_data["compliance_rules"]:
                rule_id = f"{policy_id}_{rule['rule_id']}"
                self.compliance_rules[rule_id] = rule
            
            logger.info(f"Successfully processed policy {policy_id}")
            return policy_data
            
        except Exception as e:
            logger.error(f"Policy processing failed for {policy_id}: {e}")
            return {
                "policy_id": policy_id,
                "file_path": file_path,
                "processing_status": "failed",
                "error": str(e),
                "processed_at": processing_start.isoformat(),
                "processing_duration": (datetime.now() - processing_start).total_seconds()
            }
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract basic metadata from policy content"""
        lines = content.split('\n')
        metadata = {
            "word_count": len(content.split()),
            "line_count": len(lines),
            "char_count": len(content)
        }
        
        # Look for common metadata patterns
        for line in lines[:10]:  # Check first 10 lines
            line_lower = line.lower().strip()
            if 'version' in line_lower and ':' in line:
                metadata["version"] = line.split(':', 1)[1].strip()
            elif 'date' in line_lower and ':' in line:
                metadata["date"] = line.split(':', 1)[1].strip()
            elif 'title' in line_lower and ':' in line:
                metadata["title"] = line.split(':', 1)[1].strip()
        
        return metadata
    
    def _categorize_policy(self, content: str) -> List[Dict[str, Any]]:
        """Categorize policy using AI classification"""
        try:
            if not self.text_classifier:
                return self._rule_based_categorization(content)
            
            # Truncate content for classification
            text_sample = content[:500]
            
            # Define candidate categories
            candidate_labels = [
                "data protection",
                "security",
                "privacy",
                "compliance",
                "liability",
                "intellectual property"
            ]
            
            # Use zero-shot classification
            result = self.text_classifier(text_sample, candidate_labels)
            
            # Convert to our format
            categories = []
            for label, score in zip(result['labels'], result['scores']):
                if score > 0.3:  # Only include confident predictions
                    categories.append({
                        "category": label.replace(" ", "_"),
                        "confidence": float(score),
                        "matched_keywords": []
                    })
            
            return categories if categories else self._rule_based_categorization(content)
            
        except Exception as e:
            logger.warning(f"AI categorization failed, using rule-based: {e}")
            return self._rule_based_categorization(content)
    
    def _rule_based_categorization(self, content: str) -> List[Dict[str, Any]]:
        """Rule-based policy categorization"""
        content_lower = content.lower()
        categories = []
        
        category_keywords = {
            "data_protection": ["personal data", "gdpr", "data protection", "privacy policy"],
            "security": ["security", "cybersecurity", "encryption", "access control"],
            "privacy": ["privacy", "personal information", "pii", "data subject"],
            "compliance": ["compliance", "regulatory", "audit", "monitoring"],
            "liability": ["liability", "damages", "indemnification", "limitation"],
            "intellectual_property": ["intellectual property", "copyright", "trademark", "patent"]
        }
        
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                confidence = min(score / len(keywords), 1.0)
                categories.append({
                    "category": category,
                    "confidence": confidence,
                    "matched_keywords": [kw for kw in keywords if kw in content_lower]
                })
        
        return sorted(categories, key=lambda x: x["confidence"], reverse=True)
    
    def _extract_requirements_ai(self, content: str) -> List[Dict[str, Any]]:
        """Extract key requirements using AI question-answering"""
        requirements = []
        
        # Questions to extract compliance requirements
        qa_questions = [
            "What data must be protected?",
            "What are the security requirements?",
            "What are the reporting obligations?",
            "What are the penalties for non-compliance?",
            "What are the user rights?",
            "What are the retention periods?",
            "What are the consent requirements?"
        ]
        
        try:
            for question in qa_questions:
                try:
                    result = self.qa_pipeline(question=question, context=content[:2000])
                    if result["score"] > 0.1:  # Confidence threshold
                        requirements.append({
                            "question": question,
                            "requirement": result["answer"],
                            "confidence": result["score"],
                            "source": "ai_extraction"
                        })
                except Exception as e:
                    logger.warning(f"QA failed for question '{question}': {e}")
            
            return requirements
            
        except Exception as e:
            logger.error(f"AI requirement extraction failed: {e}")
            return self._extract_requirements_rules(content)
    
    def _extract_requirements_rules(self, content: str) -> List[Dict[str, Any]]:
        """Rule-based requirement extraction"""
        requirements = []
        sentences = content.split('.')
        
        requirement_indicators = [
            "must", "shall", "required", "mandatory", "obligation",
            "prohibited", "forbidden", "not allowed", "ensure", "implement"
        ]
        
        for i, sentence in enumerate(sentences):
            sentence_lower = sentence.lower().strip()
            if any(indicator in sentence_lower for indicator in requirement_indicators):
                requirements.append({
                    "requirement": sentence.strip(),
                    "confidence": 0.7,
                    "sentence_index": i,
                    "source": "rule_extraction"
                })
        
        return requirements[:10]  # Limit to top 10
    
    def _generate_compliance_rules(self, requirements: List[Dict], categories: List[Dict]) -> List[Dict[str, Any]]:
        """Generate scannable compliance rules from requirements"""
        rules = []
        
        for i, req in enumerate(requirements):
            rule_id = f"rule_{i+1}"
            
            # Extract actionable patterns
            requirement_text = req.get("requirement", "")
            
            # Create concise description (max 200 chars)
            concise_description = self._create_concise_description(requirement_text)
            
            rule = {
                "rule_id": rule_id,
                "description": concise_description,  # Use concise description
                "full_requirement": requirement_text,  # Store full text separately
                "category": categories[0]["category"] if categories else "general",
                "severity": self._determine_severity(requirement_text),
                "scan_patterns": self._extract_scan_patterns(requirement_text),
                "compliance_check": self._generate_compliance_check(requirement_text),
                "confidence": req.get("confidence", 0.5)
            }
            
            rules.append(rule)
        
        return rules
    
    def _create_concise_description(self, requirement_text: str) -> str:
        """Create a concise description from requirement text"""
        # Remove markdown headers and formatting
        cleaned = requirement_text.replace('#', '').replace('*', '').replace('\n', ' ').strip()
        
        # Take first sentence or first 150 characters
        sentences = cleaned.split('.')
        first_sentence = sentences[0].strip() if sentences else cleaned
        
        # If still too long, truncate
        if len(first_sentence) > 150:
            first_sentence = first_sentence[:147] + "..."
        
        # Clean up extra whitespace
        first_sentence = ' '.join(first_sentence.split())
        
        return first_sentence if first_sentence else "Compliance requirement"
    
    def _determine_severity(self, requirement: str) -> str:
        """Determine rule severity based on content"""
        req_lower = requirement.lower()
        
        if any(word in req_lower for word in ["must", "mandatory", "required", "shall"]):
            return "HIGH"
        elif any(word in req_lower for word in ["should", "recommended", "advised"]):
            return "MEDIUM"
        else:
            return "LOW"
    
    def _extract_scan_patterns(self, requirement: str) -> List[str]:
        """Extract patterns that can be scanned in code"""
        patterns = []
        req_lower = requirement.lower()
        
        # Common compliance patterns
        if "password" in req_lower:
            patterns.extend(["password", "pwd", "passwd", "auth"])
        if "encrypt" in req_lower:
            patterns.extend(["encrypt", "decrypt", "cipher", "crypto"])
        if "log" in req_lower:
            patterns.extend(["log", "audit", "trace", "record"])
        if "access" in req_lower:
            patterns.extend(["access", "permission", "authorize", "role"])
        if "data" in req_lower:
            patterns.extend(["personal_data", "pii", "sensitive", "confidential"])
        
        return patterns
    
    def _generate_compliance_check(self, requirement: str) -> Dict[str, Any]:
        """Generate compliance check logic"""
        return {
            "check_type": "pattern_match",
            "description": f"Check for compliance with: {requirement[:100]}...",
            "validation_rules": [
                {
                    "rule": "presence_check",
                    "description": "Verify required elements are present"
                },
                {
                    "rule": "pattern_validation",
                    "description": "Validate implementation patterns"
                }
            ]
        }
    
    def _extract_enforcement_actions(self, content: str) -> List[Dict[str, Any]]:
        """Extract enforcement actions and penalties"""
        enforcement = []
        content_lower = content.lower()
        
        enforcement_keywords = ["penalty", "fine", "violation", "breach", "sanctions", "enforcement"]
        
        sentences = content.split('.')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in enforcement_keywords):
                enforcement.append({
                    "action": sentence.strip(),
                    "type": "penalty" if "penalty" in sentence.lower() else "enforcement"
                })
        
        return enforcement[:5]  # Limit results
    
    def get_compliance_rules_for_scanning(self) -> Dict[str, Any]:
        """Get all compliance rules formatted for repository scanning"""
        return {
            "rules": list(self.compliance_rules.values()),
            "rule_count": len(self.compliance_rules),
            "categories": list(set(rule.get("category", "general") for rule in self.compliance_rules.values())),
            "scan_patterns": self._consolidate_scan_patterns()
        }
    
    def _consolidate_scan_patterns(self) -> Dict[str, List[str]]:
        """Consolidate all scan patterns by category"""
        patterns_by_category = {}
        
        for rule in self.compliance_rules.values():
            category = rule.get("category", "general")
            patterns = rule.get("scan_patterns", [])
            
            if category not in patterns_by_category:
                patterns_by_category[category] = []
            
            patterns_by_category[category].extend(patterns)
        
        # Remove duplicates
        for category in patterns_by_category:
            patterns_by_category[category] = list(set(patterns_by_category[category]))
        
        return patterns_by_category
    
    def _save_policies(self):
        """Save processed policies and rules to JSON files"""
        try:
            # Save policies
            policies_path = self.policies_dir / "processed_policies.json"
            with open(policies_path, 'w', encoding='utf-8') as f:
                json.dump(self.processed_policies, f, indent=2, ensure_ascii=False)
            
            # Save rules
            rules_path = self.policies_dir / "compliance_rules.json"
            with open(rules_path, 'w', encoding='utf-8') as f:
                json.dump(self.compliance_rules, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(self.processed_policies)} policies and {len(self.compliance_rules)} rules")
            
        except Exception as e:
            logger.error(f"Failed to save policies: {e}")
    
    def get_policy_summary(self) -> Dict[str, Any]:
        """Get summary of all processed policies"""
        categories = {}
        total_rules = len(self.compliance_rules)
        
        for policy in self.processed_policies.values():
            for category_info in policy.get("categories", []):
                category = category_info.get("category", "unknown")
                categories[category] = categories.get(category, 0) + 1
        
        return {
            "total_policies": len(self.processed_policies),
            "total_rules": total_rules,
            "categories": categories,
            "policies_by_status": {
                "success": len([p for p in self.processed_policies.values() if p.get("processing_status") == "success"]),
                "failed": len([p for p in self.processed_policies.values() if p.get("processing_status") == "failed"])
            }
        }