from flask import Blueprint, render_template
from models import Infrastructure
from utils.permissions import permission_required, Permission

infrastructures_bp = Blueprint('infrastructures', __name__)

@infrastructures_bp.route('/liste-infrastructures')
@permission_required(Permission.VIEW_ALL_CENTERS)
def liste_infrastructures():
    """
    Render the list of infrastructures with filtering capabilities.
    
    Returns:
        Rendered template with infrastructures and their types
    """
    # Fetch all infrastructures
    infrastructures = Infrastructure.query.all()
    
    # Get unique infrastructure types
    infrastructure_types = sorted(set(infra.type for infra in infrastructures))
    
    return render_template(
        'departement/exploitation/infrastructures/liste_infrastructures.html', 
        infrastructures=infrastructures,
        infrastructure_types=infrastructure_types
    )
