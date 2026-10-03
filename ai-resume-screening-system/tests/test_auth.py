import unittest
from app import create_app, db
from app.models import User

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_password_hashing(self):
        u = User(name="Test User", email="test@example.com", role="recruiter")
        u.set_password("SecurePass123!")
        self.assertTrue(u.check_password("SecurePass123!"))
        self.assertFalse(u.check_password("WrongPassword"))
        self.assertNotEqual(u.password_hash, "SecurePass123!")

    def test_user_roles(self):
        admin = User(name="Admin User", email="admin@example.com", role="admin")
        recruiter = User(name="Recruiter User", email="rec@example.com", role="recruiter")
        self.assertTrue(admin.is_admin)
        self.assertFalse(admin.is_recruiter)
        self.assertTrue(recruiter.is_recruiter)
        self.assertFalse(recruiter.is_admin)

    def test_registration_and_login_flow(self):
        # Register new recruiter
        res = self.client.post('/register', data={
            'name': 'Test Recruiter',
            'email': 'recruiter.test@company.com',
            'role': 'recruiter',
            'password': 'Password123',
            'confirm_password': 'Password123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        
        user = User.query.filter_by(email='recruiter.test@company.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.name, 'Test Recruiter')

        # Test duplicate registration prevention
        res_dup = self.client.post('/register', data={
            'name': 'Duplicate User',
            'email': 'recruiter.test@company.com',
            'role': 'recruiter',
            'password': 'Password123',
            'confirm_password': 'Password123'
        }, follow_redirects=True)
        self.assertIn(b'already exists', res_dup.data)

        # Login
        res_login = self.client.post('/login', data={
            'email': 'recruiter.test@company.com',
            'password': 'Password123'
        }, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)
        self.assertIn(b'Dashboard', res_login.data)

        # Logout
        res_logout = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(res_logout.status_code, 200)
        self.assertIn(b'Sign In', res_logout.data)

    def test_unauthorized_access_redirects(self):
        # Attempting to access dashboard when logged out redirects to login
        res = self.client.get('/', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers['Location'])

if __name__ == '__main__':
    unittest.main()
