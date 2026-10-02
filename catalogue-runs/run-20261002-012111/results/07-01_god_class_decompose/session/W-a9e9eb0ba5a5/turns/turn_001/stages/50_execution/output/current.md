# Refactored implementation

import json
import os
import hashlib
import uuid
import time
from typing import Dict, List, Tuple, Optional

# ---------- User Persistence ----------
class UserRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.users: Dict[str, Dict] = {}
        self.load_users()

    def load_users(self) -> None:
        if os.path.exists(self.db_path):
            with open(self.db_path, "r", encoding="utf-8") as f:
                self.users = json.load(f)
        else:
            self.users = {}

    def save_users(self) -> None:
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.users, f)

    def create_user(self, username: str, email: str, password: str) -> None:
        if username in self.users:
            raise ValueError("User exists")
        if not email or "@" not in email:
            raise ValueError("Invalid email")
        if len(password) < 8:
            raise ValueError("Password too short")
        salt = username[:4]
        hashed = hashlib.sha256((salt + password).encode()).hexdigest()
        self.users[username] = {
            "email": email,
            "password": hashed,
            "salt": salt,
            "active": True,
        }
        self.save_users()
        return username

    def deactivate_user(self, username: str) -> None:
        if username in self.users:
            self.users[username]["active"] = False
            self.save_users()
            return username

    def get_user(self, username: str) -> Optional[Dict]:
        return self.users.get(username)

    def list_active_users(self) -> List[str]:
        return [u for u, d in self.users.items() if d.get("active")]

# ---------- Session Handling ----------
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}

    def login(self, repo: UserRepository, username: str, password: str) -> Optional[str]:
        user = repo.get_user(username)
        if not user:
            return None
        hashed = hashlib.sha256((user["salt"] + password).encode()).hexdigest()
        if hashed != user["password"]:
            return None
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {"user": username, "created": time.time()}
        return session_id

    def logout(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)

    def get_user_from_session(self, repo: UserRepository, session_id: str) -> Optional[Dict]:
        session = self.sessions.get(session_id)
        if not session:
            return None
        return repo.get_user(session["user"])

    def cleanup_sessions(self, max_age: int = 3600) -> None:
        now = time.time()
        expired = [sid for sid, s in self.sessions.items() if now - s["created"] > max_age]
        for sid in expired:
            del self.sessions[sid]

# ---------- Email Queue ----------
class EmailQueue:
    def __init__(self):
        self.queue: List[Tuple[str, str, str]] = []

    def enqueue(self, kind: str, to: str, body: str) -> None:
        self.queue.append((kind, to, body))

    def send_all(self) -> None:
        for kind, to, body in self.queue:
            print(f"Sending {kind} to {to}: {body}")
        self.queue.clear()

# ---------- Facade (original API) ----------
class UserManager:
    def __init__(self, db_path: str):
        self.repo = UserRepository(db_path)
        self.session_mgr = SessionManager()
        self.email_queue = EmailQueue()

    # User persistence API
    def create_user(self, username: str, email: str, password: str) -> None:
        self.repo.create_user(username, email, password)
        self.email_queue.enqueue("welcome", email, f"Welcome {username}!")

    def deactivate_user(self, username: str) -> None:
        self.repo.deactivate_user(username)
        user = self.repo.get_user(username)
        if user:
            self.email_queue.enqueue("deactivation", user["email"], f"Account {username} deactivated")

    def list_active_users(self) -> List[str]:
        return self.repo.list_active_users()

    # Session API
    def login(self, username: str, password: str) -> Optional[str]:
        return self.session_mgr.login(self.repo, username, password)

    def logout(self, session_id: str) -> None:
        self.session_mgr.logout(session_id)

    def get_user(self, session_id: str) -> Optional[Dict]:
        return self.session_mgr.get_user_from_session(self.repo, session_id)

    def cleanup_sessions(self, max_age: int = 3600) -> None:
        self.session_mgr.cleanup_sessions(max_age)

    # Email API
    def send_emails(self) -> None:
        self.email_queue.send_all()

# ---------- Unit Tests ----------
import unittest
import tempfile
import shutil

class TestUserManagerRefactor(unittest.TestCase):
    def setUp(self):
        # create a temporary directory for the db file
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "users.json")
        self.um = UserManager(self.db_path)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_user_creation_and_login_logout(self):
        self.um.create_user("alice", "alice@example.com", "securepwd")
        session = self.um.login("alice", "securepwd")
        self.assertIsNotNone(session)
        user = self.um.get_user(session)
        self.assertEqual(user["email"], "alice@example.com")
        self.um.logout(session)
        self.assertIsNone(self.um.get_user(session))

    def test_deactivate_and_listing(self):
        self.um.create_user("bob", "bob@example.com", "anotherpwd")
        self.um.create_user("carol", "carol@example.com", "pwd12345")
        self.um.deactivate_user("bob")
        active = self.um.list_active_users()
        self.assertIn("carol", active)
        self.assertNotIn("bob", active)

    def test_session_cleanup(self):
        self.um.create_user("dave", "dave@example.com", "pwd12345")
        sess = self.um.login("dave", "pwd12345")
        # artificially age the session
        self.um.session_mgr.sessions[sess]["created"] -= 7200
        self.um.cleanup_sessions(max_age=3600)
        self.assertIsNone(self.um.get_user(sess))

    def test_email_queue(self):
        self.um.create_user("eve", "eve@example.com", "pwd12345")
        # capture stdout
        from io import StringIO
        import sys
        captured = StringIO()
        sys_stdout = sys.stdout
        sys.stdout = captured
        self.um.send_emails()
        sys.stdout = sys_stdout
        output = captured.getvalue()
        self.assertIn("Sending welcome to eve@example.com", output)
        self.um.deactivate_user("eve")
        captured = StringIO()
        sys.stdout = captured
        self.um.send_emails()
        sys.stdout = sys_stdout
        output = captured.getvalue()
        self.assertIn("Sending deactivation to eve@example.com", output)

if __name__ == "__main__":
    unittest.main()
