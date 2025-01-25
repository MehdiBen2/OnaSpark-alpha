"""
Store all URL endpoints as constants to avoid hardcoding them in templates
"""

# Main routes
INDEX = 'index'
MAIN_DASHBOARD = 'main_dashboard.dashboard'
DASHBOARD = 'main_dashboard.dashboard'  # Keeping both for backward compatibility
LISTES_DASHBOARD = 'main_dashboard.listes_dashboard'
SERVICES = 'services'
SELECT_UNIT = 'select_unit'

# Department routes
EXPLOITATION = 'exploitation'
DEPARTEMENTS = 'departements'
RAPPORTS = 'rapports'
STATISTIQUES = 'departement.statistiques'  # Updated to use a more specific namespace

# Reuse routes
REUSE = 'reuse'
REUSE_INTRODUCTION = 'reuse.introduction'
REUSE_REGULATIONS = 'reuse.regulations'
REUSE_METHODS = 'reuse.methods'
REUSE_CASE_STUDIES = 'reuse.case_studies'
REUSE_DOCUMENTATION = 'reuse.documentation'

# Admin routes
LIST_ZONES = 'admin.list_zones'
LIST_CENTERS = 'admin.list_centers'
CREATE_ZONE = 'admin.create_zone'
EDIT_ZONE = 'admin.edit_zone'
DELETE_ZONE = 'admin.delete_zone'
CREATE_CENTER = 'admin.create_center'
EDIT_CENTER = 'admin.edit_center'
DELETE_CENTER = 'admin.delete_center'

# API routes
GET_ZONE_UNITS = 'api.get_zone_units'

# Spark Agent routes
GET_MISTRAL_API_KEY = 'spark_agent.get_mistral_api_key'

# Incidents routes
INCIDENT_LIST = 'incidents.incident_list'
NEW_INCIDENT = 'incidents.new'
VIEW_INCIDENT = 'incidents.view'
EDIT_INCIDENT = 'incidents.edit'
DELETE_INCIDENT = 'incidents.delete'
RESOLVE_INCIDENT = 'incidents.resolve'
EXPORT_INCIDENT_PDF = 'incidents.export_pdf'
EXPORT_ALL_INCIDENTS_PDF = 'incidents.export_all_pdf'
MERGE_INCIDENT = 'incidents.merge'
BATCH_MERGE = 'incidents.batch_merge'

# Incident routes
INCIDENT_LIST = 'incidents.incident_list'
NEW_INCIDENT = 'incidents.new'
VIEW_INCIDENT = 'incidents.view'
EDIT_INCIDENT = 'incidents.edit'
DELETE_INCIDENT = 'incidents.delete'
RESOLVE_INCIDENT = 'incidents.resolve'
EXPORT_INCIDENT_PDF = 'incidents.export_pdf'
EXPORT_ALL_INCIDENTS_PDF = 'incidents.export_all_pdf'
MERGE_INCIDENT = 'incidents.merge'
BATCH_MERGE = 'incidents.batch_merge'

# Auth routes
LOGIN = 'auth.login'
LOGOUT = 'auth.logout'
REGISTER = 'auth.register'

# Profile routes
PROFILE_VIEW = 'profiles.view'
PROFILE_EDIT = 'profiles.edit'
PROFILE_CREATE = 'profiles.create'
PROFILE_ADMIN = 'profiles.admin'
PROFILE_USER_VIEW = 'profiles.user_view'

# Unit routes
SELECT_UNIT = 'unit.select'
UPDATE_UNIT = 'unit.update'
GET_UNIT_INCIDENTS = 'unit.get_incidents'

# Landing routes
LANDING_INDEX = 'landing.index'

"""URL endpoints configuration for the application."""

# Auth routes
AUTH_LOGIN = 'auth.login'
