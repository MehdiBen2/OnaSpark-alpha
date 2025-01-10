"""
Store all URL endpoints as constants to avoid hardcoding them in templates
"""

# Main routes
INDEX = 'index'
DASHBOARD = 'dashboard'
MAIN_DASHBOARD = 'main_dashboard'

# Incident routes
INCIDENT_LIST = 'incidents.incident_list'
NEW_INCIDENT = 'incidents.new_incident'
VIEW_INCIDENT = 'incidents.view_incident'
EDIT_INCIDENT = 'incidents.edit_incident'
DELETE_INCIDENT = 'incidents.delete_incident'
RESOLVE_INCIDENT = 'incidents.resolve_incident'
EXPORT_INCIDENT_PDF = 'incidents.export_incident_pdf'
EXPORT_ALL_INCIDENTS_PDF = 'incidents.export_all_incidents_pdf'
MERGE_INCIDENT = 'incidents.merge_incident'
BATCH_MERGE = 'incidents.batch_merge'

# Auth routes
LOGIN = 'auth.login'
LOGOUT = 'auth.logout'
REGISTER = 'auth.register'

# Profile routes
VIEW_PROFILE = 'profiles.view_profile'
EDIT_PROFILE = 'profiles.edit_profile'
CREATE_PROFILE = 'profiles.create_profile'
ADMIN_PROFILES = 'profiles.admin_profiles'

# Unit routes
SELECT_UNIT = 'select_unit'
UPDATE_UNIT = 'update_unite'
GET_UNIT_INCIDENTS = 'get_unit_incidents'

"""URL endpoints configuration for the application."""

# Auth routes
AUTH_LOGIN = 'auth.login'

# Main routes
INDEX = 'index'
MAIN_DASHBOARD = 'main_dashboard'
DASHBOARD = 'dashboard'
SERVICES = 'services'
LISTES_DASHBOARD = 'listes_dashboard'
SELECT_UNIT = 'select_unit'

# Department routes
EXPLOITATION = 'exploitation'
DEPARTEMENTS = 'departements'
RAPPORTS = 'rapports'
STATISTIQUES = 'statistiques'

# Reuse routes
REUSE = 'reuse'
REUSE_INTRODUCTION = 'reuse_introduction'
REUSE_REGULATIONS = 'reuse_regulations'
REUSE_METHODS = 'reuse_methods'
REUSE_CASE_STUDIES = 'reuse_case_studies'
REUSE_DOCUMENTATION = 'reuse_documentation'

# Admin routes
LIST_ZONES = 'list_zones'
LIST_CENTERS = 'list_centers'
CREATE_ZONE = 'create_zone'
EDIT_ZONE = 'edit_zone'
DELETE_ZONE = 'delete_zone'
CREATE_CENTER = 'create_center'
EDIT_CENTER = 'edit_center'
DELETE_CENTER = 'delete_center'

# API routes
GET_ZONE_UNITS = 'get_zone_units'

# Incidents routes
INCIDENT_LIST = 'incidents.incident_list'
