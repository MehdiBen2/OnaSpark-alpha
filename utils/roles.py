from enum import Enum

class UserRole:
    # Define all available roles
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

    # Role permissions
    PERMISSIONS = {
        ADMIN: {
            'can_create_users': True,
            'can_edit_users': True,
            'can_delete_users': True,
            'can_create_zones': True,
            'can_edit_zones': True,
            'can_delete_zones': True,
            'can_create_units': True,
            'can_edit_units': True,
            'can_delete_units': True,
            'can_create_centers': True,
            'can_edit_centers': True,
            'can_delete_centers': True,
            'can_manage_incidents': True,
            'requires_unit_selection': False,
            'can_view_all_zones': True,
            'can_view_all_units': True,
            'can_view_all_centers': True,
            'can_view_all_incidents': True
        },
        EMPLOYEUR_DG: {
            'can_create_users': True,
            'can_edit_users': True,
            'can_delete_users': False,
            'can_create_zones': True,
            'can_edit_zones': True,
            'can_delete_zones': False,
            'can_create_units': True,
            'can_edit_units': True,
            'can_delete_units': False,
            'can_create_centers': True,
            'can_edit_centers': True,
            'can_delete_centers': False,
            'can_manage_incidents': True,
            'requires_unit_selection': False,
            'can_view_all_zones': True,
            'can_view_all_units': True,
            'can_view_all_centers': True,
            'can_view_all_incidents': True
        },
        EMPLOYEUR_ZONE: {
            'can_create_users': False,
            'can_edit_users': False,
            'can_delete_users': False,
            'can_create_zones': False,
            'can_edit_zones': False,
            'can_delete_zones': False,
            'can_create_units': False,
            'can_edit_units': False,
            'can_delete_units': False,
            'can_create_centers': False,
            'can_edit_centers': False,
            'can_delete_centers': False,
            'can_manage_incidents': False,
            'requires_unit_selection': False,
            'can_view_all_zones': False,
            'can_view_zone_units': True,
            'can_view_zone_centers': True,
            'can_view_zone_incidents': True,
            'can_view_zone_users': True
        },
        EMPLOYEUR_UNITE: {
            'can_create_users': False,
            'can_edit_users': False,
            'can_delete_users': False,
            'can_create_zones': False,
            'can_edit_zones': False,
            'can_delete_zones': False,
            'can_create_units': False,
            'can_edit_units': False,
            'can_delete_units': False,
            'can_create_centers': True,
            'can_edit_centers': True,
            'can_delete_centers': False,
            'can_manage_incidents': True,
            'requires_unit_selection': True,
            'can_view_unit_centers': True,
            'can_view_unit_incidents': True,
            'can_view_unit_users': True
        },
        UTILISATEUR: {
            'can_create_users': False,
            'can_edit_users': False,
            'can_delete_users': False,
            'can_create_zones': False,
            'can_edit_zones': False,
            'can_delete_zones': False,
            'can_create_units': False,
            'can_edit_units': False,
            'can_delete_units': False,
            'can_create_centers': False,
            'can_edit_centers': False,
            'can_delete_centers': False,
            'can_create_incidents': True,
            'can_edit_own_incidents': True,
            'can_delete_own_incidents': False,
            'requires_unit_selection': True,
            'can_view_unit_incidents': True
        }
    }

    # Role requirements for zone and unit
    ROLES_REQUIRING_ZONE = {EMPLOYEUR_ZONE, EMPLOYEUR_UNITE, UTILISATEUR}
    ROLES_REQUIRING_UNIT = {EMPLOYEUR_UNITE, UTILISATEUR}

    @staticmethod
    def is_admin(role):
        """Check if role has admin privileges"""
        return role == UserRole.ADMIN

    @staticmethod
    def is_dg(role):
        """Check if role has global access"""
        return role == UserRole.EMPLOYEUR_DG

    @staticmethod
    def requires_zone(role):
        """Check if role requires zone assignment"""
        return role in UserRole.ROLES_REQUIRING_ZONE

    @staticmethod
    def requires_unit(role):
        """Check if role requires unit assignment"""
        return role in UserRole.ROLES_REQUIRING_UNIT

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

    @staticmethod
    def get_role_display_name(role):
        """Get the display name for a role"""
        return UserRole.ROLE_NAMES.get(role, role)

    @staticmethod
    def get_permissions(role):
        return UserRole.PERMISSIONS.get(role, UserRole.PERMISSIONS[UserRole.UTILISATEUR])

    @staticmethod
    def requires_unit_selection(role):
        """Return True if the role requires unit selection."""
        return role not in [UserRole.ADMIN, UserRole.EMPLOYEUR_DG, UserRole.EMPLOYEUR_ZONE]

    @staticmethod
    def assign_role_and_permissions(user_id, role, zone_id=None, unit_id=None):
        """
        Assign role and permissions to a user with appropriate zone and unit assignments.
        
        Args:
            user_id (int): The ID of the user to assign the role to
            role (str): The role to assign (must be one of the defined roles)
            zone_id (int, optional): The ID of the zone to assign
            unit_id (int, optional): The ID of the unit to assign
            
        Returns:
            tuple: (bool, str) - (success status, message)
        """
        from models import db, User, Zone, Unit
        
        # Validate role
        if role not in UserRole.ROLE_NAMES:
            return False, f"Invalid role: {role}"
            
        try:
            user = User.query.get(user_id)
            if not user:
                return False, f"User with ID {user_id} not found"
                
            # Validate and assign based on role
            if role == UserRole.ADMIN:
                # Admin roles don't need zone or unit assignments
                user.role = role
                user.zone_id = None
                user.unit_id = None
                
            elif role == UserRole.EMPLOYEUR_DG:
                # Global employer (DG) - no specific zone/unit needed
                user.role = role
                user.zone_id = None
                user.unit_id = None
                
            elif role == UserRole.EMPLOYEUR_ZONE:
                # Employeur Zone - requires zone assignment
                if not zone_id:
                    return False, "Zone ID is required for Employeur Zone role"
                    
                zone = Zone.query.get(zone_id)
                if not zone:
                    return False, f"Zone with ID {zone_id} not found"
                    
                user.role = role
                user.zone_id = zone_id
                user.unit_id = None
                
            elif role in [UserRole.EMPLOYEUR_UNITE, UserRole.UTILISATEUR]:
                # Unit-level roles require both zone and unit
                if not zone_id or not unit_id:
                    return False, "Both Zone ID and Unit ID are required for unit-level roles"
                    
                zone = Zone.query.get(zone_id)
                if not zone:
                    return False, f"Zone with ID {zone_id} not found"
                    
                unit = Unit.query.get(unit_id)
                if not unit:
                    return False, f"Unit with ID {unit_id} not found"
                    
                # Verify unit belongs to specified zone
                if unit.zone_id != zone_id:
                    return False, f"Unit {unit_id} does not belong to Zone {zone_id}"
                    
                user.role = role
                user.zone_id = zone_id
                user.unit_id = unit_id
                
            db.session.commit()
            return True, f"Successfully assigned role {role} to user {user.username}"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error assigning role: {str(e)}"
