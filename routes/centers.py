from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db, Center, Unit, Zone
from utils.decorators import admin_required
import traceback
import uuid
from sqlalchemy.orm import joinedload

centers = Blueprint('centers', __name__)

@centers.route('/admin/centres/listes_par_zone')
@login_required
def centres_listes_par_zone():
    # Debug print
    print("Entering centres_listes_par_zone route")
    
    # Get all zones with their units and centres
    if current_user.role == 'Admin':
        zones = Zone.query.options(
            joinedload(Zone.units).joinedload(Unit.centers)
        ).all()
        page_title = "Liste des Centres de toutes les zones de l'ONA"
    else:
        # For non-admin users, only show centres from their assigned zone
        zones = Zone.query.filter_by(id=current_user.zone_id).options(
            joinedload(Zone.units).joinedload(Unit.centers)
        ).all()
        page_title = f"Liste des Centres de la zone {current_user.zone.name}"
    
    # Add logging
    current_app.logger.info(f"Retrieved zones: {len(zones)}")
    for zone in zones:
        current_app.logger.info(f"Zone: {zone.name}, Units: {len(zone.units)}")
        for unit in zone.units:
            current_app.logger.info(f"Unit: {unit.name}, Centers: {len(unit.centers)}")
    
    return render_template('admin/centres_listes.html', zones=zones, page_title=page_title)

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
            return redirect(url_for('centers.centres_listes_par_zone'))

        if not unit_id:
            flash('L\'unité est requise.', 'danger')
            current_app.logger.warning("Center creation failed: Unit is required")
            return redirect(url_for('centers.centres_listes_par_zone'))

        # Verify the unit exists
        unit = Unit.query.get(unit_id)
        if not unit:
            flash('L\'unité sélectionnée n\'existe pas.', 'danger')
            current_app.logger.error(f"Center creation failed: Unit with ID {unit_id} not found")
            return redirect(url_for('centers.centres_listes_par_zone'))

        # Generate a unique code for the center
        # Format: ZONE_CODE-UNIT_CODE-RANDOM_4_CHARS
        unique_code = f"{unit.zone.code}-{unit.code}-{str(uuid.uuid4())[:4].upper()}"

        # Create the center
        center = Center(
            name=name,
            code=uuid.uuid4().hex[:8].upper(),  # Auto-generate code
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

    return redirect(url_for('centers.centres_listes_par_zone'))
