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

@infrastructures.route('/infrastructure/<int:id>/details', methods=['GET'])
@login_required
def get_infrastructure_details(id):
    try:
        infrastructure = Infrastructure.query.get_or_404(id)
        
        # Convert infrastructure to dictionary for JSON response
        infrastructure_details = {
            'id': infrastructure.id,
            'nom': infrastructure.nom,
            'type': infrastructure.type,
            'localisation': infrastructure.localisation,
            'capacite': infrastructure.capacite,
            'etat': infrastructure.etat
        }
        
        return jsonify(infrastructure_details)
    except Exception as e:
        logger.error(f"Error retrieving infrastructure details: {str(e)}")
        return jsonify({'error': 'Impossible de récupérer les détails de l\'infrastructure'}), 404

@infrastructures.route('/infrastructure/<int:id>/upload-files', methods=['POST'])
@login_required
def upload_infrastructure_files(id):
    try:
        infrastructure = Infrastructure.query.get_or_404(id)
        
        # Check if files are present
        if 'files' not in request.files:
            return jsonify({'error': 'Aucun fichier téléchargé'}), 400
        
        files = request.files.getlist('files')
        
        # Create a directory for infrastructure files if it doesn't exist
        import os
        upload_dir = os.path.join('static', 'uploads', 'infrastructures', str(id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Sanitize location for filename (remove spaces, special characters)
        import re
        def sanitize_filename(text):
            # Remove non-alphanumeric characters and convert to lowercase
            return re.sub(r'[^\w\s-]', '', text.lower().replace(' ', '_'))
        
        # Save each file
        saved_files = []
        for index, file in enumerate(files, 1):
            if file.filename == '':
                continue
            
            # Generate a unique filename with infrastructure number and location
            from werkzeug.utils import secure_filename
            file_extension = os.path.splitext(file.filename)[1]
            
            # Sanitize location for filename
            sanitized_location = sanitize_filename(infrastructure.localisation)
            
            # Create new filename: infra{id}_{location}_{index}{extension}
            new_filename = f"infra{id}_{sanitized_location}_{index}{file_extension}"
            file_path = os.path.join(upload_dir, new_filename)
            file.save(file_path)
            
            # Store relative path for frontend
            relative_path = os.path.join('uploads', 'infrastructures', str(id), new_filename)
            saved_files.append({
                'name': new_filename,  # Use the new filename
                'original_name': file.filename,  # Keep original filename for reference
                'path': relative_path,
                'type': file.content_type,
                'location': infrastructure.localisation  # Add location information
            })
        
        return jsonify({
            'message': f'{len(saved_files)} fichier(s) téléchargé(s) avec succès',
            'files': saved_files
        }), 200
    
    except Exception as e:
        logger.error(f"Error uploading infrastructure files: {str(e)}")
        return jsonify({'error': 'Erreur lors du téléchargement des fichiers'}), 500

@infrastructures.route('/infrastructure/<int:id>/files', methods=['GET'])
@login_required
def get_infrastructure_files(id):
    try:
        # Get the infrastructure to ensure we have location information
        infrastructure = Infrastructure.query.get_or_404(id)
        
        # Create a directory for infrastructure files
        import os
        upload_dir = os.path.join('static', 'uploads', 'infrastructures', str(id))
        
        # If directory doesn't exist, return empty list
        if not os.path.exists(upload_dir):
            return jsonify({'files': []}), 200
        
        # Get all files in the directory
        files = []
        for filename in os.listdir(upload_dir):
            file_path = os.path.join('/static', 'uploads', 'infrastructures', str(id), filename)
            files.append({
                'name': filename,
                'path': file_path,
                'type': 'image' if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) else 'pdf',
                'location': infrastructure.localisation  # Add location information
            })
        
        return jsonify({'files': files}), 200
    
    except Exception as e:
        logger.error(f"Error retrieving infrastructure files: {str(e)}")
        return jsonify({'error': 'Impossible de récupérer les fichiers'}), 500
