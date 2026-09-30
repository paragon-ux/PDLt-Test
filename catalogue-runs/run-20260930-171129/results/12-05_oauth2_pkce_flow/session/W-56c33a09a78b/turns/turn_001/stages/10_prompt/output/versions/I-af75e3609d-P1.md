READ OAuth2 Authorization Code Flow with PKCE specifications
GENERATE a code_verifier (43-128 character random string)
DERIVE a code_challenge using S256 hash of code_verifier
BUILD an authorization URL including client_id, redirect_uri, code_challenge, code_challenge_method, response_type, scope, and state for CSRF protection
USE urllib to open the authorization URL
AFTER receiving the authorization code, POST to token endpoint with code, code_verifier, client_id, redirect_uri, grant_type=authorization_code using urllib
EXTRACT access token and refresh_token from the response
IMPLEMENT token refresh by POSTing to token endpoint with refresh_token and grant_type=refresh_token using urllib
INCLUDE a test that verifies code_challenge equals BASE64URL-ENCODE(SHA256(code_verifier)) per RFC 7636
USE only the Python standard library modules: urllib, hashlib, secrets, base64
