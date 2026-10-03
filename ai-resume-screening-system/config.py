import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-super-secret-key-ai-resume-screening-2026'
    
    is_vercel = bool(os.environ.get('VERCEL'))
    default_db = '/tmp/app.db' if is_vercel else os.path.join(basedir, 'app.db')
    
    # Database config: defaults to SQLite for instant local dev, easily overridden by PostgreSQL DATABASE_URL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or ('sqlite:///' + default_db)
    
    # Handle postgres:// vs postgresql:// compatibility
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload configurations
    UPLOAD_FOLDER = os.path.join('/tmp', 'uploads') if is_vercel else os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)) # 16 MB max
    ALLOWED_EXTENSIONS = {'pdf', 'docx'}
    
    # Session security
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Pagination
    ITEMS_PER_PAGE = 10
    
    # NLP / Matching weights
    SIMILARITY_WEIGHT = 0.40
    SKILL_WEIGHT = 0.35
    EXPERIENCE_WEIGHT = 0.15
    EDUCATION_WEIGHT = 0.10
    
    # Candidate ranking combined weight
    MATCH_SCORE_WEIGHT = 0.70
    ATS_SCORE_WEIGHT = 0.30

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = os.path.join(basedir, 'tests', 'test_uploads')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
