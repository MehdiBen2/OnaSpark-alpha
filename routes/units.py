from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from models import db, Unit, Zone
from utils.decorators import admin_required
from utils.permissions import PermissionManager, Permission, UserRole

units = Blueprint('units', __name__)

@units.route('/admin/units/new', methods=['POST'])
@login_required
def new_unit():
    # Debugging print statements
    print("DEBUG: new_unit route called")
    print(f"DEBUG: Form data: {request.form}")
    print(f"DEBUG: Current user: {current_user.username}")
    print(f"DEBUG: Current user role: {current_user.role}")

    # Check if this is a POST request
    if request.method != 'POST':
        print("DEBUG: Not a POST request")
        flash('Méthode de requête invalide.', 'danger')
        return redirect(url_for('units.units_list'))

    # Debug logging
    current_app.logger.debug(f"new_unit route called")
    current_app.logger.debug(f"Current User: {current_user.username}")
    current_app.logger.debug(f"Current User Role: {current_user.role}")
    current_app.logger.debug(f"Form Data: {request.form}")

    # Check permission to create units
    if not PermissionManager.has_permission(current_user.role, Permission.CREATE_UNITS):
        current_app.logger.warning(f"User {current_user.username} lacks permission to create units")
        flash('Vous n\'avez pas la permission de créer des unités.', 'danger')
        return redirect(url_for('units.units_list'))

    name = request.form.get('name')
    address = request.form.get('location')
    description = request.form.get('description')
    zone_id = request.form.get('zone_id')

    current_app.logger.debug(f"Received data - Name: {name}, Address: {address}, Zone ID: {zone_id}")

    if not name or not zone_id:
        current_app.logger.error("Missing required fields for unit creation")
        flash('Le nom et la zone sont requis.', 'danger')
        return redirect(url_for('units.units_list'))

    # Generate unique unit code
    zone = Zone.query.get(zone_id)
    if not zone:
        current_app.logger.error(f"Invalid zone ID: {zone_id}")
        flash('Zone invalide.', 'danger')
        return redirect(url_for('units.units_list'))

    # Count existing units in the zone to generate sequential code
    existing_units_count = Unit.query.filter_by(zone_id=zone_id).count()
    unit_code = f"{zone.code}-U{existing_units_count + 1:03d}"

    # Check if the generated code already exists
    existing_unit = Unit.query.filter_by(code=unit_code).first()
    if existing_unit:
        # If code exists, increment until a unique code is found
        counter = 1
        while Unit.query.filter_by(code=unit_code).first():
            unit_code = f"{zone.code}-U{existing_units_count + counter:03d}"
            counter += 1

    try:
        unit = Unit(
            name=name,
            code=unit_code,  # Add generated code
            address=address,
            description=description,
            zone_id=zone_id
        )
        
        # Log detailed unit information before committing
        current_app.logger.debug(f"Attempting to create Unit: {unit}")
        current_app.logger.debug(f"Unit Details - Name: {unit.name}, Code: {unit.code}, Zone ID: {unit.zone_id}")

        db.session.add(unit)
        
        # Validate the unit before committing
        try:
            db.session.flush()  # This will raise an exception if there are validation errors
        except Exception as validation_error:
            current_app.logger.error(f"Validation Error: {str(validation_error)}")
            db.session.rollback()
            flash(f'Erreur de validation lors de la création de l\'unité: {str(validation_error)}', 'danger')
            return redirect(url_for('units.units_list'))

        db.session.commit()
        current_app.logger.info(f"Unit created successfully - Name: {name}, Code: {unit_code}")
        flash(f'Unité créée avec succès! Code: {unit_code}', 'success')
    except Exception as e:
        current_app.logger.error(f"Error creating unit: {str(e)}")
        db.session.rollback()
        flash(f'Erreur lors de la création de l\'unité: {str(e)}', 'danger')

    return redirect(url_for('units.units_list'))

@units.route('/admin/units/<int:unit_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_unit(unit_id):
    # Check permission to delete units
    if not PermissionManager.has_permission(current_user.role, Permission.DELETE_UNITS):
        flash('Vous n\'avez pas la permission de supprimer des unités.', 'danger')
        return redirect(url_for('units.units_list'))

    unit = Unit.query.get_or_404(unit_id)
    
    # Check if unit has associated users or incidents
    if unit.users or unit.incidents:
        flash('Impossible de supprimer cette unité car elle a des utilisateurs ou des incidents associés.', 'danger')
        return redirect(url_for('units.units_list'))

    try:
        db.session.delete(unit)
        db.session.commit()
        flash('Unité supprimée avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression de l\'unité: {str(e)}', 'danger')
    
    return redirect(url_for('units.units_list'))

@units.route('/api/units/<int:zone_id>')
@login_required
def get_zone_units(zone_id):
    """
    Get all units for a specific zone.
    
    Permissions:
    - Admin and DG can view all units
    - Zone employers can view units in their assigned zone
    """
    # Check if user has permission to view units
    if not PermissionManager.has_permission(current_user.role, Permission.VIEW_ALL_UNITS):
        # For non-admin/DG roles, only allow access to their own zone
        if current_user.zone_id != zone_id:
            return jsonify({
                'error': 'Accès non autorisé',
                'status': 'forbidden'
            }), 403

    try:
        units = Unit.query.filter_by(zone_id=zone_id).all()
        
        # Convert units to a list of dictionaries
        units_list = [
            {
                'id': unit.id, 
                'name': unit.name, 
                'code': unit.code
            } for unit in units
        ]
        
        return jsonify({
            'units': units_list,
            'total_units': len(units_list),
            'status': 'success'
        })
    
    except Exception as e:
        current_app.logger.error(f"Error fetching units for zone {zone_id}: {str(e)}")
        return jsonify({
            'error': 'Erreur lors de la récupération des unités',
            'status': 'error'
        }), 500

@units.route('/list/units')
@login_required
def units_list():
    # Comprehensive debug logging
    print(f"DEBUG: units_list route called")
    print(f"DEBUG: Current User - Username: {current_user.username}, Role: {current_user.role}")
    print(f"DEBUG: Current User ID: {current_user.id}")
    print(f"DEBUG: Current User Zone ID: {current_user.zone_id}")
    print(f"DEBUG: Current User Unit ID: {current_user.unit_id}")
    
    current_app.logger.debug(f"units_list route called. User: {current_user.username}, Role: {current_user.role}")
    
    # Detailed permission logging
    print("DEBUG: Checking permissions...")
    has_view_units_permission = PermissionManager.has_permission(current_user.role, Permission.VIEW_ALL_UNITS)
    print(f"DEBUG: Has VIEW_ALL_UNITS permission: {has_view_units_permission}")
    
    # Check permission to view units
    if not has_view_units_permission:
        print("DEBUG: User lacks permission to view units")
        current_app.logger.warning(f"User {current_user.username} lacks permission to view units")
        flash('Vous n\'avez pas la permission de voir la liste des unités.', 'danger')
        return redirect(url_for('main_dashboard.dashboard'))

    # Detailed role-based unit retrieval
    print("DEBUG: Retrieving units based on user role...")
    
    # Admin and DG see all units and zones
    if current_user.role in [UserRole.ADMIN, UserRole.EMPLOYEUR_DG]:
        print("DEBUG: User is ADMIN or DG - retrieving all units")
        units = Unit.query.all()
        zones = Zone.query.all()
    # Zone employers see units in their zone
    elif current_user.role == UserRole.EMPLOYEUR_ZONE:
        print(f"DEBUG: User is ZONE EMPLOYER - retrieving units for zone {current_user.zone_id}")
        units = Unit.query.filter_by(zone_id=current_user.zone_id).all()
        zones = [Zone.query.get(current_user.zone_id)]
    # Unit officers see their own unit
    elif current_user.role == UserRole.UNIT_OFFICER:
        print(f"DEBUG: User is UNIT OFFICER - retrieving unit {current_user.unit_id}")
        units = [Unit.query.get(current_user.unit_id)] if current_user.unit_id else []
        zones = [Zone.query.get(current_user.zone_id)] if current_user.zone_id else []
    # Other roles get limited or no access
    else:
        print(f"DEBUG: User has limited/no access. Role: {current_user.role}")
        current_app.logger.warning(f"User {current_user.username} with role {current_user.role} has no unit access")
        units = []
        zones = []
    
    print(f"DEBUG: Units found: {len(units)}, Zones found: {len(zones)}")
    current_app.logger.debug(f"Units found: {len(units)}, Zones found: {len(zones)}")
    
    # Ensure we're using the correct template
    print("DEBUG: Rendering units_management.html")
    return render_template('units/units_management.html', units=units, zones=zones)
