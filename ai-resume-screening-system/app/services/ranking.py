import logging
from typing import List, Dict, Any, Optional
from app import db
from app.models import Resume, JobDescription, Screening
from app.services.extractor import extract_resume_text
from app.services.nlp_processor import parse_resume_nlp
from app.services.job_processor import extract_key_terms
from app.services.scorer import calculate_match_score
from app.services.ats_scorer import calculate_ats_score

logger = logging.getLogger(__name__)

def calculate_combined_score(match_score: float, ats_score: float, match_weight: float = 0.70, ats_weight: float = 0.30) -> float:
    """
    Calculates final combined score:
    Combined = (Match Score * 0.70) + (ATS Score * 0.30)
    """
    combined = (match_score * match_weight) + (ats_score * ats_weight)
    return round(min(max(combined, 0.0), 100.0), 1)


def rank_candidates_for_job(job_id: int) -> List[Screening]:
    """
    Sorts all screenings for a given job descending by combined_score,
    assigns 1-indexed ranks (1, 2, 3...), updates database, and returns the sorted list.
    """
    screenings = Screening.query.filter_by(job_id=job_id).order_by(
        Screening.combined_score.desc(),
        Screening.match_score.desc(),
        Screening.ats_score.desc()
    ).all()
    
    for idx, screening in enumerate(screenings, start=1):
        screening.rank = idx
        
    db.session.commit()
    return screenings


def process_and_screen_resume(
    resume: Resume,
    job: JobDescription,
    auto_commit: bool = True
) -> Screening:
    """
    Full pipeline:
    1. Extract text from resume file if raw_text is missing.
    2. Run NLP parsing to extract candidate info, sections, and normalized skills.
    3. Update resume metadata and structured attributes.
    4. Compute multi-factor match score against Job Description.
    5. Compute explainable ATS score.
    6. Compute combined score.
    7. Save/update screening record and re-rank candidates for the job.
    """
    # 1. Text Extraction
    if not resume.raw_text or len(resume.raw_text.strip()) < 10:
        try:
            resume.raw_text = extract_resume_text(resume.file_path)
            resume.processing_status = 'processed'
        except Exception as e:
            logger.error(f"Extraction error for resume {resume.id}: {e}")
            resume.processing_status = 'failed'
            resume.error_message = str(e)
            if auto_commit:
                db.session.commit()
            raise ValueError(f"Failed to extract text from resume: {e}")

    # 2. NLP Parsing
    nlp_data = parse_resume_nlp(resume.raw_text)
    
    # Update candidate fields if newly discovered
    if nlp_data.get("name") and nlp_data["name"] != "Unknown Candidate":
        resume.candidate_name = nlp_data["name"]
    if nlp_data.get("email"):
        resume.email = nlp_data["email"]
    if nlp_data.get("phone"):
        resume.phone = nlp_data["phone"]
    if nlp_data.get("location"):
        resume.location = nlp_data["location"]
        
    resume.extracted_skills = nlp_data.get("skills", [])
    resume.education = nlp_data.get("education", [])
    resume.experience = nlp_data.get("experience", [])
    resume.projects = nlp_data.get("projects", [])
    resume.certifications = nlp_data.get("certifications", [])
    resume.experience_years = nlp_data.get("experience_years", 0.0)
    resume.processing_status = 'processed'
    
    # 3. Match Scoring
    req_skills = job.required_skills or []
    pref_skills = job.preferred_skills or []
    
    match_result = calculate_match_score(
        resume_text=resume.raw_text,
        jd_text=job.description_text,
        candidate_skills=resume.extracted_skills,
        required_skills=req_skills,
        preferred_skills=pref_skills,
        candidate_exp_years=resume.experience_years,
        required_min_years=job.min_experience_years,
        candidate_education=resume.education,
        required_education=job.min_education or "Bachelor"
    )
    
    # 4. ATS Scoring
    key_terms = extract_key_terms(job.description_text)
    ats_result = calculate_ats_score(
        resume_text=resume.raw_text,
        parsed_resume=nlp_data,
        job_description=job.description_text,
        required_skills=req_skills,
        key_terms=key_terms
    )
    
    # 5. Combined Score
    comb_score = calculate_combined_score(
        match_result["match_score"],
        ats_result["ats_score"]
    )
    
    # 6. Combined Explanation synthesis
    explanation_data = {
        "match_score": match_result["match_score"],
        "ats_score": ats_result["ats_score"],
        "combined_score": comb_score,
        "strengths": ats_result["explanation"]["strengths"],
        "warnings": ats_result["explanation"]["warnings"],
        "text_similarity": match_result["text_similarity"],
        "skill_match_score": match_result["skill_match_score"],
        "experience_match_score": match_result["experience_match_score"],
        "education_match_score": match_result["education_match_score"],
        "matched_skills": match_result["matched_skills"],
        "missing_skills": match_result["missing_skills"]
    }
    
    # 7. Create or update Screening record
    screening = Screening.query.filter_by(resume_id=resume.id, job_id=job.id).first()
    if not screening:
        screening = Screening(resume_id=resume.id, job_id=job.id)
        db.session.add(screening)
        
    screening.match_score = match_result["match_score"]
    screening.text_similarity = match_result["text_similarity"]
    screening.skill_match_score = match_result["skill_match_score"]
    screening.experience_match_score = match_result["experience_match_score"]
    screening.education_match_score = match_result["education_match_score"]
    screening.ats_score = ats_result["ats_score"]
    screening.ats_breakdown = ats_result["ats_breakdown"]
    screening.combined_score = comb_score
    screening.matched_skills = match_result["matched_skills"]
    screening.missing_skills = match_result["missing_skills"]
    screening.explanation = explanation_data
    screening.status = 'new'
    
    if auto_commit:
        db.session.commit()
        # 8. Re-rank all candidates for this job
        rank_candidates_for_job(job.id)
        
    return screening
