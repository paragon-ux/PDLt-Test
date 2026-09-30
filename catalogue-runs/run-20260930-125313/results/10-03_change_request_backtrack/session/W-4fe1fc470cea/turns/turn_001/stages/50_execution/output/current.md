import json
import urllib.request
import urllib.parse

BASE_URL = "https://jsonplaceholder.typicode.com"

def list_posts():
    """GET /posts – returns list of posts with HTTP status and JSON body."""
    url = f"{BASE_URL}/posts"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req) as resp:
        status = resp.getcode()
        data = json.loads(resp.read().decode())
    return {"status": status, "body": data}

def create_post(title, body, userId):
    """POST /posts – creates a post with given fields, returns status and response JSON."""
    url = f"{BASE_URL}/posts"
    payload = json.dumps({"title": title, "body": body, "userId": userId}).encode()
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json; charset=UTF-8")
    with urllib.request.urlopen(req) as resp:
        status = resp.getcode()
        data = json.loads(resp.read().decode())
    return {"status": status, "body": data}

def delete_post(post_id):
    """DELETE /posts/{id} – deletes the specified post, returns HTTP status."""
    url = f"{BASE_URL}/posts/{post_id}"
    req = urllib.request.Request(url, method="DELETE")
    with urllib.request.urlopen(req) as resp:
        status = resp.getcode()
        # JSONPlaceholder returns an empty body for delete
        body = resp.read().decode()
    return {"status": status, "body": body}

# Example usage (can be removed or adapted as needed):
if __name__ == "__main__":
    print("Listing posts:")
    print(list_posts())
    print("Creating a post:")
    print(create_post("foo", "bar", 1))
    print("Deleting a post:")
    print(delete_post(1))

# RESULT IR
{"files":[{"filename":"rest_client.py","satisfies":["R1","R2","R3","R4","R5"],"evidence":{"path":"execution://body","section":"body","observed":"import json
import urllib.request"}}],"reconciliation":[{"requirement":"R1","status":"satisfied","evidence":{"path":"execution://body","section":"body","observed":"def list_posts"}},{"requirement":"R2","status":"satisfied","evidence":{"path":"execution://body","section":"body","observed":"def list_posts"}},{"requirement":"R3","status":"satisfied","evidence":{"path":"execution://body","section":"body","observed":"def create_post"}},{"requirement":"R4","status":"satisfied","evidence":{"path":"execution://body","section":"body","observed":"def delete_post"}},{"requirement":"R5","status":"satisfied","evidence":{"path":"execution://body","section":"body","observed":"return {\"status\": status, \"body\": data}"}}],"open_defects":[]}
