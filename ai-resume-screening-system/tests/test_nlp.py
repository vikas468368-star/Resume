import unittest
from app.services.nlp_processor import (
    extract_email,
    extract_phone,
    extract_name,
    extract_location,
    extract_skills,
    segment_resume_sections,
    extract_experience_years,
    extract_education_details,
    parse_resume_nlp
)

class NLPProcessorTestCase(unittest.TestCase):
    def setUp(self):
        self.sample_text = """Brandon Lee
Email: brandon.lee@aiengineering.co
Phone: (415) 555-9876
Location: Seattle, WA

PROFESSIONAL SUMMARY
Senior Machine Learning Engineer with 5+ years of experience specializing in NLP, transformers, and cloud architecture.

CORE SKILLS
Python, PyTorch, Scikit-Learn, TensorFlow, Docker, Kubernetes, AWS, PostgreSQL, RESTful APIs, Git

WORK EXPERIENCE
Senior AI Engineer | NeuroCloud Systems (2021 - Present)
- Developed transformer models with PyTorch and Hugging Face.
- Deployed microservices using Docker and Kubernetes on AWS.

Machine Learning Developer | DataVenture (2019 - 2021)
- Built regression models using Scikit-Learn and Pandas.
- Automated database queries with PostgreSQL.

EDUCATION
Master of Science in Computer Science
University of Washington (2017 - 2019)

Bachelor of Science in Electrical Engineering
University of Illinois (2013 - 2017)"""

    def test_contact_information_extraction(self):
        self.assertEqual(extract_email(self.sample_text), "brandon.lee@aiengineering.co")
        self.assertEqual(extract_phone(self.sample_text), "(415) 555-9876")
        self.assertEqual(extract_name(self.sample_text), "Brandon Lee")
        self.assertIn("Seattle", extract_location(self.sample_text))

    def test_skill_extraction_and_alias_normalization(self):
        text_with_aliases = "Skilled in py, k8s, reactjs, postman, and postgres on aws ec2 with docker-compose"
        skills = extract_skills(text_with_aliases)
        
        # Verify canonical mapping
        self.assertIn("Python", skills)
        self.assertIn("Kubernetes", skills)
        self.assertIn("React", skills)
        self.assertIn("PostgreSQL", skills)
        self.assertIn("AWS", skills)
        self.assertIn("Docker", skills)

    def test_section_segmentation(self):
        sections = segment_resume_sections(self.sample_text)
        self.assertIn("summary", sections)
        self.assertIn("skills", sections)
        self.assertIn("experience", sections)
        self.assertIn("education", sections)

    def test_experience_years_extraction(self):
        years = extract_experience_years(self.sample_text)
        # Should be at least 5.0 from explicit mention "5+ years"
        self.assertGreaterEqual(years, 5.0)

    def test_education_degree_extraction(self):
        edu = extract_education_details(self.sample_text)
        degrees = [e['degree'] for e in edu]
        self.assertIn("Master's Degree", degrees)
        self.assertIn("Bachelor's Degree", degrees)

    def test_full_nlp_pipeline(self):
        parsed = parse_resume_nlp(self.sample_text)
        self.assertEqual(parsed['name'], "Brandon Lee")
        self.assertEqual(parsed['email'], "brandon.lee@aiengineering.co")
        self.assertIn("Python", parsed['skills'])
        self.assertIn("PyTorch", parsed['skills'])
        self.assertIn("Docker", parsed['skills'])
        self.assertGreaterEqual(len(parsed['experience']), 1)
        self.assertGreaterEqual(len(parsed['education']), 1)

if __name__ == '__main__':
    unittest.main()
