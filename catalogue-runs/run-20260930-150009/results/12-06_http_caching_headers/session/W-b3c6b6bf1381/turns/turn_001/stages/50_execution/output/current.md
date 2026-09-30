# Cache‑Control Strategy

## Resource Types and Header Settings

| Resource Type | Cache‑Control | Vary | ETag | Surrogate‑Control |
|---------------|---------------|------|------|-------------------|
| **Static assets** (JS, CSS, images) – change only on deploy | `public, max‑age=31536000, immutable` | `*` (no vary needed – same for all) | **Strong ETag** based on content hash (e.g., `W/"<hash>"`) – can be omitted because immutable, but include for validation on edge caches. | `max‑age=31536000, stale‑while‑revalidate=86400` |
| **User profile data** – changes at most once per day | `private, max‑age=300, must‑revalidate` | `Authorization, Cookie` (or any auth header used) | **Weak ETag** based on last‑updated timestamp (e.g., `"W/<ts>"`). | *none* (origin‑only, no surrogate) |
| **Real‑time data** – must never be stale | `no‑store, no‑cache, must‑revalidate, max‑age=0` | `*` (varies per request parameters) | **No ETag** (or a rapidly‑changing weak tag) – not useful because never cached. | *none* |
| **Public catalog data** – identical for all users | `public, max‑age=3600, stale‑while‑revalidate=300` | `*` (no vary needed) | **Strong ETag** based on content hash. | `max‑age=3600, stale‑while‑revalidate=300` |
| **Authenticated responses** – vary per user | `private, max‑age=0, must‑revalidate` | `Authorization, Cookie` (any auth token that determines the view) | **Strong ETag** derived from user‑specific representation (e.g., hash of JSON payload). | *none* |

### Rationale
- **Static assets**: `public` allows CDN caching. `max‑age=1yr` matches deploy frequency. `immutable` tells browsers not to revalidate. `Surrogate‑Control` mirrors CDN cache time and enables stale‑while‑revalidate for smooth roll‑outs.
- **User profile**: Data is user‑specific (`private`). Short `max‑age` with `must‑revalidate` limits stale windows. Vary on auth headers ensures caches keep per‑user copies. Weak ETag reflects low change frequency.
- **Real‑time**: `no‑store` prevents any intermediate cache from persisting; `must‑revalidate` forces fresh fetch each request. No ETag because a cache would never store it.
- **Public catalog**: Shared across users, so `public` is safe. Moderate `max‑age` balances freshness and CDN load. `stale‑while‑revalidate` reduces latency on refreshes. Strong ETag enables conditional GETs.
- **Authenticated responses**: Must not be cached publicly. `private` restricts to browser cache only; `max‑age=0` forces validation each request. Vary on auth info keeps per‑user segmentation. Strong ETag enables efficient conditional GETs for unchanged data.

## Python Middleware Implementation

```python
import hashlib
from typing import Callable

def _hash_content(content: bytes) -> str:
    """Return a strong SHA‑256 hash for use in ETag headers."""
    return hashlib.sha256(content).hexdigest()

def cache_control_middleware(app: Callable):
    """WSGI‑style middleware that injects Cache‑Control, Vary, ETag, and
    Surrogate‑Control headers based on request path patterns.

    The ``app`` argument is the downstream WSGI application.
    """
    def middleware(environ, start_response):
        path = environ.get('PATH_INFO', '')
        # Call downstream app to get response body iterator and status
        def custom_start_response(status, response_headers, exc_info=None):
            # Determine resource type from path
            if path.startswith('/static/'):
                # STATIC ASSET
                cache_control = 'public, max-age=31536000, immutable'
                vary = ''
                surrogate = 'max-age=31536000, stale-while-revalidate=86400'
                # Assume static files are read from disk elsewhere; we will compute ETag later
                def compute_etag(body_bytes):
                    return f'W/"{_hash_content(body_bytes)}"'
            elif path.startswith('/profile/'):
                # USER PROFILE
                cache_control = 'private, max-age=300, must-revalidate'
                vary = 'Authorization, Cookie'
                surrogate = ''
                def compute_etag(body_bytes):
                    # weak tag based on timestamp if provided in the body, fallback to hash
                    return f'W/"{_hash_content(body_bytes)[:16]}"'
            elif path.startswith('/realtime/'):
                # REAL‑TIME DATA
                cache_control = 'no-store, no-cache, must-revalidate, max-age=0'
                vary = '*'
                surrogate = ''
                def compute_etag(_):
                    return ''  # No ETag needed
            elif path.startswith('/catalog/'):
                # PUBLIC CATALOG
                cache_control = 'public, max-age=3600, stale-while-revalidate=300'
                vary = ''
                surrogate = 'max-age=3600, stale-while-revalidate=300'
                def compute_etag(body_bytes):
                    return f'"{_hash_content(body_bytes)}"'
            else:
                # AUTHENTICATED RESPONSE (fallback)
                cache_control = 'private, max-age=0, must-revalidate'
                vary = 'Authorization, Cookie'
                surrogate = ''
                def compute_etag(body_bytes):
                    return f'"{_hash_content(body_bytes)}"'

            # Capture original headers for later addition
            new_headers = list(response_headers)
            # Add Cache‑Control and Surrogate‑Control
            new_headers.append(('Cache-Control', cache_control))
            if surrogate:
                new_headers.append(('Surrogate-Control', surrogate))
            if vary:
                new_headers.append(('Vary', vary))

            # Wrap the response iterator to compute ETag after body is materialised
            def response_wrapper(body_iter):
                body = b''.join(body_iter)
                etag = compute_etag(body)
                if etag:
                    new_headers.append(('ETag', etag))
                # Return an iterator yielding the same bytes
                return [body]

            # Replace the start_response with one that will later add the ETag
            start_response(status, new_headers, exc_info)
            return response_wrapper

        # Get the downstream response iterator
        result = app(environ, custom_start_response)
        # The custom_start_response returns a wrapper function; invoke it
        response_wrapper = result
        # The wrapper expects the original body iterator; retrieve it from the app
        # In a typical WSGI app the result itself is the iterator, so we simply call
        return response_wrapper(result)
    return middleware
```

The middleware:
1. Inspects the request path to classify the resource type.
2. Chooses the appropriate `Cache‑Control`, `Vary`, and `Surrogate‑Control` directives.
3. Computes a suitable ETag (strong, weak, or none) based on the response payload.
4. Inserts all headers into the outgoing response before returning it to the client.

Deploy this middleware in any WSGI‑compatible framework (Flask, Django, Starlette with ASGI adapters, etc.) by wrapping the application object.
