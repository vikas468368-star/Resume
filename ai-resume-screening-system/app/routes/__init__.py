from functools import wraps
from flask import flash, redirect, url_for, abort, request
from flask_login import current_user

def admin_required(f):
    """Decorator to restrict access to admin users."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin privileges are required to access this resource.', 'danger')
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

def recruiter_or_admin_required(f):
    """Decorator ensuring user is logged in as recruiter or admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
