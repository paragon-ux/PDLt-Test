READ the OAuth2 Authorization Code Flow with PKCE specification
GENERATE a code_verifier as a random string of 43-128 characters using secrets
DERIVE a code_challenge by applying SHA256 to the code_verifier and encoding the result with base64url
BUILD the authorization URL including client_id, redirect_uri, response_type=code, scope, state, code_challenge, and code_challenge_method=S256
OPEN the authorization URL with urllib to initiate user authentication
RECEIVE the authorization code from the redirect response
POST to the token endpoint using urllib with parameters: grant_type=authorization_code, code, redirect_uri, client_id, code_verifier
EXTRACT access_token and refresh_token from the token response
POST to the token endpoint using urllib with parameters: grant_type=refresh_token, refresh_token, client_id to obtain a new access token
VERIFY that code_challenge equals BASE64URL-ENCODE(SHA256(code_verifier)) as required by RFC 7636
