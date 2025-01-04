from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Unit, Zone
from utils.decorators import admin_required

units = Blueprint('units', __name__)

@units.route('/admin/units')
@login_required
@admin_required
def manage_units():
    units = Unit.query.all()
    zones = Zone.query.all()
    return render_template('admin/manage_units.html', units=units, zones=zones)

@units.route('/admin/units/new', methods=['POST'])
@login_required
@admin_required
def new_unit():
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
@admin_required
def delete_unit(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    
    # Check if unit has associated users or incidents
    if unit.unit_users or unit.incidents:
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
    """Get all units for a specific zone."""
    try:
        units = Unit.query.filter_by(zone_id=zone_id).all()
        return jsonify([{'id': unit.id, 'name': unit.name} for unit in units])
    except Exception as e:
        current_app.logger.error(f"Error fetching units for zone {zone_id}: {str(e)}")
        return jsonify({'error': 'Error fetching units'}), 500
