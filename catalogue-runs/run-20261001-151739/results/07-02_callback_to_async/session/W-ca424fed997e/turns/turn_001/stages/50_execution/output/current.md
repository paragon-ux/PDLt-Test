import asyncio
from typing import Any, Dict, List

class NetworkError(Exception):
    """Exception raised when a network error occurs while fetching a user."""
    pass

class OrgNotFoundError(Exception):
    """Exception raised when the organization cannot be found."""
    pass

async def fetch_user(user_id: int) -> Dict[str, Any]:
    """Fetch a user record.

    Returns a dictionary with keys ``id``, ``name`` and ``org_id`` where ``name``
    follows the pattern ``User_<user_id>``.
    On a simulated network failure a ``NetworkError`` is raised.
    """
    # Simulate I/O delay
    await asyncio.sleep(0)
    # In a real implementation this would perform an async HTTP request.
    # Here we assume success; to test error handling the tests monkey‑patch this
    # function to raise ``NetworkError``.
    return {"id": user_id, "name": f"User_{user_id}", "org_id": user_id * 10}

async def fetch_org(org_id: int) -> Dict[str, Any]:
    """Fetch an organization record.

    Returns a dictionary with keys ``id``, ``name`` and ``plan`` where ``name``
    follows the pattern ``Org_<org_id>`` and ``plan`` is ``"enterprise"``.
    On a simulated failure a ``OrgNotFoundError`` is raised.
    """
    await asyncio.sleep(0)
    return {"id": org_id, "name": f"Org_{org_id}", "plan": "enterprise"}

async def fetch_permissions(org_id: int, user_id: int) -> List[str]:
    """Fetch permissions for a user within an organization.

    Always returns ``["read", "write", "admin"]``.  Errors could be simulated in
    tests by monkey‑patching this coroutine.
    """
    await asyncio.sleep(0)
    return ["read", "write", "admin"]

async def get_user_context(user_id: int) -> Dict[str, Any]:
    """Orchestrate the async calls to build a user context.

    The function awaits ``fetch_user``, ``fetch_org`` and ``fetch_permissions``
    in sequence and composes a result dictionary with keys ``user``, ``org`` and
    ``permissions``.  Any exception raised by the helper functions propagates
    unchanged to the caller.
    """
    user = await fetch_user(user_id)
    org = await fetch_org(user["org_id"])
    perms = await fetch_permissions(user["org_id"], user_id)
    return {"user": user, "org": org, "permissions": perms}

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
import unittest

class TestUserContext(unittest.IsolatedAsyncioTestCase):
    async def test_success_path(self):
        result = await get_user_context(1)
        expected_user = {"id": 1, "name": "User_1", "org_id": 10}
        expected_org = {"id": 10, "name": "Org_10", "plan": "enterprise"}
        expected_perms = ["read", "write", "admin"]
        self.assertEqual(result["user"], expected_user)
        self.assertEqual(result["org"], expected_org)
        self.assertEqual(result["permissions"], expected_perms)

    async def test_fetch_user_error_propagates(self):
        async def failing_fetch_user(_):
            raise NetworkError("Network error")
        # monkey‑patch fetch_user
        original = globals()["fetch_user"]
        globals()["fetch_user"] = failing_fetch_user
        try:
            with self.assertRaises(NetworkError) as cm:
                await get_user_context(1)
            self.assertEqual(str(cm.exception), "Network error")
        finally:
            globals()["fetch_user"] = original

    async def test_fetch_org_error_propagates(self):
        async def failing_fetch_org(_):
            raise OrgNotFoundError("Org not found")
        original = globals()["fetch_org"]
        globals()["fetch_org"] = failing_fetch_org
        try:
            with self.assertRaises(OrgNotFoundError) as cm:
                await get_user_context(1)
            self.assertEqual(str(cm.exception), "Org not found")
        finally:
            globals()["fetch_org"] = original

    async def test_fetch_permissions_error_propagates(self):
        async def failing_fetch_permissions(*_):
            raise Exception("Permissions error")
        original = globals()["fetch_permissions"]
        globals()["fetch_permissions"] = failing_fetch_permissions
        try:
            with self.assertRaises(Exception) as cm:
                await get_user_context(1)
            self.assertEqual(str(cm.exception), "Permissions error")
        finally:
            globals()["fetch_permissions"] = original

if __name__ == "__main__":
    unittest.main()
