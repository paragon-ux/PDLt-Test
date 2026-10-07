1. **Password storage:** hash with argon2/bcrypt and a per-user salt; minimum length and breached-password check.
2. **Login throttling:** rate limit per IP and per account; exponential backoff or temporary lockout to stop brute force and credential stuffing.
3. **JWT expiry:** short-lived access tokens (e.g. 15 min) with refresh tokens; otherwise a leaked token works forever.
4. **Revocation and logout:** a deny-list or token versioning so logout, password change and deactivation invalidate existing tokens.
5. **Email verification and uniqueness:** verify ownership before activation; unique emails compared case-insensitively (Alice@x.com vs alice@x.com).
6. **Password reset:** a single-use, expiring reset token sent to the verified email; it invalidates sessions.
7. **Admin assignment:** how a user becomes admin, who can grant it, and that the role isn't settable through registration or profile updates (privilege escalation).
8. **Profile authorization:** "users can only view their own profile" must be enforced server-side on the ID in the request (IDOR), not trusted from the client.
9. **JWT validation:** fixed algorithm (reject `alg: none`), secret/key rotation, audience and issuer checks.
10. **Error messages:** identical responses for unknown email and wrong password, to prevent user enumeration.
