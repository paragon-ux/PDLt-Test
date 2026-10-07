```python
import os

class Config:
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', '5432'))

_cache = {}
_request_count = 0

def query(sql, get_connection=lambda: f"postgresql://{Config.DB_HOST}:{Config.DB_PORT}/mydb"):
    global _request_count
    _request_count += 1
    if sql in _cache: return _cache[sql]
    result = f"[result of '{sql}' from {get_connection()}]"
    _cache[sql] = result
    return result
```
The connection is now injectable through `get_connection`, so tests can pass a mock connection function.
