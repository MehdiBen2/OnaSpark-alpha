from enum import Enum, auto
from functools import wraps
from flask import abort, flash, redirect
from flask_login import current_user, login_required

class Permission(Enum):
    """
    Centralized Enum for all system permissions.
    Each permission is a unique, descriptive identifier.
    """
    # Incident Permissions
    VIEW_INCIDENT = auto()
    CREATE_INCIDENT = auto()
    EDIT_INCIDENT = auto()
    DELETE_INCIDENT = auto()
    RESOLVE_INCIDENT = auto()

    # Export and Analysis Permissions
    EXPORT_INCIDENT_PDF = auto()
    EXPORT_ALL_INCIDENTS_PDF = auto()
    GET_AI_EXPLANATION = auto()
    DEEP_ANALYSIS = auto()

    # User Management Permissions
    VIEW_USERS = auto()
    CREATE_USERS = auto()
    EDIT_USERS = auto()
    DELETE_USERS = auto()

    # Zone and Unit Permissions
    VIEW_ZONES = auto()
    MANAGE_ZONES = auto()
    VIEW_UNITS = auto()
    MANAGE_UNITS = auto()

class PermissionManager:
    """
    Centralized permission management with role-based access control.
    Provides a flexible and extensible way to define and check permissions.
    """
    _ROLE_PERMISSIONS = {
        'Admin': {
            Permission.VIEW_INCIDENT,
            Permission.CREATE_INCIDENT,
            Permission.EDIT_INCIDENT,
            Permission.DELETE_INCIDENT,
            Permission.RESOLVE_INCIDENT,
            Permission.VIEW_ZONES,
            Permission.MANAGE_ZONES,
            Permission.VIEW_UNITS,
            Permission.MANAGE_UNITS,
            Permission.EXPORT_INCIDENT_PDF,
            Permission.EXPORT_ALL_INCIDENTS_PDF,
            Permission.GET_AI_EXPLANATION,
            Permission.DEEP_ANALYSIS,
        },
        'Employeur DG': {
            # Strictly limited to viewing incidents
            Permission.VIEW_INCIDENT,
        },
        'Employeur Zone': {
            Permission.VIEW_INCIDENT,
            Permission.VIEW_UNITS,
            Permission.EXPORT_INCIDENT_PDF,
        },
        'Employeur Unité': {
            Permission.VIEW_INCIDENT,
            Permission.CREATE_INCIDENT,
            Permission.EDIT_INCIDENT,
            Permission.RESOLVE_INCIDENT,
            Permission.EXPORT_INCIDENT_PDF,
        },
        'Utilisateur': {
            Permission.VIEW_INCIDENT,
        }
    }

    @classmethod
    def has_permission(cls, user, permission):
        """
        Check if a user has a specific permission based on their role.
        
        Args:
            user: The current user
            permission (Permission): The permission to check
        
        Returns:
            bool: Whether the user has the permission
        """
        if not user or not user.is_authenticated:
            return False
        
        return permission in cls._ROLE_PERMISSIONS.get(user.role, set())

def permission_required(permission):
    """
    Decorator to enforce permission checks on route functions.
    
    Args:
        permission (Permission): The required permission
    
    Returns:
        function: Decorated function with permission check
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not PermissionManager.has_permission(current_user, permission):
                flash('Vous n\'avez pas la permission d\'effectuer cette action.', 'danger')
                return redirect('main_dashboard.dashboard')  # Redirect to dashboard
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def context_permission_check(permission):
    """
    Context manager for template-level permission checks.
    
    Args:
        permission (Permission): The permission to check
    
    Returns:
        bool: Whether the current user has the permission
    """
    return PermissionManager.has_permission(current_user, permission)
