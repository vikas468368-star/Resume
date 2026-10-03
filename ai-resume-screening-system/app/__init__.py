import os
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
        
    app = Flask(__name__)
    app_config = config.get(config_name, config['default'])
    app.config.from_object(app_config)
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Login settings
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'
    
    # Register custom Jinja template filters
    @app.template_filter('score_badge_class')
    def score_badge_class(score):
        try:
            val = float(score)
            if val >= 85:
                return 'badge-success'
            elif val >= 70:
                return 'badge-info'
            elif val >= 50:
                return 'badge-warning'
            else:
                return 'badge-danger'
        except (ValueError, TypeError):
            return 'badge-secondary'
            
    @app.template_filter('score_color')
    def score_color(score):
        try:
            val = float(score)
            if val >= 85:
                return '#10b981' # emerald green
            elif val >= 70:
                return '#3b82f6' # royal blue
            elif val >= 50:
                return '#f59e0b' # amber
            else:
                return '#ef4444' # rose red
        except (ValueError, TypeError):
            return '#6b7280'
            
    @app.template_filter('status_badge_class')
    def status_badge_class(status):
        status_map = {
            'shortlisted': 'badge-success',
            'in_review': 'badge-warning',
            'rejected': 'badge-danger',
            'new': 'badge-info',
            'active': 'badge-success',
            'closed': 'badge-secondary',
            'processed': 'badge-success',
            'pending': 'badge-warning',
            'failed': 'badge-danger'
        }
        return status_map.get(str(status).lower(), 'badge-secondary')
        
    @app.template_filter('format_datetime')
    def format_datetime(dt, fmt='%b %d, %Y'):
        if not dt:
            return 'N/A'
        return dt.strftime(fmt)

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.jobs import jobs_bp
    from app.routes.resumes import resumes_bp
    from app.routes.candidates import candidates_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(jobs_bp, url_prefix='/jobs')
    app.register_blueprint(resumes_bp)
    app.register_blueprint(candidates_bp, url_prefix='/candidates')
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Bad request', 'message': str(e)}), 400
        return render_template('errors/400.html', error=e), 400

    @app.errorhandler(403)
    def forbidden(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Forbidden', 'message': 'You do not have permission to perform this action.'}), 403
        return render_template('errors/403.html', error=e), 403

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Not found', 'message': 'The requested resource was not found.'}), 404
        return render_template('errors/404.html', error=e), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'File too large', 'message': 'Maximum allowed file size is 16MB.'}), 413
        return render_template('errors/413.html', error=e), 413

    @app.errorhandler(500)
    def internal_server_error(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred.'}), 500
        return render_template('errors/500.html', error=e), 500

    return app
