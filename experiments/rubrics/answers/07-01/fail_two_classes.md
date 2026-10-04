```python
class UserData:
    """Users, persistence and email queue."""
    ...  # load_users, save_users, create_user, deactivate_user, list_active_users, send_emails (unchanged bodies)

class SessionManager:
    """Login, logout, get_user, cleanup_sessions (unchanged bodies)."""
    ...
```
Splitting sessions out removes the main source of coupling; the rest is cohesive enough to stay together. All method bodies are moved unchanged, so behaviour is preserved.
