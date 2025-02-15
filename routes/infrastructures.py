from flask import Blueprint, render_template, request, jsonify
from models import Infrastructure, db
from utils.permissions import permission_required, Permission
from flask_login import login_required
from sqlalchemy.exc import SQLAlchemyError

infrastructures_bp = Blueprint('infrastructures', __name__)

@infrastructures_bp.route('/infrastructures')
@login_required
@permission_required(Permission.VIEW_INFRASTRUCTURES)
def liste_infrastructures():
    """
    Render the list of infrastructures with filtering capabilities.
    
    Returns:
        Rendered template with infrastructures and their types
    """
    # Fetch all infrastructures
    infrastructures = Infrastructure.query.all()
    
    # Predefined infrastructure types
    infrastructure_types = [
        "Station d'épuration",
        "Station de relevage", 
        "Station de pompage"
    ]
    
    return render_template(
        'departement/exploitation/infrastructures/liste_infrastructures.html', 
        infrastructures=infrastructures,
        infrastructure_types=infrastructure_types
    )

@infrastructures_bp.route('/create', methods=['POST'])
@login_required
@permission_required(Permission.CREATE_INFRASTRUCTURE)
def create_infrastructure():
    """
    Create a new infrastructure entry
    
    Expected JSON payload:
    {
        'nom': str,
        'type': str,
        'localisation': str,
        'capacite': float,
        'etat': str,
        'epuration_type': str (optional)
    }
    """
    # Ensure JSON data is received
    if not request.is_json:
        return jsonify({
            'success': False, 
            'message': 'Requête invalide. Données JSON requises.'
        }), 400
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['nom', 'type', 'localisation', 'capacite', 'etat']
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                'success': False, 
                'message': f'Le champ {field} est requis'
            }), 400
    
    try:
        # Create new infrastructure instance
        new_infrastructure = Infrastructure(
            nom=data['nom'],
            type=data['type'],
            localisation=data['localisation'],
            capacite=float(data['capacite']),
            etat=data['etat'],
            epuration_type=data.get('epuration_type')
        )
        
        # Add and commit to database
        db.session.add(new_infrastructure)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Infrastructure créée avec succès',
            'infrastructure_id': new_infrastructure.id
        }), 201
    
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': 'Erreur lors de la création de l\'infrastructure',
            'error': str(e)
        }), 500
    except ValueError:
        return jsonify({
            'success': False, 
            'message': 'Capacité invalide'
        }), 400
