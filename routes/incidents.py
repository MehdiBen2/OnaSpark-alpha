from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file, jsonify
from flask_login import login_required, current_user
from models import db, Incident, Unit, UserRole
from datetime import datetime
from functools import wraps
from utils.decorators import admin_required, unit_required
from utils.pdf_generator import create_incident_pdf
from utils.url_endpoints import SELECT_UNIT, INCIDENT_LIST, VIEW_INCIDENT, MERGE_INCIDENT, BATCH_MERGE
import os
import json
from typing import Dict, Any, Optional
import requests

incidents = Blueprint('incidents', __name__)

def parse_drawn_shapes(drawn_shapes_json: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Parse and validate drawn shapes from JSON input.
    
    Args:
        drawn_shapes_json (str): JSON string representing drawn shapes
    
    Returns:
        Dict or None: Parsed and validated shapes, or None if invalid
    """
    if not drawn_shapes_json:
        return None
    
    try:
        shapes = json.loads(drawn_shapes_json)
        
        # Validate shapes
        validated_shapes = []
        for shape in shapes:
            if not isinstance(shape, dict):
                continue
            
            # Validate shape type and coordinates
            if shape.get('type') not in ['Polygon', 'Rectangle', 'Circle']:
                continue
            
            if not shape.get('coordinates'):
                continue
            
            validated_shapes.append({
                'type': shape['type'],
                'coordinates': shape['coordinates']
            })
        
        return validated_shapes if validated_shapes else None
    
    except (json.JSONDecodeError, TypeError):
        # Log the error for debugging
        current_app.logger.warning(f"Invalid drawn shapes JSON: {drawn_shapes_json}")
        return None

@incidents.route('/incidents')
@login_required
def incident_list():
    # Centralized incident fetching logic
    def get_incidents_for_user():
        if current_user.role == UserRole.ADMIN:
            return Incident.query.order_by(Incident.date_incident.desc()).all()
        
        if current_user.role == UserRole.EMPLOYEUR_ZONE:
            if not current_user.zone_id:
                flash('Vous devez être assigné à une zone pour voir les incidents.', 'warning')
                return []
            
            zone_units = Unit.query.filter_by(zone_id=current_user.zone_id).all()
            unit_ids = [unit.id for unit in zone_units]
            return Incident.query.filter(Incident.unit_id.in_(unit_ids)).order_by(Incident.date_incident.desc()).all()
        
        # For unit-level and regular users
        if not current_user.unit_id:
            flash('Vous devez sélectionner une unité pour voir les incidents.', 'warning')
            return []
        
        return Incident.query.filter_by(unit_id=current_user.unit_id).order_by(Incident.date_incident.desc()).all()
    
    incidents = get_incidents_for_user()
    return render_template('incidents/incident_list.html', incidents=incidents)

@incidents.route('/incident/new', methods=['GET', 'POST'])
@login_required
@unit_required
def new_incident():
    # Get all available units for admin, or just the user's unit for others
    if current_user.role == UserRole.ADMIN:
        units = Unit.query.all()
    else:
        if not current_user.unit_id:
            flash('Vous devez être assigné à une unité pour signaler un incident.', 'warning')
            return redirect(url_for(SELECT_UNIT))
        units = [current_user.assigned_unit] if current_user.assigned_unit else []

    if request.method == 'POST':
        try:
            # Check if it's an AJAX request
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

            # Log all form data for debugging
            current_app.logger.info(f"Incident Creation Form Data: {dict(request.form)}")

            # Get the unit_id from the form
            unit_id = request.form.get('unit_id', current_user.assigned_unit.id)
            
            # Validate unit_id
            if not unit_id:
                error_msg = 'Une unité est requise pour créer un incident.'
                current_app.logger.warning(f"Incident creation failed: {error_msg}")
                if is_ajax:
                    return jsonify({'status': 'error', 'message': error_msg}), 400
                flash(error_msg, 'error')
                return render_template('incidents/new_incident.html', units=units)

            # For non-admin users, verify they're creating an incident for their own unit
            if current_user.role != UserRole.ADMIN and str(current_user.assigned_unit.id) != str(unit_id):
                error_msg = 'Vous ne pouvez créer des incidents que pour votre unité.'
                current_app.logger.warning(f"Incident creation unauthorized: {error_msg}")
                if is_ajax:
                    return jsonify({'status': 'error', 'message': error_msg}), 403
                flash(error_msg, 'error')
                return render_template('incidents/new_incident.html', units=units)

            # Validate date_incident
            date_incident_str = request.form.get('date_incident')
            if not date_incident_str:
                error_msg = 'Vous devez spécifier la date de l\'incident.'
                current_app.logger.warning(f"Incident creation failed: {error_msg}")
                if is_ajax:
                    return jsonify({'status': 'error', 'message': error_msg}), 400
                flash(error_msg, 'error')
                return render_template('incidents/new_incident.html', units=units)

            try:
                date_incident = datetime.strptime(date_incident_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                error_msg = 'Le format de la date de l\'incident est invalide.'
                current_app.logger.warning(f"Incident creation failed: {error_msg}")
                if is_ajax:
                    return jsonify({'status': 'error', 'message': error_msg}), 400
                flash(error_msg, 'error')
                return render_template('incidents/new_incident.html', units=units)

            # New fields for map selection
            latitude = request.form.get('latitude')
            longitude = request.form.get('longitude')

            # Extract drawn shapes
            drawn_shapes_json = request.form.get('drawn-shapes')
            drawn_shapes = parse_drawn_shapes(drawn_shapes_json)

            # Create the incident
            incident = Incident(
                title=request.form.get('title'),
                wilaya=request.form.get('wilaya'),
                commune=request.form.get('commune'),
                localite=request.form.get('localite'),
                structure_type=request.form.get('structure_type'),
                nature_cause=request.form.get('nature_cause'),
                date_incident=date_incident,
                mesures_prises=request.form.get('mesures_prises'),
                impact=request.form.get('impact'),
                gravite=request.form.get('gravite').lower(),
                status='Nouveau',
                user_id=current_user.id,
                unit_id=unit_id,
                latitude=float(latitude) if latitude else None,
                longitude=float(longitude) if longitude else None,
                drawn_shapes=drawn_shapes
            )
            db.session.add(incident)
            db.session.commit()

            # Log successful incident creation
            current_app.logger.info(f"Incident created successfully: ID {incident.id}")

            # Success response
            success_msg = 'Incident signalé avec succès.'
            if is_ajax:
                return jsonify({
                    'status': 'success', 
                    'message': success_msg,
                    'redirect_url': url_for(INCIDENT_LIST)
                }), 201
            
            flash(success_msg, 'success')
            return redirect(url_for(INCIDENT_LIST))

        except Exception as e:
            # Rollback the session to prevent any partial commits
            db.session.rollback()

            # Log the full error details
            current_app.logger.error(f"Incident creation error: {str(e)}", exc_info=True)
            
            # Prepare error message
            error_msg = f'Une erreur est survenue lors de la création de l\'incident: {str(e)}'
            
            # Detailed logging of request data for debugging
            current_app.logger.error(f"Request Form Data: {dict(request.form)}")
            
            # Differentiate between AJAX and traditional form submission
            if is_ajax:
                return jsonify({
                    'status': 'error', 
                    'message': error_msg
                }), 500
            
            flash(error_msg, 'error')
            return render_template('incidents/new_incident.html', units=units)

    return render_template('incidents/new_incident.html', units=units)

@incidents.route('/incident/<int:incident_id>')
@login_required
@unit_required
def view_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    if not current_user.role == UserRole.ADMIN and current_user.unit_id != incident.unit_id:
        flash('Vous n\'avez pas accès à cet incident.', 'danger')
        return redirect(url_for(INCIDENT_LIST))
    return render_template('incidents/view_incident.html', incident=incident)

@incidents.route('/incident/<int:incident_id>/edit', methods=['GET', 'POST'])
@login_required
@unit_required
def edit_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    if not current_user.role == UserRole.ADMIN and current_user.unit_id != incident.unit_id:
        flash('Vous n\'avez pas accès à cet incident.', 'danger')
        return redirect(url_for(INCIDENT_LIST))
    
    if request.method == 'POST':
        try:
            incident.wilaya = request.form.get('wilaya')
            incident.commune = request.form.get('commune')
            incident.localite = request.form.get('localite')
            incident.structure_type = request.form.get('structure_type')
            incident.nature_cause = request.form.get('nature_cause')
            incident.date_incident = datetime.strptime(request.form.get('date_incident'), '%Y-%m-%dT%H:%M')
            incident.mesures_prises = request.form.get('mesures_prises')
            incident.impact = request.form.get('impact')
            incident.gravite = request.form.get('gravite')
            
            db.session.commit()
            flash('Incident mis à jour avec succès.', 'success')
            return redirect(url_for(VIEW_INCIDENT, incident_id=incident.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour de l\'incident: {str(e)}', 'danger')
            return render_template('incidents/edit_incident.html', incident=incident)
    
    return render_template('incidents/edit_incident.html', incident=incident)

@incidents.route('/incident/<int:incident_id>/delete', methods=['POST'])
@login_required
@unit_required
def delete_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    
    if not current_user.role == UserRole.ADMIN and current_user.unit_id != incident.unit_id:
        flash('Vous n\'avez pas la permission de supprimer cet incident.', 'danger')
        return redirect(url_for(INCIDENT_LIST))
    
    try:
        db.session.delete(incident)
        db.session.commit()
        flash('Incident supprimé avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression de l\'incident: {str(e)}', 'danger')
    
    return redirect(url_for(INCIDENT_LIST))

@incidents.route('/incident/<int:incident_id>/resolve', methods=['POST'])
@login_required
@unit_required
def resolve_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    if not current_user.role == UserRole.ADMIN and current_user.unit_id != incident.unit_id:
        flash('Vous n\'êtes pas autorisé à résoudre cet incident.', 'danger')
        return redirect(url_for(INCIDENT_LIST))
    
    if incident.status == 'Résolu':
        flash('Cet incident est déjà résolu.', 'warning')
        return redirect(url_for(INCIDENT_LIST))
    
    mesures_prises = request.form.get('mesures_prises')
    if not mesures_prises:
        flash('Veuillez décrire les mesures prises pour résoudre l\'incident.', 'danger')
        return redirect(url_for(INCIDENT_LIST))
    
    incident.status = 'Résolu'
    incident.mesures_prises = mesures_prises
    incident.date_resolution = datetime.now()
    db.session.commit()
    
    flash('L\'incident a été marqué comme résolu.', 'success')
    return redirect(url_for(INCIDENT_LIST))

@incidents.route('/incident/<int:incident_id>/export_pdf')
@login_required
@unit_required
def export_incident_pdf(incident_id):
    try:
        incident = Incident.query.get_or_404(incident_id)
        
        # Create temporary directory if it doesn't exist
        temp_dir = os.path.join(current_app.root_path, 'temp')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        # Generate PDF filename
        filename = f'incident_{incident.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        pdf_path = os.path.join(temp_dir, filename)
        
        # Get unit name safely
        unit_name = incident.unit.name if incident.unit else "Unité non spécifiée"
        
        # Generate PDF
        create_incident_pdf([incident], pdf_path, unit_name)
        
        # Send file to user and delete after sending
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'Erreur lors de la génération du PDF: {str(e)}', 'danger')
        return redirect(url_for(INCIDENT_LIST))

@incidents.route('/incidents/export_all_pdf')
@login_required
@unit_required
def export_all_incidents_pdf():
    try:
        # Get all incidents based on user role
        if current_user.role == UserRole.ADMIN:
            incidents = Incident.query.all()
        else:
            incidents = Incident.query.filter_by(unit_id=current_user.unit_id).all()
        
        if not incidents:
            flash('Aucun incident à exporter.', 'warning')
            return redirect(url_for(INCIDENT_LIST))
        
        # Create temporary directory if it doesn't exist
        temp_dir = os.path.join(current_app.root_path, 'temp')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        # Generate PDF filename
        filename = f'all_incidents_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        pdf_path = os.path.join(temp_dir, filename)
        
        # Get unit name safely
        unit_name = current_user.assigned_unit.name if current_user.assigned_unit else "Toutes les unités" if current_user.role == UserRole.ADMIN else "Unité non spécifiée"
        
        # Generate PDF
        create_incident_pdf(incidents, pdf_path, unit_name)
        
        # Send file to user
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'Erreur lors de la génération du PDF: {str(e)}', 'danger')
        return redirect(url_for(INCIDENT_LIST))

@incidents.route('/incident/<int:incident_id>/merge', methods=['GET', 'POST'])
@login_required
@admin_required
def merge_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    units = Unit.query.filter(Unit.id != incident.unit_id).all()
    
    if request.method == 'POST':
        new_unit_id = request.form.get('new_unit')
        merge_note = request.form.get('merge_note')
        
        if not new_unit_id:
            flash('Veuillez sélectionner une unité de destination.', 'danger')
            return redirect(url_for(MERGE_INCIDENT, incident_id=incident_id))
            
        try:
            # Update the incident's unit
            new_unit = Unit.query.get(new_unit_id)
            old_unit_name = incident.unit.name if incident.unit else "Unité non spécifiée"
            
            incident.unit_id = new_unit_id
            
            # Add merge note to mesures_prises if provided
            if merge_note:
                merge_info = f"\n\n[Fusion d'unité le {datetime.now().strftime('%d/%m/%Y %H:%M')}]\n"
                merge_info += f"Transféré de l'unité '{old_unit_name}' vers '{new_unit.name}'\n"
                merge_info += f"Note: {merge_note}"
                
                if incident.mesures_prises:
                    incident.mesures_prises += merge_info
                else:
                    incident.mesures_prises = merge_info
            
            db.session.commit()
            flash(f'L\'incident a été fusionné avec succès vers l\'unité {new_unit.name}.', 'success')
            return redirect(url_for(VIEW_INCIDENT, incident_id=incident.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la fusion de l\'incident: {str(e)}', 'danger')
            return redirect(url_for(MERGE_INCIDENT, incident_id=incident_id))
    
    return render_template('incidents/merge_incident.html', incident=incident, units=units)

@incidents.route('/incidents/batch_merge', methods=['GET', 'POST'])
@login_required
@admin_required
def batch_merge():
    units = Unit.query.all()
    
    if request.method == 'POST':
        source_unit_id = request.form.get('source_unit')
        target_unit_id = request.form.get('target_unit')
        incident_ids = request.form.getlist('incidents')
        merge_note = request.form.get('merge_note')
        
        if not all([source_unit_id, target_unit_id, incident_ids]):
            flash('Veuillez sélectionner les unités source et destination et au moins un incident.', 'danger')
            return redirect(url_for(BATCH_MERGE))
            
        try:
            source_unit = Unit.query.get(source_unit_id)
            target_unit = Unit.query.get(target_unit_id)
            
            # Add merge note
            merge_info = f"\n\n[Fusion en lot le {datetime.now().strftime('%d/%m/%Y %H:%M')}]\n"
            merge_info += f"Transféré de l'unité '{source_unit.name}' vers '{target_unit.name}'\n"
            if merge_note:
                merge_info += f"Note: {merge_note}"
            
            # Update all selected incidents
            for incident_id in incident_ids:
                incident = Incident.query.get(incident_id)
                if incident and incident.unit_id == int(source_unit_id):
                    incident.unit_id = target_unit_id
                    if incident.mesures_prises:
                        incident.mesures_prises += merge_info
                    else:
                        incident.mesures_prises = merge_info
            
            db.session.commit()
            flash(f'{len(incident_ids)} incidents ont été fusionnés avec succès vers l\'unité {target_unit.name}.', 'success')
            return redirect(url_for(INCIDENT_LIST))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la fusion des incidents: {str(e)}', 'danger')
            return redirect(url_for(BATCH_MERGE))
    
    return render_template('incidents/batch_merge.html', units=units)

@incidents.route('/get_ai_explanation', methods=['GET', 'POST'])
@login_required
def get_ai_explanation():
    """
    Generate AI explanation for incident nature and cause using Mistral API.
    
    Returns:
        JSON response with AI-generated explanation and solutions
    """
    # Add a simple GET handler to help with debugging
    if request.method == 'GET':
        return jsonify({
            'message': 'AI Explanation endpoint. Use POST method with incident details.'
        }), 200

    try:
        # Log the incoming request data for debugging
        current_app.logger.info(f"Received AI explanation request: {request.get_json()}")
        
        data = request.get_json()
        nature_cause = data.get('nature_cause', '')
        incident_id = data.get('incident_id')

        # Validate input
        if not nature_cause:
            current_app.logger.warning('No incident description provided')
            return jsonify({
                'error': 'Aucune description de l\'incident fournie'
            }), 400

        # Get Mistral API key from environment
        mistral_api_key = os.environ.get('MISTRAL_API_KEY') or current_app.config.get('MISTRAL_API_KEY')
        
        # Log key retrieval details (without exposing full key)
        current_app.logger.info(f'Mistral API key retrieved: {bool(mistral_api_key)}')
        current_app.logger.info(f'Key length: {len(mistral_api_key) if mistral_api_key else 0}')
        
        # Validate API key format
        if not mistral_api_key or len(mistral_api_key) < 10:
            current_app.logger.error('Mistral API key is invalid or missing')
            return jsonify({
                'error': 'Clé API Mistral invalide ou manquante'
            }), 400

        # Call Mistral API
        import requests
        import traceback
        
        try:
            # Prepare request payload following AI explanation rules
            payload = {
                'model': 'mistral-large-latest',
                'messages': [
                    {'role': 'system', 'content': """Règles Strictes pour l'Analyse d'Incident :
- INTERDICTION ABSOLUE D'INVENTER DES INFORMATIONS
- Utilise UNIQUEMENT les faits fournis
- Ne pas ajouter de détails non mentionnés
- Analyse technique basée strictement sur le contexte donné
- Langage technique précis et factuel
- Rapporter exactement ce qui est communiqué
- Aucune supposition ou extrapolation non fondée
- Format clair et professionnel
- Concentre-toi sur les informations disponibles"""},
                    {'role': 'user', 'content': f"""Incident ID: {incident_id}
{nature_cause}

INSTRUCTIONS:
- Explique directement l'incident et les causes possibles
- Évite les détails superflus
- Langage technique et concis
- Solutions pratiques et immédiates"""}
                ],
                'temperature': 0.7,
                'max_tokens': 750
            }

            # Log full payload for debugging
            current_app.logger.info(f"Mistral API Payload: {payload}")

            # Validate API key
            if not mistral_api_key:
                current_app.logger.error("Mistral API key is missing")
                return jsonify({
                    'error': 'Clé API Mistral manquante',
                    'details': 'Aucune clé API trouvée pour Mistral'
                }), 400

            # Make API request
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {mistral_api_key}'
            }

            try:
                response = requests.post(
                    'https://api.mistral.ai/v1/chat/completions', 
                    json=payload, 
                    headers=headers
                )
                
                # Log full response for debugging
                current_app.logger.info(f"Mistral API Response Status: {response.status_code}")
                current_app.logger.info(f"Mistral API Response Body: {response.text}")

                # Check response
                if response.status_code != 200:
                    current_app.logger.error(f"Mistral API Error: {response.text}")
                    return jsonify({
                        'error': 'Erreur lors de la génération de l\'explication',
                        'details': response.text
                    }), 500

                # Parse response
                result = response.json()
                explanation = result['choices'][0]['message']['content']

                return jsonify({
                    'explanation': explanation
                }), 200

            except requests.RequestException as req_err:
                current_app.logger.error(f"Request Exception: {req_err}")
                current_app.logger.error(traceback.format_exc())
                return jsonify({
                    'error': 'Erreur de connexion à l\'API Mistral',
                    'details': str(req_err)
                }), 500

        except Exception as e:
            current_app.logger.error(f"Unexpected Error: {e}")
            current_app.logger.error(traceback.format_exc())
            return jsonify({
                'error': 'Erreur inattendue lors de la génération de l\'explication',
                'details': str(e)
            }), 500

    except Exception as e:
        # Log the full stack trace for internal server errors
        current_app.logger.exception(f'Unexpected error in AI explanation: {str(e)}')
        return jsonify({
            'error': 'Une erreur inattendue s\'est produite'
        }), 500
