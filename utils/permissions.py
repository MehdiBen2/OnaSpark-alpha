from enum import Enum, auto
from typing import Dict, Set, Any
from functools import wraps
from flask import abort, flash, redirect
from flask_login import current_user, login_required

class UserRole:
    """Defines all available user roles in the system."""
    ADMIN = 'Admin'
    EMPLOYEUR_DG = 'Employeur DG'
    EMPLOYEUR_ZONE = 'Employeur Zone'
    EMPLOYEUR_UNITE = 'Employeur Unité'
    UTILISATEUR = 'Utilisateur'

    # Role display names
    ROLE_NAMES = {
        ADMIN: 'Admin',
        EMPLOYEUR_DG: 'Employeur DG',
        EMPLOYEUR_ZONE: 'Employeur Zone',
        EMPLOYEUR_UNITE: 'Employeur Unité',
        UTILISATEUR: 'Utilisateur'
    }

    # Role descriptions
    ROLE_DESCRIPTIONS = {
        ADMIN: 'Accès complet au système',
        EMPLOYEUR_DG: 'Gestion globale de l\'organisation',
        EMPLOYEUR_ZONE: 'Supervision et consultation des unités de la zone',
        EMPLOYEUR_UNITE: 'Gestion d\'une unité spécifique',
        UTILISATEUR: 'Accès limité aux fonctionnalités de base'
    }

class Permission:
    """Defines granular permissions for specific features and actions."""
    # Incident-related permissions
    VIEW_INCIDENT = 'view_incident'
    CREATE_INCIDENT = 'create_incident'
    EDIT_INCIDENT = 'edit_incident'
    DELETE_INCIDENT = 'delete_incident'
    RESOLVE_INCIDENT = 'resolve_incident'
    GET_AI_EXPLANATION = 'get_ai_explanation'
    DEEP_ANALYSIS = 'deep_analysis'

    # Export permissions
    EXPORT_INCIDENT_PDF = 'export_incident_pdf'
    EXPORT_ALL_INCIDENTS_PDF = 'export_all_incidents_pdf'

    # User management permissions
    CREATE_USERS = 'create_users'
    EDIT_USERS = 'edit_users'
    DELETE_USERS = 'delete_users'

    # Zone and unit management permissions
    CREATE_ZONES = 'create_zones'
    EDIT_ZONES = 'edit_zones'
    DELETE_ZONES = 'delete_zones'
    CREATE_UNITS = 'create_units'
    EDIT_UNITS = 'edit_units'
    DELETE_UNITS = 'delete_units'

    # Viewing permissions
    VIEW_ALL_ZONES = 'view_all_zones'
    VIEW_ALL_UNITS = 'view_all_units'
    VIEW_ALL_CENTERS = 'view_all_centers'
    VIEW_ALL_INCIDENTS = 'view_all_incidents'

class PermissionManager:
    """Manages role-based access control for the entire system."""
    
    # Comprehensive role permissions mapping
    _ROLE_PERMISSIONS: Dict[str, Set[str]] = {
        UserRole.ADMIN: {
            # Full system access
            Permission.VIEW_INCIDENT,
            Permission.CREATE_INCIDENT,
            Permission.EDIT_INCIDENT,
            Permission.DELETE_INCIDENT,
            Permission.RESOLVE_INCIDENT,
            Permission.GET_AI_EXPLANATION,
            Permission.DEEP_ANALYSIS,
            Permission.EXPORT_INCIDENT_PDF,
            Permission.EXPORT_ALL_INCIDENTS_PDF,
            
            Permission.CREATE_USERS,
            Permission.EDIT_USERS,
            Permission.DELETE_USERS,
            
            Permission.CREATE_ZONES,
            Permission.EDIT_ZONES,
            Permission.DELETE_ZONES,
            Permission.CREATE_UNITS,
            Permission.EDIT_UNITS,
            Permission.DELETE_UNITS,
            
            Permission.VIEW_ALL_ZONES,
            Permission.VIEW_ALL_UNITS,
            Permission.VIEW_ALL_CENTERS,
            Permission.VIEW_ALL_INCIDENTS
        },
        UserRole.EMPLOYEUR_DG: {
            # Global management with limited destructive actions
            Permission.VIEW_INCIDENT,
            Permission.RESOLVE_INCIDENT,
            Permission.GET_AI_EXPLANATION,
            Permission.DEEP_ANALYSIS,
            Permission.EXPORT_INCIDENT_PDF,
            Permission.EXPORT_ALL_INCIDENTS_PDF,
            
            Permission.CREATE_USERS,
            Permission.EDIT_USERS,
            
            Permission.CREATE_ZONES,
            Permission.EDIT_ZONES,
            Permission.CREATE_UNITS,
            Permission.EDIT_UNITS,
            
            Permission.VIEW_ALL_ZONES,
            Permission.VIEW_ALL_UNITS,
            Permission.VIEW_ALL_CENTERS,
            Permission.VIEW_ALL_INCIDENTS
        },
        UserRole.EMPLOYEUR_ZONE: {
            # Zone-level access
            Permission.VIEW_INCIDENT,
            Permission.RESOLVE_INCIDENT,
            Permission.EXPORT_INCIDENT_PDF,
            Permission.GET_AI_EXPLANATION,
            Permission.DEEP_ANALYSIS,
            Permission.VIEW_ALL_ZONES,
            Permission.VIEW_ALL_UNITS,
            Permission.VIEW_ALL_CENTERS,
            Permission.VIEW_ALL_INCIDENTS
        },
        UserRole.EMPLOYEUR_UNITE: {
            # Unit-level access
            Permission.VIEW_INCIDENT,
            Permission.CREATE_INCIDENT,
            Permission.EDIT_INCIDENT,
            Permission.RESOLVE_INCIDENT,
            Permission.EXPORT_INCIDENT_PDF
        },
        UserRole.UTILISATEUR: {
            # Basic access
            Permission.VIEW_INCIDENT
        }
    }

    @classmethod
    def get_role_permissions(cls, role: str) -> Set[str]:
        """
        Retrieve all permissions for a given role.
        
        Args:
            role (str): The role to get permissions for.
        
        Returns:
            Set[str]: A set of permissions for the specified role.
        """
        return cls._ROLE_PERMISSIONS.get(role, set())

    @classmethod
    def has_permission(cls, role: str, permission: str) -> bool:
        """
        Check if a role has a specific permission.
        
        Args:
            role (str): The role to check.
            permission (str): The permission to verify.
        
        Returns:
            bool: True if the role has the permission, False otherwise.
        """
        return permission in cls.get_role_permissions(role)

    @classmethod
    def get_available_roles_for_user(cls, current_user_role: str) -> list:
        """
        Determine available roles that can be assigned based on current user's role.
        
        Args:
            current_user_role (str): Role of the current user.
        
        Returns:
            list: List of roles that can be assigned.
        """
        available_roles = [
            UserRole.EMPLOYEUR_DG,
            UserRole.EMPLOYEUR_ZONE,
            UserRole.EMPLOYEUR_UNITE,
            UserRole.UTILISATEUR
        ]
        
        if current_user_role == UserRole.ADMIN:
            available_roles.insert(0, UserRole.ADMIN)
        
        return available_roles

def permission_required(permission):
    """
    Decorator to enforce permission checks on route functions.
    
    Args:
        permission (str): The required permission
    
    Returns:
        function: Decorated function with permission check
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not PermissionManager.has_permission(current_user.role, permission):
                flash('Vous n\'avez pas la permission d\'effectuer cette action.', 'danger')
                return redirect('main_dashboard.dashboard')  # Redirect to dashboard
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def context_permission_check(permission):
    """
    Context manager for template-level permission checks.
    
    Args:
        permission (str): The permission to check
    
    Returns:
        bool: Whether the current user has the permission
    """
    return PermissionManager.has_permission(current_user.role, permission)
