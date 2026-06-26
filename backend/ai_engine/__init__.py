# AI Engine for Legal Compliance Detection
# Using lazy imports to avoid loading heavy dependencies (torch, transformers) until needed

__all__ = ['LegalBERTPipeline', 'ComplianceAnalyzer', 'LegalEntityExtractor']

def __getattr__(name):
    """Lazy load components on demand"""
    if name == 'LegalBERTPipeline':
        from .legal_bert_pipeline import LegalBERTPipeline
        return LegalBERTPipeline
    elif name == 'ComplianceAnalyzer':
        from .compliance_analyzer import ComplianceAnalyzer
        return ComplianceAnalyzer
    elif name == 'LegalEntityExtractor':
        from .entity_extractor import LegalEntityExtractor
        return LegalEntityExtractor
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")