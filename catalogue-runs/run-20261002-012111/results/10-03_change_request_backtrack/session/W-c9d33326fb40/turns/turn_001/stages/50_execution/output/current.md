import requests

class JsonPlaceholderClient:
    """A simple client for the JSONPlaceholder API supporting listing, creating, and deleting posts."""

    def __init__(self, base_url: str = "https://jsonplaceholder.typicode.com"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def list_posts(self):
        """Retrieve a list of all posts.

        Returns:
            list: A list of post dictionaries.
        """
        url = f"{self.base_url}/posts"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def create_post(self, title: str, body: str, user_id: int):
        """Create a new post.

        Args:
            title (str): The title of the post.
            body (str): The body content of the post.
            user_id (int): The ID of the user creating the post.

        Returns:
            dict: The created post as returned by the API.
        """
        url = f"{self.base_url}/posts"
        payload = {"title": title, "body": body, "userId": user_id}
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def delete_post(self, post_id: int):
        """Delete a post by its ID.

        Args:
            post_id (int): The ID of the post to delete.

        Returns:
            bool: True if the deletion was successful (status code 200 or 204).
        """
        url = f"{self.base_url}/posts/{post_id}"
        response = self.session.delete(url)
        # JSONPlaceholder returns a 200 status code for deletions.
        if response.status_code in (200, 204):
            return True
        response.raise_for_status()
        return False

# Example usage (would be removed or guarded in production code):
if __name__ == "__main__":
    client = JsonPlaceholderClient()
    print("Listing posts (first 3):", client.list_posts()[:3])
    new_post = client.create_post("Foo", "Bar content", 1)
    print("Created post:", new_post)
    success = client.delete_post(new_post.get("id", 101))
    print("Deleted post success:", success)
