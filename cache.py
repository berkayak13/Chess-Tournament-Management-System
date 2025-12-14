"""
Caching module for Chess Tournament Management System.
Provides Redis-backed caching with fallback to simple in-memory cache.
"""

import os
import json
import functools
from datetime import datetime

# Try to import Flask-Caching
try:
    from flask_caching import Cache
    CACHING_AVAILABLE = True
except ImportError:
    CACHING_AVAILABLE = False
    Cache = None


def init_cache(app):
    """Initialize caching for the Flask app."""
    if not CACHING_AVAILABLE:
        app.logger.warning("Flask-Caching not installed. Caching disabled.")
        return None

    redis_url = os.getenv('REDIS_URL')

    if redis_url:
        # Use Redis
        cache_config = {
            'CACHE_TYPE': 'redis',
            'CACHE_REDIS_URL': redis_url,
            'CACHE_DEFAULT_TIMEOUT': int(os.getenv('CACHE_TIMEOUT', 300)),
            'CACHE_KEY_PREFIX': 'chess_'
        }
        app.logger.info(f"Caching enabled with Redis: {redis_url.split('@')[-1] if '@' in redis_url else redis_url}")
    else:
        # Use simple in-memory cache
        cache_config = {
            'CACHE_TYPE': 'simple',
            'CACHE_DEFAULT_TIMEOUT': int(os.getenv('CACHE_TIMEOUT', 300)),
            'CACHE_THRESHOLD': 500
        }
        app.logger.info("Caching enabled with simple in-memory cache")

    cache = Cache(app, config=cache_config)
    return cache


def make_cache_key(*args, **kwargs):
    """Create a cache key from function arguments."""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    return ':'.join(key_parts)


class CacheHelper:
    """Helper class for caching operations."""

    def __init__(self, cache):
        self.cache = cache
        self.enabled = cache is not None

    def get(self, key):
        """Get value from cache."""
        if not self.enabled:
            return None
        return self.cache.get(key)

    def set(self, key, value, timeout=None):
        """Set value in cache."""
        if not self.enabled:
            return
        self.cache.set(key, value, timeout=timeout)

    def delete(self, key):
        """Delete value from cache."""
        if not self.enabled:
            return
        self.cache.delete(key)

    def clear_pattern(self, pattern):
        """Clear all keys matching pattern (Redis only)."""
        if not self.enabled:
            return
        if hasattr(self.cache, 'delete_memoized'):
            # Flask-Caching doesn't support pattern deletion directly
            # This would need custom Redis commands for pattern matching
            pass

    def cached(self, timeout=None, key_prefix='view'):
        """Decorator for caching function results."""
        if not self.enabled:
            def decorator(f):
                return f
            return decorator

        return self.cache.cached(timeout=timeout, key_prefix=key_prefix)

    def memoize(self, timeout=None):
        """Decorator for memoizing function results with arguments."""
        if not self.enabled:
            def decorator(f):
                return f
            return decorator

        return self.cache.memoize(timeout=timeout)


# Cache timeouts for different types of data
CACHE_TIMEOUTS = {
    'statistics': 30,      # Player/arbiter statistics - 30 seconds
    'halls': 300,          # Hall information - 5 minutes
    'api_tables': 300,     # API table data - 5 minutes
    'admin_stats': 60,     # Admin stats page - 1 minute
    'dashboard': 15,       # Dashboard data - 15 seconds
}
