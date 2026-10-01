READ the DNS resolution request for domain "api.staging.example.com" starting from a cold cache
TRACE the query sequence to the root nameserver
QUERY the root nameserver for the NS records of the TLD
TRACE the query to the TLD nameserver
QUERY the TLD nameserver for the authoritative NS records of the domain
TRACE the query to the authoritative nameserver
REQUEST the A (or AAAA) record from the authoritative nameserver
IF the domain is a CNAME alias THEN REQUEST the target name's record and INCLUDE the CNAME resolution steps
OUTPUT each DNS query and response at every level in chronological order
IMPLEMENT a simplified iterative DNS resolver in Python using only UDP sockets without external libraries such as dnspython or socket.getaddrinfo
ENSURE the resolver follows the iterative process, handling referrals and CNAME chaining as described
RETURN the complete resolution trace as text
