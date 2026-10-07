```python
import hashlib, json, os, uuid, time

class UserStore:
    def __init__(self, path):
        self.path = path
        self.users = json.load(open(path)) if os.path.exists(path) else {}
    def save(self): json.dump(self.users, open(self.path, 'w'))

class Auth:
    def __init__(self, store): self.store, self.sessions = store, {}
    def create_user(self, username, email, password):
        self.store.users[username] = {'email': email, 'password': hashlib.sha256(password.encode()).hexdigest(), 'active': True}
        self.store.save()
    def login(self, username, password):
        u = self.store.users.get(username)
        if u and u['password'] == hashlib.sha256(password.encode()).hexdigest():
            sid = str(uuid.uuid4()); self.sessions[sid] = {'user': username, 'created': time.time()}; return sid

class Mailer:
    def __init__(self): self.queue = []
    def send_emails(self):
        for kind, to, body in self.queue: print(f"Sending {kind} to {to}: {body}")
        self.queue.clear()
```
Tests: create a user and log in successfully; send an email.
