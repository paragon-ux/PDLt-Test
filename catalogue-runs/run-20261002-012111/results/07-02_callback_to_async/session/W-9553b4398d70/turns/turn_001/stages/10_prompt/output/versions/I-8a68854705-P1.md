READ the callback-based Python code containing functions fetch_user, fetch_org, fetch_permissions, and get_user_context
CONVERT the code to an async/await Python version using async def for each function
USE await when calling fetch_user, fetch_org, and fetch_permissions within get_user_context
PRESERVE the original logical flow and error handling with try/except blocks capturing exceptions as e
ENSURE that any identifier such as id is correctly handled in the async version
PROPAGATE any exceptions raised by fetch_user, fetch_org, fetch_permissions, or get_user_context to the caller
CREATE unit tests that verify successful execution of get_user_context with correct user, org, and permissions data
CREATE unit tests that verify error propagation when fetch_user raises an exception
CREATE unit tests that verify error propagation when fetch_org raises an exception
CREATE unit tests that verify error propagation when fetch_permissions raises an exception
USE a testing framework such as unittest or pytest for the tests
