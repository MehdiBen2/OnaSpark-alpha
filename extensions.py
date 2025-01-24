from flask_caching import Cache

# Initialize cache as a global object
cache = Cache(config={
    'CACHE_TYPE': 'SimpleCache',  # Use in-memory caching
    'CACHE_DEFAULT_TIMEOUT': 300  # Cache for 5 minutes
})
