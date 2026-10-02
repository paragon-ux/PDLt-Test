DESIGN injection points for DB_HOST, DB_PORT, cache, and request count.
REFRACTOR get_connection to accept DB_HOST and DB_PORT parameters and construct its connection string.
REFRACTOR query to accept sql argument, injected connection, request count, and cache.
    INCREMENT the injected request count.
    CACHE the query result in the injected cache.
    RETURN a result string formatted as "[result of '{sql}' from {conn}]".
REFRACTOR get_stats to accept injected request count, cache, and DB_HOST and RETURN a dictionary with keys 'requests', 'cache_size', and 'host' mapping to the injected values.
REFRACTOR reset to accept injected request count and cache and RESET them to their initial states.
REMOVE all module-level global references and environment variable lookups.
WRITE unit tests that instantiate the module with injected dependencies and verify behavior matches the original external contract.
ENSURE the refactored code is testable in isolation and preserves original function semantics.
