from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from flask_migrate import Migrate
from werkzeug.security import check_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv
import random
from functools import wraps
from models import db, User, Unit, Incident, Zone, Center, Infrastructure
from routes.auth import auth
from routes.profiles import profiles
from routes.incidents import incidents
from routes.infrastructures import infrastructures
from routes.units import units
from routes.users import users
from routes.database_admin import database_admin
from routes.water_quality import water_quality
from routes.documentation import documentation
from flask.cli import with_appcontext
import click
from utils.url_endpoints import *  # Import all URL endpoints
from utils.permissions import UserRole
from routes.landing import landing
from extensions import cache  # Import cache from extensions
from utils.incident_utils import get_user_incident_counts  # Import from new utils module
from routes.spark_agent_routes import get_mistral_api_key, spark_agent
from routes.main_dashboard import main_dashboard
from routes.departement import departement  # Add this import
from routes.centers import centers
from routes.bilan_routes import bilan_bp

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///OnaDB.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize cache with app after creating the app
cache.init_app(app)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = AUTH_LOGIN
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'warning'

# Register blueprints
app.register_blueprint(spark_agent, url_prefix='/spark-agent')
app.register_blueprint(auth)
app.register_blueprint(incidents)
app.register_blueprint(infrastructures)
app.register_blueprint(main_dashboard)
app.register_blueprint(departement)
app.register_blueprint(landing)
app.register_blueprint(users)
app.register_blueprint(water_quality)
app.register_blueprint(profiles)
app.register_blueprint(units)
app.register_blueprint(documentation)
app.register_blueprint(database_admin)
app.register_blueprint(centers)
app.register_blueprint(bilan_bp, url_prefix='/departement/exploitation')

# Remove the old route definition for statistiques
# This is now handled by the departement Blueprint

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
        # Exempt certain roles from unit requirement
        if current_user.role in [UserRole.EMPLOYEUR_ZONE, UserRole.ADMIN, UserRole.EMPLOYEUR_DG]:
            return f(*args, **kwargs)
        
        # Check if user has a unit
        if not current_user.unit_id:
            flash('Vous devez sélectionner une unité avant de continuer.', 'warning')
            return redirect(url_for('select_unit'))
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/invalidate_incident_cache', methods=['POST'])
@login_required
def invalidate_incident_cache():
    """
    Endpoint to manually invalidate incident count cache.
    Useful after creating, updating, or deleting incidents.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.EMPLOYEUR_DG]:
        flash('Unauthorized to invalidate cache', 'error')
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    # Clear all keys starting with 'incident_counts_'
    cache.delete_memoized(get_user_incident_counts)
    
    flash('Incident count cache has been invalidated', 'success')
    return jsonify({'status': 'success', 'message': 'Cache invalidated'}), 200

@app.route('/services')
@login_required
def services():
    return render_template('services.html')

@app.route('/exploitation')
@login_required
def exploitation():
    return render_template('departement/exploitation.html')

@app.route('/departements')
@login_required
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
def reuse():
    return redirect(url_for('reuse_section', section='introduction'))

@app.route('/departements/reuse/<section>')
@login_required
def reuse_section(section):
    if section not in REUSE_SECTIONS:
        flash('Section non trouvée.', 'danger')
        return redirect(url_for('reuse_section', section='introduction'))
    
    template = REUSE_SECTIONS[section]
    return render_template(template, active_page=section)

@app.route('/departements/reuse/rapports')
@login_required
def rapports():
    
    # Get the count of incidents (you can modify this based on your needs)
    incident_counts = get_user_incident_counts(current_user)
    incidents_count = incident_counts['total_incidents']
    return render_template('departement/rapports.html', incidents_count=incidents_count)


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
        return redirect(url_for('main_dashboard.dashboard'))
    
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
    
    return redirect(url_for('main_dashboard.dashboard'))

@app.route('/zones/edit/<int:id>', methods=['POST'])
@login_required
def edit_zone(id):
    if current_user.role != UserRole.ADMIN:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('main_dashboard.dashboard'))
    
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
    
    return redirect(url_for('main_dashboard.dashboard'))

@app.route('/zones/delete/<int:id>', methods=['POST'])
@login_required
def delete_zone(id):
    if current_user.role != UserRole.ADMIN:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('main_dashboard.dashboard'))
    
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
    
    return redirect(url_for('main_dashboard.dashboard'))

@app.route('/centers/create', methods=['POST'])
@login_required
def create_center():
    if current_user.role not in [UserRole.ADMIN, UserRole.UNIT_OFFICER]:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('main_dashboard.dashboard'))
    
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
    
    return redirect(url_for('main_dashboard.dashboard'))

@app.route('/centers/edit/<int:id>', methods=['POST'])
@login_required
def edit_center(id):
    center = Center.query.get_or_404(id)
    
    # Check permissions
    if current_user.role == UserRole.UNIT_OFFICER and center.unit_id != current_user.unit_id:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('main_dashboard.dashboard'))
    
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
    
    return redirect(url_for('main_dashboard.dashboard'))

@app.route('/centers/delete/<int:id>', methods=['POST'])
@login_required
def delete_center(id):
    center = Center.query.get_or_404(id)
    
    # Check permissions
    if current_user.role == UserRole.UNIT_OFFICER and center.unit_id != current_user.unit_id:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('main_dashboard.dashboard'))
    
    try:
        db.session.delete(center)
        db.session.commit()
        flash('Centre supprimé avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression du centre: {str(e)}', 'danger')
    
    return redirect(url_for('main_dashboard.dashboard'))

@app.route('/select-unit', methods=['GET', 'POST'])
@login_required
def select_unit():
    # Exempt certain roles from unit selection
    if current_user.role in [UserRole.EMPLOYEUR_ZONE, UserRole.ADMIN, UserRole.EMPLOYEUR_DG]:
        return redirect(url_for('main_dashboard.dashboard'))
    
    # If user has no zone, they need to be assigned first
    if not current_user.zone_id:
        flash("Vous devez d'abord être assigné à une zone par un administrateur.", "warning")
        return redirect(url_for('main_dashboard.dashboard'))
    
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
        return redirect(url_for('main_dashboard.dashboard'))
        
    # GET request - show selection form
    zones = [Zone.query.get(current_user.zone_id)]
    
    # Get units for the zone
    units = Unit.query.filter_by(zone_id=current_user.zone_id).all()
    
    return render_template('select_unit.html', zones=zones, units=units)

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

@app.route('/test_error')
def test_error():
    # This will deliberately cause a 500 error
    return 1 / 0

@app.route('/spark-agent')
@login_required
def spark_agent():
    return render_template('sparkagent/spark_agent.html')

@app.route(f'/{GET_MISTRAL_API_KEY}')
@login_required
def get_mistral_api_key_route():
    """
    Wrapper route for the Mistral API key retrieval function.
    """
    return get_mistral_api_key()

# Utility function to convert enum-style strings to human-readable labels
def format_epuration_type(epuration_type):
    if not epuration_type:
        return None
    
    epuration_type_mapping = {
        'BOUES_ACTIVEES': 'Boues activées',
        'LAGUNAGE_NATUREL': 'Lagunage naturel',
        'FILTRES_PLANTES': 'Filtres plantés',
        'DISQUES_BIOLOGIQUES': 'Disques biologiques',
        'MEMBRANES': 'Traitement membranaire',
        'AUTRE': 'Autre type de traitement'
    }
    
    return epuration_type_mapping.get(epuration_type, epuration_type)

@app.route('/departements/infrastructure/<int:infrastructure_id>', methods=['GET'])
def get_infrastructure_details(infrastructure_id):
    try:
        # Get infrastructure details from database
        infrastructure = Infrastructure.query.get_or_404(infrastructure_id)
        
        return jsonify({
            'success': True,
            'infrastructure': {
                'id': infrastructure.id,
                'nom': infrastructure.nom,
                'type': infrastructure.type,
                'localisation': infrastructure.localisation,
                'capacite': infrastructure.capacite,
                'etat': infrastructure.etat,
                'epuration_type': format_epuration_type(infrastructure.epuration_type)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Add error handling for common HTTP errors and exceptions
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/error.html', error_code=404, error_message="Page non trouvée"), 404

@app.errorhandler(500)
def internal_error(error):
    import traceback
    error_details = traceback.format_exc()
    return render_template('errors/error.html', error_code=500, error_message="Erreur interne du serveur", error_details=error_details), 500

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/error.html', error_code=403, error_message="Accès non autorisé"), 403

@app.errorhandler(Exception)
def handle_exception(error):
    import traceback
    error_details = traceback.format_exc()
    return render_template('errors/error.html', error_code=500, error_message="Une erreur inattendue s'est produite", error_details=error_details), 500

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
