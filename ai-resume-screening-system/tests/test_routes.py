import unittest
from app import create_app, db
from app.models import User, JobDescription, Resume, Screening
from app.services.ranking import process_and_screen_resume

class RoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client(use_cookies=True)

        # Create Recruiter
        self.recruiter = User(name="Recruiter One", email="recruiter@test.com", role="recruiter")
        self.recruiter.set_password("Pass123!")
        db.session.add(self.recruiter)
        db.session.commit()

        # Login recruiter
        self.client.post('/login', data={'email': 'recruiter@test.com', 'password': 'Pass123!'}, follow_redirects=True)

        # Create sample job
        self.job = JobDescription(
            title="Backend Python Developer",
            department="Engineering",
            location="Remote",
            experience_level="Mid-Senior",
            min_experience_years=3.0,
            min_education="Bachelor",
            description_text="Need Python, Flask, and PostgreSQL engineer.",
            required_skills=["Python", "Flask", "PostgreSQL"],
            created_by_user_id=self.recruiter.id
        )
        db.session.add(self.job)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_dashboard_route(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Recruiter Dashboard', res.data)

    def test_jobs_list_and_create(self):
        res_list = self.client.get('/jobs/')
        self.assertEqual(res_list.status_code, 200)
        self.assertIn(b'Backend Python Developer', res_list.data)

        res_create = self.client.post('/jobs/create', data={
            'title': 'Frontend Engineer',
            'department': 'UI',
            'location': 'Remote',
            'experience_level': 'Mid-Level',
            'min_experience_years': '2.0',
            'min_education': 'Bachelor',
            'description_text': 'Looking for React and TypeScript expert with HTML/CSS.',
            'required_skills': 'React, TypeScript, HTML5',
            'preferred_skills': 'Next.js'
        }, follow_redirects=True)
        self.assertEqual(res_create.status_code, 200)
        self.assertIsNotNone(JobDescription.query.filter_by(title='Frontend Engineer').first())

    def test_candidate_screening_and_profile_flow(self):
        # Create Resume and screen against job
        resume = Resume(
            candidate_name="Alice Smith",
            email="alice@smith.org",
            phone="555-0199",
            location="Boston, MA",
            file_name="alice_resume.docx",
            file_path="alice_resume.docx",
            raw_text="Alice Smith. Email: alice@smith.org. Python and Flask backend engineer with PostgreSQL and 4 years experience.",
            uploaded_by_user_id=self.recruiter.id
        )
        db.session.add(resume)
        db.session.commit()

        screening = process_and_screen_resume(resume, self.job, auto_commit=True)
        self.assertIsNotNone(screening.id)
        self.assertGreater(screening.match_score, 50.0)

        # Test Candidate Directory
        res_cand = self.client.get('/candidates/')
        self.assertEqual(res_cand.status_code, 200)
        self.assertIn(b'Alice Smith', res_cand.data)

        # Test Candidate Detail
        res_detail = self.client.get(f'/candidates/{screening.id}')
        self.assertEqual(res_detail.status_code, 200)
        self.assertIn(b'Alice Smith', res_detail.data)
        self.assertIn(b'Multi-Factor Match Score Architecture', res_detail.data)

        # Test Status Update
        res_status = self.client.post(f'/candidates/{screening.id}/status', data={'status': 'shortlisted'}, follow_redirects=True)
        self.assertEqual(res_status.status_code, 200)
        updated_s = Screening.query.get(screening.id)
        self.assertEqual(updated_s.status, 'shortlisted')

    def test_analytics_api(self):
        res = self.client.get('/api/analytics/data')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('match_distribution', data)
        self.assertIn('candidate_trend', data)

if __name__ == '__main__':
    unittest.main()
