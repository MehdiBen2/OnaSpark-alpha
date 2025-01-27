from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db, Center, Unit, Zone
from utils.decorators import admin_required
import traceback
import uuid

centers = Blueprint('centers', __name__)

@centers.route('/admin/centers')
@login_required
def list_centers():
    centers = Center.query.all()
    zones = Zone.query.all()
    return render_template('admin/centers.html', centers=centers, zones=zones)

@centers.route('/admin/centers/new', methods=['POST'])
@login_required
@admin_required
def new_center():
    try:
        # Log all form data for debugging
        current_app.logger.info(f"Form data received: {request.form}")
        
        name = request.form.get('name')
        description = request.form.get('description')
        email = request.form.get('email')
        phone = request.form.get('phone')
        unit_id = request.form.get('unit_id')

        # More detailed validation
        if not name:
            flash('Le nom du centre est requis.', 'danger')
            current_app.logger.warning("Center creation failed: Name is required")
            return redirect(url_for('centers.list_centers'))

        if not unit_id:
            flash('L\'unité est requise.', 'danger')
            current_app.logger.warning("Center creation failed: Unit is required")
            return redirect(url_for('centers.list_centers'))

        # Verify the unit exists
        unit = Unit.query.get(unit_id)
        if not unit:
            flash('L\'unité sélectionnée n\'existe pas.', 'danger')
            current_app.logger.error(f"Center creation failed: Unit with ID {unit_id} not found")
            return redirect(url_for('centers.list_centers'))

        # Generate a unique code for the center
        # Format: ZONE_CODE-UNIT_CODE-RANDOM_4_CHARS
        unique_code = f"{unit.zone.code}-{unit.code}-{str(uuid.uuid4())[:4].upper()}"

        # Create the center
        center = Center(
            name=name,
            code=unique_code,
            description=description or '',
            email=email or None,
            phone=phone or None,
            unit_id=unit_id
        )
        
        db.session.add(center)
        db.session.commit()
        
        current_app.logger.info(f"Center created successfully: {center.name} with code {center.code}")
        flash('Centre créé avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating center: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        flash(f'Erreur lors de la création du centre: {str(e)}', 'danger')

    return redirect(url_for('centers.list_centers'))
