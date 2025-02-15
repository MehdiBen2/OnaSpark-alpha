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

    # Role descriptions
    ROLE_DESCRIPTIONS = {
        ADMIN: 'Accès complet au système',
        EMPLOYEUR_DG: 'Accès global à toutes les zones et unités',
        EMPLOYEUR_ZONE: 'Accès aux unités de sa zone',
        EMPLOYEUR_UNITE: 'Accès aux incidents de son unité',
        UTILISATEUR: 'Accès limité aux fonctionnalités de base'
    }

    # Role display names
    ROLE_NAMES = {
        ADMIN: 'Admin',
        EMPLOYEUR_DG: 'Employeur DG',
        EMPLOYEUR_ZONE: 'Employeur Zone',
        EMPLOYEUR_UNITE: 'Employeur Unité',
        UTILISATEUR: 'Utilisateur'
    }

    @staticmethod
    def is_admin(role):
        """
        Check if the given role is an admin role
        
        :param role: Role to check
        :return: Boolean indicating if the role is admin
        """
        return role == UserRole.ADMIN

    @staticmethod
    def get_role_display_name(role):
        """
        Get the display name for a given role
        
        :param role: Role to get display name for
        :return: Display name of the role
        """
        return UserRole.ROLE_NAMES.get(role, role)

    # Alias method to ensure compatibility
    is_admin_role = is_admin

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

    # Infrastructure-related permissions
    VIEW_INFRASTRUCTURES = 'view_infrastructures'
    CREATE_INFRASTRUCTURE = 'create_infrastructure'
    EDIT_INFRASTRUCTURE = 'edit_infrastructure'
    DELETE_INFRASTRUCTURE = 'delete_infrastructure'
    EXPORT_INFRASTRUCTURES = 'export_infrastructures'

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
            Permission.VIEW_ALL_INCIDENTS,
            Permission.VIEW_INFRASTRUCTURES,
            Permission.CREATE_INFRASTRUCTURE,
            Permission.EDIT_INFRASTRUCTURE,
            Permission.DELETE_INFRASTRUCTURE,
            Permission.EXPORT_INFRASTRUCTURES
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
            Permission.VIEW_ALL_INCIDENTS,
            Permission.VIEW_INFRASTRUCTURES
        },
        UserRole.EMPLOYEUR_ZONE: {
            # Zone-level access
            Permission.VIEW_INCIDENT,
            Permission.CREATE_INCIDENT,
            Permission.EDIT_INCIDENT,
            Permission.DELETE_INCIDENT,
            Permission.RESOLVE_INCIDENT,
            Permission.GET_AI_EXPLANATION,
            Permission.DEEP_ANALYSIS,
            Permission.EXPORT_INCIDENT_PDF,
            Permission.EXPORT_ALL_INCIDENTS_PDF,
            Permission.DEEP_ANALYSIS,
            Permission.VIEW_ALL_ZONES,
            Permission.VIEW_ALL_UNITS,
            Permission.VIEW_ALL_CENTERS,
            Permission.VIEW_ALL_INCIDENTS,
            Permission.VIEW_INFRASTRUCTURES
        },
        UserRole.EMPLOYEUR_UNITE: {
            # Unit-level access
            Permission.VIEW_INCIDENT,
            Permission.CREATE_INCIDENT,
            Permission.EDIT_INCIDENT,
            Permission.RESOLVE_INCIDENT,
            Permission.EXPORT_INCIDENT_PDF,
            Permission.VIEW_INFRASTRUCTURES
        },
        UserRole.UTILISATEUR: {
            # Basic access
             Permission.CREATE_INCIDENT,
            Permission.VIEW_INCIDENT,
            Permission.GET_AI_EXPLANATION,
            Permission.DEEP_ANALYSIS,
            Permission.EXPORT_INCIDENT_PDF,
            Permission.EXPORT_ALL_INCIDENTS_PDF,
            Permission.DEEP_ANALYSIS,
            Permission.VIEW_INFRASTRUCTURES
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

    @staticmethod
    def is_admin(role):
        """Check if role has admin privileges"""
        return UserRole.is_admin(role)

    @staticmethod
    def is_dg(role):
        """Check if role has global access"""
        return role == UserRole.EMPLOYEUR_DG

    @staticmethod
    def requires_zone(role):
        """Check if role requires zone assignment"""
        return role in {UserRole.EMPLOYEUR_ZONE, UserRole.EMPLOYEUR_UNITE, UserRole.UTILISATEUR}

    @staticmethod
    def requires_unit(role):
        """Check if role requires unit assignment"""
        return role in {UserRole.EMPLOYEUR_UNITE, UserRole.UTILISATEUR}

    @staticmethod
    def get_all_roles():
        """Get list of all available roles"""
        return [
            UserRole.ADMIN,
            UserRole.EMPLOYEUR_DG,
            UserRole.EMPLOYEUR_ZONE,
            UserRole.EMPLOYEUR_UNITE,
            UserRole.UTILISATEUR
        ]

    @staticmethod
    def get_role_description(role):
        """Get the description for a role"""
        return UserRole.ROLE_DESCRIPTIONS.get(role, '')

    @classmethod
    def get_role_display_names(cls):
        """Get a dictionary of role display names"""
        return UserRole.ROLE_NAMES

    @staticmethod
    def requires_unit_selection(role):
        """Return True if the role requires unit selection."""
        return role not in {UserRole.ADMIN, UserRole.EMPLOYEUR_DG, UserRole.EMPLOYEUR_ZONE}

    @staticmethod
    def has_higher_or_equal_role(user_role, target_role):
        """
        Check if the user's role has equal or higher privileges
        Hierarchy: ADMIN > EMPLOYEUR_DG > EMPLOYEUR_ZONE > EMPLOYEUR_UNITE > UTILISATEUR
        """
        role_hierarchy = [
            UserRole.UTILISATEUR, 
            UserRole.EMPLOYEUR_UNITE, 
            UserRole.EMPLOYEUR_ZONE, 
            UserRole.EMPLOYEUR_DG, 
            UserRole.ADMIN
        ]
        
        try:
            user_role_index = role_hierarchy.index(user_role)
            target_role_index = role_hierarchy.index(target_role)
            return user_role_index >= target_role_index
        except ValueError:
            # If either role is not in the hierarchy, return False
            return False

    @staticmethod
    def get_role_hierarchy():
        """Return the role hierarchy from lowest to highest privilege"""
        return [
            UserRole.UTILISATEUR, 
            UserRole.EMPLOYEUR_UNITE, 
            UserRole.EMPLOYEUR_ZONE, 
            UserRole.EMPLOYEUR_DG, 
            UserRole.ADMIN
        ]

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
