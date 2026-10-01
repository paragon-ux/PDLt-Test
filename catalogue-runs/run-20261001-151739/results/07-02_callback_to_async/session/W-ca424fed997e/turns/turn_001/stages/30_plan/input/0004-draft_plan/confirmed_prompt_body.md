VERBATIM ENTITIES: fetch_user, fetch_org, fetch_permissions, get_user_context, user_id, org_id, on_success, on_error, final_callback, User_, Org_, Network error, Org not found, enterprise, read, write, admin, permissions, async, await, tests
CONVERT the provided callback-hell Node.js-style code to clean async/await Python, preserving the exact same logical flow and error handling.
USE async def and await to define asynchronous functions.
IMPLEMENT try/except blocks to translate on_error callbacks into raised exceptions.
MAP each original function (fetch_user, fetch_org, fetch_permissions, get_user_context) to an equivalent Python async function that returns the same data structures.
ENSURE fetch_user returns a dictionary with keys id, name, org_id where name follows the pattern User_<user_id>. ON ERROR, raise an exception with message "Network error".
ENSURE fetch_org returns a dictionary with keys id, name, plan where name follows the pattern Org_<org_id> and plan is "enterprise". ON ERROR, raise an exception with message "Org not found".
ENSURE fetch_permissions returns a list containing the strings read, write, admin.
IMPLEMENT get_user_context to orchestrate the async calls and produce a final result dictionary containing keys user, org, permissions.
INCLUDE tests that verify the success path and error propagation for each async function, confirming that the final result contains the expected user, org, and permissions data.
