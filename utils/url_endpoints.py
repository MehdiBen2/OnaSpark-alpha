"""
URL Endpoints Configuration for OnaSpark Application

This module centralizes all URL endpoint constants to:
1. Avoid hardcoding route names throughout the application
2. Provide a single source of truth for route names
3. Facilitate easier route management and refactoring
4. Improve code maintainability and readability

Last Updated: 2025-02-14
"""

# Main routes
INDEX = 'index'
MAIN_DASHBOARD = 'main_dashboard.dashboard'
DASHBOARD = 'main_dashboard.dashboard'  # Keeping for backward compatibility
LISTES_DASHBOARD = 'main_dashboard.listes_dashboard'
GET_DASHBOARD_DATA = 'main_dashboard.get_dashboard_data'
SERVICES = 'services'

# Department routes
EXPLOITATION = 'exploitation'
DEPARTEMENTS = 'departements'
RAPPORTS = 'rapports'
STATISTIQUES = 'departement.statistiques'
DEPARTEMENT_EXPLOITATION = 'departement.exploitation'
DEPARTEMENT_REUSE = 'departement.reuse'
DEPARTEMENT_RAPPORTS = 'departement.rapports'

# Reuse routes
REUSE = 'reuse'
REUSE_INTRODUCTION = 'reuse.introduction'
REUSE_REGULATIONS = 'reuse.regulations'
REUSE_METHODS = 'reuse.methods'
REUSE_CASE_STUDIES = 'reuse.case_studies'
REUSE_DOCUMENTATION = 'reuse.documentation'
REUSE_SECTIONS = {
    'introduction': REUSE_INTRODUCTION,
    'regulations': REUSE_REGULATIONS,
    'methods': REUSE_METHODS,
    'case_studies': REUSE_CASE_STUDIES,
    'documentation': REUSE_DOCUMENTATION
}

# Admin routes
LIST_ZONES = 'admin.list_zones'
LIST_CENTERS = 'admin.list_centers'
CREATE_ZONE = 'admin.create_zone'
EDIT_ZONE = 'admin.edit_zone'
DELETE_ZONE = 'admin.delete_zone'
CREATE_CENTER = 'admin.create_center'
EDIT_CENTER = 'admin.edit_center'
DELETE_CENTER = 'admin.delete_center'

# Unit routes
SELECT_UNIT = 'unit.select'
GET_ZONE_UNITS = 'api.get_zone_units'
UNITS_LIST = 'units.units_list'
UNITS_CREATE = '/units/create'  # Keeping original path for compatibility
UNITS_EDIT = '/units/<int:unit_id>/edit'  # Keeping original path for compatibility
UNITS_DELETE = '/units/<int:unit_id>/delete'  # Keeping original path for compatibility
UPDATE_UNIT = 'unit.update'
GET_UNIT_INCIDENTS = 'unit.get_incidents'

# Spark Agent routes
SPARK_AGENT_PAGE = 'spark_agent.page'
GET_MISTRAL_API_KEY = 'spark_agent.get_mistral_api_key'
GET_DEFAULT_MODEL = 'spark_agent.get_default_model'

# Authentication routes
LOGIN = 'auth.login'
AUTH_LOGIN = 'auth.login'  # Keeping for backward compatibility
LOGOUT = 'auth.logout'
REGISTER = 'auth.register'

# Profile routes
PROFILE_VIEW = 'profiles.view_profile'
PROFILE_CREATE = 'profiles.create_profile'
PROFILE_EDIT = 'profiles.edit_profile'
PROFILE_ADMIN = 'profiles.admin_profiles'
PROFILE_USER_VIEW = 'profiles.view_user_profile'

# Incidents routes
INCIDENT_LIST = 'incidents.incident_list'
NEW_INCIDENT = 'incidents.new'
VIEW_INCIDENT = 'incidents.view'
EDIT_INCIDENT = 'incidents.edit'
DELETE_INCIDENT = 'incidents.delete'
RESOLVE_INCIDENT = 'incidents.resolve'
EXPORT_INCIDENT_PDF = 'incidents.export_pdf'
EXPORT_ALL_INCIDENTS_PDF = 'incidents.export_all_pdf'
INVALIDATE_INCIDENT_CACHE = 'incidents.invalidate_cache'

# Water Quality routes
WATER_QUALITY_ASSESSMENT = 'water_quality.assessment'
WATER_QUALITY_EVALUATION = 'water_quality.evaluate'
WATER_QUALITY_RESULTS = 'water_quality.results'
WATER_QUALITY_PDF_DOWNLOAD = 'water_quality.download_pdf'

# Documentation routes
SERVE_DOCS = 'docs.serve'

# Landing routes
LANDING_INDEX = 'landing.index'

# Error handling routes
ERROR_404 = 'error.not_found'
ERROR_500 = 'error.internal_server'
ERROR_403 = 'error.forbidden'
