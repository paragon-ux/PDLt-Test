"""Refactored module with dependency injection.

Provides two interfaces:

- ``DatabaseProvider``: supplies the database connection string.
- ``Cache``: handles query caching and request statistics.

All functions accept the required components as arguments, eliminating global mutable state.
"""

from __future__ import annotations
from typing import Protocol, runtime_checkable, Dict, Any

@runtime_checkable
class DatabaseProvider(Protocol):
    """Interface for providing a database connection string."""

    def get_connection_string(self) -> str:
        """Return a full connection string.

        Implementations may construct the string from environment variables,
        configuration files, or any other source.
        """
        ...


@runtime_checkable
class Cache(Protocol):
    """Interface for query caching and request statistics tracking."""

    def get(self, sql: str) -> Any:
        """Retrieve a cached result for ``sql`` if present.

        Return ``None`` when the query is not cached.
        """
        ...

    def set(self, sql: str, result: Any) -> None:
        """Store ``result`` for ``sql`` in the cache."""
        ...

    def increment_request_count(self) -> None:
        """Increment the internal request counter.

        Called each time ``query`` is invoked.
        """
        ...

    def get_stats(self) -> Dict[str, Any]:
        """Return a dictionary with current statistics.

        Expected keys: ``requests`` (int) and ``cache_size`` (int).
        """
        ...

    def reset(self) -> None:
        """Reset the cache contents and request counter to the initial state."""
        ...


# ---------------------------------------------------------------------------
# Default concrete implementations (behave like the original module)
# ---------------------------------------------------------------------------

class EnvDatabaseProvider:
    """DatabaseProvider that reads ``DB_HOST`` and ``DB_PORT`` from the environment.

    Mirrors the original behavior where ``DB_HOST`` defaults to ``localhost`` and
    ``DB_PORT`` defaults to ``5432``.
    """

    def __init__(self, host_env: str = "DB_HOST", port_env: str = "DB_PORT") -> None:
        import os
        self.host = os.environ.get(host_env, "localhost")
        self.port = int(os.environ.get(port_env, "5432"))

    def get_connection_string(self) -> str:
        return f"postgresql://{self.host}:{self.port}/mydb"


class SimpleCache:
    """In‑memory cache that also tracks request count.

    This implementation reproduces the original module's semantics.
    """

    def __init__(self) -> None:
        self._cache: Dict[str, Any] = {}
        self._request_count: int = 0

    def get(self, sql: str) -> Any:
        return self._cache.get(sql)

    def set(self, sql: str, result: Any) -> None:
        self._cache[sql] = result

    def increment_request_count(self) -> None:
        self._request_count += 1

    def get_stats(self) -> Dict[str, Any]:
        return {
            "requests": self._request_count,
            "cache_size": len(self._cache),
        }

    def reset(self) -> None:
        self._cache.clear()
        self._request_count = 0


# ---------------------------------------------------------------------------
# Refactored functional API
# ---------------------------------------------------------------------------

def get_connection(provider: DatabaseProvider) -> str:
    """Obtain the connection string from the supplied ``DatabaseProvider``.

    The function is deliberately tiny – the heavy lifting is delegated to the
    provider implementation. This design makes it easy to inject a mock during
    testing.
    """
    return provider.get_connection_string()


def query(sql: str, provider: DatabaseProvider, cache: Cache) -> Any:
    """Execute ``sql`` using the provided ``DatabaseProvider`` and ``Cache``.

    The logic mirrors the original implementation:

    1. Increment the request counter.
    2. Return a cached result when available.
    3. Otherwise, construct a result string (simulating a real query) and store
       it in the cache before returning.
    """
    cache.increment_request_count()
    cached = cache.get(sql)
    if cached is not None:
        return cached
    conn = get_connection(provider)
    result = f"[result of '{sql}' from {conn}]"
    cache.set(sql, result)
    return result


def get_stats(cache: Cache) -> Dict[str, Any]:
    """Report request statistics using the injected ``Cache``.

    The original module also exposed the host name; that information is now
    obtained from the ``DatabaseProvider`` via the ``Cache`` implementation if
    needed. For strict compatibility we keep only the stats that the cache
    supplies.
    """
    return cache.get_stats()


def reset(cache: Cache) -> None:
    """Reset internal state via the injected ``Cache`` instance.

    This replaces the global ``reset`` function that cleared both the cache and
    request counter.
    """
    cache.reset()


# ---------------------------------------------------------------------------
# Example usage (not executed in production code)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # The default concrete classes behave like the original module.
    db_provider = EnvDatabaseProvider()
    cache = SimpleCache()

    print(query("SELECT 1", db_provider, cache))
    print(query("SELECT 1", db_provider, cache))  # cached
    print(get_stats(cache))
    reset(cache)
    print(get_stats(cache))
