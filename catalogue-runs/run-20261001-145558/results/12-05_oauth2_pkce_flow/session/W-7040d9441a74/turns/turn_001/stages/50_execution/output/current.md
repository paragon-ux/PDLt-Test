import urllib.parse
import urllib.request
import hashlib
import secrets
import base64
import json

# Configuration (replace with actual values)
CLIENT_ID = 'your_client_id'
REDIRECT_URI = 'https://example.com/callback'
AUTHORIZATION_ENDPOINT = 'https://authorization.server/authorize'
TOKEN_ENDPOINT = 'https://authorization.server/token'
SCOPE = 'openid profile email'

def generate_code_verifier(length: int = 64) -> str:
    """Generate a high‑entropy code_verifier string (43‑128 chars)."""
    # secrets.token_urlsafe returns a string of variable length; ensure minimum length
    verifier = ''
    while len(verifier) < length:
        verifier += secrets.token_urlsafe(4)
    return verifier[:length]

def derive_code_challenge(verifier: str) -> str:
    """Derive the S256 code_challenge from a verifier.
    RFC 7636: base64url‑encode SHA‑256 digest, no padding.
    """
    digest = hashlib.sha256(verifier.encode('ascii')).digest()
    challenge = base64.urlsafe_b64encode(digest).decode('ascii').rstrip('=')
    return challenge

def generate_state(length: int = 32) -> str:
    """Generate a CSRF protection state token."""
    return secrets.token_urlsafe(length)

def build_authorization_url(state: str, code_challenge: str) -> str:
    """Construct the authorization URL with PKCE parameters."""
    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPE,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
        'state': state,
    }
    return f"{AUTHORIZATION_ENDPOINT}?{urllib.parse.urlencode(params)}"

def exchange_code_for_tokens(code: str, verifier: str) -> dict:
    """POST to the token endpoint to obtain access/refresh tokens."""
    data = urllib.parse.urlencode({
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'code_verifier': verifier,
    }).encode('utf-8')
    req = urllib.request.Request(TOKEN_ENDPOINT, data=data)
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)

def refresh_tokens(refresh_token: str) -> dict:
    """POST to the token endpoint to refresh the access token."""
    data = urllib.parse.urlencode({
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,
    }).encode('utf-8')
    req = urllib.request.Request(TOKEN_ENDPOINT, data=data)
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)

# Example flow (commented out; replace with actual interaction)
# state = generate_state()
# verifier = generate_code_verifier()
# challenge = derive_code_challenge(verifier)
# auth_url = build_authorization_url(state, challenge)
# print('Visit this URL and authorize:', auth_url)
# # After redirect, capture "code" from query parameters and verify "state" matches.
# # code = ...
# # tokens = exchange_code_for_tokens(code, verifier)
# # refreshed = refresh_tokens(tokens['refresh_token'])

# Unit test for code_challenge derivation
if __name__ == '__main__':
    import unittest

    class TestPKCE(unittest.TestCase):
        def test_code_challenge(self):
            verifier = 'dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk'
            expected_challenge = 'E9Melhoa2 O. . '  # placeholder, will compute below
            # Compute expected using the same algorithm for verification
            expected = derive_code_challenge(verifier)
            self.assertEqual(expected, 'E9Melhoa2 O. . ')  # ensure deterministic

    # Run test
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
