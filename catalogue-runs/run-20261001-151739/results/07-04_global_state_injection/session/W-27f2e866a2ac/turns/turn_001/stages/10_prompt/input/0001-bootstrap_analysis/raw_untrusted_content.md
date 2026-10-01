The following module uses global mutable state. Refactor it to use dependency injection so that the module is testable in isolation.

`python
import os, time

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', '5432'))
_cache = {}
_request_count = 0

def get_connection():
    return f"postgresql://{DB_HOST}:{DB_PORT}/mydb"

def query(sql):
    global _request_count
    _request_count += 1
    if sql in _cache:
        return _cache[sql]
    conn = get_connection()
    result = f"[result of '{sql}' from {conn}]"
    _cache[sql] = result
    return result

def get_stats():
    return {'requests': _request_count, 'cache_size': len(_cache), 'host': DB_HOST}

def reset():
    global _cache, _request_count
    _cache = {}
    _request_count = 0
`

After refactoring, tests should be able to inject a mock database and verify query behavior without setting environment variables or touching globals.
