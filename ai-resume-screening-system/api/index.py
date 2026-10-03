import os
import sys

# Add root directory to sys.path so app imports work seamlessly in Vercel Serverless
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User

# Instantiate WSGI Flask application
app = create_app(os.environ.get('FLASK_ENV', 'production'))

def init_db_if_needed():
    """Ensure database tables and initial admin accounts exist on cold start."""
    with app.app_context():
        try:
            db.create_all()
            if User.query.first() is None:
                admin = User(
                    
                    name="Alex Sterling (Admin)",
                    email="admin@resumescreen.ai",
                    role="admin"
                )
                admin.set_password("Admin@123")

                recruiter = User(
                    name="Sarah Jenkins (Lead Recruiter)",
                    email="recruiter@resumescreen.ai",
                    role="recruiter"
                )
                recruiter.set_password("Recruiter@123")

                db.session.add_all([admin, recruiter])
                db.session.commit()
        except Exception as e:
            app.logger.warning(f"Database auto-init notice: {e}")

try:
    init_db_if_needed()
except Exception:
    pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
