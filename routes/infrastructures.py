from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, Infrastructure
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

infrastructures = Blueprint('infrastructures', __name__, url_prefix='/departements')

@infrastructures.route('/infrastructures', methods=['GET'])
@login_required
def list_infrastructures():
    try:
        infrastructures = Infrastructure.query.all()
        return render_template('departement/exploitation/infrastructures/infrastructures.html', 
                               infrastructures=infrastructures)
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error listing infrastructures: {str(e)}")
        return jsonify({'error': str(e)}), 500

@infrastructures.route('/infrastructure/create', methods=['POST'])
@login_required
def create_infrastructure():
    try:
        # Log the incoming request data for debugging
        logger.info(f"Received infrastructure create request from user {current_user.username}")
        logger.info(f"Request data: {request.get_json()}")
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['nom', 'type', 'localisation', 'capacite', 'etat']
        for field in required_fields:
            if not data.get(field):
                logger.warning(f"Missing required field: {field}")
                return jsonify({'error': f'Champ requis manquant: {field}'}), 400
        
        # Create new infrastructure
        new_infrastructure = Infrastructure(
            nom=data['nom'],
            type=data['type'],
            localisation=data['localisation'],
            capacite=float(data['capacite']),
            etat=data['etat']
        )
        
        db.session.add(new_infrastructure)
        db.session.commit()
        
        logger.info(f"Infrastructure '{new_infrastructure.nom}' created successfully")
        
        return jsonify({
            'message': 'Infrastructure créée avec succès', 
            'id': new_infrastructure.id
        }), 201
    
    except ValueError as ve:
        logger.error(f"Value error: {str(ve)}")
        return jsonify({'error': 'Capacité doit être un nombre valide'}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Une erreur inattendue est survenue'}), 500

@infrastructures.route('/infrastructures/delete/<int:id>', methods=['DELETE'])
@login_required
def delete_infrastructure(id):
    """
    Delete an infrastructure by its ID.
    
    Args:
        id (int): The ID of the infrastructure to delete.
    
    Returns:
        JSON response with a success or error message.
    """
    try:
        # Find the infrastructure by ID
        infrastructure = Infrastructure.query.get_or_404(id)
        
        # Delete the infrastructure
        db.session.delete(infrastructure)
        db.session.commit()
        
        return jsonify({
            'message': 'Infrastructure supprimée avec succès.',
            'status': 'success'
        }), 200
    
    except Exception as e:
        # Rollback the session in case of error
        db.session.rollback()
        
        # Log the full error for server-side debugging
        logger.error(f"Erreur lors de la suppression de l'infrastructure {id}: {str(e)}", exc_info=True)
        
        return jsonify({
            'message': f'Erreur lors de la suppression: {str(e)}',
            'status': 'error'
        }), 500
