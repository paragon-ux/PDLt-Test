```python
import requests

class JSONPlaceholderClient:
    BASE = "https://jsonplaceholder.typicode.com"
    def list_posts(self): return requests.get(f"{self.BASE}/posts").json()
    def create_post(self, title, body, user_id=1):
        return requests.post(f"{self.BASE}/posts", json={"title": title, "body": body, "userId": user_id}).json()
    def delete_post(self, post_id): return requests.delete(f"{self.BASE}/posts/{post_id}").status_code == 200
```
