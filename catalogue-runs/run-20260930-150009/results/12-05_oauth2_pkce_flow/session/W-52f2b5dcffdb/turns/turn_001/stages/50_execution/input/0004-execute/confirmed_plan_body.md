READ the OAuth2 Authorization Code Flow with PKCE requirements
GENERATE a code_verifier as a random string of 43-128 characters using the standard library
DERIVE a code_challenge by applying an S256 hash to the code_verifier and encoding it with base64 URL-safe format
BUILD the authorization URL including client_id, redirect_uri, code_challenge, code_challenge_method=S256, response_type=code, scope, and a randomly generated state parameter for CSRF protection
REDIRECT the user agent to the authorization URL and await the redirect containing the authorization code
POST to the token endpoint with grant_type=authorization_code, the received code, code_verifier, client_id, and redirect_uri to obtain access and refresh tokens
POST to the token endpoint with grant_type=refresh_token, the refresh_token, and client_id to refresh the access token when needed
PROVIDE a test that creates a known code_verifier, computes the expected code_challenge per RFC 7636, runs the DERIVE step, and asserts that the derived code_challenge matches the expected value
