READ the OpenSSL s_client output showing the certificate chain
IDENTIFY the error message "unable to get local issuer certificate"
EXPLAIN why the presented chain contains only the leaf certificate and why the intermediate CA certificate is missing
DESCRIBE the role of the intermediate CA certificate and where it should be obtained from
PROVIDE server‑side steps to retrieve the intermediate certificate and assemble a full chain file
CONFIGURE the server to use the full chain (leaf + intermediate + root) in its TLS settings
LIST OpenSSL commands to verify the corrected chain, e.g., `openssl s_client -connect <host>:443 -servername <host>` and `openssl verify`
INCLUDE client‑side debugging steps to test the chain and interpret verification results
