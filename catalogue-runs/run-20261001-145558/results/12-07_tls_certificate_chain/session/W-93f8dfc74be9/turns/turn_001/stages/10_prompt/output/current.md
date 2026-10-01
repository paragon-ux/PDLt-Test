READ the OpenSSL s_client output showing a broken certificate chain
IDENTIFY the error message "unable to get local issuer certificate"
EXPLAIN why the chain contains only one certificate and why the intermediate CA certificate is missing
DESCRIBE the role of the intermediate CA certificate and where it should be obtained from
PROVIDE exact steps to fix the issue on the server side, including how to configure the server with the complete certificate chain
LIST the OpenSSL commands to verify the fixed chain, such as `openssl s_client -connect <host>:443 -servername <host>` and `openssl verify`
INCLUDE debugging steps for the client side, showing how to test the chain and interpret verification results
