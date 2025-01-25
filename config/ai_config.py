"""
AI Configuration Module

This module manages configuration settings for AI-related services.
"""

import os
from typing import Optional

def get_default_model() -> str:
    """
    Retrieve the default AI model from environment variables.
    
    Returns:
        str: Default AI model name, with a fallback to 'mistral-small'
    """
    return os.getenv('DEFAULT_MODEL', 'mistral-small')

def get_mistral_api_key() -> Optional[str]:
    """
    Retrieve the Mistral API key from environment variables.
    
    Returns:
        Optional[str]: Mistral API key or None if not set
    """
    return os.getenv('MISTRAL_API_KEY')

def validate_model(model: str) -> bool:
    """
    Validate if the provided model is supported.
    
    Args:
        model (str): Model name to validate
    
    Returns:
        bool: True if model is supported, False otherwise
    """
    SUPPORTED_MODELS = [
        'mistral-small', 
        'mistral-medium', 
        'mistral-large'
    ]
    return model in SUPPORTED_MODELS
