## Explanation of OpenSSL Errors

- **"unable to get local issuer certificate"** – OpenSSL could not locate a trusted certificate that issued the server’s certificate in the supplied trust store. This usually means the intermediate CA certificate (the issuer of the server certificate) is missing from the chain presented to the client.
- **"unable to verify the first certificate"** – After the previous failure, OpenSSL stops verification because the first certificate (the server’s leaf) could not be linked to a trusted root.

## Why the Chain Shows Only the Server Certificate
The `s_client` output shows a single certificate in the *Certificate chain* section. The server is only sending its own leaf certificate; it does not send the intermediate CA certificate that signed it. Consequently the client has no way to build a complete chain to a trusted root, leading to the errors above.

## Role of the Intermediate CA Certificate
The intermediate CA certificate bridges the leaf certificate to a root CA that is trusted by clients. It must be provided by the issuing CA – typically downloaded from the CA’s repository (e.g., a URL like `https://ca.example.com/intermediate.crt` or supplied together with the leaf certificate by the CA in a bundle).

## Server‑Side Fix Procedure
1. **Obtain the intermediate certificate** from the CA (download the PEM file).
2. **Create a full‑chain bundle** by concatenating the leaf and intermediate certificates (order: leaf first, then intermediate). Optionally append the root if desired, but most servers only need leaf + intermediates.
   ```bash
   cat server.crt intermediate.crt > fullchain.pem
   ```
3. **Configure the server** to use the full‑chain file.
   - *Nginx*:
     ```nginx
     ssl_certificate /etc/ssl/fullchain.pem;   # contains leaf + intermediate
     ssl_certificate_key /etc/ssl/server.key;
     ```
   - *Apache*:
     ```apache
     SSLCertificateFile /etc/ssl/server.crt
     SSLCertificateChainFile /etc/ssl/intermediate.crt
     ```
4. **Reload/restart the service**.
   ```bash
   sudo systemctl reload nginx   # or apache2
   ```
5. **Verify the corrected chain**:
   ```bash
   openssl s_client -connect api.example.com:443 -servername api.example.com -showcerts </dev/null \
     | openssl verify -CAfile fullchain.pem -untrusted intermediate.crt -
   ```
   The output should end with `OK` and show the complete chain.

## Local Debugging Procedure
1. **Download the server’s leaf and intermediate certificates** (if not already available).
2. **Test the server’s presented chain**:
   ```bash
   openssl s_client -connect api.example.com:443 -servername api.example.com -showcerts </dev/null
   ```
   Observe the `Certificate chain` section; it should list both leaf and intermediate.
3. **Verify against a trusted store**:
   ```bash
   openssl verify -CApath /etc/ssl/certs -untrusted intermediate.crt server.crt
   ```
   Expect `server.crt: OK`.
4. **Check for missing intermediates** using `openssl x509 -noout -text -in server.crt | grep Authority` to confirm the issuer matches the intermediate’s subject.
5. **Inspect the intermediate certificate**:
   ```bash
   openssl x509 -in intermediate.crt -noout -text | grep Subject
   ```
   Ensure it matches the `issuer` field shown in the leaf certificate.

Following these steps restores a proper certificate chain, eliminating the "unable to get local issuer certificate" and "unable to verify the first certificate" errors.

---

```json
{"files":[{"filename":"certificate_chain_fix.md","satisfies":["R1","R2","R3","R4","R5"],"evidence":{"path":"execution://body","section":null,"observed":null}}],"reconciliation":[{"requirement":"R1","status":"satisfied","evidence":{"path":"execution://body","section":null,"observed":null}},{"requirement":"R2","status":"satisfied","evidence":{"path":"execution://body","section":null,"observed":null}},{"requirement":"R3","status":"satisfied","evidence":{"path":"execution://body","section":null,"observed":null}},{"requirement":"R4","status":"satisfied","evidence":{"path":"execution://body","section":null,"observed":null}},{"requirement":"R5","status":"satisfied","evidence":{"path":"execution://body","section":null,"observed":null}}],"open_defects":[]} 
```
