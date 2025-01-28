from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import db, User, UserProfile, Unit
from datetime import datetime
from sqlalchemy import or_
from utils.form_validation import FormValidator, handle_form_exception
from utils.url_endpoints import (
    PROFILE_VIEW,
    PROFILE_EDIT,
    PROFILE_CREATE,
    PROFILE_ADMIN,
    PROFILE_USER_VIEW
)

profiles = Blueprint('profiles', __name__)

FIELD_LABELS = {
    'first_name': 'Prénom',
    'last_name': 'Nom de famille',
    'date_of_birth': 'Date de naissance',
    'email': 'Adresse e-mail',
    'professional_number': 'Numéro professionnel',
    'job_function': 'Fonction',
    'recruitment_date': 'Date de recrutement'
}

def validate_profile_creation(form_data):
    """
    Validate profile creation form data with enhanced error messages.
    
    Args:
        form_data (dict): Dictionary of form submission data
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # Identify missing required fields
    missing_fields = [
        FIELD_LABELS.get(field, field) 
        for field in ['first_name', 'last_name', 'date_of_birth', 'email', 
                      'professional_number', 'job_function', 'recruitment_date'] 
        if not form_data.get(field)
    ]
    
    # Generate error message if fields are missing
    if missing_fields:
        return False, f"Les champs suivants sont obligatoires : {', '.join(missing_fields)}"
    
    return True, ""

@profiles.route('/profile/create', methods=['GET', 'POST'], endpoint='create_profile')
@login_required
def create_profile():
    if request.method == 'POST':
        try:
            # Get form data
            form_data = {
                'first_name': request.form.get('first_name', '').strip(),
                'last_name': request.form.get('last_name', '').strip(),
                'date_of_birth': request.form.get('date_of_birth', '').strip(),
                'email': request.form.get('email', '').strip(),
                'professional_number': request.form.get('professional_number', '').strip(),
                'job_function': request.form.get('job_function', '').strip(),
                'recruitment_date': request.form.get('recruitment_date', '').strip()
            }

            # Validate form data
            is_valid, error_message = validate_profile_creation(form_data)
            if not is_valid:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': error_message})
                flash(error_message, 'error')
                return render_template('profiles/create_profile.html', form_data=form_data)

            # Check if professional number is already in use
            existing_profile = UserProfile.query.filter_by(
                professional_number=form_data['professional_number']
            ).first()
            if existing_profile:
                error_msg = 'Ce numéro professionnel est déjà utilisé'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': error_msg})
                flash(error_msg, 'error')
                return render_template('profiles/create_profile.html', form_data=form_data)

            # Check if email is already in use
            existing_email = UserProfile.query.filter_by(
                email=form_data['email']
            ).first()
            if existing_email:
                error_msg = 'Cette adresse email est déjà utilisée'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': error_msg})
                flash(error_msg, 'error')
                return render_template('profiles/create_profile.html', form_data=form_data)

            # Create new profile
            try:
                profile = UserProfile(
                    first_name=form_data['first_name'],
                    last_name=form_data['last_name'],
                    date_of_birth=datetime.strptime(form_data['date_of_birth'], '%Y-%m-%d').date(),
                    email=form_data['email'],
                    professional_number=form_data['professional_number'],
                    job_function=form_data['job_function'],
                    recruitment_date=datetime.strptime(form_data['recruitment_date'], '%Y-%m-%d'),
                    user_id=current_user.id
                )

                db.session.add(profile)
                db.session.commit()

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': True,
                        'redirect': url_for(PROFILE_VIEW)
                    })

                flash('Profil créé avec succès', 'success')
                return redirect(url_for(PROFILE_VIEW))

            except Exception as e:
                db.session.rollback()
                if 'UNIQUE constraint' in str(e):
                    if 'professional_number' in str(e):
                        error_msg = 'Ce numéro professionnel est déjà utilisé'
                    elif 'email' in str(e):
                        error_msg = 'Cette adresse email est déjà utilisée'
                    else:
                        error_msg = 'Une erreur de doublon s\'est produite'
                else:
                    error_msg = 'Erreur lors de la création du profil: ' + str(e)

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': error_msg})
                flash(error_msg, 'error')
                return render_template('profiles/create_profile.html', form_data=form_data)

        except Exception as e:
            error_msg = 'Une erreur inattendue s\'est produite: ' + str(e)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': error_msg})
            flash(error_msg, 'error')
            return render_template('profiles/create_profile.html', form_data=form_data)

    return render_template('profiles/create_profile.html', form_data={})

@profiles.route('/profile', methods=['GET'], endpoint='view_profile')
@login_required
def view_profile():
    if not current_user.profile:
        flash('Vous n\'avez pas encore créé votre profil.', 'info')
        return redirect(url_for(PROFILE_CREATE))
    
    return render_template('profiles/view_profile.html', profile=current_user.profile)

@profiles.route('/profile/<int:user_id>', methods=['GET'], endpoint='view_user_profile')
@login_required
def view_user_profile(user_id):
    # Check if the current user is an admin or viewing their own profile
    if not current_user.role == 'Admin' and current_user.id != user_id:
        flash('Vous n\'avez pas la permission de voir ce profil.', 'error')
        return redirect(url_for(PROFILE_VIEW))
    
    user = User.query.get_or_404(user_id)
    if not user.profile:
        flash('Ce utilisateur n\'a pas encore créé son profil.', 'info')
        return redirect(url_for(PROFILE_ADMIN))
    
    return render_template('profiles/view_profile.html', profile=user.profile, is_admin_view=True)

@profiles.route('/profile/edit', methods=['GET', 'POST'], endpoint='edit_profile')
@login_required
def edit_profile():
    profile = current_user.profile
    if not profile:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Profile not found'})
        flash('Profile not found', 'error')
        return redirect(url_for(PROFILE_CREATE))

    if request.method == 'POST':
        try:
            # Get form data
            form_data = {
                'first_name': request.form.get('first_name'),
                'last_name': request.form.get('last_name'),
                'date_of_birth': request.form.get('date_of_birth'),
                'email': request.form.get('email'),
                'professional_number': request.form.get('professional_number'),
                'job_function': request.form.get('job_function'),
                'recruitment_date': request.form.get('recruitment_date')
            }

            # Define required fields and validations
            required_fields = [
                'first_name', 'last_name', 'date_of_birth', 
                'email', 'professional_number', 'job_function', 'recruitment_date'
            ]

            def validate_professional_number(data):
                # Check if professional number is already in use by another profile
                existing_profile = UserProfile.query.filter(
                    UserProfile.professional_number == data['professional_number'],
                    UserProfile.id != profile.id
                ).first()
                return 'Ce numéro professionnel est déjà utilisé' if existing_profile else None

            def validate_email_format(data):
                # Validate email format
                if not FormValidator.validate_email(data['email']):
                    return 'Format d\'email invalide'
                return None

            def validate_dates(data):
                # Validate date formats
                for date_field in ['date_of_birth', 'recruitment_date']:
                    if not FormValidator.validate_date(data[date_field]):
                        return f'Format de date invalide pour {date_field}'
                return None

            # Perform validation
            validation_result = FormValidator.validate_form(
                form_data, 
                required_fields, 
                [
                    validate_professional_number,
                    validate_email_format,
                    validate_dates
                ]
            )

            # If validation fails, handle based on request type
            if validation_result:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'errors': validation_result})
                return render_template('profiles/edit_profile.html', profile=profile, form_data=validation_result)

            # Update profile
            profile.first_name = form_data['first_name']
            profile.last_name = form_data['last_name']
            profile.date_of_birth = datetime.strptime(form_data['date_of_birth'], '%Y-%m-%d').date()
            profile.email = form_data['email']
            profile.professional_number = form_data['professional_number']
            profile.job_function = form_data['job_function']
            profile.recruitment_date = datetime.strptime(form_data['recruitment_date'], '%Y-%m-%d')

            db.session.commit()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True})
            
            flash('Profil mis à jour avec succès', 'success')
            return redirect(url_for(PROFILE_VIEW))

        except Exception as e:
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': str(e)})
            form_data = handle_form_exception(e, form_data)
            return render_template('profiles/edit_profile.html', profile=profile, form_data=form_data)

    return render_template('profiles/edit_profile.html', profile=profile)

@profiles.route('/profile/<int:user_id>/edit', methods=['GET', 'POST'], endpoint='edit_user_profile')
@login_required
def edit_user_profile(user_id):
    if current_user.role != 'Admin':
        flash('Vous n\'avez pas la permission de modifier ce profil.', 'error')
        return redirect(url_for(PROFILE_VIEW))
    
    user = User.query.get_or_404(user_id)
    profile = user.profile
    
    if not profile:
        flash('Profile not found', 'error')
        return redirect(url_for(PROFILE_ADMIN))
    
    if request.method == 'POST':
        try:
            # Get form data
            form_data = {
                'first_name': request.form.get('first_name'),
                'last_name': request.form.get('last_name'),
                'date_of_birth': request.form.get('date_of_birth'),
                'email': request.form.get('email'),
                'professional_number': request.form.get('professional_number'),
                'job_function': request.form.get('job_function'),
                'recruitment_date': request.form.get('recruitment_date')
            }

            # Define required fields and validations
            required_fields = [
                'first_name', 'last_name', 'date_of_birth', 
                'email', 'professional_number', 'job_function', 'recruitment_date'
            ]

            def validate_professional_number(data):
                # Check if professional number is already in use by another profile
                existing_profile = UserProfile.query.filter(
                    UserProfile.professional_number == data['professional_number'],
                    UserProfile.id != profile.id
                ).first()
                return 'Ce numéro professionnel est déjà utilisé' if existing_profile else None

            def validate_email_format(data):
                # Validate email format
                if not FormValidator.validate_email(data['email']):
                    return 'Format d\'email invalide'
                return None

            def validate_dates(data):
                # Validate date formats
                for date_field in ['date_of_birth', 'recruitment_date']:
                    if not FormValidator.validate_date(data[date_field]):
                        return f'Format de date invalide pour {date_field}'
                return None

            # Perform validation
            validation_result = FormValidator.validate_form(
                form_data, 
                required_fields, 
                [
                    validate_professional_number,
                    validate_email_format,
                    validate_dates
                ]
            )

            # If validation fails, re-render the form
            if validation_result:
                return render_template('profiles/edit_profile.html', profile=profile, form_data=validation_result, is_admin_view=True)

            # Update profile
            profile.first_name = form_data['first_name']
            profile.last_name = form_data['last_name']
            profile.date_of_birth = datetime.strptime(form_data['date_of_birth'], '%Y-%m-%d').date()
            profile.email = form_data['email']
            profile.professional_number = form_data['professional_number']
            profile.job_function = form_data['job_function']
            profile.recruitment_date = datetime.strptime(form_data['recruitment_date'], '%Y-%m-%d')

            db.session.commit()
            flash('Profile updated successfully', 'success')
            return redirect(url_for(PROFILE_USER_VIEW, user_id=user_id))

        except Exception as e:
            db.session.rollback()
            form_data = handle_form_exception(e, form_data)
            return render_template('profiles/edit_profile.html', profile=profile, form_data=form_data, is_admin_view=True)

    return render_template('profiles/edit_profile.html', profile=profile, form_data={}, is_admin_view=True)

@profiles.route('/admin/profiles', methods=['GET'], endpoint='admin_profiles')
@login_required
def admin_profiles():
    if current_user.role != 'Admin':
        flash('Vous n\'avez pas la permission d\'accéder à cette page.', 'error')
        return redirect(url_for(PROFILE_VIEW))
    
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'last_name')
    order = request.args.get('order', 'asc')

    query = UserProfile.query
    
    if search_query:
        query = query.join(User).join(Unit).filter(
            or_(
                UserProfile.first_name.ilike(f'%{search_query}%'),
                UserProfile.last_name.ilike(f'%{search_query}%'),
                UserProfile.email.ilike(f'%{search_query}%'),
                UserProfile.professional_number.ilike(f'%{search_query}%'),
                Unit.name.ilike(f'%{search_query}%')
            )
        )

    if hasattr(UserProfile, sort_by):
        sort_column = getattr(UserProfile, sort_by)
        if order == 'desc':
            sort_column = sort_column.desc()
        query = query.order_by(sort_column)

    profiles = query.all()
    return render_template('profiles/admin_profiles.html', profiles=profiles)

@profiles.route('/api/profiles/search', methods=['GET'])
@login_required
def search_profiles():
    if current_user.role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), 403

    search_query = request.args.get('q', '')
    profiles = UserProfile.query.join(User).join(Unit).filter(
        or_(
            UserProfile.first_name.ilike(f'%{search_query}%'),
            UserProfile.last_name.ilike(f'%{search_query}%'),
            UserProfile.email.ilike(f'%{search_query}%'),
            UserProfile.professional_number.ilike(f'%{search_query}%'),
            Unit.name.ilike(f'%{search_query}%')
        )
    ).all()

    return jsonify([{
        'id': p.id,
        'first_name': p.first_name,
        'last_name': p.last_name,
        'email': p.email,
        'professional_number': p.professional_number,
        'unit': p.user.unit.name if p.user.unit else None
    } for p in profiles])
