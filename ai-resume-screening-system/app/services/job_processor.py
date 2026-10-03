import re
from typing import Dict, List, Any
from app.services.nlp_processor import extract_skills

def extract_jd_skills(description_text: str) -> Dict[str, List[str]]:
    """
    Extracts required and preferred skills from a job description.
    Differentiates based on sections like 'Requirements' vs 'Nice to have' / 'Preferred'.
    """
    if not description_text:
        return {"required": [], "preferred": []}
        
    lines = description_text.split('\n')
    required_text = []
    preferred_text = []
    current_mode = "required"
    
    for line in lines:
        lower = line.strip().lower()
        if any(h in lower for h in ['preferred', 'nice to have', 'bonus', 'plus', 'good to have', 'desired']):
            current_mode = "preferred"
        elif any(h in lower for h in ['required', 'requirements', 'must have', 'qualifications', 'what you will bring', 'minimum qualifications']):
            current_mode = "required"
            
        if current_mode == "preferred":
            preferred_text.append(line)
        else:
            required_text.append(line)
            
    all_skills = extract_skills(description_text)
    pref_skills = extract_skills("\n".join(preferred_text)) if preferred_text else []
    
    # If explicit preferred section found, separate; otherwise default all to required
    req_skills = [s for s in all_skills if s not in pref_skills]
    if not req_skills and all_skills:
        req_skills = all_skills
        pref_skills = []
        
    return {
        "required": req_skills,
        "preferred": pref_skills
    }


def extract_min_experience_years(text: str) -> float:
    """Extracts minimum years of experience required from JD text."""
    if not text:
        return 0.0
        
    patterns = [
        r'(\d+(?:\.\d+)?)\s*\+?\s*(?:-\s*\d+\s*)?(?:years|yrs)(?:\s+of)?\s+(?:relevant\s+)?experience',
        r'minimum\s+(?:of\s+)?(\d+)\s*(?:years|yrs)',
        r'at\s+least\s+(\d+)\s*(?:years|yrs)'
    ]
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
    return 0.0


def extract_min_education(text: str) -> str:
    """Extracts minimum education degree requirement from JD text."""
    if not text:
        return "Bachelor"
        
    if re.search(r'\b(Ph\.?D\.?|Doctorate)\b', text, re.IGNORECASE):
        return "Ph.D."
    elif re.search(r'\b(Master\'?s?|M\.?S\.?|M\.?Tech\.?|M\.?B\.?A\.?)\b', text, re.IGNORECASE):
        return "Master"
    elif re.search(r'\b(Bachelor\'?s?|B\.?S\.?|B\.?Tech\.?|B\.?E\.?|Degree)\b', text, re.IGNORECASE):
        return "Bachelor"
    elif re.search(r'\b(Associate|Diploma)\b', text, re.IGNORECASE):
        return "Associate / Diploma"
    return "Bachelor"


def extract_key_terms(text: str, top_n: int = 15) -> List[str]:
    """Extracts high-value domain keywords from the job description for ATS checking."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    
    if not text or len(text.split()) < 5:
        return []
        
    try:
        vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=top_n
        )
        vectorizer.fit([text])
        feature_names = vectorizer.get_feature_names_out()
        return list(feature_names)
    except Exception:
        # Fallback to simple words
        words = re.findall(r'\b[A-Za-z]{4,20}\b', text.lower())
        stopwords = {'with', 'have', 'from', 'this', 'that', 'your', 'will', 'about', 'must', 'work', 'team'}
        filtered = [w for w in words if w not in stopwords]
        return list(set(filtered))[:top_n]


def parse_job_description(title: str, description_text: str) -> Dict[str, Any]:
    """
    Parses and structures a job description.
    """
    skills_dict = extract_jd_skills(description_text)
    min_exp = extract_min_experience_years(description_text)
    min_edu = extract_min_education(description_text)
    key_terms = extract_key_terms(description_text)
    
    return {
        "required_skills": skills_dict["required"],
        "preferred_skills": skills_dict["preferred"],
        "min_experience_years": min_exp,
        "min_education": min_edu,
        "key_terms": key_terms
    }
