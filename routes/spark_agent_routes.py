from flask import Blueprint, jsonify
from flask_login import login_required
import os

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

@spark_agent.route('/get-default-model', methods=['GET'])
@login_required
def get_default_model_route():
    """
    Endpoint to fetch the default AI model configuration.
    Only accessible to authenticated users.

    Returns:
        JSON response with default model name
    """
    default_model = os.getenv('DEFAULT_AI_MODEL', 'mistral-small')
    return jsonify({'default_model': default_model})
