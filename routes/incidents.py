from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
from flask_login import login_required, current_user
from models import db, Incident, Unit
from datetime import datetime
from functools import wraps
from utils.decorators import admin_required, unit_required
from utils.pdf_generator import create_incident_pdf
import os

incidents = Blueprint('incidents', __name__)

@incidents.route('/incidents')
@login_required
@unit_required
def incident_list():
    if current_user.role == 'Admin':
        incidents = Incident.query.order_by(Incident.date_incident.desc()).all()
    else:
        incidents = Incident.query.filter_by(unit_id=current_user.unit_id).order_by(Incident.date_incident.desc()).all()
    return render_template('incident_list.html', incidents=incidents)

@incidents.route('/incident/new', methods=['GET', 'POST'])
@login_required
@unit_required
def new_incident():
    # Get all available units for admin, or just the user's unit for others
    if current_user.role == 'Admin':
        units = Unit.query.all()
    else:
        if not current_user.unit_id:
            flash('Vous devez être assigné à une unité pour signaler un incident.', 'warning')
            return redirect(url_for('select_unit'))
        units = [current_user.assigned_unit] if current_user.assigned_unit else []

    if request.method == 'POST':
        try:
            # Get the unit_id from the form
            unit_id = request.form.get('unit_id')
            
            # Validate unit_id
            if not unit_id:
                flash('Une unité est requise pour créer un incident.', 'error')
                return render_template('new_incident.html', units=units)

            # For non-admin users, verify they're creating an incident for their own unit
            if current_user.role != 'Admin' and str(current_user.assigned_unit.id) != str(unit_id):
                flash('Vous ne pouvez créer des incidents que pour votre unité.', 'error')
                return render_template('new_incident.html', units=units)

            # Create the incident
            incident = Incident(
                title=request.form.get('title'),
                wilaya=request.form.get('wilaya'),
                commune=request.form.get('commune'),
                localite=request.form.get('localite'),
                structure_type=request.form.get('structure_type'),
                nature_cause=request.form.get('nature_cause'),
                date_incident=datetime.strptime(request.form.get('date_incident'), '%Y-%m-%dT%H:%M'),
                mesures_prises=request.form.get('mesures_prises'),
                impact=request.form.get('impact'),
                gravite=request.form.get('gravite').lower(),
                status='Nouveau',
                user_id=current_user.id,
                unit_id=unit_id
            )
            db.session.add(incident)
            db.session.commit()
            flash('Incident signalé avec succès.', 'success')
            return redirect(url_for('incidents.incident_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Une erreur est survenue lors de la création de l\'incident: {str(e)}', 'error')
            return render_template('new_incident.html', units=units)

    return render_template('new_incident.html', units=units)

@incidents.route('/incident/<int:incident_id>')
@login_required
@unit_required
def view_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    if not current_user.role == 'Admin' and current_user.unit_id != incident.unit_id:
        flash('Vous n\'avez pas accès à cet incident.', 'danger')
        return redirect(url_for('incidents.incident_list'))
    return render_template('view_incident.html', incident=incident)

@incidents.route('/incident/<int:incident_id>/edit', methods=['GET', 'POST'])
@login_required
@unit_required
def edit_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    if not current_user.role == 'Admin' and current_user.unit_id != incident.unit_id:
        flash('Vous n\'avez pas accès à cet incident.', 'danger')
        return redirect(url_for('incidents.incident_list'))
    
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
            return redirect(url_for('incidents.view_incident', incident_id=incident.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour de l\'incident: {str(e)}', 'danger')
            return render_template('edit_incident.html', incident=incident)
    
    return render_template('edit_incident.html', incident=incident)

@incidents.route('/incident/<int:incident_id>/delete', methods=['POST'])
@login_required
@unit_required
def delete_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    
    if not current_user.role == 'Admin' and current_user.unit_id != incident.unit_id:
        flash('Vous n\'avez pas la permission de supprimer cet incident.', 'danger')
        return redirect(url_for('incidents.incident_list'))
    
    try:
        db.session.delete(incident)
        db.session.commit()
        flash('Incident supprimé avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression de l\'incident: {str(e)}', 'danger')
    
    return redirect(url_for('incidents.incident_list'))

@incidents.route('/incident/<int:incident_id>/resolve', methods=['POST'])
@login_required
@unit_required
def resolve_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    if not current_user.role == 'Admin' and current_user.unit_id != incident.unit_id:
        flash('Vous n\'êtes pas autorisé à résoudre cet incident.', 'danger')
        return redirect(url_for('incidents.incident_list'))
    
    if incident.status == 'Résolu':
        flash('Cet incident est déjà résolu.', 'warning')
        return redirect(url_for('incidents.incident_list'))
    
    mesures_prises = request.form.get('mesures_prises')
    if not mesures_prises:
        flash('Veuillez décrire les mesures prises pour résoudre l\'incident.', 'danger')
        return redirect(url_for('incidents.incident_list'))
    
    incident.status = 'Résolu'
    incident.mesures_prises = mesures_prises
    incident.date_resolution = datetime.now()
    db.session.commit()
    
    flash('L\'incident a été marqué comme résolu.', 'success')
    return redirect(url_for('incidents.incident_list'))

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
        return redirect(url_for('incidents.incident_list'))

@incidents.route('/incidents/export_all_pdf')
@login_required
@unit_required
def export_all_incidents_pdf():
    try:
        # Get all incidents based on user role
        if current_user.role == 'Admin':
            incidents = Incident.query.all()
        else:
            incidents = Incident.query.filter_by(unit_id=current_user.unit_id).all()
        
        if not incidents:
            flash('Aucun incident à exporter.', 'warning')
            return redirect(url_for('incidents.incident_list'))
        
        # Create temporary directory if it doesn't exist
        temp_dir = os.path.join(current_app.root_path, 'temp')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        # Generate PDF filename
        filename = f'all_incidents_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        pdf_path = os.path.join(temp_dir, filename)
        
        # Get unit name safely
        unit_name = current_user.assigned_unit.name if current_user.assigned_unit else "Toutes les unités" if current_user.role == 'Admin' else "Unité non spécifiée"
        
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
        return redirect(url_for('incidents.incident_list'))

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
            return redirect(url_for('incidents.merge_incident', incident_id=incident_id))
            
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
            return redirect(url_for('incidents.view_incident', incident_id=incident.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la fusion de l\'incident: {str(e)}', 'danger')
            return redirect(url_for('incidents.merge_incident', incident_id=incident_id))
    
    return render_template('merge_incident.html', incident=incident, units=units)

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
            return redirect(url_for('incidents.batch_merge'))
            
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
            return redirect(url_for('incidents.incident_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la fusion des incidents: {str(e)}', 'danger')
            return redirect(url_for('incidents.batch_merge'))
    
    return render_template('batch_merge.html', units=units)
