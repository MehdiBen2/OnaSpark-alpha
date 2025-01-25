from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from datetime import datetime
import traceback
import logging

from models import db, User, Unit, Incident, Zone, Center
from utils.roles import UserRole
from utils.url_endpoints import *
from utils.incident_utils import get_user_incident_counts
from utils.decorators import unit_required
from extensions import cache

# Create a logger for this module
logger = logging.getLogger(__name__)

# Create a blueprint for dashboard routes
main_dashboard = Blueprint('main_dashboard', __name__)

def get_dashboard_data():
    """
    Centralized dashboard data fetching based on user role
    
    Returns:
        dict: Dashboard data specific to user's role and permissions
    """
    # Centralized dashboard data fetching
    permissions = UserRole.get_permissions(current_user.role)

    # Default values
    total_incidents = None
    resolved_incidents = None
    pending_incidents = None
    recent_incidents = None
    total_users = None
    total_units = None
    total_zones = None
    total_centers = None

    if current_user.role == UserRole.ADMIN:
        # Admin sees everything
        incident_counts = get_user_incident_counts(current_user)
        total_incidents = incident_counts['total_incidents']
        resolved_incidents = incident_counts['resolved_incidents']
        closed_incidents = incident_counts['closed_incidents']
        pending_incidents = total_incidents - resolved_incidents - closed_incidents
        recent_incidents = Incident.query.order_by(Incident.date_incident.desc()).limit(5).all()
        
        total_users = User.query.count()
        total_units = Unit.query.count()
        total_zones = Zone.query.count()
        total_centers = Center.query.count()
        
    elif current_user.role == UserRole.EMPLOYEUR_ZONE:
        # Zone employer sees all incidents in their zone
        incident_counts = get_user_incident_counts(current_user)
        total_incidents = incident_counts['total_incidents']
        resolved_incidents = incident_counts['resolved_incidents']
        closed_incidents = incident_counts['closed_incidents']
        pending_incidents = total_incidents - resolved_incidents - closed_incidents
        recent_incidents = Incident.query.filter(Incident.unit_id.in_([unit.id for unit in Unit.query.filter_by(zone_id=current_user.zone_id).all()])).order_by(Incident.date_incident.desc()).limit(5).all()
        
        # Zone statistics
        total_users = User.query.filter_by(zone_id=current_user.zone_id).count()
        total_units = len(Unit.query.filter_by(zone_id=current_user.zone_id).all())
        total_zones = 1  # Their own zone
        total_centers = Center.query.join(Unit).filter(Unit.zone_id == current_user.zone_id).count()
        
    elif current_user.role in [UserRole.EMPLOYEUR_UNITE, UserRole.UTILISATEUR]:
        # Unit employers and regular users see their unit's incidents
        incident_counts = get_user_incident_counts(current_user)
        total_incidents = incident_counts['total_incidents']
        resolved_incidents = incident_counts['resolved_incidents']
        closed_incidents = incident_counts['closed_incidents']
        pending_incidents = total_incidents - resolved_incidents - closed_incidents
        recent_incidents = Incident.query.filter_by(unit_id=current_user.unit_id).order_by(Incident.date_incident.desc()).limit(5).all()
    
    return {
        'datetime': datetime,
        'total_incidents': total_incidents,
        'resolved_incidents': resolved_incidents,
        'closed_incidents': closed_incidents,
        'pending_incidents': pending_incidents,
        'recent_incidents': recent_incidents,
        'total_users': total_users,
        'total_units': total_units,
        'total_zones': total_zones,
        'total_centers': total_centers,
        'permissions': permissions
    }

@main_dashboard.route('/main')
@login_required
def dashboard_main():
    """
    Main dashboard route with incident counts and user-specific data.
    
    Returns:
        Rendered dashboard template with incident counts and user information
    """
    try:
        # Get recent incidents (last 5)
        if current_user.role == UserRole.ADMIN:
            recent_incidents = Incident.query.order_by(Incident.date_incident.desc()).limit(5).all()
        else:
            recent_incidents = Incident.query.filter_by(author=current_user).order_by(Incident.date_incident.desc()).limit(5).all()
        
        # Get statistics
        incident_counts = get_user_incident_counts(current_user)
        total_incidents = incident_counts['total_incidents']
        resolved_incidents = incident_counts['resolved_incidents']
        nouveau_incidents = incident_counts['nouveau_incidents']
        pending_incidents = nouveau_incidents
        
        return render_template('dashboard/main_dashboard.html',
                             recent_incidents=recent_incidents,
                             total_incidents=total_incidents,
                             resolved_incidents=resolved_incidents,
                             pending_incidents=pending_incidents,
                             datetime=datetime)
    
    except Exception as e:
        # Comprehensive error logging
        logger.error(f"Dashboard rendering error: {str(e)}")
        logger.error(f"Error details: {traceback.format_exc()}")
        logger.error(f"Current user: {current_user.username if current_user.is_authenticated else 'Not authenticated'}")
        logger.error(f"Current user role: {current_user.role if current_user.is_authenticated else 'N/A'}")
        
        # Flash a user-friendly error message
        flash('Une erreur s\'est produite lors du chargement du tableau de bord.', 'danger')
        
        # Attempt to redirect to a safe fallback route
        try:
            return redirect(url_for('landing.index'))
        except Exception as redirect_error:
            logger.critical(f"Failed to redirect: {str(redirect_error)}")
            # If all else fails, return a simple error response
            return "Une erreur critique s'est produite. Veuillez contacter le support.", 500

@main_dashboard.route('/dashboard')
@login_required
def dashboard():
    """
    Detailed dashboard route with comprehensive user and incident information
    
    Returns:
        Rendered dashboard template with detailed context
    """
    try:
        # Get incident counts for the current user
        incident_counts = get_user_incident_counts(current_user)
        
        # Get user's unit and zone information
        user_unit = Unit.query.get(current_user.unit_id) if current_user.unit_id else None
        user_zone = Zone.query.get(current_user.zone_id) if current_user.zone_id else None
        
        # Prepare context for dashboard rendering
        context = {
            'total_incidents': incident_counts.get('total_incidents', 0),
            'resolved_incidents': incident_counts.get('resolved_incidents', 0),
            'closed_incidents': incident_counts.get('closed_incidents', 0),
            'pending_incidents': incident_counts.get('nouveau_incidents', 0),
            'user_unit': user_unit,
            'user_zone': user_zone,
        }
        
        # Render dashboard with context
        return render_template('dashboard/main_dashboard.html', **context)
    
    except Exception as e:
        # Comprehensive error logging
        logger.error(f"Dashboard rendering error: {str(e)}")
        logger.error(f"Error details: {traceback.format_exc()}")
        logger.error(f"Current user: {current_user.username if current_user.is_authenticated else 'Not authenticated'}")
        logger.error(f"Current user role: {current_user.role if current_user.is_authenticated else 'N/A'}")
        
        # Flash a user-friendly error message
        flash('Une erreur s\'est produite lors du chargement du tableau de bord.', 'danger')
        
        # Attempt to redirect to a safe fallback route
        try:
            return redirect(url_for('landing.index'))
        except Exception as redirect_error:
            logger.critical(f"Failed to redirect: {str(redirect_error)}")
            # If all else fails, return a simple error response
            return "Une erreur critique s'est produite. Veuillez contacter le support.", 500

@main_dashboard.route('/listes_dashboard')
@login_required
def listes_dashboard():
    """
    Dashboard listing route with incident counts
    
    Returns:
        Rendered dashboard listing template
    """
    try:
        incident_counts = get_user_incident_counts(current_user)
        total_incidents = incident_counts['total_incidents']
        resolved_incidents = incident_counts['resolved_incidents']
        closed_incidents = incident_counts['closed_incidents']
        return render_template('listes_dashboard.html',
                             total_incidents=total_incidents,
                             resolved_incidents=resolved_incidents,
                             closed_incidents=closed_incidents)
    
    except Exception as e:
        # Comprehensive error logging
        logger.error(f"Dashboard rendering error: {str(e)}")
        logger.error(f"Error details: {traceback.format_exc()}")
        logger.error(f"Current user: {current_user.username if current_user.is_authenticated else 'Not authenticated'}")
        logger.error(f"Current user role: {current_user.role if current_user.is_authenticated else 'N/A'}")
        
        # Flash a user-friendly error message
        flash('Une erreur s\'est produite lors du chargement du tableau de bord.', 'danger')
        
        # Attempt to redirect to a safe fallback route
        try:
            return redirect(url_for('landing.index'))
        except Exception as redirect_error:
            logger.critical(f"Failed to redirect: {str(redirect_error)}")
            # If all else fails, return a simple error response
            return "Une erreur critique s'est produite. Veuillez contacter le support.", 500
