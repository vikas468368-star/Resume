import re
import numpy as np
from typing import Dict, List, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Degree hierarchy levels for qualification scoring
DEGREE_LEVELS = {
    'ph.d.': 5,
    'doctorate': 5,
    "master's degree": 4,
    'master': 4,
    "bachelor's degree": 3,
    'bachelor': 3,
    'associate / diploma': 2,
    'diploma': 2,
    'associate': 2,
    'high school': 1
}

def compute_tfidf_similarity(resume_text: str, jd_text: str) -> float:
    """
    Computes cosine similarity between resume text and job description using TF-IDF.
    Returns a score between 0.0 and 100.0.
    """
    if not resume_text or not jd_text:
        return 0.0
        
    try:
        # Preprocessing: lowercase and clean
        cleaned_resume = resume_text.lower()
        cleaned_jd = jd_text.lower()
        
        vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=1
        )
        
        tfidf_matrix = vectorizer.fit_transform([cleaned_resume, cleaned_jd])
        sim_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        
        raw_similarity = float(sim_matrix[0][0])
        # Scale to 0-100 with smooth normalization
        scaled_score = min(max(raw_similarity * 100.0, 0.0), 100.0)
        return round(scaled_score, 1)
    except Exception as e:
        return 0.0


def compute_skill_overlap(candidate_skills: List[str], required_skills: List[str], preferred_skills: List[str] = None) -> Tuple[float, List[str], List[str]]:
    """
    Calculates skill match percentage, matched skills, and missing skills.
    Required skills carry 80% weight, Preferred skills carry 20% weight.
    """
    cand_set = set(s.lower() for s in candidate_skills)
    req_set = set(s.lower() for s in (required_skills or []))
    pref_set = set(s.lower() for s in (preferred_skills or []))
    
    if not req_set and not pref_set:
        return 100.0, candidate_skills, []
        
    # Find matched and missing in required
    matched_req = [s for s in (required_skills or []) if s.lower() in cand_set]
    missing_req = [s for s in (required_skills or []) if s.lower() not in cand_set]
    
    matched_pref = [s for s in (preferred_skills or []) if s.lower() in cand_set]
    missing_pref = [s for s in (preferred_skills or []) if s.lower() not in cand_set]
    
    req_score = (len(matched_req) / len(req_set) * 100.0) if req_set else 100.0
    pref_score = (len(matched_pref) / len(pref_set) * 100.0) if pref_set else 100.0
    
    if req_set and pref_set:
        final_skill_score = 0.80 * req_score + 0.20 * pref_score
    elif req_set:
        final_skill_score = req_score
    else:
        final_skill_score = pref_score
        
    matched_all = matched_req + [s for s in matched_pref if s not in matched_req]
    missing_all = missing_req + [s for s in missing_pref if s not in missing_req]
    
    return round(final_skill_score, 1), matched_all, missing_all


def compute_experience_score(candidate_exp_years: float, required_min_years: float) -> float:
    """
    Scores experience match from 0 to 100 based on candidate years vs JD requirement.
    """
    if required_min_years <= 0.0:
        return 100.0
        
    ratio = candidate_exp_years / required_min_years
    if ratio >= 1.0:
        # Full score plus minor boost for seniority up to 100
        return 100.0
    else:
        # Pro-rated score (e.g. 3 yrs for 4 yrs req = 75%)
        return round(ratio * 100.0, 1)


def compute_education_score(candidate_education: List[Dict[str, str]], required_education: str) -> float:
    """
    Scores education relevance based on candidate's highest degree vs minimum JD requirement.
    """
    req_level = DEGREE_LEVELS.get(required_education.lower().strip(), 3) # default Bachelor = 3
    
    cand_level = 0
    for edu in (candidate_education or []):
        deg = edu.get('degree', '').lower().strip()
        lvl = DEGREE_LEVELS.get(deg, 0)
        if lvl > cand_level:
            cand_level = lvl
            
    if cand_level == 0:
        cand_level = 2 # Assume standard diploma/experience if unspecified
        
    if cand_level >= req_level:
        return 100.0
    elif cand_level == req_level - 1:
        return 75.0
    elif cand_level == req_level - 2:
        return 50.0
    else:
        return 30.0


def calculate_match_score(
    resume_text: str,
    jd_text: str,
    candidate_skills: List[str],
    required_skills: List[str],
    preferred_skills: List[str] = None,
    candidate_exp_years: float = 0.0,
    required_min_years: float = 0.0,
    candidate_education: List[Dict[str, str]] = None,
    required_education: str = "Bachelor"
) -> Dict[str, Any]:
    """
    Calculates multi-factor Match Score:
    - Text Similarity: 40%
    - Skill Match: 35%
    - Experience Match: 15%
    - Education Match: 10%
    """
    # 1. Text similarity
    text_sim = compute_tfidf_similarity(resume_text, jd_text)
    
    # 2. Skill match
    skill_score, matched_skills, missing_skills = compute_skill_overlap(
        candidate_skills, required_skills, preferred_skills
    )
    
    # 3. Experience match
    exp_score = compute_experience_score(candidate_exp_years, required_min_years)
    
    # 4. Education match
    edu_score = compute_education_score(candidate_education, required_education)
    
    # Combined weighted Match Score
    final_match_score = (
        0.40 * text_sim +
        0.35 * skill_score +
        0.15 * exp_score +
        0.10 * edu_score
    )
    
    return {
        "match_score": round(final_match_score, 1),
        "text_similarity": text_sim,
        "skill_match_score": skill_score,
        "experience_match_score": exp_score,
        "education_match_score": edu_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills
    }
