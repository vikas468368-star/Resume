import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import or_
from app import db
from app.models import JobDescription, Resume, Screening
from app.services.ranking import process_and_screen_resume, rank_candidates_for_job

candidates_bp = Blueprint('candidates', __name__)

@candidates_bp.route('/')
@login_required
def index():
    """
    Candidates List view with Search, Multi-criteria Filtering, Sorting, and Pagination.
    """
    # 1. Base query scoped by role
    if current_user.is_admin:
        query = Screening.query.join(Resume).join(JobDescription)
        jobs = JobDescription.query.all()
    else:
        user_job_ids = [j.id for j in JobDescription.query.filter_by(created_by_user_id=current_user.id).all()]
        if not user_job_ids:
            return render_template('candidates/list.html', screenings=[], jobs=[], pagination=None)
        query = Screening.query.join(Resume).join(JobDescription).filter(Screening.job_id.in_(user_job_ids))
        jobs = JobDescription.query.filter(JobDescription.id.in_(user_job_ids)).all()

    # 2. Search query filter
    search = request.args.get('q', '').strip()
    if search:
        query = query.filter(
            or_(
                Resume.candidate_name.ilike(f'%{search}%'),
                Resume.email.ilike(f'%{search}%'),
                Resume.location.ilike(f'%{search}%'),
                JobDescription.title.ilike(f'%{search}%')
            )
        )
        
    # 3. Filter by Job
    job_id = request.args.get('job_id', type=int)
    if job_id:
        query = query.filter(Screening.job_id == job_id)
        
    # 4. Filter by Status
    status = request.args.get('status', '').strip()
    if status and status != 'all':
        query = query.filter(Screening.status == status)
        
    # 5. Filter by Score Range
    score_tier = request.args.get('score_tier', '')
    if score_tier == '90':
        query = query.filter(Screening.match_score >= 90)
    elif score_tier == '70':
        query = query.filter(Screening.match_score >= 70, Screening.match_score < 90)
    elif score_tier == '50':
        query = query.filter(Screening.match_score >= 50, Screening.match_score < 70)
    elif score_tier == 'below50':
        query = query.filter(Screening.match_score < 50)
        
    # 6. Sorting
    sort_by = request.args.get('sort', 'combined_score')
    if sort_by == 'match_score':
        query = query.order_by(Screening.match_score.desc())
    elif sort_by == 'ats_score':
        query = query.order_by(Screening.ats_score.desc())
    elif sort_by == 'name':
        query = query.order_by(Resume.candidate_name.asc())
    elif sort_by == 'date':
        query = query.order_by(Screening.screened_at.desc())
    else: # default combined_score
        query = query.order_by(Screening.combined_score.desc())

    # 7. Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    screenings = pagination.items

    return render_template(
        'candidates/list.html',
        screenings=screenings,
        pagination=pagination,
        jobs=jobs,
        selected_job_id=job_id,
        selected_status=status,
        selected_tier=score_tier,
        search_query=search,
        sort_by=sort_by
    )


@candidates_bp.route('/<int:id>')
@login_required
def detail(id):
    """
    Detailed Candidate Profile with Explainable ATS & Match Score Breakdown.
    """
    screening = Screening.query.get_or_404(id)
    
    # Permission verification
    if not current_user.is_admin and screening.job.created_by_user_id != current_user.id:
        flash('You do not have permission to view this candidate profile.', 'danger')
        return abort(403)
        
    resume = screening.resume
    job = screening.job

    return render_template(
        'candidates/detail.html',
        screening=screening,
        resume=resume,
        job=job
    )


@candidates_bp.route('/<int:id>/status', methods=['POST'])
@login_required
def update_status(id):
    """
    Updates the candidate screening status (shortlisted, rejected, in_review, new).
    """
    screening = Screening.query.get_or_404(id)
    
    if not current_user.is_admin and screening.job.created_by_user_id != current_user.id:
        flash('Permission denied.', 'danger')
        return abort(403)
        
    new_status = request.form.get('status', '').strip().lower()
    if new_status in ['shortlisted', 'rejected', 'in_review', 'new']:
        screening.status = new_status
        db.session.commit()
        flash(f'Candidate status updated to "{new_status.replace("_", " ").title()}".', 'success')
        
    return redirect(request.referrer or url_for('candidates.detail', id=screening.id))


@candidates_bp.route('/<int:id>/rescreen', methods=['POST'])
@login_required
def rescreen(id):
    """
    Re-runs the NLP & Match/ATS scoring engine for this candidate against the job description.
    """
    screening = Screening.query.get_or_404(id)
    
    if not current_user.is_admin and screening.job.created_by_user_id != current_user.id:
        flash('Permission denied.', 'danger')
        return abort(403)
        
    try:
        updated_screening = process_and_screen_resume(screening.resume, screening.job, auto_commit=True)
        flash('Candidate successfully re-screened with the latest scoring algorithms!', 'success')
    except Exception as e:
        flash(f'Re-screening failed: {str(e)}', 'danger')
        
    return redirect(url_for('candidates.detail', id=screening.id))


@candidates_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """
    Deletes the screening and associated resume.
    """
    screening = Screening.query.get_or_404(id)
    
    if not current_user.is_admin and screening.job.created_by_user_id != current_user.id:
        flash('Permission denied.', 'danger')
        return abort(403)
        
    job_id = screening.job_id
    resume = screening.resume
    
    # Remove file from disk if exists
    if resume and os.path.exists(resume.file_path):
        try:
            os.remove(resume.file_path)
        except Exception:
            pass
            
    db.session.delete(screening)
    if resume:
        db.session.delete(resume)
    db.session.commit()
    
    rank_candidates_for_job(job_id)
    flash('Candidate record removed successfully.', 'info')
    return redirect(url_for('candidates.index'))
