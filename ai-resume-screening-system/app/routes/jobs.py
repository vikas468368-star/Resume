from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app import db
from app.models import JobDescription, Screening
from app.services.job_processor import parse_job_description, extract_jd_skills
from app.services.ranking import rank_candidates_for_job

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('/')
@login_required
def index():
    """List of all available Job Descriptions."""
    if current_user.is_admin:
        jobs = JobDescription.query.order_by(JobDescription.created_at.desc()).all()
    else:
        jobs = JobDescription.query.filter_by(created_by_user_id=current_user.id).order_by(JobDescription.created_at.desc()).all()
        
    return render_template('jobs/list.html', jobs=jobs)


@jobs_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new Job Description with automated skill parsing."""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        department = request.form.get('department', 'Engineering').strip()
        location = request.form.get('location', 'Remote').strip()
        experience_level = request.form.get('experience_level', 'Mid-Senior').strip()
        min_experience_years = float(request.form.get('min_experience_years') or 0.0)
        min_education = request.form.get('min_education', 'Bachelor').strip()
        description_text = request.form.get('description_text', '').strip()
        
        # Skills can be provided as comma-separated or parsed automatically
        req_skills_raw = request.form.get('required_skills', '').strip()
        pref_skills_raw = request.form.get('preferred_skills', '').strip()
        
        if not title or not description_text:
            flash('Job Title and Job Description text are required.', 'warning')
            return render_template('jobs/create.html')
            
        # Parse auto-skills if user didn't specify manually
        parsed_jd = parse_job_description(title, description_text)
        
        if req_skills_raw:
            required_skills = [s.strip() for s in req_skills_raw.split(',') if s.strip()]
        else:
            required_skills = parsed_jd['required_skills']
            
        if pref_skills_raw:
            preferred_skills = [s.strip() for s in pref_skills_raw.split(',') if s.strip()]
        else:
            preferred_skills = parsed_jd['preferred_skills']
            
        if min_experience_years == 0.0 and parsed_jd['min_experience_years'] > 0:
            min_experience_years = parsed_jd['min_experience_years']
            
        new_job = JobDescription(
            title=title,
            department=department,
            location=location,
            experience_level=experience_level,
            min_experience_years=min_experience_years,
            min_education=min_education,
            description_text=description_text,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            created_by_user_id=current_user.id
        )
        
        db.session.add(new_job)
        db.session.commit()
        
        flash(f'Job "{title}" created successfully with {len(required_skills)} required skills identified.', 'success')
        return redirect(url_for('jobs.detail', id=new_job.id))
        
    return render_template('jobs/create.html')


@jobs_bp.route('/<int:id>')
@login_required
def detail(id):
    """View job details, required skills, and all ranked candidates."""
    job = JobDescription.query.get_or_404(id)
    
    # Recruiter permission check
    if not current_user.is_admin and job.created_by_user_id != current_user.id:
        flash('You do not have permission to view this job posting.', 'danger')
        return abort(403)
        
    # Get all screenings ranked for this job
    screenings = Screening.query.filter_by(job_id=job.id).order_by(
        Screening.rank.asc(),
        Screening.combined_score.desc()
    ).all()
    
    return render_template('jobs/detail.html', job=job, screenings=screenings)


@jobs_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit existing Job Description."""
    job = JobDescription.query.get_or_404(id)
    
    # Permission check
    if not current_user.is_admin and job.created_by_user_id != current_user.id:
        flash('You can only edit your own job postings.', 'danger')
        return abort(403)
        
    if request.method == 'POST':
        job.title = request.form.get('title', job.title).strip()
        job.department = request.form.get('department', job.department).strip()
        job.location = request.form.get('location', job.location).strip()
        job.experience_level = request.form.get('experience_level', job.experience_level).strip()
        job.min_experience_years = float(request.form.get('min_experience_years') or 0.0)
        job.min_education = request.form.get('min_education', job.min_education).strip()
        job.description_text = request.form.get('description_text', job.description_text).strip()
        job.status = request.form.get('status', job.status)
        
        req_skills_raw = request.form.get('required_skills', '')
        pref_skills_raw = request.form.get('preferred_skills', '')
        
        job.required_skills = [s.strip() for s in req_skills_raw.split(',') if s.strip()]
        job.preferred_skills = [s.strip() for s in pref_skills_raw.split(',') if s.strip()]
        
        db.session.commit()
        flash('Job updated successfully.', 'success')
        return redirect(url_for('jobs.detail', id=job.id))
        
    return render_template('jobs/edit.html', job=job)


@jobs_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete Job Description and cascade screenings."""
    job = JobDescription.query.get_or_404(id)
    
    # Permission check
    if not current_user.is_admin and job.created_by_user_id != current_user.id:
        flash('You can only delete your own job postings.', 'danger')
        return abort(403)
        
    job_title = job.title
    db.session.delete(job)
    db.session.commit()
    
    flash(f'Job "{job_title}" and associated candidate screenings have been deleted.', 'info')
    return redirect(url_for('jobs.index'))


@jobs_bp.route('/api/extract-skills', methods=['POST'])
@login_required
def api_extract_skills():
    """AJAX endpoint for instant skill discovery while drafting JD."""
    data = request.get_json() or {}
    text = data.get('text', '')
    parsed = extract_jd_skills(text)
    return jsonify(parsed)
