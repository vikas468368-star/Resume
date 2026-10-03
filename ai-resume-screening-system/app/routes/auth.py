from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        
        if not email or not password:
            flash('Please enter both email and password.', 'warning')
            return render_template('auth/login.html')
            
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.name}!', 'success')
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid email or password. Please check your credentials.', 'danger')
            
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'recruiter').strip().lower()
        
        if role not in ['admin', 'recruiter']:
            role = 'recruiter'
            
        # Validation checks
        if not name or not email or not password:
            flash('All fields are required.', 'warning')
            return render_template('auth/register.html')
            
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'warning')
            return render_template('auth/register.html')
            
        if password != confirm_password:
            flash('Passwords do not match.', 'warning')
            return render_template('auth/register.html')
            
        # Check duplicate email
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email address already exists. Please log in.', 'danger')
            return render_template('auth/register.html')
            
        # Create user
        new_user = User(name=name, email=email, role=role)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
