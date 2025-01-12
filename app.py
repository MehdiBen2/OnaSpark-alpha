from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from flask_migrate import Migrate
from werkzeug.security import check_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv
import random
from functools import wraps
from models import db, User, Unit, Incident, Zone, Center
from routes.auth import auth
from routes.profiles import profiles
from routes.incidents import incidents
from routes.units import units
from routes.users import users
from routes.database_admin import database_admin
from routes.water_quality import water_quality
from flask.cli import with_appcontext
import click
from utils.url_endpoints import *  # Import all URL endpoints
from utils.roles import UserRole

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///OnaDB.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = AUTH_LOGIN
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'warning'

# Register blueprints
app.register_blueprint(auth)
app.register_blueprint(profiles)
app.register_blueprint(incidents)
app.register_blueprint(units)
app.register_blueprint(users)
app.register_blueprint(database_admin)
app.register_blueprint(water_quality)

@app.cli.command("init-db")
@with_appcontext
def init_db_command():
    """Initialize the database."""
    from scripts.init_db import init_database
    init_database()
    click.echo('Initialized the database.')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not UserRole.has_permission(current_user.role, 'can_view_all_incidents'):
            flash('Vous devez être administrateur pour accéder à cette page.', 'danger')
            return redirect(url_for(INCIDENT_LIST))
        return f(*args, **kwargs)
    return decorated_function

def unit_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
            
        # Check if the role requires unit selection
        if not UserRole.requires_unit_selection(current_user.role):
            return f(*args, **kwargs)
            
        # All other roles need a unit
        if current_user.unit_id is None:
            flash("Vous devez sélectionner une unité pour accéder à cette page.", "warning")
            return redirect(url_for('select_unit'))
            
        return f(*args, **kwargs)
    return decorated_function

def get_user_incident_counts(user, include_author=False):
    """
    Retrieve incident counts based on user role and permissions.
    
    Args:
        user: Currently logged-in user
        include_author: If True, use author for filtering instead of unit_id
    
    Returns:
        Tuple of (total_incidents, resolved_incidents)
    """
    if user.role in [UserRole.ADMIN, UserRole.EMPLOYEUR_DG]:
        total_incidents = Incident.query.count()
        resolved_incidents = Incident.query.filter_by(status='Résolu').count()
    elif user.role == UserRole.EMPLOYEUR_ZONE:
        zone_units = Unit.query.filter_by(zone_id=user.zone_id).all()
        unit_ids = [unit.id for unit in zone_units]
        total_incidents = Incident.query.filter(Incident.unit_id.in_(unit_ids)).count()
        resolved_incidents = Incident.query.filter(Incident.unit_id.in_(unit_ids), Incident.status=='Résolu').count()
    else:
        # Use either unit_id or author based on the include_author flag
        if include_author:
            total_incidents = Incident.query.filter_by(author=user).count()
            resolved_incidents = Incident.query.filter_by(author=user, status='Résolu').count()
        else:
            total_incidents = Incident.query.filter_by(unit_id=user.unit_id).count()
            resolved_incidents = Incident.query.filter_by(unit_id=user.unit_id, status='Résolu').count()
    
    return total_incidents, resolved_incidents

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for(MAIN_DASHBOARD))
    return render_template('dashboard/landing.html')

@app.route('/main')
@login_required
def main_dashboard():
    # Get recent incidents (last 5)
    if current_user.role == UserRole.ADMIN:
        recent_incidents = Incident.query.order_by(Incident.date_incident.desc()).limit(5).all()
    else:
        recent_incidents = Incident.query.filter_by(author=current_user).order_by(Incident.date_incident.desc()).limit(5).all()
    
    # Get statistics
    total_incidents, resolved_incidents = get_user_incident_counts(current_user)
    pending_incidents = total_incidents - resolved_incidents
    
    return render_template('dashboard/main_dashboard.html',
                         recent_incidents=recent_incidents,
                         total_incidents=total_incidents,
                         resolved_incidents=resolved_incidents,
                         pending_incidents=pending_incidents,
                         datetime=datetime)

def get_dashboard_data():
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
        total_incidents, resolved_incidents = get_user_incident_counts(current_user)
        pending_incidents = total_incidents - resolved_incidents
        recent_incidents = Incident.query.order_by(Incident.date_incident.desc()).limit(5).all()
        
        total_users = User.query.count()
        total_units = Unit.query.count()
        total_zones = Zone.query.count()
        total_centers = Center.query.count()
        
    elif current_user.role == UserRole.EMPLOYEUR_ZONE:
        # Zone employer sees all incidents in their zone
        total_incidents, resolved_incidents = get_user_incident_counts(current_user)
        pending_incidents = total_incidents - resolved_incidents
        recent_incidents = Incident.query.filter(Incident.unit_id.in_([unit.id for unit in Unit.query.filter_by(zone_id=current_user.zone_id).all()])).order_by(Incident.date_incident.desc()).limit(5).all()
        
        # Zone statistics
        total_users = User.query.filter_by(zone_id=current_user.zone_id).count()
        total_units = len(Unit.query.filter_by(zone_id=current_user.zone_id).all())
        total_zones = 1  # Their own zone
        total_centers = Center.query.join(Unit).filter(Unit.zone_id == current_user.zone_id).count()
        
    elif current_user.role in [UserRole.EMPLOYEUR_UNITE, UserRole.UTILISATEUR]:
        # Unit employers and regular users see their unit's incidents
        total_incidents, resolved_incidents = get_user_incident_counts(current_user)
        pending_incidents = total_incidents - resolved_incidents
        recent_incidents = Incident.query.filter_by(unit_id=current_user.unit_id).order_by(Incident.date_incident.desc()).limit(5).all()
    
    return {
        'datetime': datetime,
        'total_incidents': total_incidents,
        'resolved_incidents': resolved_incidents,
        'pending_incidents': pending_incidents,
        'recent_incidents': recent_incidents,
        'total_users': total_users,
        'total_units': total_units,
        'total_zones': total_zones,
        'total_centers': total_centers,
        'permissions': permissions
    }

@app.route('/dashboard')
@login_required
@unit_required
def dashboard():
    dashboard_data = get_dashboard_data()
    return render_template('dashboard/main_dashboard.html', **dashboard_data)

@app.route('/services')
@login_required
@unit_required
def services():
    return render_template('services.html')

@app.route('/listes_dashboard')
@login_required
@unit_required
def listes_dashboard():
    total_incidents, resolved_incidents = get_user_incident_counts(current_user)
    return render_template('listes_dashboard.html',
                         total_incidents=total_incidents,
                         resolved_incidents=resolved_incidents)

@app.route('/exploitation')
@login_required
@unit_required
def exploitation():
    return render_template('departement/exploitation.html')

@app.route('/departements')
@login_required
@unit_required
def departements():
    return render_template('departement/departement.html')

REUSE_SECTIONS = {
    'introduction': 'departement/reuse/introduction.html',
    'regulations': 'departement/reuse/regulations.html',
    'methods': 'departement/reuse/methods.html',
    'case-studies': 'departement/reuse/case_studies.html',
    'documentation': 'departement/reuse/documentation.html'
}

@app.route('/departements/reuse')
@login_required
@unit_required
def reuse():
    return redirect(url_for('reuse_section', section='introduction'))

@app.route('/departements/reuse/<section>')
@login_required
@unit_required
def reuse_section(section):
    if section not in REUSE_SECTIONS:
        flash('Section non trouvée.', 'danger')
        return redirect(url_for('reuse_section', section='introduction'))
    
    template = REUSE_SECTIONS[section]
    return render_template(template, active_page=section)

@app.route('/departements/reuse/rapports')
@login_required
@unit_required
def rapports():
    # Get the count of incidents (you can modify this based on your needs)
    incidents_count = Incident.query.count()
    return render_template('departement/rapports.html', incidents_count=incidents_count)

@app.route('/departement/statistiques')
@login_required
@unit_required
def statistiques():
    return render_template('departement/statistiques.html', datetime=datetime)

# Remove Water Quality Assessment Routes
# These routes have been moved to routes/water_quality.py

@app.route('/units')
@login_required
def list_units():
    # Admin and DG see all units
    if current_user.role in [UserRole.ADMIN, UserRole.EMPLOYEUR_DG]:
        units = Unit.query.all()
        zones = Zone.query.all()
    # Zone employers see units in their zone
    elif current_user.role == UserRole.EMPLOYEUR_ZONE:
        units = Unit.query.filter_by(zone_id=current_user.zone_id).all()
        zones = [Zone.query.get(current_user.zone_id)]
    # Others only see their unit
    else:
        if current_user.unit_id:
            units = [Unit.query.get(current_user.unit_id)]
            zones = [Zone.query.get(current_user.zone_id)] if current_user.zone_id else []
        else:
            units = []
            zones = []
    
    return render_template('dashboard/list_units.html', units=units, zones=zones)

@app.route('/zones')
@login_required
def list_zones():
    zones = Zone.query.all()
    return render_template('admin/zones.html', zones=zones)

@app.route('/centers')
@login_required
def list_centers():
    # If user is admin, show all centers
    if current_user.role == UserRole.ADMIN:
        centers = Center.query.all()
        zones = Zone.query.all()
    # If user is Unit Officer, show only centers in their unit
    elif current_user.assigned_unit:
        centers = Center.query.filter_by(unit_id=current_user.assigned_unit.id).all()
        zones = []
    else:
        centers = []
        zones = []
    return render_template('admin/centers.html', centers=centers, zones=zones)

@app.route('/zones/create', methods=['POST'])
@login_required
def create_zone():
    if current_user.role != UserRole.ADMIN:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for(MAIN_DASHBOARD))
    
    try:
        zone = Zone(
            code=request.form['code'],
            name=request.form['name'],
            description=request.form['description'],
            address=request.form['address'],
            phone=request.form['phone'],
            email=request.form['email']
        )
        db.session.add(zone)
        db.session.commit()
        flash('Zone créée avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la création de la zone: {str(e)}', 'danger')
    
    return redirect(url_for(LIST_ZONES))

@app.route('/zones/edit/<int:id>', methods=['POST'])
@login_required
def edit_zone(id):
    if current_user.role != UserRole.ADMIN:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for(MAIN_DASHBOARD))
    
    zone = Zone.query.get_or_404(id)
    try:
        zone.code = request.form['code']
        zone.name = request.form['name']
        zone.description = request.form['description']
        zone.address = request.form['address']
        zone.phone = request.form['phone']
        zone.email = request.form['email']
        db.session.commit()
        flash('Zone mise à jour avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la mise à jour de la zone: {str(e)}', 'danger')
    
    return redirect(url_for(LIST_ZONES))

@app.route('/zones/delete/<int:id>', methods=['POST'])
@login_required
def delete_zone(id):
    if current_user.role != UserRole.ADMIN:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for(MAIN_DASHBOARD))
    
    try:
        zone = Zone.query.get_or_404(id)
        
        # Delete all units in the zone first
        for unit in zone.units:
            # Delete all centers in each unit
            for center in unit.centers:
                db.session.delete(center)
            db.session.delete(unit)
        
        # Finally delete the zone
        db.session.delete(zone)
        db.session.commit()
        flash('Zone supprimée avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression de la zone: {str(e)}', 'danger')
    
    return redirect(url_for(LIST_ZONES))

@app.route('/centers/create', methods=['POST'])
@login_required
def create_center():
    if current_user.role not in [UserRole.ADMIN, UserRole.UNIT_OFFICER]:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for(MAIN_DASHBOARD))
    
    try:
        # If Unit Officer, use their unit_id
        unit_id = current_user.unit_id if current_user.role == UserRole.UNIT_OFFICER else request.form['unit_id']
        
        center = Center(
            name=request.form['name'],
            description=request.form['description'],
            address=request.form['address'],
            phone=request.form['phone'],
            email=request.form['email'],
            unit_id=unit_id
        )
        db.session.add(center)
        db.session.commit()
        flash('Centre créé avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la création du centre: {str(e)}', 'danger')
    
    return redirect(url_for(LIST_CENTERS))

@app.route('/centers/edit/<int:id>', methods=['POST'])
@login_required
def edit_center(id):
    center = Center.query.get_or_404(id)
    
    # Check permissions
    if current_user.role == UserRole.UNIT_OFFICER and center.unit_id != current_user.unit_id:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for(MAIN_DASHBOARD))
    
    try:
        center.name = request.form['name']
        center.description = request.form['description']
        center.address = request.form['address']
        center.phone = request.form['phone']
        center.email = request.form['email']
        if current_user.role == UserRole.ADMIN:
            center.unit_id = request.form['unit_id']
        db.session.commit()
        flash('Centre mis à jour avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la mise à jour du centre: {str(e)}', 'danger')
    
    return redirect(url_for(LIST_CENTERS))

@app.route('/centers/delete/<int:id>', methods=['POST'])
@login_required
def delete_center(id):
    center = Center.query.get_or_404(id)
    
    # Check permissions
    if current_user.role == UserRole.UNIT_OFFICER and center.unit_id != current_user.unit_id:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for(MAIN_DASHBOARD))
    
    try:
        db.session.delete(center)
        db.session.commit()
        flash('Centre supprimé avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression du centre: {str(e)}', 'danger')
    
    return redirect(url_for(LIST_CENTERS))

@app.route('/select-unit', methods=['GET', 'POST'])
@login_required
def select_unit():
    # Zone employers, Admin, and DG don't need to select a unit
    if current_user.role in [UserRole.EMPLOYEUR_ZONE, UserRole.ADMIN, UserRole.EMPLOYEUR_DG]:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        zone_id = request.form.get('zone')
        unit_id = request.form.get('unit_id')
        
        if not zone_id or not unit_id:
            flash("Veuillez sélectionner une zone et une unité.", "warning")
            return redirect(url_for('select_unit'))
            
        # Verify the unit belongs to the selected zone
        unit = Unit.query.get(unit_id)
        if not unit or str(unit.zone_id) != zone_id:
            flash("Unité invalide sélectionnée.", "danger")
            return redirect(url_for('select_unit'))
            
        # Update user's unit
        current_user.unit_id = unit_id
        db.session.commit()
        
        flash(f"Vous êtes maintenant connecté à l'unité: {unit.name}", "success")
        return redirect(url_for('dashboard'))
        
    # GET request - show selection form
    if current_user.role == UserRole.ADMIN:
        zones = Zone.query.all()
    elif current_user.zone_id:
        zones = [Zone.query.get(current_user.zone_id)]
    else:
        zones = []
        
    return render_template('incidents/select_unit.html', zones=zones)

@app.route('/api/units/<int:zone_id>')
@login_required
def get_zone_units(zone_id):
    permissions = UserRole.get_permissions(current_user.role)
    
    # Check if user has access to this zone
    if not permissions.get('can_view_all_units', False):
        if current_user.zone_id != zone_id:
            return jsonify([])
            
    units = Unit.query.filter_by(zone_id=zone_id).all()
    return jsonify([{'id': unit.id, 'name': unit.name} for unit in units])

@app.route('/login')
def login():
    return render_template('auth/login.html')

@app.route('/new-incident')
@login_required
def new_incident():
    return render_template('incidents/new_incident.html')

@app.route('/docs')
def serve_docs():
    return send_file('docs/index.html')

if __name__ == '__main__':
    # Create default admin user if it doesn't exist
    with app.app_context():
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                role=UserRole.ADMIN
            )
            admin_user.set_password('admin')
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created successfully!")
    
    print("\n" + "="*50)
    print("Application is running!")
    print("Default admin credentials:")
    print("Username: admin")
    print("Password: admin")
    print("Please change these credentials after first login.")
    print("="*50 + "\n")
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)
