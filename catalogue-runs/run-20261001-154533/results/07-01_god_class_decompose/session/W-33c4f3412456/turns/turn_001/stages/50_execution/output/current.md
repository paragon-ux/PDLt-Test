```python
# refactored_user_manager.py
import json
import os
import hashlib
import uuid
import time
from typing import Dict, List, Optional

class UserRepository:
    """Handles persistence of user data to a JSON file."""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.users: Dict[str, Dict] = {}
        self.load_users()

    def load_users(self) -> None:
        if os.path.exists(self.db_path):
            with open(self.db_path, "r") as f:
                self.users = json.load(f)
        else:
            self.users = {}

    def save_users(self) -> None:
        with open(self.db_path, "w") as f:
            json.dump(self.users, f)

    def add_user(self, username: str, email: str, password_hash: str, salt: str) -> None:
        self.users[username] = {
            "email": email,
            "password": password_hash,
            "salt": salt,
            "active": True,
        }
        self.save_users()

    def deactivate(self, username: str) -> None:
        if username in self.users:
            self.users[username]["active"] = False
            self.save_users()

    def get_user(self, username: str) -> Optional[Dict]:
        return self.users.get(username)

    def list_active_users(self) -> List[str]:
        return [u for u, d in self.users.items() if d.get("active")]

class SessionManager:
    """Manages user login sessions in memory."""
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}

    def create_session(self, username: str) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {"user": username, "created": time.time()}
        return session_id

    def get_username(self, session_id: str) -> Optional[str]:
        sess = self.sessions.get(session_id)
        return sess["user"] if sess else None

    def logout(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)

    def cleanup_sessions(self, max_age: int = 3600) -> None:
        now = time.time()
        expired = [sid for sid, s in self.sessions.items() if now - s["created"] > max_age]
        for sid in expired:
            del self.sessions[sid]

class EmailQueue:
    """Simple in‑memory email queue for outgoing messages."""
    def __init__(self):
        self.queue: List[tuple] = []

    def enqueue(self, kind: str, to: str, body: str) -> None:
        self.queue.append((kind, to, body))

    def send_all(self) -> None:
        for kind, to, body in self.queue:
            print(f"Sending {kind} to {to}: {body}")
        self.queue.clear()

class UserManager:
    """Public façade preserving the original interface while delegating.

    The original monolithic responsibilities are now split across
    UserRepository, SessionManager, and EmailQueue.
    """
    def __init__(self, db_path: str):
        self.repo = UserRepository(db_path)
        self.sessions = SessionManager()
        self.email_queue = EmailQueue()

    # ----- User lifecycle -------------------------------------------------
    def create_user(self, username: str, email: str, password: str) -> None:
        if username in self.repo.users:
            raise ValueError("User exists")
        if not email or "@" not in email:
            raise ValueError("Invalid email")
        if len(password) < 8:
            raise ValueError("Password too short")
        salt = username[:4]
        hashed = hashlib.sha256((salt + password).encode()).hexdigest()
        self.repo.add_user(username, email, hashed, salt)
        self.email_queue.enqueue("welcome", email, f"Welcome {username}!")

    def deactivate_user(self, username: str) -> None:
        if username in self.repo.users:
            self.repo.deactivate(username)
            email = self.repo.users[username]["email"]
            self.email_queue.enqueue(
                "deactivation", email, f"Account {username} deactivated"
            )

    def list_active_users(self) -> List[str]:
        return self.repo.list_active_users()

    # ----- Authentication -------------------------------------------------
    def login(self, username: str, password: str) -> Optional[str]:
        user = self.repo.get_user(username)
        if not user:
            return None
        hashed = hashlib.sha256((user["salt"] + password).encode()).hexdigest()
        if hashed != user["password"]:
            return None
        return self.sessions.create_session(username)

    def logout(self, session_id: str) -> None:
        self.sessions.logout(session_id)

    def get_user(self, session_id: str) -> Optional[Dict]:
        username = self.sessions.get_username(session_id)
        if not username:
            return None
        return self.repo.get_user(username)

    # ----- Email handling -------------------------------------------------
    def send_emails(self) -> None:
        self.email_queue.send_all()

    # ----- Session housekeeping -------------------------------------------
    def cleanup_sessions(self, max_age: int = 3600) -> None:
        self.sessions.cleanup_sessions(max_age)
```
```python
# test_user_manager.py
import os
import tempfile
import unittest
from refactored_user_manager import UserManager

class TestUserManager(unittest.TestCase):
    def setUp(self):
        # create a temporary file for the JSON DB
        self.db_fd, self.db_path = tempfile.mkstemp()
        os.close(self.db_fd)
        self.um = UserManager(self.db_path)

    def tearDown(self):
        os.remove(self.db_path)

    def test_create_and_login_flow(self):
        self.um.create_user("alice", "alice@example.com", "strongpwd")
        session = self.um.login("alice", "strongpwd")
        self.assertIsNotNone(session)
        user_data = self.um.get_user(session)
        self.assertEqual(user_data["email"], "alice@example.com")
        self.um.logout(session)
        self.assertIsNone(self.um.get_user(session))

    def test_invalid_login(self):
        self.um.create_user("bob", "bob@example.com", "anotherpwd")
        self.assertIsNone(self.um.login("bob", "wrongpwd"))
        self.assertIsNone(self.um.login("nonexistent", "pw"))

    def test_deactivate_user(self):
        self.um.create_user("carol", "carol@example.com", "pwd12345")
        self.um.deactivate_user("carol")
        self.assertNotIn("carol", self.um.list_active_users())

    def test_email_queue(self):
        # capture stdout
        from io import StringIO
        import sys
        captured = StringIO()
        sys_stdout = sys.stdout
        sys.stdout = captured
        try:
            self.um.create_user("dave", "dave@example.com", "pwd67890")
            self.um.deactivate_user("dave")
            self.um.send_emails()
        finally:
            sys.stdout = sys_stdout
        output = captured.getvalue()
        self.assertIn("Sending welcome to dave@example.com", output)
        self.assertIn("Sending deactivation to dave@example.com", output)

    def test_cleanup_sessions(self):
        # create a session with custom older timestamp
        self.um.create_user("eve", "eve@example.com", "pwd111111")
        session = self.um.login("eve", "pwd111111")
        # manually age the session
        self.um.sessions.sessions[session]["created"] -= 7200  # 2 hours ago
        self.um.cleanup_sessions(max_age=3600)
        self.assertIsNone(self.um.get_user(session))

if __name__ == "__main__":
    unittest.main()
```
