import unittest
from app.services.scorer import (
    compute_tfidf_similarity,
    compute_skill_overlap,
    calculate_match_score
)
from app.services.ats_scorer import calculate_ats_score
from app.services.ranking import calculate_combined_score

class ScorerTestCase(unittest.TestCase):
    def setUp(self):
        self.resume_text = """John Doe
Email: john.doe@email.com | Phone: (555) 019-2834 | Location: New York, NY
Summary: Experienced Full-Stack Python Engineer with 4 years building Flask and PostgreSQL backends.
Skills: Python, Flask, PostgreSQL, Docker, Git, RESTful APIs
Experience: 2020 - Present at TechCorp building Python microservices with PostgreSQL and Docker.
Education: Bachelor of Science in Computer Science (2020)"""

        self.jd_text = """Senior Python Developer
Requirements:
- 3+ years experience with Python, Flask, and PostgreSQL.
- Experience with Docker, Git, and RESTful APIs.
- Bachelor's degree in Computer Science."""

    def test_tfidf_cosine_similarity(self):
        sim = compute_tfidf_similarity(self.resume_text, self.jd_text)
        self.assertIsInstance(sim, float)
        self.assertGreater(sim, 20.0) # Relevant text should have strong non-zero similarity
        self.assertLessEqual(sim, 100.0)

        # Disconnected text should have very low/zero similarity
        unrelated_text = "Experienced culinary pastry chef specialized in french bakeries and chocolate."
        low_sim = compute_tfidf_similarity(unrelated_text, self.jd_text)
        self.assertLess(low_sim, sim)

    def test_skill_overlap_calculation(self):
        cand_skills = ["Python", "Flask", "PostgreSQL", "Docker", "Git"]
        req_skills = ["Python", "Flask", "PostgreSQL", "Docker", "AWS"]
        pref_skills = ["Redis", "Git"]

        score, matched, missing = compute_skill_overlap(cand_skills, req_skills, pref_skills)
        self.assertIn("Python", matched)
        self.assertIn("AWS", missing)
        self.assertGreater(score, 60.0)

    def test_multi_factor_match_score(self):
        result = calculate_match_score(
            resume_text=self.resume_text,
            jd_text=self.jd_text,
            candidate_skills=["Python", "Flask", "PostgreSQL", "Docker", "Git", "RESTful APIs"],
            required_skills=["Python", "Flask", "PostgreSQL", "Docker", "RESTful APIs"],
            preferred_skills=["AWS", "Redis"],
            candidate_exp_years=4.0,
            required_min_years=3.0,
            candidate_education=[{"degree": "Bachelor's Degree"}],
            required_education="Bachelor"
        )
        self.assertIn("match_score", result)
        self.assertGreaterEqual(result["match_score"], 60.0)
        self.assertEqual(result["experience_match_score"], 100.0)
        self.assertEqual(result["education_match_score"], 100.0)

    def test_ats_scoring_rubric_and_explainability(self):
        parsed = {
            "name": "John Doe",
            "email": "john.doe@email.com",
            "phone": "(555) 019-2834",
            "location": "New York, NY",
            "skills": ["Python", "Flask", "PostgreSQL", "Docker"],
            "experience": [{"title_company": "Software Engineer", "description": "Built APIs"}],
            "education": [{"degree": "Bachelor's Degree"}],
            "sections": {"summary": "Experienced", "experience": "Work", "education": "BS", "skills": "Python"}
        }
        
        ats = calculate_ats_score(
            resume_text=self.resume_text,
            parsed_resume=parsed,
            job_description=self.jd_text,
            required_skills=["Python", "Flask", "PostgreSQL", "Docker"],
            key_terms=["python", "flask", "postgresql", "docker"]
        )
        self.assertGreaterEqual(ats["ats_score"], 80.0)
        self.assertIn("contact_info", ats["ats_breakdown"])
        self.assertIn("section_completeness", ats["ats_breakdown"])
        self.assertGreater(len(ats["explanation"]["strengths"]), 0)

    def test_combined_score_calculation(self):
        comb = calculate_combined_score(match_score=80.0, ats_score=90.0)
        # 80 * 0.70 + 90 * 0.30 = 56 + 27 = 83.0
        self.assertEqual(comb, 83.0)

if __name__ == '__main__':
    unittest.main()
