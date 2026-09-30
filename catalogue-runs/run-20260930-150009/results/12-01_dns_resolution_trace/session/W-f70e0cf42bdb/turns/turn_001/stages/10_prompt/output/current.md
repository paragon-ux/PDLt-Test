TRACE the complete DNS resolution path for "api.staging.example.com" starting from a cold cache
SHOW every DNS query and response at each hierarchy level: root nameserver, TLD nameserver, authoritative nameserver
EXPLAIN CNAME handling if the domain is an alias
IMPLEMENT a simplified iterative DNS resolver in Python that performs this resolution using only UDP sockets (no dnspython, no socket.getaddrinfo)
