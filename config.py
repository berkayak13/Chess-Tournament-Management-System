"""
Configuration module for Chess Tournament Management System.
Supports environment-based configuration for local dev, testing, and production (GCP).
"""
import os

# Load dotenv if available (optional for production)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required in production


class Config:
    """Base configuration with defaults."""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '1234')
    DB_NAME = os.getenv('DB_NAME', 'chessdb')

    # Cloud Function URL (for audit logging)
    FUNCTION_URL = os.getenv('FUNCTION_URL', None)

    # Redis/Caching
    REDIS_URL = os.getenv('REDIS_URL', None)
    CACHE_TYPE = 'redis' if os.getenv('REDIS_URL') else 'simple'
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', 300))

    @classmethod
    def get_db_config(cls):
        """Return database configuration dictionary for mysql.connector."""
        return {
            'host': cls.DB_HOST,
            'port': cls.DB_PORT,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD,
            'database': cls.DB_NAME
        }


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration with test database."""
    DEBUG = False
    TESTING = True
    DB_NAME = os.getenv('TEST_DB_NAME', 'chessdb_test')
    # Use a different secret key for tests
    SECRET_KEY = 'test-secret-key'
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration for GCP deployment."""
    DEBUG = False
    TESTING = False

    # In production, these MUST be set via environment variables
    # SECRET_KEY - required
    # DB_HOST - Cloud SQL private IP or proxy socket
    # DB_USER - application user (not root)
    # DB_PASSWORD - strong password
    # FUNCTION_URL - Cloud Function endpoint
    # REDIS_URL - Memorystore endpoint


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on FLASK_ENV environment variable."""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
