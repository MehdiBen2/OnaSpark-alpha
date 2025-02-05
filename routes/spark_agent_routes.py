from flask import Blueprint, jsonify, request
from flask_login import login_required
import os
import requests
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
    default_model = os.getenv('DEFAULT_AI_MODEL', 'anthropic/claude-3-haiku:beta')
    return jsonify({'default_model': default_model})

@spark_agent.route('/proxy/chat-completion', methods=['POST'])
def proxy_chat_completion():
    """
    Proxy route for OpenRouter AI chat completions to bypass CORS
    """
    try:
        # Log incoming request details
        logger.debug("Received chat completion request")
        
        # Get the request data from the client
        request_data = request.get_json()
        logger.debug(f"Received request data: {request_data}")

        # Retrieve API key from environment variable
        openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        
        # Validate API key
        if not openrouter_api_key:
            logger.error("OpenRouter API key is not configured")
            return jsonify({
                'error': 'OpenRouter API key is not configured',
                'details': 'No API key found in environment variables'
            }), 500

        # Validate request data
        if not request_data:
            logger.error("No request data provided")
            return jsonify({
                'error': 'Invalid request',
                'details': 'No request data provided'
            }), 400

        # Prepare headers for OpenRouter API
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {openrouter_api_key}',
            'HTTP-Referer': 'https://onaspark.com',
            'X-Title': 'OnaSpark Spark Agent'
        }

        # Log request details (be careful with sensitive data)
        logger.debug(f"OpenRouter API Request:")
        logger.debug(f"Model: {request_data.get('model', 'No model specified')}")
        logger.debug(f"API Key Length: {len(openrouter_api_key)}")
        logger.debug(f"Message Count: {len(request_data.get('messages', []))}")

        # Make the request to OpenRouter
        try:
            logger.debug("Attempting to send request to OpenRouter API")
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions', 
                json=request_data, 
                headers=headers,
                timeout=30  # Add a timeout to prevent hanging
            )

            # Log full response details
            logger.debug(f"OpenRouter API Response:")
            logger.debug(f"Status Code: {response.status_code}")
            logger.debug(f"Response Headers: {response.headers}")
            logger.debug(f"Response Text: {response.text}")
            
            # Check if the request was successful
            response.raise_for_status()

            # Parse and return the response
            response_json = response.json()
            logger.debug(f"Parsed Response: {response_json}")
            return jsonify(response_json)

        except requests.exceptions.RequestException as api_error:
            # More detailed error logging
            logger.error(f"OpenRouter API Request Error: {str(api_error)}")
            logger.error(traceback.format_exc())
            
            # If possible, get the response text for more details
            try:
                error_details = api_error.response.text
            except:
                error_details = str(api_error)

            return jsonify({
                'error': 'Failed to communicate with OpenRouter API',
                'details': error_details,
                'api_error_type': type(api_error).__name__,
                'traceback': traceback.format_exc()
            }), 500

    except Exception as e:
        # Catch-all for any unexpected errors
        logger.error(f"Unexpected Error in Proxy Route: {str(e)}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            'error': 'Unexpected server error',
            'details': str(e),
            'traceback': traceback.format_exc()
        }), 500
