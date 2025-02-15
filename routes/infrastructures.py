from flask import Blueprint, render_template, request, jsonify, current_app
from models import Infrastructure, db, InfrastructureFile
from utils.permissions import permission_required, Permission
from flask_login import login_required
import os
from werkzeug.utils import secure_filename
import json
import uuid

infrastructures_bp = Blueprint('infrastructures', __name__)

# File upload settings
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file, infrastructure_id):
    """Simple file save function that handles both images and PDFs"""
    if not file or not allowed_file(file.filename):
        current_app.logger.warning(f"File not allowed or empty: {file.filename if file else 'No file'}")
        return None
    
    try:
        # Create upload directory
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'infrastructures', str(infrastructure_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex[:8]}_{secure_filename(file.filename)}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        
        # Determine file type
        file_type = 'image' if ext in {'png', 'jpg', 'jpeg', 'gif'} else 'pdf'
        mime_type = 'image/' + ext if file_type == 'image' else 'application/pdf'
        
        # Convert to relative path for storage
        relative_path = file_path.replace(current_app.root_path, '').replace('\\', '/')
        
        current_app.logger.info(f"File saved: {unique_filename}, Type: {file_type}, Size: {file_size} bytes")
        
        return InfrastructureFile(
            infrastructure_id=infrastructure_id,
            filename=unique_filename,
            filepath=relative_path,
            file_type=file_type,
            mime_type=mime_type,
            file_size=file_size
        )
    except Exception as e:
        current_app.logger.error(f"Error saving file {file.filename}: {str(e)}")
        return None

@infrastructures_bp.route('/')
@login_required
@permission_required(Permission.VIEW_INFRASTRUCTURES)
def liste_infrastructures():
    """List all infrastructures"""
    infrastructures = Infrastructure.query.all()
    infrastructure_types = ["Station d'épuration", "Station de relevage", "Station de pompage"]
    return render_template(
        'departement/exploitation/infrastructures/liste_infrastructures.html',
        infrastructures=infrastructures,
        infrastructure_types=infrastructure_types
    )

@infrastructures_bp.route('/create', methods=['POST'])
@login_required
@permission_required(Permission.CREATE_INFRASTRUCTURE)
def create_infrastructure():
    """Create new infrastructure with files"""
    try:
        # Validate form data
        data = request.form
        if not all(data.get(field) for field in ['nom', 'type', 'localisation', 'capacite', 'etat']):
            return jsonify({'success': False, 'message': 'Tous les champs sont requis'}), 400

        # Create infrastructure
        infrastructure = Infrastructure(
            nom=data['nom'],
            type=data['type'],
            localisation=data['localisation'],
            capacite=float(data['capacite']),
            etat=data['etat'],
            epuration_type=data.get('epuration_type')
        )
        db.session.add(infrastructure)
        db.session.flush()  # Get ID without committing

        # Handle file uploads
        files_uploaded = 0
        current_app.logger.info(f"Received files: {request.files}")
        if 'files' in request.files:
            for file in request.files.getlist('files'):
                current_app.logger.info(f"Processing file: {file.filename}")
                if file and file.filename:
                    if file.content_length > MAX_FILE_SIZE:
                        db.session.rollback()
                        return jsonify({'success': False, 'message': f'Fichier {file.filename} trop volumineux (max 10 Mo)'}), 400
                    
                    infra_file = save_file(file, infrastructure.id)
                    if infra_file:
                        db.session.add(infra_file)
                        files_uploaded += 1
                        current_app.logger.info(f"Successfully uploaded file: {file.filename}")
                    else:
                        current_app.logger.warning(f"Failed to save file: {file.filename}")

        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Infrastructure créée avec succès',
            'files_uploaded': files_uploaded
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@infrastructures_bp.route('/<int:infrastructure_id>/details')
@login_required
@permission_required(Permission.VIEW_INFRASTRUCTURES)
def get_infrastructure_details(infrastructure_id):
    """Get infrastructure details with files"""
    try:
        infrastructure = Infrastructure.query.get_or_404(infrastructure_id)
        files = [{
            'id': f.id,
            'filename': f.filename,
            'filepath': f.filepath,
            'file_type': f.file_type,
            'size': f.get_file_size_human_readable()
        } for f in infrastructure.infrastructure_files]

        return jsonify({
            'id': infrastructure.id,
            'nom': infrastructure.nom,
            'type': infrastructure.type,
            'localisation': infrastructure.localisation,
            'capacite': infrastructure.capacite,
            'etat': infrastructure.etat,
            'epuration_type': infrastructure.epuration_type,
            'files': files
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 404

@infrastructures_bp.route('/<int:infrastructure_id>/edit', methods=['POST'])
@login_required
@permission_required(Permission.EDIT_INFRASTRUCTURE)
def edit_infrastructure(infrastructure_id):
    """Edit infrastructure and manage files"""
    try:
        infrastructure = Infrastructure.query.get_or_404(infrastructure_id)
        data = request.form

        # Update basic info
        if not all(data.get(field) for field in ['nom', 'type', 'localisation', 'capacite', 'etat']):
            return jsonify({'success': False, 'message': 'Tous les champs sont requis'}), 400

        infrastructure.nom = data['nom']
        infrastructure.type = data['type']
        infrastructure.localisation = data['localisation']
        infrastructure.capacite = float(data['capacite'])
        infrastructure.etat = data['etat']
        infrastructure.epuration_type = data.get('epuration_type')

        # Handle file deletions
        files_deleted = 0
        try:
            deleted_files = json.loads(data.get('deleted_files', '[]'))
            if not isinstance(deleted_files, list):
                raise ValueError("deleted_files must be a list")

            for file_id in deleted_files:
                file = InfrastructureFile.query.get(int(file_id))
                if file and file.infrastructure_id == infrastructure_id:
                    # Delete physical file
                    file_path = os.path.join(current_app.root_path, file.filepath.lstrip('/'))
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    db.session.delete(file)
                    files_deleted += 1
        except Exception as e:
            current_app.logger.error(f"Error deleting files: {e}")

        # Handle new file uploads
        files_uploaded = 0
        current_app.logger.info(f"Received files: {request.files}")
        if 'files' in request.files:
            for file in request.files.getlist('files'):
                current_app.logger.info(f"Processing file: {file.filename}")
                if file and file.filename:
                    if file.content_length > MAX_FILE_SIZE:
                        return jsonify({'success': False, 'message': f'Fichier {file.filename} trop volumineux (max 10 Mo)'}), 400
                    
                    infra_file = save_file(file, infrastructure_id)
                    if infra_file:
                        db.session.add(infra_file)
                        files_uploaded += 1
                        current_app.logger.info(f"Successfully uploaded file: {file.filename}")
                    else:
                        current_app.logger.warning(f"Failed to save file: {file.filename}")

        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Infrastructure mise à jour avec succès',
            'files_uploaded': files_uploaded,
            'files_deleted': files_deleted
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
