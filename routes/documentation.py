from flask import Blueprint, render_template
from flask_login import login_required

documentation = Blueprint('documentation', __name__)

@documentation.route('/documentation')
@login_required
def view_documentation():
    """
    Render the documentation page.
    
    Returns:
        Rendered documentation template
    """
    return render_template('docs/documentation_fr.html')
