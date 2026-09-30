# Refactored implementation
# File: user_repository.py
class UserRepository:
    """Handles persistence of user data."""
    def __init__(self, db_path):
        self.db_path = db_path
        self.users = {}
        self.load_users()

    def load_users(self):
        import json, os
        if os.path.exists(self.db_path):
            with open(self.db_path) as f:
                self.users = json.load(f)
        else:
            self.users = {}

    def save_users(self):
        import json
        with open(self.db_path, "w") as f:
            json.dump(self.users, f)

    def add_user(self, username, email, password_hash, salt):
        self.users[username] = {
            "email": email,
            "password": password_hash,
            "salt": salt,
            "active": True,
        }
        self.save_users()

    def get_user(self, username):
        return self.users.get(username)

    def deactivate(self, username):
        if username in self.users:
            self.users[username]["active"] = False
            self.save_users()
            return self.users[username]
        return None

    def list_active(self):
        return [u for u, d in self.users.items() if d.get("active")]

# File: session_service.py
import uuid, time
class SessionService:
    """Manages login sessions and cleanup."""
    def __init__(self):
        self.sessions = {}

    def create_session(self, username):
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {"user": username, "created": time.time()}
        return session_id

    def get_username(self, session_id):
        sess = self.sessions.get(session_id)
        return sess["user"] if sess else None

    def logout(self, session_id):
        self.sessions.pop(session_id, None)

    def cleanup(self, max_age=3600):
        now = time.time()
        expired = [sid for sid, s in self.sessions.items() if now - s["created"] > max_age]
        for sid in expired:
            del self.sessions[sid]

# File: email_queue.py
class EmailQueue:
    """Simple in‑memory email queue."""
    def __init__(self):
        self.queue = []

    def enqueue(self, kind, to, body):
        self.queue.append((kind, to, body))

    def send_all(self):
        for kind, to, body in self.queue:
            print(f"Sending {kind} to {to}: {body}")
        self.queue.clear()

# File: user_manager.py
import hashlib
class UserManager:
    """Facade that coordinates repository, session service and email queue."""
    def __init__(self, db_path):
        self.repo = UserRepository(db_path)
        self.sessions = SessionService()
        self.emails = EmailQueue()

    def create_user(self, username, email, password):
        if username in self.repo.users:
            raise ValueError("User exists")
        if not email or '@' not in email:
            raise ValueError("Invalid email")
        if len(password) < 8:
            raise ValueError("Password too short")
        salt = username[:4]
        hashed = hashlib.sha256((salt + password).encode()).hexdigest()
        self.repo.add_user(username, email, hashed, salt)
        self.emails.enqueue('welcome', email, f'Welcome {username}!')

    def login(self, username, password):
        user = self.repo.get_user(username)
        if not user:
            return None
        hashed = hashlib.sha256((user['salt'] + password).encode()).hexdigest()
        if hashed != user['password']:
            return None
        return self.sessions.create_session(username)

    def logout(self, session_id):
        self.sessions.logout(session_id)

    def get_user(self, session_id):
        username = self.sessions.get_username(session_id)
        return self.repo.get_user(username) if username else None

    def send_emails(self):
        self.emails.send_all()

    def deactivate_user(self, username):
        user = self.repo.deactivate(username)
        if user:
            self.emails.enqueue('deactivation', user['email'], f'Account {username} deactivated')

    def list_active_users(self):
        return self.repo.list_active()

    def cleanup_sessions(self, max_age=3600):
        self.sessions.cleanup(max_age)

# Tests (using unittest)
import unittest
import os, json, tempfile

class TestUserManagerRefactor(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, 'users.json')
        self.um = UserManager(self.db_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_user_creation_and_persistence(self):
        self.um.create_user('alice', 'alice@example.com', 'securepwd')
        # reload manager to verify persistence
        um2 = UserManager(self.db_path)
        self.assertIn('alice', um2.repo.users)
        self.assertEqual(um2.repo.users['alice']['email'], 'alice@example.com')

    def test_login_and_session(self):
        self.um.create_user('bob', 'bob@example.com', 'password123')
        sid = self.um.login('bob', 'password123')
        self.assertIsNotNone(sid)
        user = self.um.get_user(sid)
        self.assertEqual(user['email'], 'bob@example.com')
        self.um.logout(sid)
        self.assertIsNone(self.um.get_user(sid))

    def test_deactivate_and_email(self):
        self.um.create_user('carol', 'c@example.com', 'pwdpwdpwd')
        self.um.deactivate_user('carol')
        self.assertFalse(self.um.repo.users['carol']['active'])
        # capture email output
        from io import StringIO
        import sys
        captured = StringIO()
        sys.stdout = captured
        self.um.send_emails()
        sys.stdout = sys.__stdout__
        output = captured.getvalue()
        self.assertIn('deactivation', output)
        self.assertIn('carol', output)

    def test_list_active_users(self):
        self.um.create_user('dave', 'd@example.com', 'pass1234')
        self.um.create_user('eve', 'e@example.com', 'pass1234')
        self.um.deactivate_user('eve')
        active = self.um.list_active_users()
        self.assertIn('dave', active)
        self.assertNotIn('eve', active)

    def test_cleanup_sessions(self):
        self.um.create_user('frank', 'f@example.com', 'passwd123')
        sid = self.um.login('frank', 'passwd123')
        # artificially age the session
        self.um.sessions.sessions[sid]['created'] -= 7200
        self.um.cleanup_sessions(max_age=3600)
        self.assertIsNone(self.um.sessions.get_username(sid))

if __name__ == '__main__':
    unittest.main()
