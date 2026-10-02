TRACE the DNS resolution path for the domain "api.staging.example.com" starting from a cold cache.
DISPLAY each DNS query and response at the root nameserver, the TLD nameserver, and the authoritative nameserver.
EXPLAIN CNAME handling if the domain is an alias.
IMPLEMENT a simplified iterative DNS resolver in Python using only UDP sockets, WITHOUT using dnspython or socket.getaddrinfo.
OUTPUT the Python code that performs the iterative resolution and prints the queries and responses as described.
