from flask import (
    Blueprint, 
    render_template, 
    request, 
    redirect, 
    url_for, 
    flash, 
    jsonify
)
from flask_login import (
    login_user, 
    current_user, 
    logout_user, 
    login_required
)
from urllib.parse import urlparse
from datetime import datetime
import logging

from models import db, User
from utils.url_endpoints import MAIN_DASHBOARD, LANDING_INDEX
from utils.permissions import UserRole

# Configure logging
logger = logging.getLogger(__name__)

# Create the blueprint
auth = Blueprint('auth', __name__)

def validate_login_credentials(username: str, password: str) -> tuple:
    """
    Validate user login credentials.
    
    Args:
        username (str): User's username
        password (str): User's password
    
    Returns:
        tuple: (user, error_message)
            - user: User object if credentials are valid, None otherwise
            - error_message: Error message if login fails, None if successful
    """
    try:
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return None, "Utilisateur non trouvé"
        
        if not user.check_password(password):
            return None, "Mot de passe incorrect"
        
        return user, None
    
    except Exception as e:
        logger.error(f"Login validation error: {str(e)}")
        return None, "Une erreur interne est survenue"

def handle_login_success(user: User, is_ajax: bool = False):
    """
    Handle successful login logic.
    
    Args:
        user (User): Authenticated user
        is_ajax (bool, optional): Whether the request is an AJAX request
    
    Returns:
        Union[dict, Response]: Login response
    """
    try:
        login_user(user, remember=True)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Determine next page
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for(MAIN_DASHBOARD)
        
        if is_ajax:
            return {
                'success': True, 
                'redirect': next_page,
                'username': user.username,
                'nickname': user.nickname or user.username
            }
        
        flash('Connexion réussie!', 'success')
        return redirect(next_page)
    
    except Exception as e:
        logger.error(f"Login success handling error: {str(e)}")
        if is_ajax:
            return {'success': False, 'message': 'Erreur lors de la connexion'}
        
        flash('Une erreur est survenue lors de la connexion.', 'danger')
        return redirect(url_for(LANDING_INDEX))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login process with AJAX support.
    
    Returns:
        Union[str, dict, Response]: Login page or login response
    """
    # Check if user is already authenticated
    if current_user.is_authenticated:
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if is_ajax:
            return jsonify({
                'status': 'success', 
                'redirect_url': url_for('main_dashboard.dashboard')
            })
        return redirect(url_for('main_dashboard.dashboard'))
    
    # Handle login form submission
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        user, error = validate_login_credentials(username, password)
        
        if user:
            login_user(user)
            if is_ajax:
                return jsonify({
                    'status': 'success', 
                    'redirect_url': url_for('main_dashboard.dashboard'),
                    'username': user.username
                })
            return redirect(url_for('main_dashboard.dashboard'))
        
        # If login fails
        if is_ajax:
            return jsonify({
                'status': 'error', 
                'message': error or 'Identifiants invalides'
            }), 401
        
        flash(error or 'Identifiants invalides', 'danger')
    
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/disconnect-all', methods=['POST'])
@login_required
def disconnect_all_users():
    """
    Route to disconnect all users from the system.
    Only accessible by admin users.
    """
    if current_user.role != UserRole.ADMIN:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('main_dashboard.dashboard'))
    
    try:
        User.disconnect_all_users()
        flash('Tous les utilisateurs ont été déconnectés.', 'success')
        return redirect(url_for('main_dashboard.dashboard'))
    except Exception as e:
        flash(f'Erreur lors de la déconnexion des utilisateurs: {str(e)}', 'danger')
        return redirect(url_for('main_dashboard.dashboard'))
