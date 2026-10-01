1. Enforce password strength requirements (minimum length, complexity, and prohibited common passwords).
2. Store passwords using a strong, salted hashing algorithm such as Argon2 or bcrypt.
3. Secure transmission of credentials and JWTs via TLS (HTTPS) and include token integrity checks.
4. Implement JWT expiration and a revocation mechanism (e.g., token blacklist or short-lived tokens with refresh tokens).
5. Protect session management with secure, HttpOnly, SameSite cookies and enforce token rotation on login.
6. Restrict admin capabilities with role‑based access control and audit logging of all admin actions.
7. Log authentication events (successful and failed logins, password changes, token revocations) for auditability.
8. Provide users with mechanisms to manage their credentials securely (password change, recovery, MFA setup) and respect privacy by not exposing personal data to other users.
9. Ensure JWTs are signed with a strong algorithm (e.g., RS256) and that the secret/key is stored securely.
10. Validate and sanitize all input fields to prevent injection attacks.
