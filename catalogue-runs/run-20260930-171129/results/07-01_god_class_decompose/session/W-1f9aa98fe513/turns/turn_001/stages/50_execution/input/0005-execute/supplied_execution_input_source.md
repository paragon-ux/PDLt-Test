The following 300-line class does too many things. Decompose it into at least 3 cohesive classes with clear single responsibilities. Preserve all existing behavior.

`python
class UserManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.users = {}
        self.sessions = {}
        self.email_queue = []
        self.load_users()
    
    def load_users(self):
        import json, os
        if os.path.exists(self.db_path):
            with open(self.db_path) as f:
                self.users = json.load(f)
    
    def save_users(self):
        import json
        with open(self.db_path, 'w') as f:
            json.dump(self.users, f)
    
    def create_user(self, username, email, password):
        import hashlib
        if username in self.users:
            raise ValueError("User exists")
        if not email or '@' not in email:
            raise ValueError("Invalid email")
        if len(password) < 8:
            raise ValueError("Password too short")
        salt = username[:4]
        hashed = hashlib.sha256((salt + password).encode()).hexdigest()
        self.users[username] = {'email': email, 'password': hashed, 'salt': salt, 'active': True}
        self.save_users()
        self.email_queue.append(('welcome', email, f'Welcome {username}!'))
    
    def login(self, username, password):
        import hashlib, uuid
        if username not in self.users:
            return None
        user = self.users[username]
        hashed = hashlib.sha256((user['salt'] + password).encode()).hexdigest()
        if hashed != user['password']:
            return None
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {'user': username, 'created': __import__('time').time()}
        return session_id
    
    def logout(self, session_id):
        self.sessions.pop(session_id, None)
    
    def get_user(self, session_id):
        session = self.sessions.get(session_id)
        if not session:
            return None
        return self.users.get(session['user'])
    
    def send_emails(self):
        for kind, to, body in self.email_queue:
            print(f"Sending {kind} to {to}: {body}")
        self.email_queue.clear()
    
    def deactivate_user(self, username):
        if username in self.users:
            self.users[username]['active'] = False
            self.save_users()
            self.email_queue.append(('deactivation', self.users[username]['email'], f'Account {username} deactivated'))
    
    def list_active_users(self):
        return [u for u, d in self.users.items() if d.get('active')]
    
    def cleanup_sessions(self, max_age=3600):
        import time
        now = time.time()
        expired = [sid for sid, s in self.sessions.items() if now - s['created'] > max_age]
        for sid in expired:
            del self.sessions[sid]
`

Include tests proving all original behaviors still work after refactoring.
