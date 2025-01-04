from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user
from utils.roles import UserRole

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not UserRole.is_admin(current_user.role):
            flash('Vous devez être administrateur pour accéder à cette page.', 'danger')
            return redirect(url_for('incident_list'))
        return f(*args, **kwargs)
    return decorated_function

def unit_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        # Skip unit requirement check for admin users
        if UserRole.is_admin(current_user.role):
            return f(*args, **kwargs)
        if not hasattr(current_user, 'unit_id') or current_user.unit_id is None:
            return redirect(url_for('select_unit'))
        return f(*args, **kwargs)
    return decorated_function
