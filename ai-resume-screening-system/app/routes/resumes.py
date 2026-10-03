import os
import uuid
import logging
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file, jsonify, abort
from flask_login import login_required, current_user
from app import db
from app.models import JobDescription, Resume, Screening
from app.services.ranking import process_and_screen_resume, rank_candidates_for_job

logger = logging.getLogger(__name__)
resumes_bp = Blueprint('resumes', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@resumes_bp.route('/screening', methods=['GET', 'POST'])
@login_required
def screening():
    """
    Main Resume Screening Interface.
    Allows recruiters to select a target Job Description and upload single or multiple resumes.
    Runs full text extraction, NLP parsing, Match Scoring, ATS scoring, and candidate ranking.
    """
    if current_user.is_admin:
        jobs = JobDescription.query.filter_by(status='active').order_by(JobDescription.created_at.desc()).all()
    else:
        jobs = JobDescription.query.filter_by(created_by_user_id=current_user.id, status='active').order_by(JobDescription.created_at.desc()).all()
        
    selected_job_id = request.args.get('job_id', type=int)
    if not selected_job_id and jobs:
        selected_job_id = jobs[0].id

    screened_results = []
    
    if request.method == 'POST':
        job_id = request.form.get('job_id', type=int)
        if not job_id:
            flash('Please select a target Job Description.', 'warning')
            return redirect(url_for('resumes.screening'))
            
        target_job = JobDescription.query.get_or_404(job_id)
        
        # Check permissions
        if not current_user.is_admin and target_job.created_by_user_id != current_user.id:
            flash('You do not have permission to screen candidates for this job.', 'danger')
            return abort(403)
            
        files = request.files.getlist('resumes')
        if not files or all(f.filename == '' for f in files):
            flash('Please select at least one resume file to upload (.pdf or .docx).', 'warning')
            return redirect(url_for('resumes.screening', job_id=job_id))
            
        success_count = 0
        error_count = 0
        
        for file in files:
            if file and file.filename != '':
                if not allowed_file(file.filename):
                    flash(f'File "{file.filename}" is not an allowed format (.pdf, .docx only).', 'danger')
                    error_count += 1
                    continue
                    
                orig_filename = secure_filename(file.filename)
                # Generate unique filename to avoid collision
                ext = orig_filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}_{orig_filename}"
                save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                
                try:
                    file.save(save_path)
                    
                    # Create Resume DB record
                    new_resume = Resume(
                        candidate_name=os.path.splitext(orig_filename)[0].replace('_', ' ').title(),
                        file_name=orig_filename,
                        file_path=save_path,
                        file_type=ext,
                        uploaded_by_user_id=current_user.id,
                        processing_status='pending'
                    )
                    db.session.add(new_resume)
                    db.session.flush() # get ID
                    
                    # Execute full screening pipeline
                    screening_record = process_and_screen_resume(new_resume, target_job, auto_commit=True)
                    screened_results.append(screening_record)
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing resume {orig_filename}: {e}")
                    db.session.rollback()
                    flash(f'Error processing "{orig_filename}": {str(e)}', 'danger')
                    error_count += 1
                    
        # Re-rank after batch
        if success_count > 0:
            rank_candidates_for_job(target_job.id)
            flash(f'Successfully screened and ranked {success_count} candidate(s)!', 'success')
            return redirect(url_for('jobs.detail', id=target_job.id))
            
    # If GET with selected job, fetch existing screenings for preview
    existing_screenings = []
    if selected_job_id:
        existing_screenings = Screening.query.filter_by(job_id=selected_job_id).order_by(Screening.rank.asc()).all()

    return render_template(
        'screening/index.html',
        jobs=jobs,
        selected_job_id=selected_job_id,
        existing_screenings=existing_screenings
    )


@resumes_bp.route('/resumes/<int:id>/download')
@login_required
def download_resume(id):
    """Safely streams uploaded resume document."""
    resume = Resume.query.get_or_404(id)
    
    if not os.path.exists(resume.file_path):
        flash('The original resume file could not be located on disk.', 'warning')
        return redirect(request.referrer or url_for('dashboard.index'))
        
    return send_file(
        resume.file_path,
        as_attachment=True,
        download_name=resume.file_name
    )
