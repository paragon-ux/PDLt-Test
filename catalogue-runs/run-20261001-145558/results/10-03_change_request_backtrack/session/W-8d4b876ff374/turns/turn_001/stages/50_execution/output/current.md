import requests

BASE_URL = "https://jsonplaceholder.typicode.com"

def list_posts():
    """Return a list of posts."""
    response = requests.get(f"{BASE_URL}/posts")
    response.raise_for_status()
    return response.json()

def create_post(title, body, user_id):
    """Create a new post.

    Args:
        title (str): Title of the post.
        body (str): Content of the post.
        user_id (int): ID of the user creating the post.
    Returns:
        dict: The created post as returned by the API.
    """
    payload = {"title": title, "body": body, "userId": user_id}
    response = requests.post(f"{BASE_URL}/posts", json=payload)
    response.raise_for_status()
    return response.json()

def delete_post(post_id):
    """Delete a post by its ID.

    Args:
        post_id (int): Identifier of the post to delete.
    Returns:
        bool: True if the deletion was successful (status code 200 or 204).
    """
    response = requests.delete(f"{BASE_URL}/posts/{post_id}")
    # JSONPlaceholder returns a 200 with an empty body for deletions
    return response.status_code in (200, 204)
