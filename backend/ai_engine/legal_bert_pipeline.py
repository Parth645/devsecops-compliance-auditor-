"""
Legal-BERT Pipeline for Compliance Text Analysis
Uses HuggingFace Transformers with Legal-BERT model for legal document processing
"""

import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    AutoModelForTokenClassification,
    pipeline
)
import logging
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)

class LegalBERTPipeline:
    """
    Legal-BERT pipeline for compliance analysis and legal text processing
    """
    
    def __init__(self, model_name: str = "nlpaueb/legal-bert-base-uncased"):
        """
        Initialize Legal-BERT pipeline
        
        Args:
            model_name: HuggingFace model identifier for Legal-BERT
        """
        self.model_name = model_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # Initialize components
        self.tokenizer = None
        self.classification_model = None
        self.ner_model = None
        self.classification_pipeline = None
        self.ner_pipeline = None
        
        # Load models
        self._load_models()
    
    def _load_models(self):
        """Load Legal-BERT models and create pipelines"""
        try:
            logger.info(f"Loading Legal-BERT tokenizer: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Try to load classification model
            try:
                logger.info("Loading Legal-BERT classification model...")
                self.classification_model = AutoModelForSequenceClassification.from_pretrained(
                    self.model_name
                )
                self.classification_pipeline = pipeline(
                    "text-classification",
                    model=self.classification_model,
                    tokenizer=self.tokenizer,
                    device=0 if torch.cuda.is_available() else -1
                )
                logger.info("Classification model loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load classification model: {e}")
                # Fallback to a general legal classification model
                self.classification_pipeline = pipeline(
                    "text-classification",
                    model="ProsusAI/finbert",
                    device=0 if torch.cuda.is_available() else -1
                )
            
            # Try to load NER model
            try:
                logger.info("Loading Legal-BERT NER model...")
                # Try legal-specific NER model first
                self.ner_pipeline = pipeline(
                    "ner",
                    model="law-ai/InLegalBERT",
                    tokenizer="law-ai/InLegalBERT",
                    aggregation_strategy="simple",
                    device=0 if torch.cuda.is_available() else -1
                )
                logger.info("Legal NER model loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load legal NER model: {e}")
                # Fallback to general NER
                self.ner_pipeline = pipeline(
                    "ner",
                    model="dbmdz/bert-large-cased-finetuned-conll03-english",
                    aggregation_strategy="simple",
                    device=0 if torch.cuda.is_available() else -1
                )
                
        except Exception as e:
            logger.error(f"Failed to load Legal-BERT models: {e}")
            raise
    
    def classify_compliance_text(self, text: str) -> Dict[str, Any]:
        """
        Classify legal/compliance text using Legal-BERT
        
        Args:
            text: Input text to classify
            
        Returns:
            Classification results with confidence scores
        """
        try:
            if not self.classification_pipeline:
                raise ValueError("Classification pipeline not available")
            
            # Truncate text if too long
            max_length = 512
            if len(text.split()) > max_length:
                text = ' '.join(text.split()[:max_length])
            
            results = self.classification_pipeline(text)
            
            # Process results
            if isinstance(results, list):
                results = results[0]
            
            return {
                "label": results.get("label", "UNKNOWN"),
                "confidence": results.get("score", 0.0),
                "text_length": len(text),
                "model_used": "legal-bert"
            }
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return {
                "label": "ERROR",
                "confidence": 0.0,
                "error": str(e),
                "text_length": len(text)
            }
    
    def extract_legal_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract legal entities using Legal-BERT NER
        
        Args:
            text: Input text for entity extraction
            
        Returns:
            List of extracted entities with types and confidence
        """
        try:
            if not self.ner_pipeline:
                raise ValueError("NER pipeline not available")
            
            # Truncate text if too long
            max_length = 512
            if len(text.split()) > max_length:
                text = ' '.join(text.split()[:max_length])
            
            entities = self.ner_pipeline(text)
            
            # Process and enhance entities
            processed_entities = []
            for entity in entities:
                processed_entity = {
                    "text": entity.get("word", ""),
                    "label": entity.get("entity_group", entity.get("entity", "UNKNOWN")),
                    "confidence": entity.get("score", 0.0),
                    "start": entity.get("start", 0),
                    "end": entity.get("end", 0),
                    "entity_type": self._classify_legal_entity_type(entity.get("entity_group", ""))
                }
                processed_entities.append(processed_entity)
            
            return processed_entities
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return [{
                "text": "",
                "label": "ERROR",
                "confidence": 0.0,
                "error": str(e)
            }]
    
    def _classify_legal_entity_type(self, entity_label: str) -> str:
        """
        Classify entity type for legal context
        """
        legal_mappings = {
            "PER": "legal_person",
            "PERSON": "legal_person", 
            "ORG": "organization",
            "ORGANIZATION": "organization",
            "LOC": "jurisdiction",
            "LOCATION": "jurisdiction",
            "MISC": "legal_concept",
            "DATE": "legal_date",
            "MONEY": "financial_amount",
            "LAW": "legal_reference",
            "COURT": "legal_institution",
            "JUDGE": "legal_person",
            "LAWYER": "legal_person"
        }
        
        return legal_mappings.get(entity_label.upper(), "other")
    
    def analyze_compliance_obligations(self, text: str) -> Dict[str, Any]:
        """
        Analyze text for compliance obligations, subjects, and actions
        
        Args:
            text: Legal/compliance text to analyze
            
        Returns:
            Analysis results with obligations, subjects, and actions
        """
        try:
            # Get classification
            classification = self.classify_compliance_text(text)
            
            # Get entities
            entities = self.extract_legal_entities(text)
            
            # Extract compliance-specific information
            obligations = self._extract_obligations(text, entities)
            subjects = self._extract_subjects(entities)
            actions = self._extract_actions(text, entities)
            
            return {
                "classification": classification,
                "entities": entities,
                "compliance_analysis": {
                    "obligations": obligations,
                    "subjects": subjects,
                    "actions": actions,
                    "compliance_score": self._calculate_compliance_score(text, entities),
                    "risk_level": self._assess_risk_level(classification, obligations)
                }
            }
            
        except Exception as e:
            logger.error(f"Compliance analysis failed: {e}")
            return {
                "error": str(e),
                "classification": {},
                "entities": [],
                "compliance_analysis": {}
            }
    
    def _extract_obligations(self, text: str, entities: List[Dict]) -> List[Dict[str, Any]]:
        """Extract compliance obligations from text"""
        obligations = []
        
        # Look for obligation keywords
        obligation_keywords = [
            "must", "shall", "required", "mandatory", "obligated", "duty",
            "responsible", "liable", "compliance", "regulation", "law"
        ]
        
        sentences = text.split('.')
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip().lower()
            
            for keyword in obligation_keywords:
                if keyword in sentence:
                    obligations.append({
                        "text": sentence,
                        "keyword": keyword,
                        "sentence_index": i,
                        "entities_in_sentence": [
                            e for e in entities 
                            if e.get("start", 0) >= len('.'.join(sentences[:i])) and 
                               e.get("end", 0) <= len('.'.join(sentences[:i+1]))
                        ]
                    })
                    break
        
        return obligations
    
    def _extract_subjects(self, entities: List[Dict]) -> List[Dict[str, Any]]:
        """Extract legal subjects from entities"""
        subjects = []
        
        for entity in entities:
            if entity.get("entity_type") in ["legal_person", "organization"]:
                subjects.append({
                    "name": entity.get("text", ""),
                    "type": entity.get("entity_type", ""),
                    "confidence": entity.get("confidence", 0.0)
                })
        
        return subjects
    
    def _extract_actions(self, text: str, entities: List[Dict]) -> List[str]:
        """Extract compliance actions from text"""
        action_keywords = [
            "implement", "establish", "maintain", "report", "disclose",
            "monitor", "audit", "review", "assess", "document", "file",
            "submit", "notify", "inform", "register", "license"
        ]
        
        actions = []
        text_lower = text.lower()
        
        for keyword in action_keywords:
            if keyword in text_lower:
                actions.append(keyword)
        
        return list(set(actions))  # Remove duplicates
    
    def _calculate_compliance_score(self, text: str, entities: List[Dict]) -> float:
        """Calculate compliance score based on analysis"""
        score = 0.0
        
        # Score based on entities found
        score += min(len(entities) * 0.1, 0.5)
        
        # Score based on text length and complexity
        if len(text) > 100:
            score += 0.2
        
        # Score based on legal keywords
        legal_keywords = ["compliance", "regulation", "law", "legal", "requirement"]
        for keyword in legal_keywords:
            if keyword.lower() in text.lower():
                score += 0.1
        
        return min(score, 1.0)
    
    def _assess_risk_level(self, classification: Dict, obligations: List[Dict]) -> str:
        """Assess risk level based on analysis"""
        confidence = classification.get("confidence", 0.0)
        num_obligations = len(obligations)
        
        if confidence > 0.8 and num_obligations > 3:
            return "HIGH"
        elif confidence > 0.6 and num_obligations > 1:
            return "MEDIUM"
        else:
            return "LOW"