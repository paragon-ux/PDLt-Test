import typing

class Database:
    """Simple database connection holder.

    Parameters
    ----------
    host: str
        Database host name.
    port: int
        Database port number.
    """
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def get_connection(self) -> str:
        """Return a connection string.

        The format mirrors the original implementation:
        ``postgresql://{host}:{port}/mydb``.
        """
        return f"postgresql://{self.host}:{self.port}/mydb"

class QueryService:
    """Service that performs queries using injected state.

    Parameters
    ----------
    db: Database
        The database provider.
    cache: dict[str, str]
        Mapping from SQL string to cached result.
    request_counter: typing.MutableMapping[str, int]
        Mutable mapping used to store the request count. The mapping must
        contain the key ``'count'``; the service increments this value on
        each call to :meth:`query`.
    """
    def __init__(
        self,
        db: Database,
        cache: dict[str, str] | None = None,
        request_counter: typing.MutableMapping[str, int] | None = None,
    ) -> None:
        self.db = db
        self._cache = cache if cache is not None else {}
        # Using a mutable holder allows the count to be shared across
        # injected instances if required.
        self._request_counter = request_counter if request_counter is not None else {"count": 0}

    def query(self, sql: str) -> str:
        """Execute *sql* and return a formatted result.

        The function increments the injected request counter, caches the
        result, and returns a string identical to the original behaviour:
        ``[result of '{sql}' from {conn}]`` where *conn* is the connection
        string from :meth:`Database.get_connection`.
        """
        # Increment request count
        self._request_counter["count"] += 1

        # Return cached result if present
        if sql in self._cache:
            return self._cache[sql]

        conn = self.db.get_connection()
        result = f"[result of '{sql}' from {conn}]"
        self._cache[sql] = result
        return result

    def get_stats(self) -> dict[str, typing.Any]:
        """Return statistics mirroring the original module.

        Returns a dictionary with keys:
        * ``requests`` – total number of queries performed.
        * ``cache_size`` – number of cached entries.
        * ``host`` – the injected database host.
        """
        return {
            "requests": self._request_counter.get("count", 0),
            "cache_size": len(self._cache),
            "host": self.db.host,
        }

    def reset(self) -> None:
        """Reset the injected state to its initial values.

        Clears the cache and sets the request counter back to zero.
        """
        self._cache.clear()
        self._request_counter["count"] = 0

# Example usage (for illustration only; not executed in tests)
# db = Database(host="localhost", port=5432)
# service = QueryService(db)
# print(service.query("SELECT 1"))
# print(service.get_stats())
# service.reset()
