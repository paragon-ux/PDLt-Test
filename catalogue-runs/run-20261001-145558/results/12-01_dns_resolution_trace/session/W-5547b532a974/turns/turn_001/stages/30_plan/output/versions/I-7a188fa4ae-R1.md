PARSE the domain name and requested record type from the input specification
INITIALIZE an empty ordered collection to store each DNS query and its response
SET the initial nameserver target to the root DNS server address (.")
WHILE the desired answer has not been obtained DO
    SEND a DNS query via a UDP socket to the current nameserver for the domain and record type
    RECORD the sent query and the received response in the trace collection
    IF the response includes an answer RR of the requested type THEN
        BREAK the loop
    ENDIF
    IF the response includes a CNAME RR THEN
        UPDATE the domain name to the CNAME target
        CONTINUE the loop
    ENDIF
    IF the response includes NS referral RR THEN
        EXTRACT the next nameserver address from the additional section or resolve its address iteratively
        SET the current nameserver target to the extracted address
        CONTINUE the loop
    ENDIF
ENDWHILE
FORMAT and RETURN the accumulated query/response trace as plain text
GENERATE Python source code that implements the above iterative resolution process using only the built‑in socket module for UDP communication
