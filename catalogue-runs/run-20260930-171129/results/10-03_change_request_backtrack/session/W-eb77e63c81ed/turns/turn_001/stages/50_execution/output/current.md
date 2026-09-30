# jsonplaceholder_client.py
"""A simple REST API client for the JSONPlaceholder service.
Provides functions to list posts, create a post, and delete a post.
"""
import json
import urllib.request
import urllib.parse

BASE_URL = "https://jsonplaceholder.typicode.com"

def _request(method: str, path: str, data=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if data is not None:
        data_bytes = json.dumps(data).encode("utf-8")
    else:
        data_bytes = None
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return json.load(resp) if resp.status != 204 else None

def list_posts():
    """Retrieve all posts.
    Returns the JSON array of posts.
    """
    return _request("GET", "/posts")

def create_post(post_data):
    """Create a new post.
    `post_data` should be a dict with keys like "title", "body", "userId".
    Returns the created post as JSON.
    """
    return _request("POST", "/posts", post_data)

def delete_post(post_id):
    """Delete a post by ID.
    Returns None on successful deletion (204 No Content).
    """
    return _request("DELETE", f"/posts/{post_id}")

# Example usage (commented out for import safety):
# if __name__ == "__main__":
#     print(list_posts())
#     new = create_post({"title": "foo", "body": "bar", "userId": 1})
#     print(new)
#     print(delete_post(new["id"]))
