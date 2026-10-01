# Refactored implementation

import json
import os
import hashlib
import uuid
import time
from typing import List, Dict, Optional

# ---------- Repository (Persistence) ----------
class UserRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._users: Dict[str, Dict] = {}
        self.load()

    def load(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, "r") as f:
                self._users = json.load(f)
        else:
            self._users = {}

    def save(self):
        with open(self.db_path, "w") as f:
            json.dump(self._users, f)

    def add_user(self, username: str, email: str, password_hash: str, salt: str):
        self._users[username] = {
            "email": email,
            "password": password_hash,
            "salt": salt,
            "active": True,
        }
        self.save()

    def get_user(self, username: str) -> Optional[Dict]:
        return self._users.get(username)

    def deactivate(self, username: str):
        if username in self._users:
            self._users[username]["active"] = False
            self.save()

    def list_active(self) -> List[str]:
        return [u for u, d in self._users.items() if d.get("active")]

# ---------- Email Dispatcher ----------
class EmailDispatcher:
    def __init__(self):
        self.queue: List[tuple] = []

    def enqueue(self, kind: str, to: str, body: str):
        self.queue.append((kind, to, body))

    def send_all(self):
        for kind, to, body in self.queue:
            print(f"Sending {kind} to {to}: {body}")
        self.queue.clear()

# ---------- Session Manager ----------
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}

    def create(self, username: str) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {"user": username, "created": time.time()}
        return session_id

    def destroy(self, session_id: str):
        self.sessions.pop(session_id, None)

    def get_user(self, session_id: str) -> Optional[Dict]:
        sess = self.sessions.get(session_id)
        if not sess:
            return None
        return {"username": sess["user"], "created": sess["created"]}

    def cleanup(self, max_age: int = 3600):
        now = time.time()
        expired = [sid for sid, s in self.sessions.items() if now - s["created"] > max_age]
        for sid in expired:
            del self.sessions[sid]

# ---------- Authentication Service ----------
class AuthService:
    def __init__(self, repo: UserRepository, sessions: SessionManager, emails: EmailDispatcher):
        self.repo = repo
        self.sessions = sessions
        self.emails = emails

    def _hash(self, salt: str, password: str) -> str:
        return hashlib.sha256((salt + password).encode()).hexdigest()

    def create_user(self, username: str, email: str, password: str):
        if self.repo.get_user(username):
            raise ValueError("User exists")
        if not email or "@" not in email:
            raise ValueError("Invalid email")
        if len(password) < 8:
            raise ValueError("Password too short")
        salt = username[:4]
        password_hash = self._hash(salt, password)
        self.repo.add_user(username, email, password_hash, salt)
        self.emails.enqueue("welcome", email, f"Welcome {username}!")

    def login(self, username: str, password: str) -> Optional[str]:
        user = self.repo.get_user(username)
        if not user:
            return None
        expected = self._hash(user["salt"], password)
        if expected != user["password"]:
            return None
        return self.sessions.create(username)

    def logout(self, session_id: str):
        self.sessions.destroy(session_id)

    def get_user(self, session_id: str) -> Optional[Dict]:
        sess = self.sessions.get_user(session_id)
        if not sess:
            return None
        return self.repo.get_user(sess["username"])

    def deactivate_user(self, username: str):
        self.repo.deactivate(username)
        user = self.repo.get_user(username)
        if user:
            self.emails.enqueue("deactivation", user["email"], f"Account {username} deactivated")

    def list_active_users(self) -> List[str]:
        return self.repo.list_active()

    def cleanup_sessions(self, max_age: int = 3600):
        self.sessions.cleanup(max_age)

    def send_emails(self):
        self.emails.send_all()

# ---------- Unit Tests ----------
import unittest
import tempfile
import shutil

class TestUserManagement(unittest.TestCase):
    def setUp(self):
        # create a temporary directory for the db file
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "users.json")
        repo = UserRepository(self.db_path)
        sessions = SessionManager()
        emails = EmailDispatcher()
        self.auth = AuthService(repo, sessions, emails)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_create_user_success(self):
        self.auth.create_user("alice", "alice@example.com", "password123")
        user = self.auth.repo.get_user("alice")
        self.assertIsNotNone(user)
        self.assertTrue(user["active"])
        self.assertEqual(user["email"], "alice@example.com")
        # email queued
        self.assertEqual(len(self.auth.emails.queue), 1)
        self.assertEqual(self.auth.emails.queue[0][0], "welcome")

    def test_create_user_existing(self):
        self.auth.create_user("bob", "bob@example.com", "securepwd")
        with self.assertRaises(ValueError) as cm:
            self.auth.create_user("bob", "bob2@example.com", "anotherpwd")
        self.assertEqual(str(cm.exception), "User exists")

    def test_create_user_invalid_email(self):
        with self.assertRaises(ValueError) as cm:
            self.auth.create_user("charlie", "not-an-email", "pwd12345")
        self.assertEqual(str(cm.exception), "Invalid email")

    def test_create_user_short_password(self):
        with self.assertRaises(ValueError) as cm:
            self.auth.create_user("dave", "dave@example.com", "short")
        self.assertEqual(str(cm.exception), "Password too short")

    def test_login_logout(self):
        self.auth.create_user("eve", "eve@example.com", "strongpwd")
        sid = self.auth.login("eve", "strongpwd")
        self.assertIsNotNone(sid)
        user = self.auth.get_user(sid)
        self.assertIsNotNone(user)
        self.assertEqual(user["email"], "eve@example.com")
        self.auth.logout(sid)
        self.assertIsNone(self.auth.sessions.get_user(sid))

    def test_login_wrong_password(self):
        self.auth.create_user("frank", "frank@example.com", "correctpwd")
        sid = self.auth.login("frank", "wrongpwd")
        self.assertIsNone(sid)

    def test_deactivate_user(self):
        self.auth.create_user("grace", "grace@example.com", "gracepwd")
        self.auth.deactivate_user("grace")
        user = self.auth.repo.get_user("grace")
        self.assertFalse(user["active"])
        self.assertEqual(self.auth.emails.queue[-1][0], "deactivation")

    def test_list_active_users(self):
        self.auth.create_user("henry", "henry@example.com", "henrypwd")
        self.auth.create_user("irene", "irene@example.com", "irenepwd")
        self.auth.deactivate_user("henry")
        active = self.auth.list_active_users()
        self.assertListEqual(active, ["irene"])

    def test_cleanup_sessions(self):
        self.auth.create_user("jack", "jack@example.com", "jackpwd")
        sid = self.auth.login("jack", "jackpwd")
        # artificially age the session
        self.auth.sessions.sessions[sid]["created"] -= 4000
        self.auth.cleanup_sessions(max_age=3600)
        self.assertIsNone(self.auth.sessions.get_user(sid))

    def test_send_emails(self):
        self.auth.create_user("kate", "kate@example.com", "katepwd")
        self.auth.deactivate_user("kate")
        # capture stdout
        from io import StringIO
        import sys
        captured = StringIO()
        sys_stdout = sys.stdout
        sys.stdout = captured
        try:
            self.auth.send_emails()
        finally:
            sys.stdout = sys_stdout
        output = captured.getvalue()
        self.assertIn("Sending welcome to kate@example.com", output)
        self.assertIn("Sending deactivation to kate@example.com", output)

if __name__ == "__main__":
    unittest.main()
