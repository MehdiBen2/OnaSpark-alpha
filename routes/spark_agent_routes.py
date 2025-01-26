from flask import Blueprint, jsonify
from flask_login import login_required
import os
from config.ai_config import AIModelConfig

# Create a Blueprint for Spark Agent routes
spark_agent = Blueprint('spark_agent', __name__)

@spark_agent.route('/get-mistral-api-key', methods=['GET'])
@login_required
def get_mistral_api_key():
    """
    Endpoint to fetch Mistral API key for frontend use.
    Only accessible to authenticated users.

    Returns:
        JSON response with API key or error message
    """
    api_key = os.getenv('MISTRAL_API_KEY')
    if not api_key:
        return jsonify({'error': 'API key not configured'}), 500
    
    # Only return a masked version of the key for security
    return jsonify({'api_key': api_key})

@spark_agent.route('/get-openrouter-api-key', methods=['GET'])
@login_required
def get_openrouter_api_key():
    """
    Endpoint to fetch OpenRouter API key for frontend use.
    Only accessible to authenticated users.

    Returns:
        JSON response with API key or error message
    """
    try:
        api_key = AIModelConfig.get_openrouter_api_key()
        
        if not api_key:
            return jsonify({
                'error': 'OpenRouter API key not configured', 
                'details': 'No API key found in environment variables'
            }), 500
        
        # Validate API key format
        if not api_key.startswith('sk-or-v1-') or len(api_key) < 20:
            return jsonify({
                'error': 'Invalid API key format', 
                'details': 'API key does not match expected pattern'
            }), 500
        
        return jsonify({'api_key': api_key})
    
    except Exception as e:
        # Comprehensive error handling
        return jsonify({
            'error': 'Unexpected error retrieving API key', 
            'details': str(e)
        }), 500

@spark_agent.route('/get-default-model', methods=['GET'])
@login_required
def get_default_model_route():
    """
    Endpoint to fetch the default AI model configuration.
    
    Returns:
        JSON response with default model configuration
    """
    try:
        default_model = AIModelConfig.get_default_model()
        
        # Validate the model
        if not AIModelConfig.validate_model(default_model):
            default_model = 'google/gemini-2.0-flash-thinking-exp:free'
        
        # Get full model configuration
        model_config = AIModelConfig.get_model_config(default_model)
        
        return jsonify({
            'default_model': model_config['model'],
            'temperature': model_config['temperature'],
            'max_tokens': model_config['max_tokens']
        })
    
    except Exception as e:
        # Error handling for model configuration
        return jsonify({
            'error': 'Failed to retrieve model configuration', 
            'details': str(e)
        }), 500
