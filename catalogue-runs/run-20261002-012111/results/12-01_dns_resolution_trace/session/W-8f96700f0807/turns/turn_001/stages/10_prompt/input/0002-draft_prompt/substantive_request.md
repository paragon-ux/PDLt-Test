TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Trace the complete DNS resolution path for the domain "api.staging.example.com" starting from a cold cache. Show each query and response at the root nameserver, TLD nameserver, and authoritative nameserver. Explain CNAME handling if the domain is an alias. Implement a simplified iterative DNS resolver in Python that uses only UDP sockets, without relying on dnspython or socket.getaddrinfo.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- api.staging.example.com
