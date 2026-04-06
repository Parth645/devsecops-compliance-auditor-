"""
Policy Processing Configuration
"""

# Model Configuration
POLICY_PROCESSING_CONFIG = {
    # Use lightweight models for faster processing
    "use_lightweight_models": True,
    
    # Model selection
    "models": {
        "text_classifier": {
            "lightweight": "facebook/bart-large-mnli",  # Zero-shot classification
            "full": "microsoft/DialoGPT-medium"
        },
        "qa_pipeline": {
            "lightweight": "distilbert-base-cased-distilled-squad",
            "full": "deepset/roberta-base-squad2"
        },
        "summarizer": {
            "lightweight": "sshleifer/distilbart-cnn-6-6",  # Smaller distilled model
            "full": "facebook/bart-large-cnn"
        }
    },
    
    # Processing options
    "processing": {
        "max_text_length": 2000,  # Max text length for AI processing
        "min_confidence": 0.3,     # Minimum confidence for AI predictions
        "max_rules_per_policy": 50, # Limit rules generated per policy
        "enable_summarization": True,
        "enable_qa_extraction": True
    },
    
    # Performance options
    "performance": {
        "batch_size": 1,
        "use_gpu": False,  # Set to True if GPU available
        "num_workers": 1
    }
}


def get_model_name(model_type: str, use_lightweight: bool = True) -> str:
    """
    Get the appropriate model name based on configuration
    
    Args:
        model_type: Type of model (text_classifier, qa_pipeline, summarizer)
        use_lightweight: Whether to use lightweight models
        
    Returns:
        Model name/identifier
    """
    models = POLICY_PROCESSING_CONFIG["models"].get(model_type, {})
    
    if use_lightweight:
        return models.get("lightweight", models.get("full"))
    else:
        return models.get("full", models.get("lightweight"))


def should_use_lightweight() -> bool:
    """Check if lightweight models should be used"""
    return POLICY_PROCESSING_CONFIG.get("use_lightweight_models", True)


def get_processing_config() -> dict:
    """Get processing configuration"""
    return POLICY_PROCESSING_CONFIG.get("processing", {})


def get_performance_config() -> dict:
    """Get performance configuration"""
    return POLICY_PROCESSING_CONFIG.get("performance", {})
