READ the Python module that defines DB_HOST, DB_PORT, _cache, _request_count, get_connection, query, get_stats, and reset.
IDENTIFY global mutable state elements such as DB_HOST, DB_PORT, _cache, and _request_count.
DEFINE a DatabaseProvider interface that supplies the connection string.
DEFINE a Cache interface that provides query caching behavior and tracks request statistics.
DESIGN the DatabaseProvider and Cache interfaces to be injectable and mockable for testing.
REPLACE usage of DB_HOST and DB_PORT with a DatabaseProvider instance passed to functions.
REPLACE usage of _cache and _request_count with a Cache instance passed to functions.
MODIFY get_connection to obtain the connection string from the injected DatabaseProvider.
MODIFY query to use the injected Cache for caching query results.
MODIFY get_stats to report request statistics using the injected Cache.
MODIFY reset to reset state via the injected components.
VERIFY that the refactored functions preserve the original behavior regarding connection string, query caching, request statistics, and state resetting.
