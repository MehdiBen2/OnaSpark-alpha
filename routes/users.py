from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, User, Unit, Zone
from utils.decorators import admin_required
from utils.roles import UserRole
from datetime import datetime

users = Blueprint('users', __name__)

@users.route('/admin/users')
@login_required
@admin_required
def manage_users():
    users = User.query.options(
        db.joinedload(User.assigned_zone),
        db.joinedload(User.assigned_unit)
    ).all()
    zones = Zone.query.order_by(Zone.name).all()
    zones_data = [{'id': zone.id, 'name': zone.name} for zone in zones]
    
    # Get available roles based on current user's role
    available_roles = [
        UserRole.EMPLOYEUR_DG,
        UserRole.EMPLOYEUR_ZONE,
        UserRole.EMPLOYEUR_UNITE,
        UserRole.UTILISATEUR
    ]
    
    # Only admin can create other admins
    if current_user.role == UserRole.ADMIN:
        available_roles = [UserRole.ADMIN] + available_roles
    
    return render_template('admin/users.html', 
                         users=users, 
                         zones=zones, 
                         zones_data=zones_data,
                         UserRole=UserRole,
                         available_roles=available_roles,
                         current_user=current_user)  # Pass current_user and available_roles to template

@users.route('/admin/users/<int:user_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    nickname = request.form.get('nickname')
    unit_id = request.form.get('unit_id')
    zone_id = request.form.get('zone_id')

    existing_user = User.query.filter_by(username=username).first()
    if existing_user and existing_user.id != user_id:
        flash('Un utilisateur avec ce nom existe déjà.', 'error')
        return redirect(url_for('users.manage_users'))

    # Update basic user information
    user.username = username
    user.nickname = nickname
    if password:
        user.set_password(password)

    # Use the new role assignment system
    success, message = UserRole.assign_role_and_permissions(
        user_id=user_id,
        role=role,
        zone_id=zone_id if zone_id else None,
        unit_id=unit_id if unit_id else None
    )

    if success:
        db.session.commit()
        flash('Utilisateur mis à jour avec succès.', 'success')
    else:
        flash(f'Erreur lors de la mise à jour du rôle: {message}', 'error')

    return redirect(url_for('users.manage_users'))

@users.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'})

@users.route('/admin/users/<int:user_id>/get')
@login_required
@admin_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'unit_id': user.unit_id,
        'zone_id': user.zone_id
    })

@users.route('/admin/users/<int:user_id>/update', methods=['PUT', 'POST'])
@login_required
@admin_required
def update_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        
        # Get form data
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        nickname = request.form.get('nickname')
        unit_id = request.form.get('unit_id')
        zone_id = request.form.get('zone_id')

        # Check if username exists for other users
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user_id:
            message = 'Un utilisateur avec ce nom existe déjà.'
            return (jsonify({'success': False, 'message': message}), 400) if request.method == 'PUT' else (flash(message, 'error'), redirect(url_for('users.manage_users')))

        # Update basic user information
        user.username = username
        user.nickname = nickname if nickname else None
        if password:  # Only update password if provided
            user.set_password(password)
        
        # Update role and assignments
        user.role = role
        user.unit_id = int(unit_id) if unit_id else None
        user.zone_id = int(zone_id) if zone_id else None
        user.updated_at = datetime.utcnow()

        try:
            db.session.commit()
            message = 'Utilisateur mis à jour avec succès.'
            return (jsonify({'success': True, 'message': message})) if request.method == 'PUT' else (flash(message, 'success'), redirect(url_for('users.manage_users')))
            
        except Exception as db_error:
            db.session.rollback()
            message = f'Erreur lors de la mise à jour dans la base de données: {str(db_error)}'
            return (jsonify({'success': False, 'message': message}), 500) if request.method == 'PUT' else (flash(message, 'error'), redirect(url_for('users.manage_users')))

    except Exception as e:
        db.session.rollback()
        message = f'Erreur lors de la mise à jour: {str(e)}'
        return (jsonify({'success': False, 'message': message}), 500) if request.method == 'PUT' else (flash(message, 'error'), redirect(url_for('users.manage_users')))

@users.route('/admin/users/create', methods=['POST'])
@login_required
@admin_required
def create_user():
    try:
        # Get form data
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        nickname = request.form.get('nickname')
        unit_id = request.form.get('unit_id')
        zone_id = request.form.get('zone_id')

        # Validate required fields
        if not username or not password or not role:
            message = "Missing required fields"
            return jsonify({'success': False, 'message': message}), 400

        # Check if username exists
        if User.query.filter_by(username=username).first():
            message = 'Un utilisateur avec ce nom existe déjà.'
            return jsonify({'success': False, 'message': message}), 400

        # Create new user
        new_user = User(
            username=username,
            nickname=nickname,
            role=role
        )
        new_user.set_password(password)
        new_user.unit_id = int(unit_id) if unit_id else None
        new_user.zone_id = int(zone_id) if zone_id else None
        
        try:
            db.session.add(new_user)
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Utilisateur créé avec succès.',
                'user_id': new_user.id
            })
                
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Erreur lors de la création de l\'utilisateur: {str(e)}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur inattendue: {str(e)}'
        }), 500

@users.route('/api/zones')
@login_required
def get_zones():
    zones = Zone.query.all()
    return jsonify([{'id': zone.id, 'name': zone.name} for zone in zones])

@users.route('/api/zones/<int:zone_id>/units')
@login_required
def get_zone_units(zone_id):
    try:
        # Get the zone
        zone = Zone.query.get_or_404(zone_id)
        
        # Get all units for this zone from OnaDB
        units = Unit.query.filter_by(zone_id=zone_id).order_by(Unit.name).all()
        
        if not units:
            return jsonify({
                'success': True,
                'units': [],
                'zone': {'id': zone.id, 'name': zone.name},
                'message': 'No units found for this zone'
            })

        # Format the response
        units_data = [{
            'id': unit.id,
            'name': unit.name,
            'code': unit.code
        } for unit in units]

        return jsonify({
            'success': True,
            'units': units_data,
            'zone': {'id': zone.id, 'name': zone.name}
        })

    except Exception as e:
        print(f"Error fetching units: {str(e)}")  # Add logging for debugging
        return jsonify({
            'success': False,
            'message': f"Error fetching units: {str(e)}"
        }), 500

@users.route('/api/users', methods=['POST'])
@login_required
@admin_required
def api_create_user():
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    nickname = data.get('nickname')
    zone_id = data.get('zone')
    unit_id = data.get('unit')

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Un utilisateur avec ce nom existe déjà.'}), 400

    # Validate role-specific requirements
    if role in [UserRole.EMPLOYEUR_ZONE, UserRole.EMPLOYEUR_UNITE, UserRole.UTILISATEUR] and not zone_id:
        return jsonify({'message': 'Une zone doit être sélectionnée pour ce rôle.'}), 400
    
    if role in [UserRole.EMPLOYEUR_UNITE, UserRole.UTILISATEUR] and not unit_id:
        return jsonify({'message': 'Une unité doit être sélectionnée pour ce rôle.'}), 400

    # If unit is selected, verify it belongs to the selected zone
    if unit_id:
        unit = Unit.query.get(unit_id)
        if not unit or str(unit.zone_id) != str(zone_id):
            return jsonify({'message': 'L\'unité sélectionnée n\'appartient pas à la zone sélectionnée.'}), 400

    # Create new user with basic information
    new_user = User(
        username=username,
        nickname=nickname,
        role=role  # Initial role assignment needed for the model
    )
    new_user.set_password(password)
    
    try:
        # Add user to get an ID
        db.session.add(new_user)
        db.session.flush()  # This assigns an ID to new_user
        
        # Use the new role assignment system
        success, message = UserRole.assign_role_and_permissions(
            user_id=new_user.id,
            role=role,
            zone_id=zone_id if zone_id else None,
            unit_id=unit_id if unit_id else None
        )
        
        if success:
            db.session.commit()
            return jsonify({'message': 'Utilisateur créé avec succès'}), 201
        else:
            db.session.rollback()
            return jsonify({'message': f'Erreur lors de la création de l\'utilisateur: {message}'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erreur lors de la création de l\'utilisateur: {str(e)}'}), 500
