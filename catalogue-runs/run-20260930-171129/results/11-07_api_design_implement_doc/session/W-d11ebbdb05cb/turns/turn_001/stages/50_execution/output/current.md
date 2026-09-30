# api_server.py
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import datetime

# In‑memory storage
bookmarks = {}
next_id = 1

def get_timestamp():
    return datetime.datetime.utcnow().isoformat() + 'Z'

class Handler(BaseHTTPRequestHandler):
    def _send(self, code, payload=None):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        if payload is not None:
            self.wfile.write(json.dumps(payload).encode())

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/bookmarks':
            # optional tag filter
            qs = parse_qs(parsed.query)
            tag = qs.get('tag', [None])[0]
            result = []
            for bid, bm in bookmarks.items():
                if tag is None or tag in bm['tags']:
                    result.append({**bm, 'id': bid})
            self._send(200, result)
        elif parsed.path.startswith('/bookmarks/'):
            try:
                bid = int(parsed.path.split('/')[-1])
                bm = bookmarks[bid]
                self._send(200, {**bm, 'id': bid})
            except (ValueError, KeyError):
                self._send(404, {'error': 'Not found'})
        else:
            self._send(404, {'error': 'Invalid endpoint'})

    def do_POST(self):
        if self.path != '/bookmarks':
            self._send(404, {'error': 'Invalid endpoint'})
            return
        length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(length))
        global next_id
        bm = {
            'url': data['url'],
            'title': data.get('title', ''),
            'tags': data.get('tags', []),
            'created_at': get_timestamp()
        }
        bookmarks[next_id] = bm
        response = {**bm, 'id': next_id}
        next_id += 1
        self._send(201, response)

    def do_PUT(self):
        if not self.path.startswith('/bookmarks/'):
            self._send(404, {'error': 'Invalid endpoint'})
            return
        try:
            bid = int(self.path.split('/')[-1])
            if bid not in bookmarks:
                raise KeyError
        except (ValueError, KeyError):
            self._send(404, {'error': 'Not found'})
            return
        length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(length))
        bm = bookmarks[bid]
        bm.update({
            'url': data.get('url', bm['url']),
            'title': data.get('title', bm['title']),
            'tags': data.get('tags', bm['tags'])
        })
        self._send(200, {**bm, 'id': bid})

    def do_DELETE(self):
        if not self.path.startswith('/bookmarks/'):
            self._send(404, {'error': 'Invalid endpoint'})
            return
        try:
            bid = int(self.path.split('/')[-1])
            del bookmarks[bid]
            self._send(204)
        except (ValueError, KeyError):
            self._send(404, {'error': 'Not found'})

def run(server_class=HTTPServer, handler_class=Handler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Serving on port {port}…')
    httpd.serve_forever()

if __name__ == '__main__':
    run()

---
# openapi.yaml
openapi: 3.0.0
info:
  title: Bookmarks API
  version: 1.0.0
paths:
  /bookmarks:
    get:
      summary: List bookmarks (optionally filter by tag)
      parameters:
        - in: query
          name: tag
          schema:
            type: string
          description: Tag to filter bookmarks
      responses:
        '200':
          description: A list of bookmarks
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Bookmark'
    post:
      summary: Create a new bookmark
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/NewBookmark'
      responses:
        '201':
          description: Bookmark created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Bookmark'
  /bookmarks/{id}:
    parameters:
      - in: path
        name: id
        required: true
        schema:
          type: integer
    get:
      summary: Retrieve a bookmark by ID
      responses:
        '200':
          description: Bookmark data
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Bookmark'
        '404':
          description: Not found
    put:
      summary: Update a bookmark
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateBookmark'
      responses:
        '200':
          description: Updated bookmark
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Bookmark'
        '404':
          description: Not found
    delete:
      summary: Delete a bookmark
      responses:
        '204':
          description: Deleted
        '404':
          description: Not found
components:
  schemas:
    Bookmark:
      type: object
      properties:
        id:
          type: integer
          example: 1
        url:
          type: string
          format: uri
          example: https://example.com
        title:
          type: string
          example: Example Site
        tags:
          type: array
          items:
            type: string
          example: ["news","tech"]
        created_at:
          type: string
          format: date-time
          example: 2023-01-01T12:00:00Z
    NewBookmark:
      type: object
      required: [url]
      properties:
        url:
          type: string
          format: uri
          example: https://example.com
        title:
          type: string
          example: Example Site
        tags:
          type: array
          items:
            type: string
          example: ["news","tech"]
    UpdateBookmark:
      type: object
      properties:
        url:
          type: string
          format: uri
        title:
          type: string
        tags:
          type: array
          items:
            type: string
---
# test_script.py
import subprocess
import sys
import time
import json
import urllib.request
import urllib.error

SERVER_CMD = [sys.executable, 'api_server.py']
BASE_URL = 'http://localhost:8000'

def start_server():
    proc = subprocess.Popen(SERVER_CMD, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(1)  # give it a moment to start
    return proc

def stop_server(proc):
    proc.terminate()
    proc.wait()

def request(method, path, data=None, params=None):
    url = BASE_URL + path
    if params:
        q = urllib.parse.urlencode(params)
        url += '?' + q
    req = urllib.request.Request(url, method=method)
    if data is not None:
        body = json.dumps(data).encode()
        req.add_header('Content-Type', 'application/json')
        req.data = body
    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read()
            if resp_body:
                return resp.status, json.loads(resp_body)
            return resp.status, None
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

def assert_equal(a, b, msg):
    if a != b:
        raise AssertionError(f'{msg}: {a!r} != {b!r}')

def run_tests():
    # CREATE
    status, bm = request('POST', '/bookmarks', {'url': 'https://example.com', 'title': 'Ex', 'tags': ['test']})
    assert_equal(status, 201, 'Create status')
    bid = bm['id']
    # READ
    status, fetched = request('GET', f'/bookmarks/{bid}')
    assert_equal(status, 200, 'Read status')
    assert_equal(fetched['url'], 'https://example.com', 'Read url')
    # UPDATE
    status, updated = request('PUT', f'/bookmarks/{bid}', {'title': 'Example', 'tags': ['demo']})
    assert_equal(status, 200, 'Update status')
    assert_equal(updated['title'], 'Example', 'Updated title')
    # SEARCH by tag
    status, results = request('GET', '/bookmarks', params={'tag': 'demo'})
    assert_equal(status, 200, 'Search status')
    assert_equal(len(results), 1, 'Search count')
    # DELETE
    status, _ = request('DELETE', f'/bookmarks/{bid}')
    assert_equal(status, 204, 'Delete status')
    # VERIFY DELETE
    status, _ = request('GET', f'/bookmarks/{bid}')
    assert_equal(status, 404, 'Post-delete fetch')
    print('All tests passed')

if __name__ == '__main__':
    srv = start_server()
    try:
        run_tests()
    finally:
        stop_server(srv)
