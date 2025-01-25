from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Incident, Unit
from datetime import datetime
from functools import wraps

# Create a Blueprint for departement routes
departement = Blueprint('departement', __name__)

def unit_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
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
    # If no unit is assigned, use the user's zone
    if not current_user.unit_id and current_user.zone_id:
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

        if not current_unit:
            flash('Aucune unité assignée', 'error')
            return redirect(url_for('main_dashboard.dashboard'))

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

    # Prepare incident stats with default values if no incidents
    incident_stats = {
        'total_incidents': total_incidents or 0,
        'critical_incidents': critical_incidents or 0,
        'resolved_incidents': resolved_incidents or 0,
        'resolution_rate': round(resolution_rate, 2) if total_incidents > 0 else 0
    }

    return render_template(
        'departement/exploitation/statistiques.html', 
        datetime=datetime,
        incident_stats=incident_stats
    )
