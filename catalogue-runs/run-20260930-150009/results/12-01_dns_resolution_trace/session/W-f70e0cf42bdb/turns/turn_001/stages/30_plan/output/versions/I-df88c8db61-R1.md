TRACE the DNS resolution path for the target domain starting from an empty cache
FOR each hierarchy level (root, TLD, authoritative) DO
SEND a DNS query over UDP to the appropriate nameserver
RECEIVE and RECORD the DNS response
IF the response contains a delegation THEN
EXTRACT the next‑level nameserver addresses
ENDIF
IF the response contains a CNAME record THEN
NOTE the alias target and CONTINUE resolution for the canonical name
ENDIF
ENDFOR
DISPLAY the sequence of queries and responses, indicating the nameserver queried and the records returned at each step
DESCRIBE how CNAME handling redirects the lookup to the canonical name and how subsequent queries follow the same resolution process
IMPLEMENT a simplified iterative DNS resolver in Python that
CREATES UDP sockets without using high‑level libraries
FORMULATES DNS query messages for the target name
SENDS queries to the appropriate nameserver addresses
PARSES received DNS responses to extract answer, authority, and additional sections
FOLLOWS delegations iteratively until an answer is obtained or a CNAME is encountered
HANDLES CNAME by restarting the lookup for the canonical name
RETURNS the final resolution result and a log of each query/response pair
