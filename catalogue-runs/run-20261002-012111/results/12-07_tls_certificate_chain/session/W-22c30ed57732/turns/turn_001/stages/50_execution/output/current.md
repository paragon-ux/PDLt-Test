**Explanation of the error**

- `unable to get local issuer certificate` means that OpenSSL could not build a trust chain from the server certificate back to a trusted root because it is missing the issuing (intermediate) certificate that signed the server certificate.
- In the provided `s_client` output the **Certificate chain** section shows only one certificate (depth 0, the leaf for `api.example.com`). No intermediate certificates are listed, which is why the verification fails.
- The server certificate’s issuer is `CN = Example Intermediate CA, O = Example Inc`. This indicates that the server certificate was signed by an intermediate CA that should be supplied by the server in the TLS handshake. That intermediate certificate is missing from the configuration, so the client cannot locate it locally.

**What certificate is missing?**

- The missing certificate is the *intermediate* CA certificate whose subject is `CN = Example Intermediate CA, O = Example Inc`. It is typically provided by the CA that issued the leaf certificate (e.g., via a download link or a public repository such as the CA’s website or a CDN).

**Server‑side remediation steps**

1. **Obtain the intermediate certificate**
   ```bash
   # Example: download from the CA’s repository (replace URL with the actual one for Example Intermediate CA)
   curl -o example-intermediate.pem https://example.com/ca/intermediate.pem
   ```
   Verify the file contains a PEM‑encoded certificate ending with `-----END CERTIFICATE-----`.

2. **Create a full chain file**
   - Concatenate the server certificate (already on disk, e.g., `example-com.crt`) with the intermediate certificate.
   ```bash
   cat example-com.crt example‑intermediate.pem > example-com-fullchain.pem
   ```
   - If the CA also provides a root certificate, you may append it, but most TLS stacks already trust the root bundle.

3. **Configure the TLS service to use the full chain**
   - **Apache (mod_ssl)**:
     ```apache
     SSLCertificateFile      /path/to/example-com.crt
     SSLCertificateChainFile /path/to/example-intermediate.pem   # or use the fullchain file via SSLCertificateFile
     ```
   - **Nginx**:
     ```nginx
     ssl_certificate /path/to/example-com-fullchain.pem;   # contains leaf + intermediate
     ssl_certificate_key /path/to/example-com.key;
     ```
   - **HAProxy**:
     ```haproxy
     crt /path/to/example-com-fullchain.pem
     ```
   Adjust the directive names according to your server software.

4. **Reload / restart the service**
   ```bash
   # Apache
   sudo systemctl reload apache2
   # Nginx
   sudo systemctl reload nginx
   # HAProxy
   sudo systemctl restart haproxy
   ```

5. **Verify the fix**
   ```bash
   openssl s_client -connect api.example.com:443 -servername api.example.com -showcerts </dev/null |
   grep -A2 "Verify return code"
   ```
   - The output should end with `Verify return code: 0 (ok)`.
   - You can also explicitly request the verification of the chain:
   ```bash
   openssl verify -CApath /etc/ssl/certs example-com-fullchain.pem
   ```
   It should report `OK`.

**Debugging steps (client‑side)**

- **View the presented chain**:
  ```bash
  openssl s_client -connect api.example.com:443 -servername api.example.com -showcerts </dev/null
  ```
  Ensure you now see both the leaf and the intermediate certificates.
- **Check which CA files OpenSSL trusts**:
  ```bash
  openssl version -d   # shows the default CA directory
  ls $(openssl version -d | cut -d'"' -f2)/certs
  ```
- **Test with a custom CA bundle** (useful for local testing):
  ```bash
  cat example-intermediate.pem > my-ca-bundle.pem
  openssl s_client -connect api.example.com:443 -servername api.example.com -CAfile my-ca-bundle.pem </dev/null
  ```
  The verification should succeed if the intermediate is correctly supplied.

By adding the missing intermediate CA certificate to the server’s TLS configuration and restarting the service, the client will be able to build a complete trust chain, eliminating the `unable to get local issuer certificate` error.
