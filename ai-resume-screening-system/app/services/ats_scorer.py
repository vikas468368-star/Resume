import re
from typing import Dict, List, Any

def calculate_ats_score(
    resume_text: str,
    parsed_resume: Dict[str, Any],
    job_description: str,
    required_skills: List[str],
    key_terms: List[str] = None
) -> Dict[str, Any]:
    """
    Calculates explainable ATS score (0-100) across 5 standard recruiting benchmarks:
    - Contact Information (15 pts)
    - Section Completeness (25 pts)
    - Keyword Relevance (25 pts)
    - Skill Relevance (25 pts)
    - Formatting Quality (10 pts)
    """
    breakdown = {
        "contact_info": 0.0,
        "section_completeness": 0.0,
        "keyword_relevance": 0.0,
        "skill_relevance": 0.0,
        "formatting_quality": 0.0
    }
    
    strengths = []
    warnings = []
    
    # 1. Contact Information Completeness (15 pts max)
    email = parsed_resume.get("email")
    phone = parsed_resume.get("phone")
    location = parsed_resume.get("location")
    
    contact_pts = 0.0
    if email:
        contact_pts += 5.0
        strengths.append("Professional email address detected.")
    else:
        warnings.append("Missing or unreadable email address.")
        
    if phone:
        contact_pts += 5.0
        strengths.append("Phone number properly formatted.")
    else:
        warnings.append("Missing or unreadable contact phone number.")
        
    if location and "Not Specified" not in location:
        contact_pts += 5.0
        strengths.append(f"Geographic location identified ({location}).")
    elif bool(re.search(r'linkedin\.com|github\.com', resume_text, re.IGNORECASE)):
        contact_pts += 5.0
        strengths.append("Professional profile link (LinkedIn/GitHub) present.")
    else:
        contact_pts += 2.0
        warnings.append("Location or professional web links (LinkedIn/GitHub) not explicitly detected.")
        
    breakdown["contact_info"] = round(contact_pts, 1)
    
    # 2. Section Completeness (25 pts max)
    sections = parsed_resume.get("sections", {})
    sec_pts = 0.0
    
    if parsed_resume.get("experience") or "experience" in sections:
        sec_pts += 8.0
        strengths.append("Work Experience section clearly identified and structured.")
    else:
        warnings.append("Missing distinct Work Experience section header.")
        
    if parsed_resume.get("skills") or "skills" in sections:
        sec_pts += 6.0
        strengths.append("Dedicated Skills section present for keyword indexing.")
    else:
        warnings.append("No dedicated Skills / Core Competencies section found.")
        
    if parsed_resume.get("education") or "education" in sections:
        sec_pts += 6.0
        strengths.append("Education and academic background clearly demarcated.")
    else:
        warnings.append("Education section is missing or lacks standard degree terminology.")
        
    if "summary" in sections or "header" in sections:
        sec_pts += 5.0
        strengths.append("Executive Summary / Professional Objective included.")
    else:
        sec_pts += 2.5
        
    breakdown["section_completeness"] = round(sec_pts, 1)
    
    # 3. Keyword Relevance (25 pts max)
    kw_pts = 0.0
    text_lower = resume_text.lower()
    
    if key_terms:
        matched_kw = [kw for kw in key_terms if kw.lower() in text_lower]
        kw_ratio = len(matched_kw) / len(key_terms) if key_terms else 1.0
        kw_pts = min(kw_ratio * 25.0, 25.0)
        if kw_ratio >= 0.6:
            strengths.append(f"Strong alignment with job description keywords ({len(matched_kw)}/{len(key_terms)} key terms matched).")
        else:
            warnings.append(f"Low frequency of job-specific keywords ({len(matched_kw)}/{len(key_terms)} key terms matched).")
    else:
        kw_pts = 20.0
        
    breakdown["keyword_relevance"] = round(kw_pts, 1)
    
    # 4. Skill Relevance (25 pts max)
    cand_skills = set(s.lower() for s in parsed_resume.get("skills", []))
    req_skills_list = required_skills or []
    
    if req_skills_list:
        matched_req = [s for s in req_skills_list if s.lower() in cand_skills]
        skill_ratio = len(matched_req) / len(req_skills_list)
        skill_pts = min(skill_ratio * 25.0, 25.0)
        
        if skill_ratio >= 0.75:
            strengths.append(f"High technical skill match ({len(matched_req)}/{len(req_skills_list)} core skills).")
        elif skill_ratio >= 0.4:
            strengths.append(f"Moderate core skill match ({len(matched_req)}/{len(req_skills_list)} core skills).")
        else:
            warnings.append(f"Significant skill gaps ({len(matched_req)}/{len(req_skills_list)} core skills matched).")
    else:
        skill_pts = 22.0
        
    breakdown["skill_relevance"] = round(skill_pts, 1)
    
    # 5. Formatting Quality & Length (10 pts max)
    fmt_pts = 0.0
    words = resume_text.split()
    word_count = len(words)
    
    if 250 <= word_count <= 1800:
        fmt_pts += 5.0
        strengths.append(f"Optimal resume length ({word_count} words).")
    elif 150 <= word_count < 250:
        fmt_pts += 3.5
        warnings.append(f"Resume is relatively brief ({word_count} words). Consider adding more project details.")
    elif word_count > 1800:
        fmt_pts += 3.0
        warnings.append(f"Resume is lengthy ({word_count} words). Consider condensing to 1-2 pages.")
    else:
        fmt_pts += 1.0
        warnings.append(f"Resume content is extremely sparse ({word_count} words).")
        
    # Check special characters hygiene
    clean_char_ratio = len(re.findall(r'[a-zA-Z0-9\s.,\-\'\"()/@]', resume_text)) / max(len(resume_text), 1)
    if clean_char_ratio >= 0.92:
        fmt_pts += 5.0
        strengths.append("Clean text formatting without encoding artifacts or irregular symbols.")
    else:
        fmt_pts += 2.5
        warnings.append("Contains non-standard symbols or complex table layouts that might hinder legacy ATS parsers.")
        
    breakdown["formatting_quality"] = round(fmt_pts, 1)
    
    # Calculate Total ATS Score
    total_ats = sum(breakdown.values())
    total_ats = round(min(max(total_ats, 0.0), 100.0), 1)
    
    explanation = {
        "score": total_ats,
        "strengths": strengths,
        "warnings": warnings,
        "word_count": word_count,
        "summary": f"ATS compatibility evaluated at {total_ats}%. Contact score: {breakdown['contact_info']}/15, Sections: {breakdown['section_completeness']}/25, Keywords: {breakdown['keyword_relevance']}/25, Skills: {breakdown['skill_relevance']}/25, Formatting: {breakdown['formatting_quality']}/10."
    }
    
    return {
        "ats_score": total_ats,
        "ats_breakdown": breakdown,
        "explanation": explanation
    }
