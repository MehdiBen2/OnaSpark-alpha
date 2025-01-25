from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Incident
from datetime import datetime
from functools import wraps

# Create a Blueprint for departement routes
departement = Blueprint('departement', __name__)

def unit_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.unit:
            flash('Aucune unité assignée', 'error')
            return redirect(url_for('main_dashboard.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@departement.route('/departement/statistiques', methods=['GET'])
@login_required
@unit_required
def statistiques():
    # Get current user's unit
    current_unit = current_user.unit

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
    
    # Calculate resolution rate
    resolution_rate = (resolved_incidents / total_incidents * 100) if total_incidents > 0 else 0

    incident_stats = {
        'total_incidents': total_incidents,
        'critical_incidents': critical_incidents,
        'resolved_incidents': resolved_incidents,
        'resolution_rate': round(resolution_rate, 2)
    }

    return render_template(
        'departement/exploitation/statistiques.html', 
        datetime=datetime,
        incident_stats=incident_stats
    )
