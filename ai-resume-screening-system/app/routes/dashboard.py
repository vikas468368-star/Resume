from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta
from app import db
from app.models import JobDescription, Resume, Screening, User

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """
    Main Recruiter / Admin Dashboard.
    Calculates live KPI metrics, top candidates, match distribution, and candidate submission trends.
    """
    # Scope queries based on user role
    if current_user.is_admin:
        job_query = JobDescription.query
        screening_query = Screening.query
        resume_query = Resume.query
    else:
        # Recruiter scopes to their own created jobs and associated screenings
        job_query = JobDescription.query.filter_by(created_by_user_id=current_user.id)
        user_job_ids = [j.id for j in job_query.all()]
        screening_query = Screening.query.filter(Screening.job_id.in_(user_job_ids)) if user_job_ids else Screening.query.filter_by(id=-1)
        resume_query = Resume.query.filter_by(uploaded_by_user_id=current_user.id)

    # 1. KPI Statistics
    total_jobs = job_query.count()
    total_resumes = resume_query.count() if not current_user.is_admin else Resume.query.count()
    total_screenings = screening_query.count()
    shortlisted_count = screening_query.filter_by(status='shortlisted').count()
    
    # Average Match and ATS Scores
    avg_match = db.session.query(func.avg(Screening.match_score)).filter(
        Screening.id.in_([s.id for s in screening_query.all()])
    ).scalar() if total_screenings > 0 else 0.0
    
    avg_ats = db.session.query(func.avg(Screening.ats_score)).filter(
        Screening.id.in_([s.id for s in screening_query.all()])
    ).scalar() if total_screenings > 0 else 0.0
    
    # 2. Top Candidates (sorted by combined score)
    top_screenings = screening_query.order_by(Screening.combined_score.desc()).limit(8).all()
    
    # 3. Active Jobs for Quick Screening Selector
    active_jobs = job_query.filter_by(status='active').order_by(JobDescription.created_at.desc()).all()

    stats = {
        'total_jobs': total_jobs,
        'total_resumes': total_resumes,
        'total_screenings': total_screenings,
        'shortlisted_count': shortlisted_count,
        'avg_match_score': round(float(avg_match or 0.0), 1),
        'avg_ats_score': round(float(avg_ats or 0.0), 1)
    }

    return render_template(
        'dashboard/index.html',
        stats=stats,
        top_screenings=top_screenings,
        active_jobs=active_jobs
    )


@dashboard_bp.route('/analytics')
@login_required
def analytics():
    """
    Dedicated Analytics View with comprehensive recruitment insights.
    """
    if current_user.is_admin:
        job_query = JobDescription.query
        screening_query = Screening.query
    else:
        job_query = JobDescription.query.filter_by(created_by_user_id=current_user.id)
        user_job_ids = [j.id for j in job_query.all()]
        screening_query = Screening.query.filter(Screening.job_id.in_(user_job_ids)) if user_job_ids else Screening.query.filter_by(id=-1)

    jobs = job_query.all()
    screenings = screening_query.all()
    
    # Aggregate stats per job
    job_metrics = []
    for job in jobs:
        j_screenings = [s for s in screenings if s.job_id == job.id]
        count = len(j_screenings)
        avg_match = sum(s.match_score for s in j_screenings) / count if count else 0.0
        avg_ats = sum(s.ats_score for s in j_screenings) / count if count else 0.0
        shortlisted = sum(1 for s in j_screenings if s.status == 'shortlisted')
        
        job_metrics.append({
            'job': job,
            'candidate_count': count,
            'avg_match': round(avg_match, 1),
            'avg_ats': round(avg_ats, 1),
            'shortlisted_count': shortlisted
        })

    return render_template(
        'dashboard/analytics.html',
        job_metrics=job_metrics,
        total_screenings=len(screenings)
    )


@dashboard_bp.route('/api/analytics/data')
@login_required
def analytics_data():
    """
    JSON API for Chart.js interactive charts:
    - Match Score Distribution (Donut Chart: 90-100%, 70-89%, 50-69%, <50%)
    - Candidate Submission Trend (Line Chart over past 7-30 days)
    - ATS vs Match Comparison (Bar Chart)
    """
    if current_user.is_admin:
        screening_query = Screening.query
        resume_query = Resume.query
    else:
        user_job_ids = [j.id for j in JobDescription.query.filter_by(created_by_user_id=current_user.id).all()]
        screening_query = Screening.query.filter(Screening.job_id.in_(user_job_ids)) if user_job_ids else Screening.query.filter_by(id=-1)
        resume_query = Resume.query.filter_by(uploaded_by_user_id=current_user.id)

    screenings = screening_query.all()
    
    # 1. Match Distribution Buckets
    tier_90_100 = sum(1 for s in screenings if s.match_score >= 90)
    tier_70_89 = sum(1 for s in screenings if 70 <= s.match_score < 90)
    tier_50_69 = sum(1 for s in screenings if 50 <= s.match_score < 70)
    tier_below_50 = sum(1 for s in screenings if s.match_score < 50)
    
    match_distribution = {
        'labels': ['90-100% (Exceptional)', '70-89% (Strong)', '50-69% (Moderate)', '<50% (Low Match)'],
        'data': [tier_90_100, tier_70_89, tier_50_69, tier_below_50],
        'colors': ['#10b981', '#3b82f6', '#f59e0b', '#ef4444']
    }
    
    # 2. Time-series Candidate Trend (Last 7 Days)
    today = datetime.utcnow().date()
    date_labels = []
    trend_counts = []
    
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        date_labels.append(day.strftime('%b %d'))
        
        # Count resumes uploaded on this day
        count = sum(1 for s in screenings if s.screened_at and s.screened_at.date() == day)
        trend_counts.append(count)
        
    candidate_trend = {
        'labels': date_labels,
        'data': trend_counts
    }
    
    # 3. Status Breakdown
    status_counts = {
        'New': sum(1 for s in screenings if s.status == 'new'),
        'Shortlisted': sum(1 for s in screenings if s.status == 'shortlisted'),
        'In Review': sum(1 for s in screenings if s.status == 'in_review'),
        'Rejected': sum(1 for s in screenings if s.status == 'rejected')
    }

    return jsonify({
        'match_distribution': match_distribution,
        'candidate_trend': candidate_trend,
        'status_counts': status_counts
    })
