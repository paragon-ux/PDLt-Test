# oauth_pkce.py
"""OAuth2 Authorization Code Flow with PKCE (client-side only) using Python standard library.

This module demonstrates:
1. Generation of a code_verifier and code_challenge (S256).
2. Construction of the authorization URL with required parameters (client_id, redirect_uri, response_type, scope, state, code_challenge, code_challenge_method).
3. Exchange of the authorization code for access and refresh tokens.
4. Refreshing an access token using the refresh token.
5. Simple test verifying the code_challenge derivation per RFC 7636.

All network interactions use ``urllib.request``. No external dependencies are required.
"""
import base64
import hashlib
import secrets
import urllib.parse
import urllib.request
import json
from typing import Tuple

# ---------------------------------------------------------------------------
# Configuration (replace with real values for actual use)
# ---------------------------------------------------------------------------
CLIENT_ID = "your_client_id"
REDIRECT_URI = "https://example.com/callback"
AUTHORIZATION_ENDPOINT = "https://authorization.server/authorize"
TOKEN_ENDPOINT = "https://authorization.server/token"
SCOPE = "openid profile email"

# ---------------------------------------------------------------------------
# PKCE helpers
# ---------------------------------------------------------------------------
def generate_code_verifier(length: int = 64) -> str:
    """Return a high‑entropy URL‑safe string (43‑128 chars) per RFC 7636.
    """
    if not 43 <= length <= 128:
        raise ValueError("code_verifier length must be between 43 and 128")
    # secrets.token_urlsafe returns a string of ~4/3 * nbytes characters
    # We generate enough bytes then truncate to the requested length.
    nbytes = (length * 3) // 4 + 1
    verifier = secrets.token_urlsafe(nbytes)[:length]
    return verifier

def derive_code_challenge(verifier: str) -> str:
    """Return the base64url‑encoded SHA256 hash of *verifier* (method S256)."""
    sha256 = hashlib.sha256(verifier.encode("ascii")).digest()
    b64 = base64.urlsafe_b64encode(sha256).decode("ascii")
    return b64.rstrip("=")

# ---------------------------------------------------------------------------
# Authorization URL construction
# ---------------------------------------------------------------------------
def build_authorization_url(state: str, verifier: str) -> str:
    challenge = derive_code_challenge(verifier)
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    return f"{AUTHORIZATION_ENDPOINT}?{urllib.parse.urlencode(params)}"

# ---------------------------------------------------------------------------
# Token exchange helpers
# ---------------------------------------------------------------------------
def _post_token(data: dict) -> dict:
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(TOKEN_ENDPOINT, data=encoded)
    with urllib.request.urlopen(req) as resp:
        resp_data = resp.read()
    return json.loads(resp_data.decode("utf-8"))

def exchange_code_for_tokens(code: str, verifier: str) -> Tuple[str, str]:
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "code_verifier": verifier,
    }
    token_response = _post_token(payload)
    return token_response.get("access_token"), token_response.get("refresh_token")

def refresh_access_token(refresh_token: str) -> str:
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
    }
    token_response = _post_token(payload)
    return token_response.get("access_token")

# ---------------------------------------------------------------------------
# Simple test for PKCE challenge derivation
# ---------------------------------------------------------------------------
def _test_code_challenge():
    verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    expected_challenge = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
    actual = derive_code_challenge(verifier)
    assert actual == expected_challenge, f"PKCE challenge mismatch: {actual} != {expected_challenge}"
    print("PKCE test passed.")

if __name__ == "__main__":
    # Run PKCE test
    _test_code_challenge()
    # Example flow (manual steps required for real OAuth interaction)
    state = secrets.token_urlsafe(16)
    verifier = generate_code_verifier()
    auth_url = build_authorization_url(state, verifier)
    print("Open the following URL in a browser to authenticate:")
    print(auth_url)
    # After user authenticates, they will be redirected to REDIRECT_URI with ?code=...&state=...
    # The developer must capture the "code" parameter from the redirect and then:
    # access_token, refresh_token = exchange_code_for_tokens(code, verifier)
    # print("Access token:", access_token)
    # print("Refresh token:", refresh_token)
    # To refresh:
    # new_access = refresh_access_token(refresh_token)
    # print("New access token:", new_access)
