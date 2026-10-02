# Cache‑Control Header Strategy

The table below lists the exact header values for each of the five resource categories and the rationale for each directive.

| Resource Type | Cache‑Control | Vary | ETag | Surrogate‑Control | Rationale |
|---------------|---------------|------|------|-------------------|----------|
| **Static assets** (JS, CSS, images) – change only on deploy | `public, max-age=31536000, immutable` | `*` (no vary – same for all) | `W/"{{asset‑hash}}"` (strong validator based on build hash) | `public, max-age=31536000, stale‑while‑revalidate=86400` | Assets are immutable after deployment; long max‑age caches them forever. `immutable` tells browsers not to revalidate. CDN can serve stale content for a day while revalidating.
| **User profile data** – changes at most once per day | `private, max-age=86400, must-revalidate` | `Authorization, Cookie` | `W/"{{profile‑version}}"` (weak validator that changes when profile updates) | `private, max-age=86400, stale‑while‑revalidate=3600` | Private because it contains user‑specific data. One‑day max‑age matches update frequency; `must-revalidate` forces a fresh check after expiry. CDN keeps stale copy for an hour while revalidating to reduce load.
| **Real‑time data** (stock prices, live scores) – must never be stale | `no-store, no-cache, must-revalidate` | `*` (no vary needed – same for all) | `W/"{{timestamp}}"` (weak ETag that changes every response) | `no-store` | Real‑time data must be fetched on every request; `no-store` prevents any caching, `must‑revalidate` adds a safety net. CDN is instructed not to cache.
| **Public catalog data** – same for all users | `public, max-age=300, stale‑while‑revalidate=60` | `*` (no vary) | `W/"{{catalog‑hash}}"` (strong validator based on dataset hash) | `public, max-age=300, stale‑while‑revalidate=60` | Frequently read but infrequently changed; 5‑minute max‑age gives good freshness while allowing CDN to serve stale for a minute while revalidating.
| **Authenticated responses** – vary by user | `private, no-cache, must-revalidate` | `Authorization, Cookie` | `W/"{{user‑session‑id}}-{{rev}}"` (weak validator that includes user‑specific revision) | `private, no-cache, must-revalidate` | Must not be cached for other users; `no-cache` forces revalidation on each request, `private` ensures CDN stores per‑user copies only if it can isolate them (most CDNs treat private as non‑shareable). |

---

## Python Middleware Implementation

The following middleware can be used with any ASGI‑compatible framework (e.g., FastAPI, Starlette). It inspects a custom attribute `response.resource_type` that the view sets to one of the five identifiers (`static`, `profile`, `realtime`, `catalog`, `auth`). Based on that attribute it applies the header set defined above.

```python
from typing import Callable, Awaitable
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.responses import Response

# Header specifications mapped by resource type
HEADER_SPECS = {
    "static": {
        "Cache-Control": "public, max-age=31536000, immutable",
        "Vary": "*",
        "ETag": lambda resp: f'W/"{resp.get("X-Asset-Hash", "unknown")}"',
        "Surrogate-Control": "public, max-age=31536000, stale-while-revalidate=86400",
    },
    "profile": {
        "Cache-Control": "private, max-age=86400, must-revalidate",
        "Vary": "Authorization, Cookie",
        "ETag": lambda resp: f'W/"{resp.get("X-Profile-Version", "v0")}"',
        "Surrogate-Control": "private, max-age=86400, stale-while-revalidate=3600",
    },
    "realtime": {
        "Cache-Control": "no-store, no-cache, must-revalidate",
        "Vary": "*",
        "ETag": lambda resp: f'W/"{resp.get("X-Timestamp", "0")}"',
        "Surrogate-Control": "no-store",
    },
    "catalog": {
        "Cache-Control": "public, max-age=300, stale-while-revalidate=60",
        "Vary": "*",
        "ETag": lambda resp: f'W/"{resp.get("X-Catalog-Hash", "unknown")}"',
        "Surrogate-Control": "public, max-age=300, stale-while-revalidate=60",
    },
    "auth": {
        "Cache-Control": "private, no-cache, must-revalidate",
        "Vary": "Authorization, Cookie",
        "ETag": lambda resp: f'W/"{resp.get("X-User-Rev", "0")}"',
        "Surrogate-Control": "private, no-cache, must-revalidate",
    },
}

class CacheControlMiddleware:
    """ASGI middleware that adds Cache‑Control, Vary, ETag, and Surrogate‑Control
    headers according to the response's ``resource_type`` attribute.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> Awaitable[None]:
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                # The downstream handler may have attached a ``resource_type``
                # attribute to the scope (or to the response object). We look for it.
                resource_type = scope.get("resource_type")
                if not resource_type:
                    # Fallback: inspect a custom header that a view could set.
                    resource_type = dict(message.get("headers", []))
                    # Header keys are bytes; decode and lower‑case.
                    for k, v in message.get("headers", []):
                        if k.decode().lower() == "x-resource-type":
                            resource_type = v.decode()
                            break
                spec = HEADER_SPECS.get(resource_type)
                if spec:
                    # Apply static headers
                    for name, value in spec.items():
                        if name == "ETag":
                            # ETag may be a callable that derives a value from headers
                            etag_val = value(message) if callable(value) else value
                            headers[b"etag"] = etag_val.encode()
                        else:
                            headers[name.lower().encode()] = value.encode()
                    # Re‑build the header list preserving the original order plus additions
                    message["headers"] = [(k, v) for k, v in headers.items()]
            await send(message)

        await self.app(scope, receive, send_wrapper)
```

### How to Use

```python
from fastapi import FastAPI, Response
from cache_middleware import CacheControlMiddleware

app = FastAPI()
app.add_middleware(CacheControlMiddleware)

@app.get("/static/{filename}")
async def static_asset(filename: str):
    resp = Response(content="...binary data...", media_type="application/octet-stream")
    resp.headers["X-Asset-Hash"] = "abcd1234"  # build hash
    # inform middleware
    resp.scope["resource_type"] = "static"
    return resp
```

The middleware inspects the `resource_type` set by the view, looks up the specification, and injects the exact header values defined in the table above.
