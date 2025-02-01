from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from models import db, Unit, Zone
from utils.decorators import admin_required
from utils.permissions import PermissionManager, Permission, UserRole

units = Blueprint('units', __name__)

@units.route('/admin/units')
@login_required
def manage_units():
    # Check permission to view all units
    if not PermissionManager.has_permission(current_user.role, Permission.VIEW_ALL_UNITS):
        flash('Vous n\'avez pas la permission de gérer les unités.', 'danger')
        return redirect(url_for('main_dashboard.dashboard'))

    units = Unit.query.all()
    zones = Zone.query.all()
    return render_template('admin/manage_units.html', units=units, zones=zones)

@units.route('/admin/units/new', methods=['POST'])
@login_required
def new_unit():
    # Check permission to create units
    if not PermissionManager.has_permission(current_user.role, Permission.CREATE_UNITS):
        flash('Vous n\'avez pas la permission de créer des unités.', 'danger')
        return redirect(url_for('units.manage_units'))

    name = request.form.get('name')
    location = request.form.get('location')
    description = request.form.get('description')
    zone_id = request.form.get('zone_id')

    if not name or not zone_id:
        flash('Le nom et la zone sont requis.', 'danger')
        return redirect(url_for('units.manage_units'))

    try:
        unit = Unit(
            name=name,
            location=location,
            description=description,
            zone_id=zone_id
        )
        db.session.add(unit)
        db.session.commit()
        flash('Unité créée avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la création de l\'unité: {str(e)}', 'danger')

    return redirect(url_for('units.manage_units'))

@units.route('/admin/units/<int:unit_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_unit(unit_id):
    # Check permission to delete units
    if not PermissionManager.has_permission(current_user.role, Permission.DELETE_UNITS):
        flash('Vous n\'avez pas la permission de supprimer des unités.', 'danger')
        return redirect(url_for('units.manage_units'))

    unit = Unit.query.get_or_404(unit_id)
    
    # Check if unit has associated users or incidents
    if unit.users or unit.incidents:
        flash('Impossible de supprimer cette unité car elle a des utilisateurs ou des incidents associés.', 'danger')
        return redirect(url_for('units.manage_units'))

    try:
        db.session.delete(unit)
        db.session.commit()
        flash('Unité supprimée avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression de l\'unité: {str(e)}', 'danger')
    
    return redirect(url_for('units.manage_units'))

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
