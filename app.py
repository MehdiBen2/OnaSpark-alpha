from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from flask_migrate import Migrate
from werkzeug.security import check_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv
from urllib.parse import urlparse
from utils.pdf_generator import create_incident_pdf
import random
from functools import wraps
from openpyxl import Workbook
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from models import db, User, Unit, Incident, Zone, Center
from routes.auth import auth
from routes.profiles import profiles
from routes.incidents import incidents
from routes.units import units
from routes.users import users
from routes.database_admin import database_admin
from flask.cli import with_appcontext
import click
from utils.url_endpoints import *  # Import all URL endpoints
from utils.water_quality import assess_water_quality, get_parameter_metadata, generate_water_quality_pdf

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

class UserRole:
    ADMIN = 'Admin'
    DG = 'DG'
    ZONE_EMPLOYER = 'Zone Employer'
    UNIT_OFFICER = 'Unit Officer'
    REGULAR_USER = 'Regular User'

    @classmethod
    def requires_unit_selection(cls, role):
        return role not in [cls.ADMIN, cls.DG, cls.ZONE_EMPLOYER]

    @classmethod
    def get_permissions(cls, role):
        permissions = {
            cls.ADMIN: {
                'can_view_all_incidents': True,
                'can_view_all_units': True,
                'can_view_zone_incidents': True,
            },
            cls.DG: {
                'can_view_all_incidents': True,
                'can_view_all_units': True,
                'can_view_zone_incidents': True,
            },
            cls.ZONE_EMPLOYER: {
                'can_view_zone_incidents': True,
            },
            cls.UNIT_OFFICER: {},
            cls.REGULAR_USER: {},
        }
        return permissions.get(role, {})

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in [UserRole.ADMIN, UserRole.DG]:
            flash('Vous devez être administrateur pour accéder à cette page.', 'danger')
            return redirect(url_for(INCIDENT_LIST))
        return f(*args, **kwargs)
    return decorated_function

def unit_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
            
        # Zone employers don't need a unit
        if current_user.role == 'Employeur Zone':
            return f(*args, **kwargs)
            
        # Admin and DG don't need a unit
        if current_user.role in ['Admin', 'Employeur DG']:
            return f(*args, **kwargs)
            
        # All other roles need a unit
        if current_user.unit_id is None:
            flash("Vous devez sélectionner une unité pour accéder à cette page.", "warning")
            return redirect(url_for('select_unit'))
            
        return f(*args, **kwargs)
    return decorated_function

# Water and sanitation phrases
WATER_PHRASES = [
    "L'eau est l'essence de la vie ; préservons-la pour les générations futures.",
    "L'assainissement est une question de dignité ; assurons-le pour tous.",
    "Chaque goutte compte dans la préservation de nos ressources en eau.",
    "Un environnement propre commence par un bon assainissement.",
    "La qualité de l'eau reflète la santé de notre société.",
    "Protéger l'eau, c'est protéger la vie.",
    "L'assainissement est la clé d'un environnement sain.",
    "L'eau propre est un droit fondamental.",
    "Ensemble pour une meilleure gestion de l'eau.",
    "La propreté de l'eau est notre responsabilité collective."
]

# Water quality assessment constants
WATER_QUALITY_THRESHOLDS = {
    'microbiological': {
        'coliform_fecal': {'A': 100, 'B': 1000},
        'nematodes': {'A': 0.1, 'B': 1.0}
    },
    'physical': {
        'ph': {'min': 6.5, 'max': 8.5},
        'mes': {'max': 30},
        'ce': {'max': 3}
    },
    'chemical': {
        'dbo5': {'max': 30},
        'dco': {'max': 90},
        'chlorure': {'max': 10}
    },
    'toxic': {
        'cadmium': {'max': 0.05},
        'mercury': {'max': 0.002},
        'arsenic': {'max': 0.5},
        'lead': {'max': 0.05}
    }
}

CROP_CATEGORIES = {
    'category1': {
        'name': 'Légumes consommés crus',
        'requirements': {'micro': 'A', 'physico': 'OK'},
        'restrictions': []
    },
    'category2': {
        'name': 'Arbres fruitiers',
        'requirements': {'micro': 'B', 'physico': 'OK'},
        'restrictions': ['Arrêter l\'irrigation 2 semaines avant la récolte', 'Ne pas ramasser les fruits tombés']
    },
    'category3': {
        'name': 'Cultures fourragères',
        'requirements': {'micro': 'B', 'physico': 'OK'},
        'restrictions': ['Pas de pâturage direct', 'Arrêter l\'irrigation 1 semaine avant la coupe']
    },
    'category4': {
        'name': 'Cultures industrielles et céréalières',
        'requirements': {'micro': 'C', 'physico': 'OK'},
        'restrictions': ['Paramètres plus permissifs possibles selon réglementation']
    }
}

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for(MAIN_DASHBOARD))
    return render_template('landing.html')

@app.route('/main')
@login_required
def main_dashboard():
    # Get recent incidents (last 5)
    if current_user.role == UserRole.ADMIN:
        recent_incidents = Incident.query.order_by(Incident.date_incident.desc()).limit(5).all()
    else:
        recent_incidents = Incident.query.filter_by(author=current_user).order_by(Incident.date_incident.desc()).limit(5).all()
    
    # Get statistics
    if current_user.role == UserRole.ADMIN:
        total_incidents = Incident.query.count()
        resolved_incidents = Incident.query.filter_by(status='Résolu').count()
        pending_incidents = Incident.query.filter_by(status='En cours').count()
    else:
        total_incidents = Incident.query.filter_by(author=current_user).count()
        resolved_incidents = Incident.query.filter_by(author=current_user, status='Résolu').count()
        pending_incidents = Incident.query.filter_by(author=current_user, status='En cours').count()
    
    return render_template('main_dashboard.html',
                         recent_incidents=recent_incidents,
                         total_incidents=total_incidents,
                         resolved_incidents=resolved_incidents,
                         pending_incidents=pending_incidents,
                         datetime=datetime)

@app.route('/dashboard')
@login_required
@unit_required
def dashboard():
    random_phrase = random.choice(WATER_PHRASES)
    
    # Get statistics based on user role and permissions
    permissions = UserRole.get_permissions(current_user.role)
    
    if permissions.get('can_view_all_incidents', False):
        # Admin and DG see everything
        total_incidents = Incident.query.count()
        resolved_incidents = Incident.query.filter_by(status='Résolu').count()
        pending_incidents = Incident.query.filter_by(status='En cours').count()
        recent_incidents = Incident.query.order_by(Incident.date_incident.desc()).limit(5).all()
        
        total_users = User.query.count()
        total_units = Unit.query.count()
        total_zones = Zone.query.count()
        total_centers = Center.query.count()
        
    elif permissions.get('can_view_zone_incidents', False):
        # Zone employer sees all incidents in their zone
        zone_units = Unit.query.filter_by(zone_id=current_user.zone_id).all()
        unit_ids = [unit.id for unit in zone_units]
        
        total_incidents = Incident.query.filter(Incident.unit_id.in_(unit_ids)).count()
        resolved_incidents = Incident.query.filter(Incident.unit_id.in_(unit_ids), Incident.status=='Résolu').count()
        pending_incidents = Incident.query.filter(Incident.unit_id.in_(unit_ids), Incident.status=='En cours').count()
        recent_incidents = Incident.query.filter(Incident.unit_id.in_(unit_ids)).order_by(Incident.date_incident.desc()).limit(5).all()
        
        # Zone statistics
        total_users = User.query.filter_by(zone_id=current_user.zone_id).count()
        total_units = len(zone_units)
        total_zones = 1  # Their own zone
        total_centers = Center.query.join(Unit).filter(Unit.zone_id == current_user.zone_id).count()
        
    else:
        # Unit employers and regular users see their unit's incidents
        total_incidents = Incident.query.filter_by(unit_id=current_user.unit_id).count()
        resolved_incidents = Incident.query.filter_by(unit_id=current_user.unit_id, status='Résolu').count()
        pending_incidents = Incident.query.filter_by(unit_id=current_user.unit_id, status='En cours').count()
        recent_incidents = Incident.query.filter_by(unit_id=current_user.unit_id).order_by(Incident.date_incident.desc()).limit(5).all()
        
        total_users = None
        total_units = None
        total_zones = None
        total_centers = None
    
    return render_template('main_dashboard.html',
                         phrase=random_phrase,
                         datetime=datetime,
                         total_incidents=total_incidents,
                         resolved_incidents=resolved_incidents,
                         pending_incidents=pending_incidents,
                         recent_incidents=recent_incidents,
                         total_users=total_users,
                         total_units=total_units,
                         total_zones=total_zones,
                         total_centers=total_centers,
                         permissions=permissions)

@app.route('/services')
@login_required
@unit_required
def services():
    return render_template('services.html')

@app.route('/listes_dashboard')
@login_required
@unit_required
def listes_dashboard():
    if current_user.role == UserRole.ADMIN:
        total_incidents = Incident.query.count()
        resolved_incidents = Incident.query.filter_by(status='Résolu').count()
    else:
        total_incidents = Incident.query.filter_by(unit_id=current_user.unit_id).count()
        resolved_incidents = Incident.query.filter_by(unit_id=current_user.unit_id, status='Résolu').count()

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

@app.route('/departements/reuse')
@login_required
@unit_required
def reuse():
    return redirect(url_for(REUSE_INTRODUCTION))

@app.route('/departements/reuse/introduction')
@login_required
@unit_required
def reuse_introduction():
    return render_template('departement/reuse/introduction.html')

@app.route('/departements/reuse/regulations')
@login_required
@unit_required
def reuse_regulations():
    return render_template('departement/reuse/regulations.html')

@app.route('/departements/reuse/methods')
@login_required
@unit_required
def reuse_methods():
    return render_template('departement/reuse/methods.html')

@app.route('/departements/reuse/case-studies')
@login_required
@unit_required
def reuse_case_studies():
    return render_template('departement/reuse/case_studies.html')

@app.route('/departements/reuse/documentation')
@login_required
@unit_required
def reuse_documentation():
    return render_template('departement/reuse/documentation.html')

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

# Water Quality Assessment Routes
@app.route('/reuse/water-quality')
@login_required
def water_quality_route():
    return render_template('departement/reuse/water_quality.html', 
                         active_page='water_quality',
                         parameter_metadata=get_parameter_metadata())

@app.route('/reuse/water-quality/assess', methods=['POST'])
@login_required
def assess_water_quality_route():
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

@app.route('/reuse/water-quality/results')
@login_required
def water_quality_results_route():
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

@app.route('/reuse/water-quality/download-pdf')
@login_required
def download_water_quality_pdf():
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
        
        # Add metadata for UI rendering
        result['parameter_metadata'] = get_parameter_metadata()
        
        # Generate PDF with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'Rapport_Qualite_Eau_{timestamp}.pdf'
        pdf_path = generate_water_quality_pdf(result)
        
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
        app.logger.error(f"Error generating water quality PDF: {str(e)}")
        flash("Une erreur s'est produite lors de la génération du PDF.", "error")
        return redirect(url_for('water_quality_route'))

@app.route('/units')
@login_required
def list_units():
    # Admin and DG see all units
    if current_user.role in ['Admin', 'Employeur DG']:
        units = Unit.query.all()
        zones = Zone.query.all()
    # Zone employers see units in their zone
    elif current_user.role == 'Employeur Zone':
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
    
    return render_template('list_units.html', units=units, zones=zones)

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
    if current_user.role in ['Employeur Zone', 'Admin', 'Employeur DG']:
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
    if current_user.role == 'Admin':
        zones = Zone.query.all()
    elif current_user.zone_id:
        zones = [Zone.query.get(current_user.zone_id)]
    else:
        zones = []
        
    return render_template('select_unit.html', zones=zones)

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
