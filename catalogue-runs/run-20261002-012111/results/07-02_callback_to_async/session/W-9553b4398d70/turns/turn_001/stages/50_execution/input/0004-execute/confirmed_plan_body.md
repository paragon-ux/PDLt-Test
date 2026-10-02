READ the callback-based Python code containing fetch_user, fetch_org, fetch_permissions, and get_user_context
ANALYZE each function to identify synchronous calls and existing error handling
CONVERT each function definition to async def
INSERT await before calls to fetch_user, fetch_org, and fetch_permissions inside get_user_context
PRESERVE the original try/except blocks capturing exceptions as e
ENSURE any identifier such as id is correctly referenced in the async version
PROPAGATE any exceptions raised by fetch_user, fetch_org, fetch_permissions, or get_user_context to the caller
SELECT a testing framework (unittest or pytest) for the unit tests
CREATE unit tests
    CREATE a unit test that mocks fetch_user, fetch_org, and fetch_permissions to return valid data and verifies that get_user_context returns the combined result
    CREATE a unit test that mocks fetch_user to raise an exception and verifies that the exception propagates from get_user_context
    CREATE a unit test that mocks fetch_org to raise an exception and verifies that the exception propagates from get_user_context
    CREATE a unit test that mocks fetch_permissions to raise an exception and verifies that the exception propagates from get_user_context
EXECUTE the test suite to confirm successful execution and correct error propagation
