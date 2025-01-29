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
    Delete an infrastructure by its ID and remove all associated files.
    
    Args:
        id (int): The ID of the infrastructure to delete.
    
    Returns:
        JSON response with a success or error message.
    """
    try:
        # Find the infrastructure by ID
        infrastructure = Infrastructure.query.get_or_404(id)
        
        # Create a directory path for infrastructure files
        import os
        import shutil
        
        upload_dir = os.path.join('static', 'uploads', 'infrastructures', str(id))
        
        # Remove associated files directory if it exists
        if os.path.exists(upload_dir):
            try:
                shutil.rmtree(upload_dir)
                logger.info(f"Deleted files directory for infrastructure {id}")
            except Exception as file_error:
                logger.error(f"Error deleting files for infrastructure {id}: {str(file_error)}")
        
        # Delete the infrastructure
        db.session.delete(infrastructure)
        db.session.commit()
        
        return jsonify({
            'message': 'Infrastructure et fichiers associés supprimés avec succès.',
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
    # Import necessary modules at the top of the function for comprehensive error tracking
    import os
    import re
    import traceback
    import sys
    import shutil
    
    try:
        # Validate infrastructure existence first
        infrastructure = Infrastructure.query.get_or_404(id)
        
        # Extensive logging for debugging
        logger.info(f"Starting file upload for infrastructure {id}")
        logger.info(f"Current user: {current_user.username}")
        
        # Log all request details for debugging
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request content type: {request.content_type}")
        
        # Comprehensive file retrieval
        try:
            files = request.files.getlist('files')
            logger.info(f"Request files keys: {list(request.files.keys())}")
        except Exception as file_list_error:
            logger.error(f"Error retrieving file list: {str(file_list_error)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'error': 'Erreur lors de la récupération des fichiers',
                'details': str(file_list_error)
            }), 400
        
        # Validate files
        if not files:
            logger.warning("No files found in the upload request")
            return jsonify({
                'error': 'Aucun fichier téléchargé',
                'details': 'La liste de fichiers est vide'
            }), 400
        
        # Validate each file
        valid_files = [f for f in files if f.filename]
        if not valid_files:
            logger.warning("No valid files found in the upload")
            return jsonify({
                'error': 'Aucun fichier valide téléchargé',
                'details': 'Tous les noms de fichiers sont vides'
            }), 400
        
        # Create upload directory with error handling
        try:
            upload_dir = os.path.join('static', 'uploads', 'infrastructures', str(id))
            os.makedirs(upload_dir, exist_ok=True)
        except Exception as dir_error:
            logger.error(f"Error creating upload directory: {str(dir_error)}")
            return jsonify({
                'error': 'Impossible de créer le répertoire de téléchargement',
                'details': str(dir_error)
            }), 500
        
        # Maximum number of files allowed
        MAX_FILES = 10
        existing_files = [
            f for f in os.listdir(upload_dir) 
            if os.path.isfile(os.path.join(upload_dir, f)) 
            and not f.startswith('.') 
            and not f.startswith('temp_')
        ]
        
        if len(existing_files) + len(valid_files) > MAX_FILES:
            logger.warning(f"Upload would exceed max file limit of {MAX_FILES}")
            return jsonify({
                'error': f'Limite maximale de {MAX_FILES} fichiers atteinte',
                'current_files': len(existing_files)
            }), 400
        
        # Sanitize filename function
        def sanitize_filename(text):
            return re.sub(r'[^\w\s-]', '', text.lower().replace(' ', '_'))
        
        # Save files with comprehensive error handling
        saved_files = []
        for index, file in enumerate(valid_files, len(existing_files) + 1):
            try:
                # Generate unique filename
                file_extension = os.path.splitext(file.filename)[1].lower()
                sanitized_location = sanitize_filename(infrastructure.localisation)
                new_filename = f"infra{id}_{sanitized_location}_{index}{file_extension}"
                temp_path = os.path.join(upload_dir, f"temp_{new_filename}")
                final_path = os.path.join(upload_dir, new_filename)
                
                # Save file with safe file handling
                file.save(temp_path)
                logger.info(f"Saved temporary file: {temp_path}")
                
                # Compress if image
                compression_result = None
                try:
                    if file_extension in ['.jpg', '.jpeg', '.png', '.webp']:
                        compression_result = compress_image(temp_path, final_path)
                        logger.info(f"Successfully compressed {new_filename}")
                    else:
                        # For non-image files, copy the file
                        shutil.copy2(temp_path, final_path)
                except Exception as compress_error:
                    logger.warning(f"Compression/copy failed for {new_filename}: {str(compress_error)}")
                    # Fallback to copying the file
                    shutil.copy2(temp_path, final_path)
                
                # Remove temporary file
                try:
                    os.remove(temp_path)
                except Exception as remove_error:
                    logger.warning(f"Could not remove temporary file {temp_path}: {str(remove_error)}")
                
                # Store file info
                relative_path = os.path.join('uploads', 'infrastructures', str(id), new_filename)
                saved_files.append({
                    'name': new_filename,
                    'original_name': file.filename,
                    'path': relative_path,
                    'type': file.content_type,
                    'location': infrastructure.localisation,
                    'compression': compression_result
                })
                
            except Exception as file_save_error:
                logger.error(f"Error processing file {file.filename}: {str(file_save_error)}")
                logger.error(traceback.format_exc())
                # Continue processing other files even if one fails
                continue
        
        # Check if any files were successfully saved
        if not saved_files:
            logger.error("No files were successfully uploaded")
            return jsonify({
                'error': 'Aucun fichier n\'a pu être téléchargé',
                'details': 'Échec du traitement de tous les fichiers'
            }), 500
        
        # Log successful upload
        logger.info(f"Successfully uploaded {len(saved_files)} files for infrastructure {id}")
        
        return jsonify({
            'message': f'{len(saved_files)} fichier(s) téléchargé(s) avec succès',
            'files': saved_files,
            'total_files': len(existing_files) + len(saved_files)
        }), 200
    
    except Exception as unexpected_error:
        # Catch-all error handling with full traceback
        logger.error(f"Unexpected error in file upload: {str(unexpected_error)}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            'error': 'Erreur inattendue lors du téléchargement',
            'details': str(unexpected_error),
            'traceback': traceback.format_exc()
        }), 500

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
                'type': 'image' if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')) else 'pdf',
                'location': infrastructure.localisation,
                'uploaded_at': os.path.getctime(os.path.join(upload_dir, filename))
            }
            all_files.append(file_info)
        
        # Sort files by upload time (newest first)
        all_files.sort(key=lambda x: x['uploaded_at'], reverse=True)
        
        # Separate images and PDFs
        image_files = [f for f in all_files if f['type'].startswith('image')]
        pdf_files = [f for f in all_files if f['type'] == 'pdf']
        
        # Combine and return files
        files = image_files + pdf_files
        
        return jsonify({
            'files': files,
            'total_images': len(image_files),
            'max_images_displayed': len(image_files)  # Show all images
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving infrastructure files: {str(e)}")
        return jsonify({'error': 'Impossible de récupérer les fichiers'}), 500

@infrastructures.route('/infrastructure/<int:id>/delete-file', methods=['POST'])
@login_required
def delete_infrastructure_file(id):
    try:
        # Validate infrastructure existence
        infrastructure = Infrastructure.query.get_or_404(id)
        
        # Get file details from request
        file_data = request.get_json()
        filename = file_data.get('filename')
        
        if not filename:
            logger.warning(f"No filename provided for deletion in infrastructure {id}")
            return jsonify({
                'error': 'Aucun fichier spécifié',
                'status': 'error'
            }), 400
        
        # Construct full file path
        file_path = os.path.join('static', 'uploads', 'infrastructures', str(id), filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return jsonify({
                'error': 'Fichier non trouvé',
                'status': 'error'
            }), 404
        
        # Remove the file
        try:
            os.remove(file_path)
            logger.info(f"Successfully deleted file: {filename} for infrastructure {id}")
            
            return jsonify({
                'message': 'Fichier supprimé avec succès',
                'status': 'success'
            }), 200
        
        except Exception as delete_error:
            logger.error(f"Error deleting file {filename}: {str(delete_error)}")
            return jsonify({
                'error': 'Impossible de supprimer le fichier',
                'details': str(delete_error),
                'status': 'error'
            }), 500
    
    except Exception as unexpected_error:
        logger.error(f"Unexpected error deleting infrastructure file: {str(unexpected_error)}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            'error': 'Erreur inattendue lors de la suppression',
            'details': str(unexpected_error),
            'status': 'error'
        }), 500
