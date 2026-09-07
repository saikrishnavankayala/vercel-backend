import os
from datetime import timedelta


def database_uri():
    """Use PyMySQL for standard MySQL URLs supplied by hosting providers."""
    url = os.environ.get('DATABASE_URL', '')
    return url.replace('mysql://', 'mysql+pymysql://', 1) if url.startswith('mysql://') else url


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'development-only-change-me')
    SQLALCHEMY_DATABASE_URI = database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_recycle': 1800,
        'pool_pre_ping': True,
        'connect_args': {'connect_timeout': 10},
    }
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    EXPORT_SECRET = os.environ.get('EXPORT_SECRET', '')
    # Requested fixed credential for the local Mobile Hub admin dashboard.
    ADMIN_PASSWORD = 'SSSM@2013'
    RATELIMIT_DEFAULT = '240 per hour'
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
