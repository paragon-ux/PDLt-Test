import asyncio
import unittest
from unittest.mock import AsyncMock, patch

# Async implementations
async def fetch_user(user_id):
    import random
    if random.random() > 0.1:
        return {'id': user_id, 'name': f'User_{user_id}', 'org_id': user_id * 10}
    else:
        raise Exception('Network error')

async def fetch_org(org_id):
    import random
    if random.random() > 0.1:
        return {'id': org_id, 'name': f'Org_{org_id}', 'plan': 'enterprise'}
    else:
        raise Exception('Org not found')

async def fetch_permissions(org_id, user_id):
    return ['read', 'write', 'admin']

async def get_user_context(user_id):
    try:
        user = await fetch_user(user_id)
        org = await fetch_org(user['org_id'])
        perms = await fetch_permissions(user['org_id'], user_id)
        return {'user': user, 'org': org, 'permissions': perms}
    except Exception as e:
        # Propagate exception to caller
        raise

# Unit tests
class TestGetUserContext(unittest.IsolatedAsyncioTestCase):
    async def test_successful_execution(self):
        user_data = {'id': 1, 'name': 'User_1', 'org_id': 10}
        org_data = {'id': 10, 'name': 'Org_10', 'plan': 'enterprise'}
        perms_data = ['read', 'write', 'admin']
        with patch('__main__.fetch_user', AsyncMock(return_value=user_data)) as mock_user,
              patch('__main__.fetch_org', AsyncMock(return_value=org_data)) as mock_org,
              patch('__main__.fetch_permissions', AsyncMock(return_value=perms_data)) as mock_perms:
            result = await get_user_context(1)
            self.assertEqual(result, {'user': user_data, 'org': org_data, 'permissions': perms_data})
            mock_user.assert_awaited_once_with(1)
            mock_org.assert_awaited_once_with(10)
            mock_perms.assert_awaited_once_with(10, 1)

    async def test_fetch_user_exception_propagates(self):
        with patch('__main__.fetch_user', AsyncMock(side_effect=Exception('Network error'))):
            with self.assertRaises(Exception) as cm:
                await get_user_context(1)
            self.assertEqual(str(cm.exception), 'Network error')

    async def test_fetch_org_exception_propagates(self):
        user_data = {'id': 1, 'name': 'User_1', 'org_id': 10}
        with patch('__main__.fetch_user', AsyncMock(return_value=user_data)):
            with patch('__main__.fetch_org', AsyncMock(side_effect=Exception('Org not found'))):
                with self.assertRaises(Exception) as cm:
                    await get_user_context(1)
                self.assertEqual(str(cm.exception), 'Org not found')

    async def test_fetch_permissions_exception_propagates(self):
        user_data = {'id': 1, 'name': 'User_1', 'org_id': 10}
        org_data = {'id': 10, 'name': 'Org_10', 'plan': 'enterprise'}
        with patch('__main__.fetch_user', AsyncMock(return_value=user_data)):
            with patch('__main__.fetch_org', AsyncMock(return_value=org_data)):
                with patch('__main__.fetch_permissions', AsyncMock(side_effect=Exception('Permissions error'))):
                    with self.assertRaises(Exception) as cm:
                        await get_user_context(1)
                    self.assertEqual(str(cm.exception), 'Permissions error')

if __name__ == '__main__':
    unittest.main()
