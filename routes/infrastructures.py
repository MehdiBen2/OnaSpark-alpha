from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, Infrastructure
from sqlalchemy.exc import SQLAlchemyError
import logging
import os
from PIL import Image
import io
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

infrastructures = Blueprint('infrastructures', __name__, url_prefix='/departements')

def compress_image(input_path, output_path, max_size=(1920, 1080), quality=85, max_file_size_kb=500):
    """
    Compress and resize an image while maintaining aspect ratio.
    
    Args:
        input_path (str): Path to the input image
        output_path (str): Path to save the compressed image
        max_size (tuple): Maximum width and height
        quality (int): JPEG compression quality (1-95)
        max_file_size_kb (int): Maximum file size in kilobytes
    
    Returns:
        dict: Compression details
    """
    try:
        # Open the image
        with Image.open(input_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize image while maintaining aspect ratio
            img.thumbnail(max_size, Image.LANCZOS)
            
            # Dynamically adjust quality to meet file size constraint
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            file_size = buffer.tell() / 1024  # Size in KB
            
            # Adjust quality if file is too large
            attempts = 0
            while file_size > max_file_size_kb and attempts < 5:
                quality -= 5
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=quality, optimize=True)
                file_size = buffer.tell() / 1024
                attempts += 1
            
            # Save the compressed image
            img.save(output_path, format='JPEG', quality=quality, optimize=True)
            
            return {
                'original_size': os.path.getsize(input_path) / 1024,
                'compressed_size': file_size,
                'quality': quality,
                'dimensions': img.size
            }
    except Exception as e:
        logger.error(f"Image compression error: {str(e)}")
        return None

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
        upload_dir = os.path.join('static', 'uploads', 'infrastructures', str(id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Sanitize location for filename (remove spaces, special characters)
        def sanitize_filename(text):
            return re.sub(r'[^\w\s-]', '', text.lower().replace(' ', '_'))
        
        # Save each file
        saved_files = []
        for index, file in enumerate(files, 1):
            if file.filename == '':
                continue
            
            # Generate a unique filename with infrastructure number and location
            file_extension = os.path.splitext(file.filename)[1].lower()
            sanitized_location = sanitize_filename(infrastructure.localisation)
            
            # Create new filename: infra{id}_{location}_{index}{extension}
            new_filename = f"infra{id}_{sanitized_location}_{index}{file_extension}"
            temp_path = os.path.join(upload_dir, f"temp_{new_filename}")
            file.save(temp_path)
            
            # Compress image if it's an image file
            compression_result = None
            if file_extension in ['.jpg', '.jpeg', '.png']:
                try:
                    final_path = os.path.join(upload_dir, new_filename)
                    compression_result = compress_image(temp_path, final_path)
                    os.remove(temp_path)  # Remove temporary file
                except Exception as e:
                    logger.warning(f"Compression failed for {new_filename}: {str(e)}")
                    # Use original file if compression fails
                    final_path = os.path.join(upload_dir, new_filename)
                    os.rename(temp_path, final_path)
            else:
                # For non-image files, just rename
                final_path = os.path.join(upload_dir, new_filename)
                os.rename(temp_path, final_path)
            
            # Store relative path for frontend
            relative_path = os.path.join('uploads', 'infrastructures', str(id), new_filename)
            saved_files.append({
                'name': new_filename,
                'original_name': file.filename,
                'path': relative_path,
                'type': file.content_type,
                'location': infrastructure.localisation,
                'compression': compression_result
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
        all_files = []
        for filename in sorted(os.listdir(upload_dir)):
            # Skip temporary or hidden files
            if filename.startswith('.') or filename.startswith('temp_'):
                continue
            
            file_path = os.path.join('/static', 'uploads', 'infrastructures', str(id), filename)
            file_info = {
                'name': filename,
                'path': file_path,
                'type': 'image' if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) else 'pdf',
                'location': infrastructure.localisation,
                'uploaded_at': os.path.getctime(os.path.join(upload_dir, filename))
            }
            all_files.append(file_info)
        
        # Sort files by upload time (newest first)
        all_files.sort(key=lambda x: x['uploaded_at'], reverse=True)
        
        # Separate images and PDFs
        image_files = [f for f in all_files if f['type'].startswith('image')]
        pdf_files = [f for f in all_files if f['type'] == 'pdf']
        
        # Limit images to 10 most recent
        image_files = image_files[:10]
        
        # Combine and return files
        files = image_files + pdf_files
        
        return jsonify({
            'files': files,
            'total_images': len(all_files),
            'max_images_displayed': 10
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving infrastructure files: {str(e)}")
        return jsonify({'error': 'Impossible de récupérer les fichiers'}), 500
