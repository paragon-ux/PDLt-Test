DEFINE the target domain "api.staging.example.com"
INITIALIZE an empty DNS cache to simulate a cold start
SPECIFY the list of root nameserver IPv4 addresses
SET the current query name to the target domain
WHILE no final answer obtained
    CONSTRUCT a DNS query packet for an A record for the current query name
    SEND the query via UDP socket to the current nameserver
    RECEIVE the DNS response packet
    PRINT the sent query and the received response, indicating the server role (root, TLD, authoritative)
    IF the response contains a CNAME record
        PRINT the CNAME record
        UPDATE the current query name to the canonical name from the CNAME
        CONTINUE the loop starting again at the root servers
    ENDIF
    IF the response contains answer A records
        PRINT the answer records
        BREAK the loop
    ENDIF
    IF the response contains NS records without an answer
        SELECT the next nameserver IP from the NS records (prefer IPv4)
        SET the current nameserver to the selected IP
        CONTINUE the loop
    ENDIF
ENDWHILE
GENERATE Python source code implementing the above iterative resolver using only the socket module and manual DNS message construction/parsing, without using dnspython or socket.getaddrinfo
ENSURE the generated code prints each DNS query and response as described
OUTPUT the complete Python code as the final deliverable
