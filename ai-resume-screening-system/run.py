import os
from app import create_app, db
from app.models import User, JobDescription, Resume, Screening

app = create_app(os.environ.get('FLASK_ENV', 'development'))

with app.app_context():
    db.create_all()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'JobDescription': JobDescription,
        'Resume': Resume,
        'Screening': Screening
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f" * Server running on http://127.0.0.1:{port}")
    print(f" * Access in your browser: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
