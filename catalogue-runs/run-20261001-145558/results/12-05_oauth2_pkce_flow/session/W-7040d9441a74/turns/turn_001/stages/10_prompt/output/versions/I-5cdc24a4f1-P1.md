GENERATE a code_verifier (43-128 character random string) using the Python standard library.
DERIVE a code_challenge from the code_verifier using the S256 hash algorithm.
BUILD the authorization URL for the OAuth2 Authorization Code Flow with PKCE including the parameters: client_id, redirect_uri, code_challenge, code_challenge_method, response_type, scope, state.
INCLUDE CSRF protection by generating and appending a state parameter.
AFTER the user is redirected back, RECEIVE the authorization code.
POST to the token endpoint to exchange the authorization code for tokens, supplying the code_verifier.
IMPLEMENT token refresh by POSTing to the token endpoint with the refresh_token.
USE only the Python standard library modules urllib, hashlib, secrets, and base64.
PROVIDE a test that verifies the code_challenge is correctly derived from the code_verifier according to RFC 7636.
