GENERATE a random code_verifier string of length between 43 and 128 characters using secrets.token_urlsafe
DERIVE a code_challenge by SHA256 hashing the code_verifier and base64url‑encoding the digest without padding
GENERATE a state token using secrets for CSRF protection
BUILD the authorization URL including client_id, redirect_uri, response_type=code, scope, code_challenge, code_challenge_method=S256, and state
WAIT for the user to be redirected back and RECEIVE the authorization code from the query parameters
POST to the token endpoint with grant_type=authorization_code, the received code, redirect_uri, client_id, and the code_verifier to obtain tokens
POST to the token endpoint with grant_type=refresh_token and the refresh_token to refresh the access token
CREATE a test that supplies a known code_verifier, derives its code_challenge using the same steps, and asserts the derived value matches the expected result according to RFC 7636
