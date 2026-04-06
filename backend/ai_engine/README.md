# AI Engine for Legal Compliance Detection

This AI engine combines **Legal-BERT** and **spaCy** to provide comprehensive compliance analysis for legal documents and code repositories.

## 🚀 Features

### Legal-BERT Pipeline
- **Text Classification**: Classify legal/compliance documents
- **Entity Recognition**: Extract legal entities (courts, regulations, legal persons)
- **Compliance Obligations**: Identify obligations, subjects, and actions
- **Risk Assessment**: Evaluate compliance risk levels
- **Confidence Scoring**: Provide confidence scores for all analyses

### spaCy Enhanced Pipeline
- **Legal Entity Ruler**: Custom patterns for legal concepts
- **Privacy Data Detection**: Identify PII, emails, SSNs, etc.
- **Legal Pattern Matching**: Find obligations, prohibitions, rights, penalties
- **Document Structure Analysis**: Analyze legal document completeness
- **Visualization**: Generate entity visualizations

### Combined Analysis
- **Multi-Pipeline Integration**: Combine results from both AI systems
- **Comprehensive Scoring**: Overall compliance and risk assessment
- **Smart Recommendations**: AI-generated compliance improvement suggestions
- **Performance Optimization**: Efficient processing for large documents

## 📦 Installation

### Quick Setup
```bash
# Run the automated setup script
./setup.sh
```

### Manual Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install PyTorch (CPU version)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install transformers and other ML libraries
pip install transformers numpy pandas scikit-learn

# Install spaCy and download English model
pip install spacy
python -m spacy download en_core_web_sm

# Install additional NLP libraries
pip install nltk textblob

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

## 🧪 Testing

### Run Test Suite
```bash
python test_ai_engine.py
```

### Run Demo
```bash
python demo_ai.py
```

### API Testing
```bash
# Start the server
python main.py

# Test AI endpoints
curl -X POST "http://localhost:8000/ai-analyze-text" \
  -H "Content-Type: application/json" \
  -d '{"text": "Users must comply with GDPR regulations.", "analysis_type": "comprehensive"}'
```

## 📚 Usage Examples

### Analyzing Legal Text
```python
from compliance_analyzer import ComplianceAnalyzer

# Initialize analyzer
analyzer = ComplianceAnalyzer()

# Analyze text
text = "This privacy policy complies with GDPR and CCPA regulations."
result = analyzer.analyze_text(text, "comprehensive")

print(f"Compliance Score: {result['compliance_score']}")
print(f"Risk Level: {result['risk_assessment']['overall_risk']}")
```

### Extract Legal Entities
```python
from entity_extractor import LegalEntityExtractor

# Initialize extractor
extractor = LegalEntityExtractor()

# Extract entities
result = extractor.extract_entities("The Supreme Court ruled on GDPR compliance.")

# View entities
for entity in result['entities']:
    print(f"{entity['text']} -> {entity['label']}")
```

### Legal-BERT Classification
```python
from legal_bert_pipeline import LegalBERTPipeline

# Initialize pipeline
bert = LegalBERTPipeline()

# Classify text
result = bert.classify_compliance_text("Terms of service agreement")
print(f"Classification: {result['label']} (confidence: {result['confidence']})")
```

## 🔧 API Endpoints

### AI Analysis Endpoints
- `POST /ai-analyze-text` - Analyze text for compliance issues
- `POST /ai-analyze-repository` - Analyze entire repository with AI
- `GET /ai-status` - Check AI pipeline status

### Request/Response Examples

#### Text Analysis
```json
POST /ai-analyze-text
{
  "text": "Users must comply with all applicable laws...",
  "analysis_type": "comprehensive"
}

Response:
{
  "status": "success",
  "ai_analysis": {
    "compliance_score": 0.85,
    "risk_assessment": {"overall_risk": "LOW"},
    "recommendations": [...],
    "entities": [...],
    "legal_patterns": {...}
  }
}
```

## 🎯 Analysis Types

1. **comprehensive** - Full Legal-BERT + spaCy analysis
2. **quick** - Fast rule-based analysis with minimal AI
3. **entities_only** - Focus on entity extraction
4. **classification_only** - Legal document classification only

## 📊 Output Interpretation

### Compliance Score (0.0 - 1.0)
- **0.8-1.0**: Excellent compliance coverage
- **0.6-0.8**: Good compliance, minor improvements needed
- **0.4-0.6**: Moderate compliance, review recommended
- **0.0-0.4**: Poor compliance, significant improvements needed

### Risk Levels
- **LOW**: Minimal compliance risks detected
- **MEDIUM**: Some compliance concerns, monitoring recommended
- **HIGH**: Significant compliance risks, immediate review required

### Entity Types
- **LEGAL_PERSON**: Individuals in legal context
- **ORGANIZATION**: Companies, institutions
- **COURT**: Legal courts and tribunals
- **REGULATOR**: Regulatory bodies (SEC, FTC, etc.)
- **LEGAL_DOC**: Legal document types
- **LEGAL_CONCEPT**: Legal concepts and principles

## ⚙️ Configuration

### Model Selection
```python
# Use different Legal-BERT model
analyzer = ComplianceAnalyzer()
analyzer.legal_bert_pipeline = LegalBERTPipeline("nlpaueb/legal-bert-small-uncased")

# Use different spaCy model
analyzer.entity_extractor = LegalEntityExtractor("en_core_web_lg")
```

### Performance Tuning
- **Text Length Limit**: 50,000 characters per analysis
- **Repository File Limit**: 20 files per analysis (configurable)
- **GPU Support**: Automatically detects and uses CUDA if available
- **Batch Processing**: Supports batch analysis for multiple documents

## 🔍 Troubleshooting

### Common Issues

1. **Model Download Failures**
   ```bash
   # Manually download spaCy model
   python -m spacy download en_core_web_sm
   
   # Clear transformers cache
   rm -rf ~/.cache/huggingface/transformers/
   ```

2. **Memory Issues**
   - Reduce text length limits in configuration
   - Use smaller models (legal-bert-small instead of legal-bert-base)
   - Process files in smaller batches

3. **Import Errors**
   ```bash
   # Check dependencies
   pip list | grep -E "(torch|transformers|spacy)"
   
   # Reinstall problematic packages
   pip uninstall torch transformers spacy
   pip install torch transformers spacy
   ```

## 📈 Performance Metrics

### Typical Processing Times
- **Short Text** (< 1000 chars): 0.5-2 seconds
- **Medium Text** (1000-5000 chars): 2-8 seconds  
- **Long Text** (5000+ chars): 8-20 seconds
- **Repository Analysis**: 30-120 seconds (depends on file count)

### Hardware Requirements
- **Minimum**: 4GB RAM, CPU-only
- **Recommended**: 8GB+ RAM, GPU with 4GB+ VRAM
- **Storage**: 2-4GB for models and cache

## 🤝 Contributing

1. **Adding New Legal Patterns**
   - Edit `entity_extractor.py` → `_create_legal_patterns()`
   - Add patterns to spaCy matcher

2. **Improving Legal-BERT**
   - Modify `legal_bert_pipeline.py`
   - Add new analysis methods
   - Integrate additional legal models

3. **Enhancing Compliance Rules**
   - Update `compliance_analyzer.py`
   - Add new recommendation generators
   - Improve risk assessment logic

## 📄 License

This AI engine is part of the Compliance Auditor project. Please refer to the main project license.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Run `python test_ai_engine.py` to diagnose problems
3. Review server logs for detailed error messages
4. Open an issue in the project repository