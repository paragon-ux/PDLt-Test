OPERATIVE TASK ENTITIES: OAuth2, Authorization Code Flow, PKCE, Python, code_verifier, code_challenge, S256, client_id, redirect_uri, code_challenge_method, response_type, scope, state, refresh_token, urllib, hashlib, secrets, base64, RFC 7636
GENERATE a random code_verifier string of length 43-128 characters using the secrets module
COMPUTE its S256 code_challenge using hashlib and base64 URL-safe encoding
CONSTRUCT the authorization URL including client_id, redirect_uri, code_challenge, code_challenge_method='S256', response_type='code', scope, and state
ENSURE the state parameter is cryptographically random to protect against CSRF
MAKE a POST request to the token endpoint using urllib to exchange the authorization code for access token and refresh_token, supplying code_verifier
IMPLEMENT token refresh by making a POST request to the token endpoint with grant_type='refresh_token' and the refresh_token using urllib
PROVIDE a test that verifies that the code_challenge derived from the code_verifier matches the S256 computation as defined in RFC 7636
USE only the Python standard library modules urllib, hashlib, secrets, and base64
