from datetime import datetime
import json
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='recruiter') # 'admin' or 'recruiter'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    jobs = db.relationship('JobDescription', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    resumes = db.relationship('Resume', backref='uploader', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_recruiter(self):
        return self.role == 'recruiter'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class JobDescription(db.Model):
    __tablename__ = 'job_descriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(100), default='Engineering')
    location = db.Column(db.String(100), default='Remote')
    experience_level = db.Column(db.String(50), default='Mid-Senior')
    min_experience_years = db.Column(db.Float, default=0.0)
    min_education = db.Column(db.String(100), default='Bachelor')
    description_text = db.Column(db.Text, nullable=False)
    
    # JSON arrays of strings
    required_skills = db.Column(db.JSON, default=list)
    preferred_skills = db.Column(db.JSON, default=list)
    
    status = db.Column(db.String(20), default='active') # 'active', 'closed', 'draft'
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    screenings = db.relationship('Screening', backref='job', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def candidate_count(self):
        return self.screenings.count()
    
    @property
    def top_candidate(self):
        return self.screenings.order_by(Screening.combined_score.desc()).first()
    
    @property
    def average_match_score(self):
        all_screenings = self.screenings.all()
        if not all_screenings:
            return 0.0
        return round(sum(s.match_score for s in all_screenings) / len(all_screenings), 1)

    @property
    def average_ats_score(self):
        all_screenings = self.screenings.all()
        if not all_screenings:
            return 0.0
        return round(sum(s.ats_score for s in all_screenings) / len(all_screenings), 1)

    @property
    def shortlisted_count(self):
        return self.screenings.filter_by(status='shortlisted').count()

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'department': self.department,
            'location': self.location,
            'experience_level': self.experience_level,
            'min_experience_years': self.min_experience_years,
            'min_education': self.min_education,
            'description_text': self.description_text,
            'required_skills': self.required_skills or [],
            'preferred_skills': self.preferred_skills or [],
            'status': self.status,
            'created_by_user_id': self.created_by_user_id,
            'candidate_count': self.candidate_count,
            'average_match_score': self.average_match_score,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }

    def __repr__(self):
        return f"<JobDescription {self.title}>"


class Resume(db.Model):
    __tablename__ = 'resumes'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_name = db.Column(db.String(150), default='Unknown Candidate')
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(10), default='pdf')
    raw_text = db.Column(db.Text, nullable=True)
    
    # Structured NLP extractions
    extracted_skills = db.Column(db.JSON, default=list)
    education = db.Column(db.JSON, default=list)
    experience = db.Column(db.JSON, default=list)
    projects = db.Column(db.JSON, default=list)
    certifications = db.Column(db.JSON, default=list)
    experience_years = db.Column(db.Float, default=0.0)
    
    processing_status = db.Column(db.String(20), default='pending') # 'pending', 'processed', 'failed'
    error_message = db.Column(db.Text, nullable=True)
    
    uploaded_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    screenings = db.relationship('Screening', backref='resume', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'candidate_name': self.candidate_name,
            'email': self.email,
            'phone': self.phone,
            'location': self.location,
            'file_name': self.file_name,
            'file_type': self.file_type,
            'extracted_skills': self.extracted_skills or [],
            'education': self.education or [],
            'experience': self.experience or [],
            'projects': self.projects or [],
            'certifications': self.certifications or [],
            'experience_years': self.experience_years,
            'processing_status': self.processing_status,
            'uploaded_at': self.uploaded_at.strftime('%Y-%m-%d %H:%M') if self.uploaded_at else None
        }

    def __repr__(self):
        return f"<Resume {self.candidate_name} ({self.file_name})>"


class Screening(db.Model):
    __tablename__ = 'screenings'
    
    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job_descriptions.id', ondelete='CASCADE'), nullable=False)
    
    # Matching Scores (0-100)
    match_score = db.Column(db.Float, default=0.0)
    text_similarity = db.Column(db.Float, default=0.0)
    skill_match_score = db.Column(db.Float, default=0.0)
    experience_match_score = db.Column(db.Float, default=0.0)
    education_match_score = db.Column(db.Float, default=0.0)
    
    # ATS Score & Breakdown (0-100)
    ats_score = db.Column(db.Float, default=0.0)
    ats_breakdown = db.Column(db.JSON, default=dict)
    
    # Combined final ranking score
    combined_score = db.Column(db.Float, default=0.0)
    rank = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='new') # 'new', 'shortlisted', 'rejected', 'in_review'
    
    # Skills alignment
    matched_skills = db.Column(db.JSON, default=list)
    missing_skills = db.Column(db.JSON, default=list)
    
    # Explainable AI checklist & feedback
    explanation = db.Column(db.JSON, default=dict)
    
    screened_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'resume_id': self.resume_id,
            'job_id': self.job_id,
            'match_score': round(self.match_score, 1),
            'text_similarity': round(self.text_similarity, 1),
            'skill_match_score': round(self.skill_match_score, 1),
            'experience_match_score': round(self.experience_match_score, 1),
            'education_match_score': round(self.education_match_score, 1),
            'ats_score': round(self.ats_score, 1),
            'ats_breakdown': self.ats_breakdown or {},
            'combined_score': round(self.combined_score, 1),
            'rank': self.rank,
            'status': self.status,
            'matched_skills': self.matched_skills or [],
            'missing_skills': self.missing_skills or [],
            'explanation': self.explanation or {},
            'screened_at': self.screened_at.strftime('%Y-%m-%d %H:%M') if self.screened_at else None,
            'candidate_name': self.resume.candidate_name if self.resume else 'N/A',
            'job_title': self.job.title if self.job else 'N/A'
        }

    def __repr__(self):
        return f"<Screening Resume {self.resume_id} -> Job {self.job_id}: {self.combined_score}% (Rank {self.rank})>"
