from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Incident, Unit, UserRole
from datetime import datetime
from functools import wraps

# Create a Blueprint for departement routes
departement = Blueprint('departement', __name__)

def unit_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Allow admin users to access the route
        if current_user.role == UserRole.ADMIN:
            return f(*args, **kwargs)
        
        # Check if user has a unit or a zone
        if not current_user.unit_id and not current_user.zone_id:
            flash('Aucune unité ou zone assignée', 'error')
            return redirect(url_for('main_dashboard.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@departement.route('/departement/statistiques', methods=['GET'])
@login_required
@unit_required
def statistiques():
    # Check if the user is an admin
    is_admin = current_user.role == UserRole.ADMIN

    # If admin, show all incidents across all zones
    if is_admin:
        total_incidents = Incident.query.count()
        critical_incidents = Incident.query.filter_by(gravite='Critique').count()
        resolved_incidents = Incident.query.filter_by(status='Résolu').count()
    # If no unit is assigned, use the user's zone
    elif not current_user.unit_id and current_user.zone_id:
        # Get all units in the user's zone
        units_in_zone = Unit.query.filter_by(zone_id=current_user.zone_id).all()
        unit_ids = [unit.id for unit in units_in_zone]

        # Calculate incident statistics for all units in the zone
        total_incidents = Incident.query.filter(Incident.unit_id.in_(unit_ids)).count()
        critical_incidents = Incident.query.filter(
            Incident.unit_id.in_(unit_ids), 
            Incident.gravite=='Critique'
        ).count()
        resolved_incidents = Incident.query.filter(
            Incident.unit_id.in_(unit_ids), 
            Incident.status=='Résolu'
        ).count()
    else:
        # If a specific unit is assigned, use that unit's stats
        current_unit = current_user.assigned_unit

        # If no unit is found, show zero incidents
        if not current_unit:
            total_incidents = 0
            critical_incidents = 0
            resolved_incidents = 0
        else:
            # Calculate incident statistics
            total_incidents = Incident.query.filter_by(unit_id=current_unit.id).count()
            critical_incidents = Incident.query.filter_by(
                unit_id=current_unit.id, 
                gravite='Critique'
            ).count()
            resolved_incidents = Incident.query.filter_by(
                unit_id=current_unit.id, 
                status='Résolu'
            ).count()
    
    # Calculate resolution rate with safe division
    resolution_rate = (resolved_incidents / total_incidents * 100) if total_incidents > 0 else 0

    # Get recently resolved incidents
    if is_admin:
        recent_resolved = Incident.query.filter_by(status='Résolu').order_by(Incident.date_resolution.desc()).limit(5).all()
    elif not current_user.unit_id and current_user.zone_id:
        recent_resolved = Incident.query.filter(
            Incident.unit_id.in_(unit_ids),
            Incident.status=='Résolu'
        ).order_by(Incident.date_resolution.desc()).limit(5).all()
    else:
        recent_resolved = Incident.query.filter_by(
            unit_id=current_unit.id if current_unit else None,
            status='Résolu'
        ).order_by(Incident.date_resolution.desc()).limit(5).all()

    # Prepare incident stats with default values if no incidents
    incident_stats = {
        'total_incidents': total_incidents or 0,
        'critical_incidents': critical_incidents or 0,
        'resolved_incidents': resolved_incidents or 0,
        'resolution_rate': round(resolution_rate, 2) if total_incidents > 0 else 0,
        'is_admin': is_admin,
        'recent_resolved': [{
            'resolution_date': incident.date_resolution.strftime('%d/%m/%Y %H:%M'),
            'type': incident.nature_cause,
            'location': f"{incident.wilaya}, {incident.commune}",
            'resolution_duration': str(incident.date_resolution - incident.date_incident).split('.')[0] if incident.date_resolution else "N/A",
            'priority': 'high' if incident.gravite == 'Critique' else ('medium' if incident.gravite == 'Élevée' else 'low')
        } for incident in recent_resolved] if recent_resolved else []
    }

    return render_template(
        'departement/exploitation/statistiques.html', 
        datetime=datetime,
        incident_stats=incident_stats
    )

@departement.route('/departement/hse/template', methods=['GET'])
@login_required
@unit_required
def hse_template():
    return render_template('departement/hse_template.html')
