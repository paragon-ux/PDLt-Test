EXTRACT the definitions of the OpenSSL verification errors \"unable to get local issuer certificate\" and \"unable to verify the first certificate\" from documentation
ANALYZE the server's presented certificate chain to show why only the server certificate appears
IDENTIFY the intermediate CA certificate that should be present in the chain but is missing
COMPILE the required server-side configuration steps to include the full certificate chain, including ordering of certificates and updating server configuration files
DEVELOP the OpenSSL command(s) to verify the complete certificate chain against trusted roots
DEVELOP the OpenSSL command(s) to test and debug the chain, showing intermediate certificates and error details
