import asyncio
import random
from typing import Any, Dict, List

# Simulated async fetch functions
async def fetch_user(user_id: int) -> Dict[str, Any]:
    """Fetch a user object asynchronously.
    Raises:
        Exception: Simulated network error.
    """
    await asyncio.sleep(0)  # simulate async boundary
    if random.random() > 0.1:
        return {"id": user_id, "name": f"User_{user_id}", "org_id": user_id * 10}
    else:
        raise Exception("Network error")

async def fetch_org(org_id: int) -> Dict[str, Any]:
    """Fetch an organization object asynchronously.
    Raises:
        Exception: Simulated not‑found error.
    """
    await asyncio.sleep(0)
    if random.random() > 0.1:
        return {"id": org_id, "name": f"Org_{org_id}", "plan": "enterprise"}
    else:
        raise Exception("Org not found")

async def fetch_permissions(org_id: int, user_id: int) -> List[str]:
    """Fetch permissions for a user in an organization.
    This mock always succeeds.
    """
    await asyncio.sleep(0)
    return ["read", "write", "admin"]

async def get_user_context(user_id: int) -> Dict[str, Any]:
    """Compose user, organization, and permissions into a context dictionary.
    Propagates any exception raised by the underlying async calls.
    """
    try:
        user = await fetch_user(user_id)
        org = await fetch_org(user["org_id"])
        perms = await fetch_permissions(user["org_id"], user_id)
        return {"user": user, "org": org, "permissions": perms}
    except Exception as e:
        # Propagate the original exception
        raise e

# --------------------- Unit Tests ---------------------
import unittest

class TestUserContextAsync(unittest.IsolatedAsyncioTestCase):
    async def test_success_path(self):
        # Patch random to ensure success
        original_random = random.random
        random.random = lambda: 0.5  # always > 0.1
        try:
            ctx = await get_user_context(1)
            self.assertIn("user", ctx)
            self.assertIn("org", ctx)
            self.assertIn("permissions", ctx)
            self.assertEqual(ctx["user"]["id"], 1)
            self.assertEqual(ctx["org"]["id"], 10)
            self.assertListEqual(ctx["permissions"], ["read", "write", "admin"])
        finally:
            random.random = original_random

    async def test_error_propagation_user_error(self):
        # Force fetch_user to raise
        original_random = random.random
        random.random = lambda: 0.05  # < 0.1 triggers error
        try:
            with self.assertRaises(Exception) as cm:
                await get_user_context(2)
            self.assertIn("Network error", str(cm.exception))
        finally:
            random.random = original_random

    async def test_error_propagation_org_error(self):
        # Force fetch_user success but fetch_org fail
        original_random = random.random
        seq = iter([0.5, 0.05])  # first call success, second fail
        random.random = lambda: next(seq)
        try:
            with self.assertRaises(Exception) as cm:
                await get_user_context(3)
            self.assertIn("Org not found", str(cm.exception))
        finally:
            random.random = original_random

if __name__ == "__main__":
    unittest.main()
