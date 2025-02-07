from flask import Blueprint, redirect
from flask_login import login_required

# Create a Blueprint for Spark Agent routes
spark_agent = Blueprint('spark_agent', __name__)

@spark_agent.route('/spark-agent', methods=['GET'])
@login_required
def spark_agent_redirect():
    """
    Redirect to the external Spark Agent web application.
    Only accessible to authenticated users.

    Returns:
        Redirect to the Spark Agent web application
    """
    return redirect('https://agentonaspark.netlify.app')
