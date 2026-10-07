```python
import asyncio, random

async def fetch_user(user_id):
    await asyncio.sleep(0)
    return {'id': user_id, 'name': f'User_{user_id}', 'org_id': user_id * 10} if random.random() > 0.1 else None

async def fetch_org(org_id):
    return {'id': org_id, 'name': f'Org_{org_id}', 'plan': 'enterprise'} if random.random() > 0.1 else None

async def fetch_permissions(org_id, user_id):
    return ['read', 'write', 'admin']

async def get_user_context(user_id):
    user, org = await asyncio.gather(fetch_user(user_id), fetch_org(user_id * 10))
    perms = await fetch_permissions(user_id * 10, user_id)
    return {'user': user, 'org': org, 'permissions': perms}
```
Test: `asyncio.run(get_user_context(1))` returns a dict with the three keys.
