import base64, hashlib, secrets, urllib.parse, urllib.request

# Configuration (replace with real values when using)
CLIENT_ID = 'your_client_id'
REDIRECT_URI = 'https://example.com/callback'
AUTH_ENDPOINT = 'https://provider.com/oauth2/authorize'
TOKEN_ENDPOINT = 'https://provider.com/oauth2/token'
SCOPE = 'openid profile email'

def generate_code_verifier(length: int = 64) -> str:
    # PKCE requires 43-128 characters; use URL-safe base64 without padding
    verifier = secrets.token_urlsafe(length)
    return verifier[:max(43, min(128, len(verifier)))]

def derive_code_challenge(verifier: str) -> str:
    sha256 = hashlib.sha256(verifier.encode('utf-8')).digest()
    challenge = base64.urlsafe_b64encode(sha256).decode('utf-8').rstrip('=')
    return challenge

def build_authorization_url(client_id: str, redirect_uri: str, code_challenge: str, state: str, scope: str) -> str:
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': scope,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
        'state': state,
    }
    return f"{AUTH_ENDPOINT}?{urllib.parse.urlencode(params)}"

def exchange_code_for_tokens(code: str, code_verifier: str, client_id: str, redirect_uri: str) -> dict:
    data = urllib.parse.urlencode({
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'code_verifier': code_verifier,
    }).encode('utf-8')
    req = urllib.request.Request(TOKEN_ENDPOINT, data=data)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def refresh_access_token(refresh_token: str, client_id: str) -> dict:
    data = urllib.parse.urlencode({
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
    }).encode('utf-8')
    req = urllib.request.Request(TOKEN_ENDPOINT, data=data)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

# -------------------- Test --------------------
import unittest, json

class TestPKCE(unittest.TestCase):
    def test_code_challenge_derivation(self):
        # Example from RFC 7636 Appendix B
        verifier = 'dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk'
        expected_challenge = 'E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM'
        self.assertEqual(derive_code_challenge(verifier), expected_challenge)

if __name__ == '__main__':
    unittest.main()
