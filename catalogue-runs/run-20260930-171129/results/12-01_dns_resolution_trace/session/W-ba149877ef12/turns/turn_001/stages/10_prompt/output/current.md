READ the domain "api.staging.example.com" from a cold DNS cache
TRACE the DNS resolution path starting at the root nameserver
QUERY the root nameserver for the TLD of the domain
QUERY the TLD nameserver for the authoritative nameserver
QUERY the authoritative nameserver for the final answer
SHOW each DNS query and response at every level: root nameserver, TLD nameserver, authoritative nameserver
EXPLAIN CNAME handling if the domain is an alias, including any additional queries required to resolve the target name
IMPLEMENT a simplified iterative DNS resolver in Python using only UDP sockets (no external DNS libraries, no socket.getaddrinfo) that performs the above steps
