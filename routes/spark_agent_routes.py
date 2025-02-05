from flask import Blueprint, jsonify, render_template
from flask_login import login_required
import os

# Create a Blueprint for Spark Agent routes
spark_agent = Blueprint('spark_agent', __name__)

@spark_agent.route('/')
@login_required
def index():
    """
    Main route for Spark Agent page.
    
    Returns:
        Rendered Spark Agent template
    """
    return render_template('sparkagent/spark_agent.html')

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
        return jsonify({'error': 'OpenRouter API key not configured'}), 500
    
    # Return the full API key for debugging
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
    default_model = os.getenv('DEFAULT_AI_MODEL', 'deepseek/deepseek-r1-distill-llama-70b:free')
    site_url = os.getenv('SITE_URL', 'https://onaspark.onrender.com')
    site_name = os.getenv('SITE_NAME', 'OnaSpark')
    
    return jsonify({
        'default_model': default_model,
        'site_url': site_url,
        'site_name': site_name
    })
