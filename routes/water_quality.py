from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required, current_user
from utils.water_quality import (
    assess_water_quality, 
    get_parameter_metadata,
    generate_pdf_report
)
from utils.url_endpoints import *
from datetime import datetime
import os

water_quality = Blueprint('water_quality', __name__)

@water_quality.route('/reuse/water-quality/assessment')
@login_required
def water_quality_assessment_route():
    """
    Render the water quality assessment page.
    
    Returns:
        Rendered water quality assessment template with parameter metadata
    """
    return render_template('departement/reuse/water_quality.html', 
                         active_page='water_quality',
                         parameter_metadata=get_parameter_metadata())

@water_quality.route('/reuse/water-quality/assessment/evaluate', methods=['POST'])
@login_required
def water_quality_evaluation_route():
    """
    Assess water quality based on submitted parameters.
    
    Returns:
        JSON response with water quality assessment results
    """
    # Get form data
    data = request.form.to_dict()
    
    # Convert string values to appropriate types
    for key, value in data.items():
        try:
            data[key] = float(value)
        except ValueError:
            pass
    
    # Perform water quality assessment
    result = assess_water_quality(data)
    return jsonify(result)

@water_quality.route('/reuse/water-quality/results', endpoint='water_quality_results')
@login_required
def water_quality_results_route():
    """
    Display water quality assessment results.
    
    Returns:
        Rendered water quality results template
    """
    # Get parameters from query string
    params = request.args.to_dict()
    
    # Convert string values to appropriate types
    for key, value in params.items():
        try:
            params[key] = float(value)
        except ValueError:
            pass
    
    # Perform water quality assessment
    result = assess_water_quality(params)
    
    # Add metadata for UI rendering
    result['parameter_metadata'] = get_parameter_metadata()
    
    return render_template('departement/reuse/water_quality_results.html', **result)

@water_quality.route('/reuse/water-quality/download-pdf', endpoint='download_water_quality_pdf')
@login_required
def download_water_quality_pdf_route():
    """
    Generate and download a PDF report of water quality assessment.
    
    Returns:
        PDF file download or error redirect
    """
    try:
        # Get parameters from query string
        params = request.args.to_dict()
        
        # Convert string values to appropriate types
        for key, value in params.items():
            try:
                params[key] = float(value)
            except ValueError:
                pass
        
        # Perform water quality assessment
        result = assess_water_quality(params)
        
        # Generate PDF with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'Rapport_Qualite_Eau_{timestamp}.pdf'
        pdf_path = generate_pdf_report(result)
        
        try:
            # Send file for download with proper headers
            response = send_file(
                pdf_path,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        finally:
            # Clean up the temporary file after sending
            try:
                os.unlink(pdf_path)
            except:
                pass
    except Exception as e:
        # Log the error (you might want to use a proper logging mechanism)
        print(f"Error generating water quality PDF: {str(e)}")
        return jsonify({"error": "Failed to generate PDF"}), 500
