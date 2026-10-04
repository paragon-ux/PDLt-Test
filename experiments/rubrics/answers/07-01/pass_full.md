```python
import hashlib, json, os, time, uuid

class UserRepository:
    """Persistence of user records as JSON at db_path."""
    def __init__(self, db_path):
        self.db_path, self.users = db_path, {}
        if os.path.exists(db_path):
            with open(db_path) as f:
                self.users = json.load(f)
    def save(self):
        with open(self.db_path, 'w') as f:
            json.dump(self.users, f)

class PasswordHasher:
    @staticmethod
    def hash(salt, password):
        return hashlib.sha256((salt + password).encode()).hexdigest()

class SessionStore:
    def __init__(self):
        self.sessions = {}
    def create(self, username):
        sid = str(uuid.uuid4())
        self.sessions[sid] = {'user': username, 'created': time.time()}
        return sid
    def remove(self, sid):
        self.sessions.pop(sid, None)
    def user_of(self, sid):
        s = self.sessions.get(sid)
        return s['user'] if s else None
    def cleanup(self, max_age=3600):
        now = time.time()
        for sid in [k for k, s in self.sessions.items() if now - s['created'] > max_age]:
            del self.sessions[sid]

class EmailQueue:
    def __init__(self):
        self.items = []
    def enqueue(self, kind, to, body):
        self.items.append((kind, to, body))
    def send_all(self):
        for kind, to, body in self.items:
            print(f"Sending {kind} to {to}: {body}")
        self.items.clear()

class UserManager:
    """Facade keeping the original API."""
    def __init__(self, db_path):
        self.repo, self.sessions_store, self.mail = UserRepository(db_path), SessionStore(), EmailQueue()
    users = property(lambda self: self.repo.users)
    sessions = property(lambda self: self.sessions_store.sessions)
    email_queue = property(lambda self: self.mail.items)

    def create_user(self, username, email, password):
        if username in self.repo.users: raise ValueError("User exists")
        if not email or '@' not in email: raise ValueError("Invalid email")
        if len(password) < 8: raise ValueError("Password too short")
        salt = username[:4]
        self.repo.users[username] = {'email': email, 'password': PasswordHasher.hash(salt, password), 'salt': salt, 'active': True}
        self.repo.save()
        self.mail.enqueue('welcome', email, f'Welcome {username}!')

    def login(self, username, password):
        user = self.repo.users.get(username)
        if user is None or PasswordHasher.hash(user['salt'], password) != user['password']:
            return None
        return self.sessions_store.create(username)

    def logout(self, session_id): self.sessions_store.remove(session_id)
    def get_user(self, session_id):
        name = self.sessions_store.user_of(session_id)
        return self.repo.users.get(name) if name else None
    def send_emails(self): self.mail.send_all()
    def deactivate_user(self, username):
        if username in self.repo.users:
            self.repo.users[username]['active'] = False
            self.repo.save()
            self.mail.enqueue('deactivation', self.repo.users[username]['email'], f'Account {username} deactivated')
    def list_active_users(self): return [u for u, d in self.repo.users.items() if d.get('active')]
    def cleanup_sessions(self, max_age=3600): self.sessions_store.cleanup(max_age)
```

Tests (pytest, `tmp_path` for the db):
```python
def test_behaviours(tmp_path, capsys):
    m = UserManager(str(tmp_path / "u.json"))
    m.create_user("alice", "a@x.io", "password1")
    for args in [("alice", "a@x.io", "password1"), ("bob", "bad", "password1"), ("bob", "b@x.io", "short")]:
        with pytest.raises(ValueError): m.create_user(*args)
    assert m.login("alice", "wrong") is None and m.login("nobody", "x") is None
    sid = m.login("alice", "password1"); assert m.get_user(sid)["email"] == "a@x.io"
    m.logout(sid); assert m.get_user(sid) is None
    sid = m.login("alice", "password1"); m.sessions[sid]["created"] -= 7200; m.cleanup_sessions(); assert sid not in m.sessions
    m.deactivate_user("alice"); assert m.list_active_users() == []
    m.send_emails(); out = capsys.readouterr().out
    assert "Sending welcome to a@x.io" in out and "Sending deactivation" in out and m.email_queue == []
    assert UserManager(str(tmp_path / "u.json")).users["alice"]["active"] is False   # persisted, same format
```
