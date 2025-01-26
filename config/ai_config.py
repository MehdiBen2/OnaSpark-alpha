"""
AI Configuration Module

This module manages configuration settings for AI-related services,
including model selection, API key management, and validation.
"""

import os
from typing import Optional, Dict, List, Any

class AIModelConfig:
    """
    Centralized configuration management for AI models and services.
    """
    
    # Supported AI models with their providers
    SUPPORTED_MODELS: Dict[str, List[str]] = {
        'openrouter': [
            'google/gemini-pro-1.5-exp',
            'google/gemini-2.0-flash-thinking-exp:free',
            'anthropic/claude-3-sonnet',
            'anthropic/claude-3-haiku',
            'mistral/mistral-large',
            'qwen/qwen-2-7b-instruct:free'
        ],
        'mistral': [
            'mistral-small', 
            'mistral-medium', 
            'mistral-large'
        ]
    }

    @classmethod
    def get_default_model(cls) -> str:
        """
        Retrieve the default AI model from environment variables.
        
        Returns:
            str: Default AI model name
        """
        return os.getenv('DEFAULT_MODEL', 'qwen/qwen-2-7b-instruct:free')

    @classmethod
    def get_openrouter_api_key(cls) -> Optional[str]:
        """
        Retrieve the OpenRouter API key from environment variables.
        
        Returns:
            Optional[str]: OpenRouter API key or None if not set
        """
        return os.getenv('OPENROUTER_API_KEY')

    @classmethod
    def validate_model(cls, model: str, provider: str = 'openrouter') -> bool:
        """
        Validate if the provided model is supported.
        
        Args:
            model (str): Model name to validate
            provider (str, optional): AI service provider. Defaults to 'openrouter'.
        
        Returns:
            bool: True if model is supported, False otherwise
        """
        return model in cls.SUPPORTED_MODELS.get(provider, [])

    @classmethod
    def get_model_config(cls, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate model-specific configuration.
        
        Args:
            model (Optional[str]): Specific model to configure. Uses default if None.
        
        Returns:
            Dict[str, Any]: Model configuration parameters
        """
        selected_model = model or cls.get_default_model()
        
        # Validate model
        if not cls.validate_model(selected_model):
            raise ValueError(f"Unsupported model: {selected_model}")
        
        return {
            'model': selected_model,
            'temperature': float(os.getenv('MODEL_TEMPERATURE', 0.7)),
            'max_tokens': int(os.getenv('MODEL_MAX_TOKENS', 300))
        }

    @classmethod
    def get_api_headers(cls) -> Dict[str, str]:
        """
        Generate API headers for OpenRouter requests.
        
        Returns:
            Dict[str, str]: API request headers
        """
        return {
            'HTTP-Referer': os.getenv('SITE_URL', 'https://ona-spark.dz'),
            'X-Title': os.getenv('SITE_NAME', 'OnaSpark Agent'),
            'Content-Type': 'application/json'
        }
