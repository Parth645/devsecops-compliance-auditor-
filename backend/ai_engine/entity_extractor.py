"""
Legal Entity Extractor using spaCy + Custom Legal Components
Enhanced entity recognition for legal and compliance documents
"""

import spacy
from spacy import displacy
from spacy.tokens import Doc, Span
from spacy.matcher import Matcher, PhraseMatcher
import re
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class LegalEntityExtractor:
    """
    Enhanced entity extractor for legal documents using spaCy
    """
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize spaCy pipeline with legal enhancements
        
        Args:
            model_name: spaCy model to use
        """
        self.model_name = model_name
        self.nlp = None
        self.matcher = None
        self.phrase_matcher = None
        
        # Legal entity patterns
        self.legal_patterns = self._create_legal_patterns()
        
        # Initialize spaCy pipeline
        self._load_spacy_pipeline()
    
    def _load_spacy_pipeline(self):
        """Load and configure spaCy pipeline"""
        try:
            logger.info(f"Loading spaCy model: {self.model_name}")
            self.nlp = spacy.load(self.model_name)
            
            # Add custom legal component
            if "legal_entity_ruler" not in self.nlp.pipe_names:
                self._add_legal_entity_ruler()
            
            # Initialize matchers
            self.matcher = Matcher(self.nlp.vocab)
            self.phrase_matcher = PhraseMatcher(self.nlp.vocab)
            
            # Add legal patterns
            self._add_legal_patterns()
            
            logger.info("spaCy pipeline loaded successfully with legal enhancements")
            
        except OSError as e:
            logger.error(f"Failed to load spaCy model {self.model_name}: {e}")
            logger.info("Trying to download the model...")
            try:
                spacy.cli.download(self.model_name)
                self.nlp = spacy.load(self.model_name)
                self._add_legal_entity_ruler()
                self.matcher = Matcher(self.nlp.vocab)
                self.phrase_matcher = PhraseMatcher(self.nlp.vocab)
                self._add_legal_patterns()
            except Exception as download_error:
                logger.error(f"Failed to download/load model: {download_error}")
                raise
    
    def _add_legal_entity_ruler(self):
        """Add custom entity ruler for legal entities"""
        from spacy.pipeline import EntityRuler
        
        ruler = EntityRuler(self.nlp, overwrite_ents=True)
        
        # Legal entity patterns
        legal_entities = [
            # Court types
            {"label": "COURT", "pattern": [{"LOWER": "supreme"}, {"LOWER": "court"}]},
            {"label": "COURT", "pattern": [{"LOWER": "district"}, {"LOWER": "court"}]},
            {"label": "COURT", "pattern": [{"LOWER": "appellate"}, {"LOWER": "court"}]},
            {"label": "COURT", "pattern": [{"LOWER": "federal"}, {"LOWER": "court"}]},
            
            # Legal documents
            {"label": "LEGAL_DOC", "pattern": [{"LOWER": "terms"}, {"LOWER": "of"}, {"LOWER": "service"}]},
            {"label": "LEGAL_DOC", "pattern": [{"LOWER": "privacy"}, {"LOWER": "policy"}]},
            {"label": "LEGAL_DOC", "pattern": [{"LOWER": "user"}, {"LOWER": "agreement"}]},
            {"label": "LEGAL_DOC", "pattern": [{"LOWER": "license"}, {"LOWER": "agreement"}]},
            
            # Regulatory bodies (using TEXT instead of UPPER for compatibility)
            {"label": "REGULATOR", "pattern": [{"TEXT": "SEC"}]},
            {"label": "REGULATOR", "pattern": [{"TEXT": "FTC"}]},
            {"label": "REGULATOR", "pattern": [{"TEXT": "FDA"}]},
            {"label": "REGULATOR", "pattern": [{"TEXT": "GDPR"}]},
            {"label": "REGULATOR", "pattern": [{"TEXT": "CCPA"}]},
            
            # Legal concepts
            {"label": "LEGAL_CONCEPT", "pattern": [{"LOWER": "intellectual"}, {"LOWER": "property"}]},
            {"label": "LEGAL_CONCEPT", "pattern": [{"LOWER": "data"}, {"LOWER": "protection"}]},
            {"label": "LEGAL_CONCEPT", "pattern": [{"LOWER": "breach"}, {"LOWER": "notification"}]},
            {"label": "LEGAL_CONCEPT", "pattern": [{"LOWER": "right"}, {"LOWER": "to"}, {"LOWER": "deletion"}]},
        ]
        
        ruler.add_patterns(legal_entities)
        self.nlp.add_pipe("entity_ruler", before="ner", config={"overwrite_ents": True})
        self.nlp.get_pipe("entity_ruler").add_patterns(legal_entities)
    
    def _create_legal_patterns(self) -> Dict[str, List[List[Dict]]]:
        """Create legal-specific patterns for matching"""
        return {
            "obligations": [
                [{"LOWER": {"IN": ["must", "shall", "required"]}}],
                [{"LOWER": "subject"}, {"LOWER": "to"}],
                [{"LOWER": "in"}, {"LOWER": "accordance"}, {"LOWER": "with"}],
                [{"LOWER": "comply"}, {"LOWER": "with"}],
                [{"LOWER": "obligation"}, {"LOWER": "to"}]
            ],
            "prohibitions": [
                [{"LOWER": {"IN": ["prohibited", "forbidden", "banned"]}}],
                [{"LOWER": "may"}, {"LOWER": "not"}],
                [{"LOWER": "shall"}, {"LOWER": "not"}],
                [{"LOWER": "is"}, {"LOWER": "not"}, {"LOWER": "permitted"}]
            ],
            "rights": [
                [{"LOWER": "right"}, {"LOWER": "to"}],
                [{"LOWER": "entitled"}, {"LOWER": "to"}],
                [{"LOWER": "has"}, {"LOWER": "the"}, {"LOWER": "right"}],
                [{"LOWER": "may"}, {"LOWER": "request"}]
            ],
            "penalties": [
                [{"LOWER": {"IN": ["fine", "penalty", "sanction"]}}],
                [{"LOWER": "liable"}, {"LOWER": "for"}],
                [{"LOWER": "subject"}, {"LOWER": "to"}, {"LOWER": "penalty"}],
                [{"LOWER": "violation"}, {"LOWER": "of"}]
            ]
        }
    
    def _add_legal_patterns(self):
        """Add legal patterns to matchers"""
        for pattern_type, patterns in self.legal_patterns.items():
            for i, pattern in enumerate(patterns):
                self.matcher.add(f"{pattern_type.upper()}_{i}", [pattern])
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract entities from legal text using enhanced spaCy pipeline
        
        Args:
            text: Input legal text
            
        Returns:
            Extracted entities and analysis
        """
        try:
            # Process text with spaCy
            doc = self.nlp(text)
            
            # Extract standard entities
            entities = []
            for ent in doc.ents:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "confidence": 1.0,  # spaCy doesn't provide confidence scores
                    "description": spacy.explain(ent.label_) or "Unknown"
                })
            
            # Extract legal patterns
            legal_matches = self._extract_legal_patterns(doc)
            
            # Extract compliance-specific entities
            compliance_entities = self._extract_compliance_entities(doc)
            
            return {
                "entities": entities,
                "legal_patterns": legal_matches,
                "compliance_entities": compliance_entities,
                "document_stats": self._get_document_stats(doc),
                "legal_analysis": self._analyze_legal_structure(doc)
            }
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return {
                "entities": [],
                "legal_patterns": {},
                "compliance_entities": [],
                "error": str(e)
            }
    
    def _extract_legal_patterns(self, doc: Doc) -> Dict[str, List[Dict]]:
        """Extract legal patterns using matcher"""
        matches = self.matcher(doc)
        pattern_matches = {}
        
        for match_id, start, end in matches:
            label = self.nlp.vocab.strings[match_id]
            pattern_type = label.split('_')[0].lower()
            
            if pattern_type not in pattern_matches:
                pattern_matches[pattern_type] = []
            
            pattern_matches[pattern_type].append({
                "text": doc[start:end].text,
                "start": doc[start].idx,
                "end": doc[end-1].idx + len(doc[end-1].text),
                "pattern_type": pattern_type
            })
        
        return pattern_matches
    
    def _extract_compliance_entities(self, doc: Doc) -> List[Dict[str, Any]]:
        """Extract compliance-specific entities"""
        compliance_entities = []
        
        # Regex patterns for compliance entities
        compliance_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "url": r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            "phone": r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
            "ssn": r'\b\d{3}-?\d{2}-?\d{4}\b',
            "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            "ip_address": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            "date": r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b'
        }
        
        text = doc.text
        for entity_type, pattern in compliance_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                compliance_entities.append({
                    "text": match.group(),
                    "type": entity_type,
                    "start": match.start(),
                    "end": match.end(),
                    "privacy_risk": self._assess_privacy_risk(entity_type)
                })
        
        return compliance_entities
    
    def _assess_privacy_risk(self, entity_type: str) -> str:
        """Assess privacy risk level for entity type"""
        high_risk = ["ssn", "credit_card", "email"]
        medium_risk = ["phone", "ip_address"]
        
        if entity_type in high_risk:
            return "HIGH"
        elif entity_type in medium_risk:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_document_stats(self, doc: Doc) -> Dict[str, Any]:
        """Get document statistics"""
        return {
            "token_count": len(doc),
            "sentence_count": len(list(doc.sents)),
            "entity_count": len(doc.ents),
            "avg_sentence_length": len(doc) / len(list(doc.sents)) if len(list(doc.sents)) > 0 else 0
        }
    
    def _analyze_legal_structure(self, doc: Doc) -> Dict[str, Any]:
        """Analyze legal document structure"""
        legal_keywords = {
            "contract": ["agreement", "contract", "terms", "conditions"],
            "privacy": ["privacy", "data", "personal", "information"],
            "liability": ["liability", "responsible", "damages", "indemnify"],
            "termination": ["terminate", "end", "expire", "cancel"],
            "governing_law": ["governed", "jurisdiction", "applicable", "law"]
        }
        
        text_lower = doc.text.lower()
        legal_sections = {}
        
        for section, keywords in legal_keywords.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            legal_sections[section] = {
                "keyword_count": count,
                "present": count > 0
            }
        
        return {
            "legal_sections": legal_sections,
            "document_type": self._classify_document_type(legal_sections),
            "completeness_score": self._calculate_completeness_score(legal_sections)
        }
    
    def _classify_document_type(self, legal_sections: Dict) -> str:
        """Classify the type of legal document"""
        if legal_sections.get("privacy", {}).get("present", False):
            return "privacy_policy"
        elif legal_sections.get("contract", {}).get("present", False):
            return "contract"
        elif legal_sections.get("liability", {}).get("present", False):
            return "terms_of_service"
        else:
            return "general_legal"
    
    def _calculate_completeness_score(self, legal_sections: Dict) -> float:
        """Calculate document completeness score"""
        total_sections = len(legal_sections)
        present_sections = sum(1 for section in legal_sections.values() if section.get("present", False))
        
        return present_sections / total_sections if total_sections > 0 else 0.0
    
    def visualize_entities(self, text: str, style: str = "ent") -> str:
        """
        Create visualization of extracted entities
        
        Args:
            text: Input text
            style: Visualization style ("ent" or "dep")
            
        Returns:
            HTML visualization
        """
        try:
            doc = self.nlp(text)
            return displacy.render(doc, style=style, jupyter=False)
        except Exception as e:
            logger.error(f"Visualization failed: {e}")
            return f"<p>Visualization error: {str(e)}</p>"