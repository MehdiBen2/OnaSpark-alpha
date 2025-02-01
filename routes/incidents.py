from flask import (
    Blueprint, render_template, request, redirect, url_for, 
    flash, current_app, send_file, jsonify, session
)
from flask_login import login_required, current_user
from models import db, Incident, Unit, UserRole
from datetime import datetime
from functools import wraps
from utils.decorators import admin_required
from utils.pdf_generator import create_incident_pdf
from utils.url_endpoints import SELECT_UNIT, INCIDENT_LIST, VIEW_INCIDENT
import os
import json
from typing import Dict, Any, Optional
import requests
from flask_caching import Cache
from extensions import cache
from utils.incident_utils import get_user_incident_counts, get_incident_cache_key
from utils.permissions import UserRole, Permission, context_permission_check, permission_required

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
            # Ensure shape is a dictionary with required keys
            if not isinstance(shape, dict) or 'type' not in shape or 'coordinates' not in shape:
                continue
            
            # Validate shape type
            if shape['type'] not in ['Polygon', 'Rectangle', 'Circle']:
                continue
            
            # Basic coordinate validation
            if not shape['coordinates'] or not isinstance(shape['coordinates'], list):
                continue
            
            validated_shapes.append({
                'type': shape['type'],
                'coordinates': shape['coordinates']
            })
        
        return validated_shapes if validated_shapes else None
    
    except (json.JSONDecodeError, TypeError) as e:
        current_app.logger.warning(f"Invalid drawn shapes JSON: {drawn_shapes_json}")
        return None

@incidents.route('/list', methods=['GET'], endpoint='incident_list')
@login_required
@permission_required(Permission.VIEW_INCIDENT)
def list_incidents():
    """
    Display a paginated list of incidents with optional filtering, searching, and sorting.
    
    Query Parameters:
    - page: Current page number
    - status: Filter incidents by status
    - search: Search term for incidents
    - sort: Sorting option
    
    Returns:
        Rendered incident list template with pagination
    """
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', None)
    search_term = request.args.get('search', '').strip()
    sort_option = request.args.get('sort', 'date_desc')
    
    # Base query setup based on user role
    if current_user.role in [UserRole.ADMIN, UserRole.EMPLOYEUR_DG]:
        query = Incident.query
    elif current_user.role == UserRole.EMPLOYEUR_ZONE:
        # Get all units in the user's zone
        zone_units = Unit.query.filter_by(zone_id=current_user.zone_id).all()
        unit_ids = [unit.id for unit in zone_units]
        query = Incident.query.filter(Incident.unit_id.in_(unit_ids))
    else:
        # Filter by current user's unit
        query = Incident.query.filter_by(unit_id=current_user.unit_id)
    
    # Apply status filter if provided
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    # Apply search filter if search term is provided
    if search_term:
        search_filter = f'%{search_term}%'
        query = query.filter(
            db.or_(
                Incident.wilaya.ilike(search_filter),
                Incident.commune.ilike(search_filter),
                Incident.localite.ilike(search_filter),
                Incident.nature_cause.ilike(search_filter),
                Incident.impact.ilike(search_filter)
            )
        )
    
    # Apply sorting
    if sort_option == 'date_desc':
        query = query.order_by(Incident.date_incident.desc())
    elif sort_option == 'date_asc':
        query = query.order_by(Incident.date_incident.asc())
    elif sort_option == 'gravite':
        # Custom sorting for severity
        gravite_order = ['Critique', 'Élevée', 'Moyenne', 'Faible']
        query = query.order_by(
            db.case(
                *[(Incident.gravite == severity, index) for index, severity in enumerate(gravite_order)],
                else_=len(gravite_order)
            )
        )
    elif sort_option == 'status':
        # Custom sorting for status
        status_order = ['En cours', 'Résolu']
        query = query.order_by(
            db.case(
                *[(Incident.status == status, index) for index, status in enumerate(status_order)],
                else_=len(status_order)
            )
        )
    
    # Paginate results
    pagination = query.paginate(
        page=page, 
        per_page=10,  # Adjust as needed
        error_out=False
    )
    
    # Prepare context for template
    context = {
        'incidents': pagination.items,
        'pagination': pagination,
        'current_page': page,
        'status_filter': status_filter,
        'total_incidents': pagination.total,
        'current_time': datetime.now(),
        'UserRole': UserRole,
        'can_view_incident': context_permission_check(Permission.VIEW_INCIDENT),
        'can_create_incident': context_permission_check(Permission.CREATE_INCIDENT),
        'can_edit_incident': context_permission_check(Permission.EDIT_INCIDENT),
        'can_delete_incident': context_permission_check(Permission.DELETE_INCIDENT),
        'can_export_pdf': context_permission_check(Permission.EXPORT_INCIDENT_PDF),
        'can_ai_analysis': context_permission_check(Permission.GET_AI_EXPLANATION),
    }
    
    return render_template('incidents/incident_list.html', **context)

@incidents.route('/incident/new', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.CREATE_INCIDENT)
def new_incident():
    # Prevent Employeur Zone from accessing this route
    if current_user.role == UserRole.EMPLOYEUR_ZONE:
        flash('Vous n\'avez pas la permission de créer des incidents.', 'danger')
        return redirect(url_for('incidents.list_incidents'))
    
    # Prevent Employeur DG from accessing this route
    if current_user.role == UserRole.EMPLOYEUR_DG:
        flash('Vous n\'avez pas la permission de créer des incidents.', 'danger')
        return redirect(url_for('incidents.list_incidents'))

    # Get available units based on user role
    if current_user.role == UserRole.ADMIN:
        units = Unit.query.all()
    else:
        # For regular users, only show their assigned unit
        if not current_user.unit_id:
            flash('Vous devez être assigné à une unité pour signaler un incident.', 'warning')
            return redirect(url_for(SELECT_UNIT))
        
        # Fetch the unit directly to ensure it exists
        assigned_unit = Unit.query.get(current_user.unit_id)
        if not assigned_unit:
            flash('Votre unité assignée est introuvable. Veuillez contacter un administrateur.', 'danger')
            return redirect(url_for(SELECT_UNIT))
        
        units = [assigned_unit]

    if request.method == 'POST':
        try:
            # Check if it's an AJAX request
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

            # Log all form data for debugging
            current_app.logger.info(f"Incident Creation Form Data: {dict(request.form)}")

            # Get the unit_id from the form or use the user's assigned unit
            unit_id = request.form.get('unit_id')
            if not unit_id and current_user.role != UserRole.ADMIN:
                # Fallback to user's unit if no unit is specified
                unit_id = current_user.unit_id

            # Validate unit_id
            if not unit_id:
                error_msg = 'Une unité est requise pour créer un incident.'
                current_app.logger.error(error_msg)
                
                if is_ajax:
                    return jsonify({
                        'status': 'error', 
                        'message': error_msg
                    }), 400

                flash(error_msg, 'danger')
                return redirect(url_for('incidents.new_incident'))
            
            # Validate other required fields
            title = request.form.get('title')
            if not title:
                error_msg = 'Un titre est requis pour l\'incident.'
                current_app.logger.error(error_msg)
                
                if is_ajax:
                    return jsonify({
                        'status': 'error', 
                        'message': error_msg
                    }), 400

                flash(error_msg, 'danger')
                return redirect(url_for('incidents.new_incident'))

            # Get coordinates
            latitude = request.form.get('latitude')
            longitude = request.form.get('longitude')

            # Parse drawn shapes
            drawn_shapes_json = request.form.get('drawn_shapes')
            drawn_shapes = parse_drawn_shapes(drawn_shapes_json)

            # Create the incident
            new_incident = Incident(
                title=title,
                wilaya=request.form.get('wilaya'),
                commune=request.form.get('commune'),
                localite=request.form.get('localite'),
                structure_type=request.form.get('structure_type'),
                nature_cause=request.form.get('nature_cause'),
                date_incident=datetime.strptime(request.form.get('date_incident'), '%Y-%m-%dT%H:%M'),
                mesures_prises=request.form.get('mesures_prises'),
                impact=request.form.get('impact'),
                gravite=request.form.get('gravite'),
                unit_id=unit_id,
                user_id=current_user.id,
                status='En cours',
                latitude=float(latitude) if latitude else None,
                longitude=float(longitude) if longitude else None,
                drawn_shapes=drawn_shapes
            )
            db.session.add(new_incident)
            db.session.commit()

            # Log successful incident creation
            current_app.logger.info(f"Incident created successfully: ID {new_incident.id}")

            # Add a flash message for successful incident creation
            flash('Incident créé avec succès', 'success')

            # Invalidate incident count cache
            cache.delete(get_incident_cache_key(current_user))
            
            # Return JSON response for AJAX request
            if is_ajax:
                return jsonify({
                    'status': 'success', 
                    'message': 'Incident créé avec succès',
                    'redirect_url': url_for('incidents.incident_list')
                }), 200
            
            # Redirect for non-AJAX request
            return redirect(url_for('incidents.incident_list'))

        except Exception as e:
            # Rollback the session to prevent any partial commits
            db.session.rollback()
            
            # Log the full error
            current_app.logger.error(f"Error creating incident: {str(e)}", exc_info=True)
            
            # Prepare error message
            error_msg = f'Une erreur est survenue lors de la création de l\'incident: {str(e)}'
            
            # Handle AJAX request
            if is_ajax:
                return jsonify({
                    'status': 'error', 
                    'message': error_msg
                }), 500
            
            # Handle non-AJAX request
            flash(error_msg, 'danger')
            return redirect(url_for('incidents.new_incident'))

    # GET request: render the new incident form
    return render_template('incidents/new_incident.html', units=units)

@incidents.route('/incident/<int:incident_id>')
@login_required
@permission_required(Permission.VIEW_INCIDENT)
def view_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    
    # Check if user has access to this incident
    if current_user.role in [UserRole.ADMIN, UserRole.EMPLOYEUR_DG]:
        # Admin and DG can view all incidents
        pass
    elif current_user.role == UserRole.EMPLOYEUR_ZONE:
        # Employeur Zone can only view incidents from units in their zone
        incident_unit = Unit.query.get(incident.unit_id)
        if not incident_unit or incident_unit.zone_id != current_user.zone_id:
            flash('Vous n\'avez pas accès à cet incident.', 'danger')
            return redirect(url_for(INCIDENT_LIST))
    else:
        # Other users can only view incidents from their unit
        if current_user.unit_id != incident.unit_id:
            flash('Vous n\'avez pas accès à cet incident.', 'danger')
            return redirect(url_for(INCIDENT_LIST))
    
    return render_template('incidents/view_incident.html', incident=incident)

@incidents.route('/incident/<int:incident_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.EDIT_INCIDENT)
def edit_incident(incident_id):
    # Prevent Employeur DG from accessing this route
    if current_user.role == UserRole.EMPLOYEUR_DG:
        flash('Vous n\'avez pas la permission de modifier des incidents.', 'danger')
        return redirect(url_for('incidents.list_incidents'))
    
    incident = Incident.query.get_or_404(incident_id)
    
    # Check if user has access to this incident
    if current_user.role == UserRole.ADMIN:
        # Admin can edit all incidents
        pass
    elif current_user.role == UserRole.EMPLOYEUR_ZONE:
        # Employeur Zone can only edit incidents from units in their zone
        incident_unit = Unit.query.get(incident.unit_id)
        if not incident_unit or incident_unit.zone_id != current_user.zone_id:
            flash('Vous n\'avez pas accès à cet incident.', 'danger')
            return redirect(url_for(INCIDENT_LIST))
    else:
        # Other users can only edit incidents from their unit
        if current_user.unit_id != incident.unit_id:
            flash('Vous n\'avez pas accès à cet incident.', 'danger')
            return redirect(url_for(INCIDENT_LIST))
    
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['wilaya', 'commune', 'localite', 'structure_type', 
                               'nature_cause', 'date_incident', 'mesures_prises', 
                               'impact', 'gravite']
            
            for field in required_fields:
                if not request.form.get(field):
                    raise ValueError(f"Le champ {field} est requis.")

            # Parse date
            try:
                date_incident = datetime.strptime(request.form.get('date_incident'), '%Y-%m-%dT%H:%M')
            except ValueError:
                raise ValueError("Format de date invalide.")

            # Update incident fields
            incident.wilaya = request.form.get('wilaya')
            incident.commune = request.form.get('commune')
            incident.localite = request.form.get('localite')
            incident.structure_type = request.form.get('structure_type')
            incident.nature_cause = request.form.get('nature_cause')
            incident.date_incident = date_incident
            incident.mesures_prises = request.form.get('mesures_prises')
            incident.impact = request.form.get('impact')
            incident.gravite = request.form.get('gravite')

            # Optional: Validate latitude and longitude if present
            latitude = request.form.get('latitude')
            longitude = request.form.get('longitude')
            if latitude and longitude:
                try:
                    incident.latitude = float(latitude)
                    incident.longitude = float(longitude)
                except ValueError:
                    current_app.logger.warning(f"Invalid coordinates: {latitude}, {longitude}")

            # Commit changes
            db.session.commit()
            flash('Incident modifié avec succès.', 'success')
            return redirect(url_for('incidents.view_incident', incident_id=incident.id))

        except ValueError as ve:
            # Handle validation errors
            db.session.rollback()
            current_app.logger.error(f"Validation Error in edit_incident: {str(ve)}")
            flash(str(ve), 'danger')
            return render_template('incidents/edit_incident.html', incident=incident)

        except Exception as e:
            # Catch-all for unexpected errors
            db.session.rollback()
            error_msg = f'Une erreur est survenue lors de la modification de l\'incident: {str(e)}'
            current_app.logger.error(error_msg, exc_info=True)
            flash(error_msg, 'danger')
            return render_template('incidents/edit_incident.html', incident=incident)

    return render_template('incidents/edit_incident.html', incident=incident)

@incidents.route('/incident/<int:incident_id>/delete', methods=['POST'])
@login_required
@permission_required(Permission.DELETE_INCIDENT)
def delete_incident(incident_id):
    # Prevent Employeur DG from accessing this route
    if current_user.role == UserRole.EMPLOYEUR_DG:
        flash('Vous n\'avez pas la permission de supprimer des incidents.', 'danger')
        return redirect(url_for('incidents.list_incidents'))
    
    incident = Incident.query.get_or_404(incident_id)
    
    if not current_user.role == UserRole.ADMIN and current_user.unit_id != incident.unit_id:
        flash('Vous n\'avez pas la permission de supprimer cet incident.', 'danger')
        return redirect(url_for(INCIDENT_LIST))
    
    try:
        db.session.delete(incident)
        db.session.commit()
        flash('Incident supprimé avec succès.', 'success')
        current_app.logger.info(f"Flash message set: Incident supprimé avec succès")
        current_app.logger.info(f"Session data: {dict(session)}")
        
        # Invalidate incident count cache
        cache.delete(get_incident_cache_key(current_user))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression de l\'incident: {str(e)}', 'danger')
    
    return redirect(url_for(INCIDENT_LIST))

@incidents.route('/incident/<int:incident_id>/resolve', methods=['POST'])
@login_required
@permission_required(Permission.RESOLVE_INCIDENT)
def resolve_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    if not current_user.role == UserRole.ADMIN and current_user.unit_id != incident.unit_id:
        flash('Vous n\'êtes pas autorisé à résoudre cet incident.', 'danger')
        return redirect(url_for(INCIDENT_LIST))
    
    if incident.status == 'Résolu':
        flash('Cet incident est déjà résolu.', 'warning')
        return redirect(url_for(INCIDENT_LIST))
    
    mesures_prises = request.form.get('mesures_prises')
    resolution_date = request.form.get('resolution_date')
    resolution_time = request.form.get('resolution_time')
    
    try:
        resolution_datetime = datetime.strptime(f"{resolution_date} {resolution_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        flash('Format de date ou d\'heure invalide.', 'error')
        return redirect(url_for(INCIDENT_LIST))
    
    if not mesures_prises:
        flash('Veuillez décrire les mesures prises pour résoudre l\'incident.', 'danger')
        return redirect(url_for(INCIDENT_LIST))
    
    incident.status = 'Résolu'
    incident.mesures_prises = mesures_prises
    incident.resolution_datetime = resolution_datetime
    db.session.commit()
    
    flash("L'incident a été marqué comme résolu.", 'success')
    current_app.logger.info("Flash message set: L'incident a été marqué comme résolu")
    current_app.logger.info(f"Session data: {dict(session)}")
    
    # Invalidate incident count cache
    cache.delete(get_incident_cache_key(current_user))
    
    return redirect(url_for(INCIDENT_LIST))

@incidents.route('/incident/<int:incident_id>/export_pdf')
@login_required
@permission_required(Permission.EXPORT_INCIDENT_PDF)
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

@incidents.route('/incidents/export/all/pdf')
@login_required
@permission_required(Permission.EXPORT_ALL_INCIDENTS_PDF)
def export_all_incidents_pdf():
    # Determine query based on user role
    if current_user.role == UserRole.ADMIN:
        # Admin can see all incidents
        incidents = Incident.query.order_by(Incident.date_incident.desc()).all()
    elif current_user.role == UserRole.EMPLOYEUR_DG:
        # DG can see all incidents
        incidents = Incident.query.order_by(Incident.date_incident.desc()).all()
    elif current_user.role == UserRole.EMPLOYEUR_ZONE:
        # Employeur Zone sees incidents from their zone
        incidents = Incident.query.join(Unit).filter(
            Unit.zone_id == current_user.zone_id
        ).order_by(Incident.date_incident.desc()).all()
    else:
        # Other roles see only incidents from their unit
        if not current_user.unit_id:
            flash('Vous n\'êtes pas assigné à une unité.', 'warning')
            return redirect(url_for('main.dashboard'))
        
        incidents = Incident.query.filter_by(unit_id=current_user.unit_id).order_by(Incident.date_incident.desc()).all()

    # Check if there are any incidents
    if not incidents:
        flash('Aucun incident à exporter.', 'warning')
        return redirect(url_for('main.dashboard'))

    # Generate PDF
    try:
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
        current_app.logger.error(f"Error generating PDF: {str(e)}")
        flash('Erreur lors de la génération du PDF.', 'danger')
        return redirect(url_for('main.dashboard'))

@incidents.route('/get_ai_explanation', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.GET_AI_EXPLANATION)
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

@incidents.route('/incidents/deep_analysis', methods=['POST'])
@login_required
@permission_required(Permission.DEEP_ANALYSIS)
def deep_incident_analysis():
    """
    Perform a deep analysis of an incident using AI.
    
    Returns:
        JSON response with comprehensive incident analysis
    """
    try:
        # Validate request
        if not request.is_json:
            current_app.logger.error('Deep Analysis: Invalid request format')
            return jsonify({
                'error': 'Format de requête invalide',
                'details': 'La requête doit être au format JSON'
            }), 400
        
        data = request.get_json()
        incident_id = data.get('incident_id')
        
        if not incident_id:
            current_app.logger.error('Deep Analysis: No incident ID provided')
            return jsonify({
                'error': 'ID de l\'incident manquant',
                'details': 'Un ID d\'incident valide est requis'
            }), 400
        
        # Fetch the incident
        incident = Incident.query.get(incident_id)
        
        if not incident:
            current_app.logger.error(f'Deep Analysis: Incident not found - ID {incident_id}')
            return jsonify({
                'error': 'Incident non trouvé',
                'details': f'Aucun incident trouvé avec l\'ID {incident_id}'
            }), 404
        
        # Prepare comprehensive context for deep analysis
        context = {
            'incident_details': {
                'id': incident.id,
                'title': incident.title or 'Aucun titre',
                'nature_cause': incident.nature_cause or 'Non spécifié',
                'impact': incident.impact or 'Non évalué',
                'mesures_prises': incident.mesures_prises or 'Aucune mesure',
                'gravite': incident.gravite or 'Non définie',
                'location': {
                    'wilaya': incident.wilaya or 'Non spécifiée',
                    'commune': incident.commune or 'Non spécifiée',
                    'localite': incident.localite or 'Non spécifiée',
                    'coordinates': f"{incident.latitude}, {incident.longitude}" if incident.latitude and incident.longitude else 'Coordonnées non disponibles'
                }
            }
        }
        
        # Use Mistral API for deep analysis
        api_key = os.getenv('MISTRAL_API_KEY') or current_app.config.get('MISTRAL_API_KEY')
        
        # Log key retrieval details (without exposing full key)
        current_app.logger.info(f'Mistral API key retrieved: {bool(api_key)}')
        current_app.logger.info(f'Key length: {len(api_key) if api_key else 0}')
        
        # Validate API key format
        if not api_key or len(api_key) < 10:
            current_app.logger.error('Mistral API key is invalid or missing')
            return jsonify({
                'error': 'Erreur de configuration du service IA',
                'details': 'La clé API Mistral n\'est pas configurée'
            }), 500
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        
        payload = {
            'model': 'mistral-large-latest',
            'messages': [
                {
                    'role': 'system', 
                    'content': """Vous êtes un analyste d'incidents expert. Fournissez une analyse approfondie, 
                    structurée et exploitable de l'incident. 
                    Votre analyse doit inclure :
                    1. Analyse détaillée des causes racines
                    2. Implications potentielles à long terme
                    3. Mesures préventives recommandées
                    4. Stratégies d'atténuation des risques
                    5. Améliorations systémiques potentielles
                    6. Analyser les données récupérées de la page :
                       - Nature et cause de l'incident
                       - Impact
                       - Mesures prises
                    7. Suggérer des solutions et expliquer les impacts
                    8. Fournir une conclusion
                    Limitez votre réponse à 800 tokens maximum.
                    Utilisez un formatage clair avec des titres et des listes à puces."""
                 
                },
                {
                    'role': 'user', 
                    'content': f"""Réalisez une analyse approfondie de cet incident :
                    
                    Contexte de l'incident :
                    {json.dumps(context, indent=2, ensure_ascii=False)}
                    
                    Fournissez une analyse comprehensive et nuancée qui va au-delà des détails superficiels.
                    Si les informations sont limitées, basez votre analyse sur ce qui est disponible."""
                }
            ],
            'temperature': 0.7,
            'max_tokens': 1800  # Increased token limit for more comprehensive analysis
        }
        
        # Make API call to Mistral
        try:
            # Configure more robust request parameters
            response = requests.post(
                'https://api.mistral.ai/v1/chat/completions', 
                headers=headers, 
                json=payload,
                timeout=(10, 45),  # (connect timeout, read timeout)
                verify=True,  # Ensure SSL certificate verification
            )
        except requests.exceptions.Timeout as timeout_error:
            current_app.logger.error(f'Deep Analysis: Request timeout - {str(timeout_error)}')
            return jsonify({
                'error': 'Délai de réponse dépassé',
                'details': 'Le service d\'analyse IA n\'a pas répondu dans le temps imparti. Veuillez réessayer plus tard.'
            }), 504  # Gateway Timeout status code
        
        except requests.exceptions.ConnectionError as conn_error:
            current_app.logger.error(f'Deep Analysis: Connection error - {str(conn_error)}')
            return jsonify({
                'error': 'Erreur de connexion',
                'details': 'Impossible de se connecter au service d\'analyse IA. Vérifiez votre connexion internet.'
            }), 503  # Service Unavailable status code
        
        except requests.exceptions.RequestException as req_error:
            current_app.logger.error(f'Deep Analysis: Request error - {str(req_error)}')
            return jsonify({
                'error': 'Erreur de communication',
                'details': 'Une erreur inattendue s\'est produite lors de la communication avec le service IA.'
            }), 500
        
        # Check response
        if response.status_code != 200:
            current_app.logger.error(f"Mistral API Error: {response.status_code} - {response.text}")
            return jsonify({
                'error': 'Échec de la génération de l\'analyse approfondie',
                'details': f'Code de statut : {response.status_code}',
                'raw_response': response.text
            }), 500
        
        # Extract the AI-generated analysis
        try:
            result = response.json()
            deep_analysis = result['choices'][0]['message']['content']
        except (KeyError, json.JSONDecodeError) as parse_error:
            current_app.logger.error(f'Deep Analysis: Parsing error - {str(parse_error)}')
            return jsonify({
                'error': 'Erreur de traitement de la réponse IA',
                'details': str(parse_error),
                'raw_response': response.text
            }), 500
        
        return jsonify({
            'deep_analysis': deep_analysis
        })
    
    except Exception as e:
        current_app.logger.error(f"Deep Analysis Unexpected Error: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Une erreur inattendue est survenue lors de l\'analyse approfondie',
            'details': str(e)
        }), 500
