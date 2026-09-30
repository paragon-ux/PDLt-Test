READ the OAuth2 Authorization Code Flow with PKCE requirements
GENERATE a code_verifier (43-128 character random string)
DERIVE a code_challenge using S256 hash of the code_verifier
BUILD the authorization URL with parameters: client_id, redirect_uri, code_challenge, code_challenge_method, response_type, scope, state
INCLUDE CSRF protection via the state parameter
AFTER receiving the authorization code, POST to the token endpoint with the code, code_verifier, client_id, redirect_uri, grant_type=authorization_code to obtain access and refresh tokens
IMPLEMENT token refresh by POSTing to the token endpoint with refresh_token and grant_type=refresh_token
USE only the standard library modules: urllib, hashlib, secrets, base64
PROVIDE a test that verifies the code_challenge is correctly derived from the code_verifier per RFC 7636
