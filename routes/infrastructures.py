from flask import Blueprint, render_template, request, jsonify
from models import Infrastructure, db, InfrastructureFile
from utils.permissions import permission_required, Permission
from flask_login import login_required
from sqlalchemy.exc import SQLAlchemyError
import os
from werkzeug.utils import secure_filename
from flask import current_app
import json

infrastructures_bp = Blueprint('infrastructures', __name__)

# Configure file upload settings
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension
    
    Args:
        filename (str): Name of the uploaded file
    
    Returns:
        bool: True if file is allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_infrastructure_file(file, infrastructure_id):
    """
    Save an uploaded file for an infrastructure
    
    Args:
        file (FileStorage): Uploaded file
        infrastructure_id (int): ID of the associated infrastructure
    
    Returns:
        InfrastructureFile: Created file record
    """
    if not file or not allowed_file(file.filename):
        return None
    
    # Ensure upload directory exists
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'infrastructures', str(infrastructure_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    # Secure filename and save
    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    
    # Determine file type and mime type
    file_type = 'image' if filename.lower().split('.')[-1] in {'png', 'jpg', 'jpeg', 'gif'} else 'pdf'
    mime_type = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'pdf': 'application/pdf'
    }[filename.lower().split('.')[-1]]
    
    # Create file record
    new_file = InfrastructureFile(
        infrastructure_id=infrastructure_id,
        filename=filename,
        filepath=filepath.replace(current_app.root_path, ''),
        file_type=file_type,
        mime_type=mime_type,
        file_size=os.path.getsize(filepath)
    )
    
    return new_file

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
    Create a new infrastructure entry with optional file uploads
    
    Expected JSON payload:
    {
        'nom': str,
        'type': str,
        'localisation': str,
        'capacite': float,
        'etat': str,
        'epuration_type': str (optional)
    }
    
    Optional multipart form data for files
    """
    # Ensure JSON data is received
    if not request.is_json and not request.form:
        return jsonify({
            'success': False, 
            'message': 'Requête invalide. Données JSON ou formulaire requis.'
        }), 400
    
    # Handle JSON or form data
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    
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
        
        # Add and commit to database to get ID
        db.session.add(new_infrastructure)
        db.session.commit()
        
        # Handle file uploads
        associated_files = []
        if 'files' in request.files:
            for file in request.files.getlist('files'):
                if file and allowed_file(file.filename):
                    # Check file size
                    file.seek(0, os.SEEK_END)
                    file_size = file.tell()
                    file.seek(0)
                    
                    if file_size > MAX_FILE_SIZE:
                        db.session.rollback()
                        return jsonify({
                            'success': False,
                            'message': f'Fichier {file.filename} trop volumineux. Limite de 10 Mo.'
                        }), 400
                    
                    # Save file and create record
                    infrastructure_file = save_infrastructure_file(file, new_infrastructure.id)
                    if infrastructure_file:
                        db.session.add(infrastructure_file)
                        associated_files.append(infrastructure_file)
        
        # Commit file records
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Infrastructure créée avec succès',
            'infrastructure_id': new_infrastructure.id,
            'files_uploaded': len(associated_files)
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

@infrastructures_bp.route('/<int:infrastructure_id>/details')
@login_required
@permission_required(Permission.VIEW_INFRASTRUCTURES)
def get_infrastructure_details(infrastructure_id):
    """
    Fetch details of a specific infrastructure by ID, including associated files
    
    Args:
        infrastructure_id (int): ID of the infrastructure to retrieve
    
    Returns:
        JSON response with infrastructure details and files or error message
    """
    try:
        infrastructure = Infrastructure.query.get_or_404(infrastructure_id)
        
        # Fetch associated files
        files = infrastructure.infrastructure_files.all()
        file_details = []
        
        for file in files:
            file_details.append({
                'id': file.id,
                'filename': file.filename,
                'filepath': file.filepath,
                'file_type': file.file_type,
                'mime_type': file.mime_type,
                'file_size': file.file_size,
                'file_size_human': file.get_file_size_human_readable()
            })
        
        return jsonify({
            'id': infrastructure.id,
            'nom': infrastructure.nom,
            'type': infrastructure.type,
            'localisation': infrastructure.localisation,
            'capacite': infrastructure.capacite,
            'etat': infrastructure.etat,
            'epuration_type': infrastructure.epuration_type,
            'files': file_details
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': 'Impossible de récupérer les détails de l\'infrastructure',
            'error': str(e)
        }), 404

@infrastructures_bp.route('/<int:infrastructure_id>/edit', methods=['POST'])
@login_required
@permission_required(Permission.EDIT_INFRASTRUCTURE)
def edit_infrastructure(infrastructure_id):
    """
    Edit an existing infrastructure entry with optional file uploads and deletions
    
    Expected multipart form data:
    - infrastructure details (nom, type, localisation, etc.)
    - files: new files to upload
    - deleted_files: JSON list of file IDs to delete
    """
    try:
        # Find the existing infrastructure
        infrastructure = Infrastructure.query.get_or_404(infrastructure_id)
        
        # Validate and process form data
        data = request.form
        
        # Validate required fields
        required_fields = ['nom', 'type', 'localisation', 'capacite', 'etat']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False, 
                    'message': f'Le champ {field} est requis'
                }), 400
        
        # Update infrastructure details
        infrastructure.nom = data['nom']
        infrastructure.type = data['type']
        infrastructure.localisation = data['localisation']
        infrastructure.capacite = float(data['capacite'])
        infrastructure.etat = data['etat']
        infrastructure.epuration_type = data.get('epuration_type')
        
        # Handle file deletions
        deleted_files = json.loads(data.get('deleted_files', '[]'))
        if deleted_files:
            # Find and delete specified files
            files_to_delete = InfrastructureFile.query.filter(
                InfrastructureFile.id.in_(deleted_files),
                InfrastructureFile.infrastructure_id == infrastructure_id
            ).all()
            
            for file_record in files_to_delete:
                # Remove physical file
                try:
                    os.remove(os.path.join(current_app.root_path, file_record.filepath.lstrip('/')))
                except FileNotFoundError:
                    pass  # File already deleted or doesn't exist
                
                # Remove database record
                db.session.delete(file_record)
        
        # Handle new file uploads
        associated_files = []
        if 'files' in request.files:
            for file in request.files.getlist('files'):
                if file and allowed_file(file.filename):
                    # Check file size
                    file.seek(0, os.SEEK_END)
                    file_size = file.tell()
                    file.seek(0)
                    
                    if file_size > MAX_FILE_SIZE:
                        return jsonify({
                            'success': False,
                            'message': f'Fichier {file.filename} trop volumineux. Limite de 10 Mo.'
                        }), 400
                    
                    # Save file and create record
                    infrastructure_file = save_infrastructure_file(file, infrastructure.id)
                    if infrastructure_file:
                        db.session.add(infrastructure_file)
                        associated_files.append(infrastructure_file)
        
        # Commit changes
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Infrastructure mise à jour avec succès',
            'infrastructure_id': infrastructure.id,
            'files_uploaded': len(associated_files),
            'files_deleted': len(deleted_files)
        }), 200
    
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': 'Erreur lors de la mise à jour de l\'infrastructure',
            'error': str(e)
        }), 500
    except ValueError:
        return jsonify({
            'success': False, 
            'message': 'Capacité invalide'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': 'Une erreur inattendue est survenue',
            'error': str(e)
        }), 500
