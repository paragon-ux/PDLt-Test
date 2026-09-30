# server.py
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

class BookmarkStore:
    def __init__(self):
        self._data = {}
        self._next_id = 1
    def create(self, bookmark):
        bid = str(self._next_id)
        self._next_id += 1
        bookmark['id'] = bid
        bookmark['created_at'] = datetime.utcnow().isoformat() + 'Z'
        self._data[bid] = bookmark
        return bookmark
    def read(self, bid):
        return self._data.get(bid)
    def update(self, bid, bookmark):
        if bid not in self._data:
            return None
        # keep immutable fields
        existing = self._data[bid]
        existing.update({k: v for k, v in bookmark.items() if k != 'id' and k != 'created_at'})
        return existing
    def delete(self, bid):
        return self._data.pop(bid, None)
    def list_by_tag(self, tag):
        return [b for b in self._data.values() if tag in b.get('tags', [])]

store = BookmarkStore()

class BookmarkHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        body = json.dumps(data).encode('utf8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _parse_path(self):
        parts = self.path.split('?', 1)
        path = parts[0]
        query = urllib.parse.parse_qs(parts[1]) if len(parts) > 1 else {}
        return path, query

    def do_POST(self):
        path, _ = self._parse_path()
        if path != '/bookmarks':
            self.send_error(404)
            return
        length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(length))
        created = store.create(data)
        self._send_json(created, status=201)

    def do_GET(self):
        path, query = self._parse_path()
        if path.startswith('/bookmarks/'):  # read single
            bid = path.split('/')[-1]
            bookmark = store.read(bid)
            if bookmark:
                self._send_json(bookmark)
            else:
                self.send_error(404)
            return
        if path == '/bookmarks' and 'tag' in query:
            tag = query['tag'][0]
            results = store.list_by_tag(tag)
            self._send_json(results)
            return
        self.send_error(404)

    def do_PUT(self):
        path, _ = self._parse_path()
        if not path.startswith('/bookmarks/'):
            self.send_error(404)
            return
        bid = path.split('/')[-1]
        length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(length))
        updated = store.update(bid, data)
        if updated:
            self._send_json(updated)
        else:
            self.send_error(404)

    def do_DELETE(self):
        path, _ = self._parse_path()
        if not path.startswith('/bookmarks/'):
            self.send_error(404)
            return
        bid = path.split('/')[-1]
        deleted = store.delete(bid)
        if deleted:
            self.send_response(204)
            self.end_headers()
        else:
            self.send_error(404)

def run(server_class=HTTPServer, handler_class=BookmarkHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Serving on port {port}')
    httpd.serve_forever()

if __name__ == '__main__':
    run()

# openapi.yaml
openapi: 3.0.0
info:
  title: Bookmarks API
  version: "1.0"
paths:
  /bookmarks:
    post:
      summary: Create a bookmark
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/BookmarkInput'
      responses:
        '201':
          description: Created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Bookmark'
    get:
      summary: Search bookmarks by tag
      parameters:
        - in: query
          name: tag
          schema:
            type: string
          required: true
          description: Tag to filter bookmarks
      responses:
        '200':
          description: List of bookmarks
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Bookmark'
  /bookmarks/{id}:
    get:
      summary: Retrieve a bookmark
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Bookmark
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Bookmark'
        '404':
          description: Not found
    put:
      summary: Update a bookmark
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/BookmarkInput'
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
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: string
      responses:
        '204':
          description: No Content
        '404':
          description: Not found
components:
  schemas:
    BookmarkInput:
      type: object
      required:
        - url
        - title
        - tags
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
    Bookmark:
      allOf:
        - $ref: '#/components/schemas/BookmarkInput'
        - type: object
          properties:
            id:
              type: string
              example: "1"
            created_at:
              type: string
              format: date-time
              example: "2023-01-01T12:00:00Z"

# test.py
import json
import urllib.request
import urllib.parse
import threading
import time
import subprocess
import sys

SERVER_PORT = 8000
BASE_URL = f'http://localhost:{SERVER_PORT}'

def start_server():
    # Run server.py as a subprocess
    proc = subprocess.Popen([sys.executable, 'server.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Wait a moment for it to start
    time.sleep(1)
    return proc

def stop_server(proc):
    proc.terminate()
    proc.wait()

def http_request(method, path, data=None, params=None):
    url = BASE_URL + path
    if params:
        url += '?' + urllib.parse.urlencode(params)
    if data is not None:
        body = json.dumps(data).encode('utf-8')
        headers = {'Content-Type': 'application/json'}
    else:
        body = None
        headers = {}
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    with urllib.request.urlopen(req) as resp:
        resp_body = resp.read()
        if resp_body:
            return json.loads(resp_body)
        return None

def assert_equal(a, b, msg):
    if a != b:
        raise AssertionError(f'{msg}: {a} != {b}')

def run_tests():
    # CREATE
    bm = {
        'url': 'https://example.com',
        'title': 'Example',
        'tags': ['test', 'example']
    }
    created = http_request('POST', '/bookmarks', bm)
    assert_equal(created['url'], bm['url'], 'Create url')
    bid = created['id']

    # READ
    fetched = http_request('GET', f'/bookmarks/{bid}')
    assert_equal(fetched['id'], bid, 'Read id')

    # UPDATE
    update_data = {'title': 'Updated Title', 'tags': ['updated']}
    updated = http_request('PUT', f'/bookmarks/{bid}', update_data)
    assert_equal(updated['title'], 'Updated Title', 'Update title')

    # SEARCH by tag
    results = http_request('GET', '/bookmarks', params={'tag': 'updated'})
    assert isinstance(results, list) and any(item['id'] == bid for item in results), 'Search result'

    # DELETE
    http_request('DELETE', f'/bookmarks/{bid}')
    try:
        http_request('GET', f'/bookmarks/{bid}')
        raise AssertionError('Delete did not remove')
    except urllib.error.HTTPError as e:
        assert e.code == 404
    print('All tests passed')

if __name__ == '__main__':
    proc = start_server()
    try:
        run_tests()
    finally:
        stop_server(proc)
