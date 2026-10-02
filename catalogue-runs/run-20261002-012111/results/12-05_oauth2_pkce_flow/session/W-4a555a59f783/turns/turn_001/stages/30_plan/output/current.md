GENERATE a cryptographically random code_verifier string of length between 43 and 128 characters using the secrets module
COMPUTE the S256 code_challenge from the code_verifier by applying SHA-256 via hashlib and encoding the digest using URL-safe base64
ENSURE that the generated code_verifier and computed code_challenge conform to RFC 7636 specifications
GENERATE a cryptographically random state value for CSRF protection using the secrets module
CONSTRUCT the authorization URL with query parameters: client_id, redirect_uri, response_type='code', scope, code_challenge_method='S256', code_challenge, and state
MAKE a POST request to the token endpoint using urllib, including the authorization code and the original code_verifier, to obtain an access token and a refresh token
IMPLEMENT token refresh by making a POST request to the token endpoint using urllib with grant_type='refresh_token' and the refresh token
PROVIDE a test that asserts the code_challenge derived from the code_verifier matches the expected S256 computation as defined in RFC 7636
