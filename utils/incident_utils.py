from models import Incident, Unit, UserRole
from typing import Dict, Union
from extensions import cache
import functools

def get_incident_cache_key(user, include_author=False):
    """
    Generate a unique cache key for incident counts.
    
    Args:
        user: Currently logged-in user
        include_author: Flag to include author in cache key
    
    Returns:
        Unique cache key string
    """
    return f"incident_counts_{user.id}_{user.role}_{include_author}"

def cached_incident_counts(func):
    """
    Decorator to cache incident count results.
    
    Args:
        func: Function to be cached
    
    Returns:
        Cached function result
    """
    @functools.wraps(func)
    def wrapper(user, include_author=False):
        # Generate cache key
        cache_key = get_incident_cache_key(user, include_author)
        
        # Try to get cached result
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Compute and cache result
        result = func(user, include_author)
        cache.set(cache_key, result, timeout=300)  # 5-minute cache
        
        return result
    
    # Attach methods for manual cache management
    wrapper.get_cache_key = get_incident_cache_key
    wrapper.invalidate_cache = lambda user, include_author=False: cache.delete(
        get_incident_cache_key(user, include_author)
    )
    
    return wrapper

@cached_incident_counts
def get_user_incident_counts(user, include_author=False):
    """
    Retrieve incident counts based on user role and permissions.
    
    Args:
        user: Currently logged-in user
        include_author: If True, use author for filtering instead of unit_id
    
    Returns:
        Dict of incident counts with total, resolved, and new incidents
    """
    # Base query setup
    if user.role in [UserRole.ADMIN, UserRole.EMPLOYEUR_DG]:
        # For admin and top-level roles, use global queries
        total_query = Incident.query
        resolved_query = total_query.filter_by(status='Résolu')
        nouveau_query = total_query.filter_by(status='Nouveau')
    
    elif user.role == UserRole.EMPLOYEUR_ZONE:
        # For zone-level users, filter by zone's units
        zone_units = Unit.query.filter_by(zone_id=user.zone_id).all()
        unit_ids = [unit.id for unit in zone_units]
        
        total_query = Incident.query.filter(Incident.unit_id.in_(unit_ids))
        resolved_query = total_query.filter(Incident.status == 'Résolu')
        nouveau_query = total_query.filter(Incident.status == 'Nouveau')
    
    else:
        # For other roles, filter by unit or author
        if include_author:
            total_query = Incident.query.filter_by(author=user)
            resolved_query = total_query.filter_by(status='Résolu')
            nouveau_query = total_query.filter_by(status='Nouveau')
        else:
            total_query = Incident.query.filter_by(unit_id=user.unit_id)
            resolved_query = total_query.filter_by(status='Résolu')
            nouveau_query = total_query.filter_by(status='Nouveau')
    
    # Execute count queries
    total_incidents = total_query.count()
    resolved_incidents = resolved_query.count()
    nouveau_incidents = nouveau_query.count()
    
    return {
        'total_incidents': total_incidents,
        'resolved_incidents': resolved_incidents,
        'nouveau_incidents': nouveau_incidents
    }
