Implement the OAuth2 Authorization Code Flow with PKCE in Python (client-side only, no server framework).

1. Generate a code_verifier (43-128 character random string) and code_challenge (S256 hash).
2. Build the authorization URL with the correct parameters (client_id, redirect_uri, code_challenge, code_challenge_method, response_type, scope, state).
3. After receiving the authorization code, exchange it for tokens by POSTing to the token endpoint with the code_verifier.
4. Implement token refresh using the refresh_token.
5. Include CSRF protection via the state parameter.

Use only the standard library (urllib, hashlib, secrets, base64). Include a test that verifies the code_challenge is correctly derived from the code_verifier per RFC 7636.
