import typing

class DBConfig:
    """Configuration holder for dependency injection.

    Attributes
    ----------
    host: str
        Database host.
    port: int
        Database port.
    connection_factory: typing.Callable[[str, int], str]
        Callable that creates a connection string or connection object given host and port.
    cache: dict
        Cache object used to store query results.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        connection_factory: typing.Callable[[str, int], str] | None = None,
        cache: dict | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.connection_factory = connection_factory or self._default_connection_factory
        self.cache = cache if cache is not None else {}
        self._request_count = 0

    def _default_connection_factory(self, host: str, port: int) -> str:
        """Default factory returning a simple connection string.
        This can be replaced with a real database connector in production.
        """
        return f"postgresql://{host}:{port}/mydb"

    def get_connection(self) -> str:
        """Return a database connection string or object.
        The implementation is delegated to the injected ``connection_factory``.
        """
        return self.connection_factory(self.host, self.port)

    def increment_request_count(self) -> None:
        self._request_count += 1

    def get_request_count(self) -> int:
        return self._request_count

    def reset(self) -> None:
        """Reset mutable state to its initial condition.
        This clears the cache and request counter.
        """
        self.cache.clear()
        self._request_count = 0

# Global default configuration – retained for backward compatibility.
_default_config = DBConfig()

# Public API – wrappers that preserve the original signatures.

def get_connection() -> str:
    """Public function preserving the original ``get_connection`` signature.
    Internally forwards to the injected configuration.
    """
    return default_config.get_connection()

def query(sql: str) -> str:
    """Execute a query with request counting and caching.

    Parameters
    ----------
    sql: str
        The SQL statement to execute.
    """
    default_config.increment_request_count()
    if sql in default_config.cache:
        return default_config.cache[sql]
    conn = default_config.get_connection()
    # Simulated result – in real usage replace with actual DB call.
    result = f"[result of '{sql}' from {conn}]"
    default_config.cache[sql] = result
    return result

def get_stats() -> dict:
    """Return statistics about request count and cache size.
    The host information comes from the injected configuration.
    """
    return {
        "requests": default_config.get_request_count(),
        "cache_size": len(default_config.cache),
        "host": default_config.host,
    }

def reset() -> None:
    """Reset the module's state – clears cache and request counter.
    """
    default_config.reset()

# Helper to allow callers (including tests) to replace the default configuration.
def set_config(config: DBConfig) -> None:
    """Inject a custom ``DBConfig`` instance for testing or alternative backends.
    """
    global default_config
    default_config = config
