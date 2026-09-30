**Explanation of OpenSSL verification errors**
- **"unable to get local issuer certificate"** – OpenSSL could not find a trusted certificate that issued the server’s certificate in the set of CA certificates it was given (the trust store or the chain supplied by the server). In practice this means the intermediate certificate that bridges the server certificate to a root CA is missing.
- **"unable to verify the first certificate"** – After the previous error, OpenSSL aborts further verification because the first certificate in the chain (the server certificate) could not be validated. It is essentially a follow‑on error for the missing issuer.

**Why the displayed chain contains only the server certificate**
The `openssl s_client` output shows a single certificate under “Certificate chain”. The server only sent its leaf certificate and did not include the intermediate CA certificate that issued it. Without that intermediate, the client cannot build a full chain to a trusted root, leading to the errors above.

**Missing intermediate CA certificate**
From the server certificate’s *Issuer* field we see:
```
Issuer: CN = Example Intermediate CA, O = Example Inc
```
Thus the missing certificate is the **Example Intermediate CA** certificate (the intermediate that signed the server’s leaf certificate). It should be obtained from the CA that issued the server certificate – typically provided as a separate PEM file by the certificate authority.

**Exact steps to fix the issue on the server side**
1. **Obtain the intermediate certificate** – download the PEM file for *Example Intermediate CA* from the CA’s repository or receive it from the CA.
2. **Create a full‑chain file** – concatenate the server certificate (leaf) and the intermediate certificate **in this order**:
   ```bash
   cat server.crt intermediate.pem > fullchain.pem
   ```
   Do **not** include the root CA certificate; it should already be trusted on client systems.
3. **Configure the server to present the full chain**:
   - **Apache (mod_ssl):**
     ```
     SSLCertificateFile      /path/to/server.crt
     SSLCertificateChainFile /path/to/intermediate.pem   # or use SSLCertificateFile with fullchain.pem and omit ChainFile in newer versions
     ```
   - **Nginx:**
     ```
     ssl_certificate /path/to/fullchain.pem;   # contains leaf + intermediate
     ssl_certificate_key /path/to/server.key;
     ```
   - **HAProxy:**
     ```
     bind *:443 ssl crt /path/to/fullchain.pem alpn h2,http/1.1
     ```
4. **Reload/restart the service** to apply the new configuration.
5. **Verify that the server now presents the full chain** (see commands below).

**OpenSSL commands to verify the certificate chain**
- Verify against the system’s default trust store:
  ```bash
  openssl s_client -connect api.example.com:443 -showcerts -CApath /etc/ssl/certs </dev/null
  ```
  Look for `Verify return code: 0 (ok)`.
- Verify using an explicit trust store (useful for testing):
  ```bash
  cat intermediate.pem > trust.pem
  cat root-ca.pem >> trust.pem   # if you have the root CA PEM
  openssl s_client -connect api.example.com:443 -CAfile trust.pem -verify_return_error </dev/null
  ```

**Debugging aids**
- Display the chain as seen by the client:
  ```bash
  openssl s_client -connect api.example.com:443 -servername api.example.com -showcerts </dev/null | awk '/-----BEGIN/,/-----END/{print}'
  ```
- Check each certificate’s subject and issuer:
  ```bash
  openssl x509 -noout -subject -issuer -in server.crt
  openssl x509 -noout -subject -issuer -in intermediate.pem
  ```
- Test verification step‑by‑step:
  ```bash
  # Verify leaf against intermediate
  openssl verify -CAfile intermediate.pem server.crt
  # Verify intermediate against root (if root not in system store)
  openssl verify -CAfile root-ca.pem intermediate.pem
  ```
These commands let you pinpoint where the chain breaks and confirm that the fix resolves the errors.

---
**Summary**: The errors arise because the server omitted the intermediate CA certificate. Obtain the intermediate, concatenate it with the leaf certificate to form a full‑chain PEM, configure the server (Apache, Nginx, HAProxy, etc.) to serve that file, reload the service, and verify with `openssl s_client`. The debugging commands above help ensure the chain is correct.

```json
{
  "files": [
    {
      "filename": "answer.txt",
      "satisfies": ["R1", "R2", "R3", "R4", "R5"],
      "evidence": { "path": "execution://body" }
    }
  ],
  "reconciliation": [
    { "requirement": "R1", "status": "satisfied", "evidence": { "path": "execution://body" } },
    { "requirement": "R2", "status": "satisfied", "evidence": { "path": "execution://body" } },
    { "requirement": "R3", "status": "satisfied", "evidence": { "path": "execution://body" } },
    { "requirement": "R4", "status": "satisfied", "evidence": { "path": "execution://body" } },
    { "requirement": "R5", "status": "satisfied", "evidence": { "path": "execution://body" } }
  ],
  "open_defects": []
}
```
