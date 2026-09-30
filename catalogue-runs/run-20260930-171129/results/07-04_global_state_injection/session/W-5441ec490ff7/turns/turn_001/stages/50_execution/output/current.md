import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

# Dependency injection context
@dataclass
class DBContext:
    host: str = field(default_factory=lambda: os.environ.get('DB_HOST', 'localhost'))
    port: int = field(default_factory=lambda: int(os.environ.get('DB_PORT', '5432')))
    cache: Dict[str, str] = field(default_factory=dict)
    request_count: int = 0

    def connection_string(self) -> str:
        return f"postgresql://{self.host}:{self.port}/mydb"

# Helper to obtain a context; callers can provide their own for testing
def _get_context(provided: Optional[DBContext] = None) -> DBContext:
    return provided if provided is not None else DBContext()

# Public API – signatures unchanged
def get_connection(context: Optional[DBContext] = None) -> str:
    """Return a PostgreSQL connection string.
    In production the context is created from environment variables.
    Tests can inject a mock DBContext.
    """
    ctx = _get_context(context)
    return ctx.connection_string()

def query(sql: str, *, context: Optional[DBContext] = None) -> str:
    """Execute a SQL query with caching.
    The function increments a request counter and caches results per context.
    """
    ctx = _get_context(context)
    ctx.request_count += 1
    if sql in ctx.cache:
        return ctx.cache[sql]
    conn = ctx.connection_string()
    result = f"[result of '{sql}' from {conn}]"
    ctx.cache[sql] = result
    return result

def get_stats(context: Optional[DBContext] = None) -> Dict[str, Any]:
    """Return statistics about requests and cache size.
    The host information comes from the context.
    """
    ctx = _get_context(context)
    return {
        'requests': ctx.request_count,
        'cache_size': len(ctx.cache),
        'host': ctx.host,
    }

def reset(context: Optional[DBContext] = None) -> None:
    """Reset cache and request counter for the given context.
    If no context is supplied a fresh one is created (no‑op on the caller).
    """
    if context is None:
        # No external context to reset – nothing to do.
        return
    context.cache.clear()
    context.request_count = 0

# Example usage (production):
# ctx = DBContext()
# print(get_connection(ctx))
# print(query('SELECT 1', context=ctx))
# print(get_stats(ctx))
# reset(ctx)

# Example usage (testing):
# mock_ctx = DBContext(host='mockhost', port=1234)
# assert query('SELECT 1', context=mock_ctx) == "[result of 'SELECT 1' from postgresql://mockhost:1234/mydb]"
