from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
import os
from datetime import datetime

bilans_bp = Blueprint('bilans', __name__)

@bilans_bp.route('/departement/exploitation/infrastructures/bilans/mensuels', methods=['GET'])
@login_required
def bilans_mensuels():
    """
    Route to render the monthly bilans (reports) page
    """
    return render_template('departement/exploitation/infrastructures/bilans/bilans_mensuels.html')

@bilans_bp.route('/save_bilan_document', methods=['POST'])
@login_required
def save_bilan_document():
    """
    Save the bilan document content
    """
    try:
        # Get document content from request
        document_content = request.json.get('content', '')
        
        # Validate content
        if not document_content:
            return jsonify({'status': 'error', 'message': 'Contenu du document vide'}), 400
        
        # Create directory for user's bilans if it doesn't exist
        user_bilans_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 
                                       'bilans', 
                                       str(current_user.id))
        os.makedirs(user_bilans_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bilan_{timestamp}.html"
        filepath = os.path.join(user_bilans_dir, filename)
        
        # Save document
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(document_content)
        
        return jsonify({
            'status': 'success', 
            'message': 'Document sauvegardé avec succès',
            'filename': filename
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la sauvegarde du document: {str(e)}")
        return jsonify({
            'status': 'error', 
            'message': 'Erreur lors de la sauvegarde du document'
        }), 500

@bilans_bp.route('/export_bilan_pdf', methods=['POST'])
@login_required
def export_bilan_pdf():
    """
    Export bilan document to PDF
    """
    try:
        # Get document content from request
        document_content = request.json.get('content', '')
        
        # Validate content
        if not document_content:
            return jsonify({'status': 'error', 'message': 'Contenu du document vide'}), 400
        
        # Create directory for user's bilans PDFs if it doesn't exist
        user_bilans_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 
                                       'bilans', 
                                       str(current_user.id), 
                                       'pdf')
        os.makedirs(user_bilans_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bilan_{timestamp}.pdf"
        filepath = os.path.join(user_bilans_dir, filename)
        
        # TODO: Implement actual PDF conversion
        # This is a placeholder - you'll need to use a library like reportlab or xhtml2pdf
        # For now, we'll just simulate PDF creation
        
        return jsonify({
            'status': 'success', 
            'message': 'Exportation PDF simulée',
            'filename': filename
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Erreur lors de l'exportation PDF: {str(e)}")
        return jsonify({
            'status': 'error', 
            'message': 'Erreur lors de l\'exportation PDF'
        }), 500
