import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import urllib.request

# In‑memory data store
bookmarks = {}
next_id = 1

class BookmarkHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.end_headers()

    def _parse_id(self):
        parts = self.path.strip("/").split("/")
        if len(parts) == 2 and parts[0] == "bookmarks":
            try:
                return int(parts[1])
            except ValueError:
                return None
        return None

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/bookmarks":
            # Tag‑search endpoint
            query = parse_qs(parsed.query)
            tag = query.get("tag", [None])[0]
            if tag is None:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Missing 'tag' query parameter"}).encode())
                return
            result = [b for b in bookmarks.values() if tag in b["tags"]]
            self._set_headers(200)
            self.wfile.write(json.dumps(result).encode())
            return
        # GET /bookmarks/{id}
        bookmark_id = self._parse_id()
        if bookmark_id is None:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
            return
        bookmark = bookmarks.get(bookmark_id)
        if bookmark is None:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Bookmark not found"}).encode())
            return
        self._set_headers(200)
        self.wfile.write(json.dumps(bookmark).encode())

    def do_POST(self):
        if self.path != "/bookmarks":
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
            return
        length = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(length))
        global next_id
        bookmark = {
            "id": next_id,
            "url": data["url"],
            "title": data["title"],
            "tags": data.get("tags", []),
            "created_at": data.get("created_at", time.strftime("%Y-%m-%dT%H:%M:%SZ"))
        }
        bookmarks[next_id] = bookmark
        next_id += 1
        self._set_headers(201)
        self.wfile.write(json.dumps(bookmark).encode())

    def do_PUT(self):
        bookmark_id = self._parse_id()
        if bookmark_id is None:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
            return
        if bookmark_id not in bookmarks:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Bookmark not found"}).encode())
            return
        length = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(length))
        bookmark = bookmarks[bookmark_id]
        bookmark.update({
            "url": data.get("url", bookmark["url"]),
            "title": data.get("title", bookmark["title"]),
            "tags": data.get("tags", bookmark["tags"]),
            "created_at": data.get("created_at", bookmark["created_at"])  # normally immutable
        })
        self._set_headers(200)
        self.wfile.write(json.dumps(bookmark).encode())

    def do_DELETE(self):
        bookmark_id = self._parse_id()
        if bookmark_id is None or bookmark_id not in bookmarks:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Bookmark not found"}).encode())
            return
        del bookmarks[bookmark_id]
        self._set_headers(204)
        # No body for 204

def run_server(server_class=HTTPServer, handler_class=BookmarkHandler, port=8000):
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

# ---------------------------------------------------
# Test harness
def test_api():
    base = "http://localhost:8000"
    # Create
    create_data = json.dumps({"url": "https://example.com", "title": "Example", "tags": ["test"], "created_at": "2023-01-01T00:00:00Z"}).encode()
    req = urllib.request.Request(base+"/bookmarks", data=create_data, method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201
        created = json.load(resp)
        assert created["url"] == "https://example.com"
        bookmark_id = created["id"]
    # Read
    with urllib.request.urlopen(f"{base}/bookmarks/{bookmark_id}") as resp:
        assert resp.status == 200
        fetched = json.load(resp)
        assert fetched["title"] == "Example"
    # Update
    update_data = json.dumps({"title": "Example Updated"}).encode()
    req = urllib.request.Request(f"{base}/bookmarks/{bookmark_id}", data=update_data, method="PUT", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        updated = json.load(resp)
        assert updated["title"] == "Example Updated"
    # Search by tag
    with urllib.request.urlopen(f"{base}/bookmarks?tag=test") as resp:
        assert resp.status == 200
        results = json.load(resp)
        assert any(b["id"] == bookmark_id for b in results)
    # Delete
    req = urllib.request.Request(f"{base}/bookmarks/{bookmark_id}", method="DELETE")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 204
    # Verify deletion
    try:
        urllib.request.urlopen(f"{base}/bookmarks/{bookmark_id}")
    except urllib.error.HTTPError as e:
        assert e.code == 404
    print("All tests passed")

if __name__ == "__main__":
    # Start server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    # Give the server a moment to start
    time.sleep(0.5)
    try:
        test_api()
    finally:
        # Shutdown server (simplified for this example)
        # The daemon thread will exit when main thread finishes
        pass
