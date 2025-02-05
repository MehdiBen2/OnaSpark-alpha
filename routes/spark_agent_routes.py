from flask import Blueprint, jsonify
from flask_login import login_required
import os

# Create a Blueprint for Spark Agent routes
spark_agent = Blueprint('spark_agent', __name__)

@spark_agent.route('/get-openrouter-api-key', methods=['GET'])
@login_required
def get_openrouter_api_key():
    """
    Endpoint to fetch OpenRouter API key for frontend use.
    Only accessible to authenticated users.

    Returns:
        JSON response with API key or error message
    """
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        return jsonify({'error': 'API key not configured'}), 500
    
    return jsonify({'api_key': api_key})

@spark_agent.route('/get-default-model', methods=['GET'])
@login_required
def get_default_model_route():
    """
    Endpoint to fetch the default AI model configuration.
    Only accessible to authenticated users.

    Returns:
        JSON response with default model name
    """
<<<<<<< HEAD
    default_model = os.getenv('DEFAULT_AI_MODEL', 'google/gemini-exp-1114:free')
=======
    default_model = os.getenv('DEFAULT_AI_MODEL', 'mistral-small')
>>>>>>> parent of 091ba5e (edit)
    return jsonify({'default_model': default_model})
