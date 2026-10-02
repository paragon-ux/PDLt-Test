import urllib.parse
import urllib.request
import hashlib
import base64
import secrets

# Configuration (replace with your actual values)
CLIENT_ID = 'your_client_id'
REDIRECT_URI = 'https://localhost/callback'
SCOPE = 'openid profile email'
AUTHORIZATION_ENDPOINT = 'https://authorization.server/authorize'
TOKEN_ENDPOINT = 'https://authorization.server/token'

def generate_code_verifier(length: int = 64) -> str:
    """Generate a cryptographically random code verifier.
    Length must be between 43 and 128 characters as per RFC 7636.
    """
    # Use URL‑safe base64 without padding to get a string of the desired length
    # 6 bits per character, so we need ceil(length*6/8) bytes.
    nbytes = (length * 6 + 7) // 8
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(nbytes)).decode('utf-8').rstrip('=')
    return verifier[:length]

def compute_code_challenge(verifier: str) -> str:
    """Compute the S256 code challenge from a verifier.
    RFC 7636: BASE64URL-ENCODE(SHA256(ASCII(verifier)))
    """
    sha256 = hashlib.sha256(verifier.encode('utf-8')).digest()
    challenge = base64.urlsafe_b64encode(sha256).decode('utf-8').rstrip('=')
    return challenge

def generate_state(length: int = 32) -> str:
    """Generate a CSRF protection state parameter (URL‑safe)."""
    return base64.urlsafe_b64encode(secrets.token_bytes(length)).decode('utf-8').rstrip('=')

def build_authorization_url(code_challenge: str, state: str) -> str:
    """Construct the authorization URL with PKCE parameters."""
    query = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPE,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
        'state': state,
    }
    return f"{AUTHORIZATION_ENDPOINT}?{urllib.parse.urlencode(query)}"

def exchange_code_for_tokens(authorization_code: str, code_verifier: str) -> dict:
    """POST to the token endpoint to exchange the auth code for tokens.
    Returns the parsed JSON response.
    """
    data = urllib.parse.urlencode({
        'grant_type': 'authorization_code',
        'code': authorization_code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'code_verifier': code_verifier,
    }).encode('utf-8')
    req = urllib.request.Request(TOKEN_ENDPOINT, data=data)
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)

def refresh_access_token(refresh_token: str) -> dict:
    """Refresh the access token using the refresh token."""
    data = urllib.parse.urlencode({
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,
    }).encode('utf-8')
    req = urllib.request.Request(TOKEN_ENDPOINT, data=data)
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)

# ---------------------------------------------------------------------------
# Test verifying the code_challenge computation matches RFC 7636
# ---------------------------------------------------------------------------
import unittest
import json

class TestPKCE(unittest.TestCase):
    def test_code_challenge(self):
        verifier = generate_code_verifier(64)
        # Manual computation as defined in RFC 7636
        sha256 = hashlib.sha256(verifier.encode('utf-8')).digest()
        expected_challenge = base64.urlsafe_b64encode(sha256).decode('utf-8').rstrip('=')
        actual_challenge = compute_code_challenge(verifier)
        self.assertEqual(actual_challenge, expected_challenge)

if __name__ == '__main__':
    # Example usage (commented out to avoid network calls during import)
    # verifier = generate_code_verifier()
    # challenge = compute_code_challenge(verifier)
    # state = generate_state()
    # print('Open this URL in a browser:')
    # print(build_authorization_url(challenge, state))
    # # After redirect, manually provide the code below
    # auth_code = input('Enter authorization code: ')
    # tokens = exchange_code_for_tokens(auth_code, verifier)
    # print('Tokens:', tokens)
    # # Refresh example
    # refreshed = refresh_access_token(tokens['refresh_token'])
    # print('Refreshed tokens:', refreshed)
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
