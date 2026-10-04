```python
import asyncio, random

async def fetch_user(user_id):
    if random.random() > 0.1:
        return {'id': user_id, 'name': f'User_{user_id}', 'org_id': user_id * 10}
    raise Exception('Network error')

async def fetch_org(org_id):
    if random.random() > 0.1:
        return {'id': org_id, 'name': f'Org_{org_id}', 'plan': 'enterprise'}
    raise Exception('Org not found')

async def fetch_permissions(org_id, user_id):
    return ['read', 'write', 'admin']

async def get_user_context(user_id):
    """Raises the first step's error, as final_callback(e, None) reported it."""
    user = await fetch_user(user_id)
    org = await fetch_org(user['org_id'])
    perms = await fetch_permissions(user['org_id'], user_id)
    return {'user': user, 'org': org, 'permissions': perms}

async def get_user_context_cb_style(user_id):
    """The original (error, result) contract, for callers that need it."""
    try:
        return None, await get_user_context(user_id)
    except Exception as e:
        return e, None
```
Tests:
```python
from unittest import mock
def test_success():
    with mock.patch("random.random", return_value=0.5):
        ctx = asyncio.run(get_user_context(7))
    assert ctx == {'user': {'id': 7, 'name': 'User_7', 'org_id': 70},
                   'org': {'id': 70, 'name': 'Org_70', 'plan': 'enterprise'}, 'permissions': ['read', 'write', 'admin']}

def test_org_error_propagates_and_stops():
    calls = iter([0.5, 0.05])                    # user succeeds, org fails
    with mock.patch("random.random", side_effect=lambda: next(calls)):
        err, result = asyncio.run(get_user_context_cb_style(7))
    assert str(err) == 'Org not found' and result is None
```
