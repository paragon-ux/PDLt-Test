PARSE the supplied Node.js callback-hell code to extract the logical flow and error handling.
IDENTIFY the functions fetch_user, fetch_org, fetch_permissions, get_user_context.
DEFINE async Python equivalents for each identified function using async def and await.
IMPLEMENT fetch_user as an async function that:
    RETURN a dictionary with keys id, name, org_id, where name follows the pattern User_<user_id>.
    USE a try/except block to catch network errors and raise an exception with message "Network error".
IMPLEMENT fetch_org as an async function that:
    RETURN a dictionary with keys id, name, plan, where name follows the pattern Org_<org_id> and plan is "enterprise".
    USE a try/except block to catch errors and raise an exception with message "Org not found".
IMPLEMENT fetch_permissions as an async function that:
    RETURN a list containing the strings read, write, admin.
DEFINE get_user_context as an async function that:
    AWAIT fetch_user.
    AWAIT fetch_org.
    AWAIT fetch_permissions.
    COMPOSE a result dictionary with keys user, org, permissions.
    ALLOW any raised exceptions to propagate naturally.
CREATE asynchronous unit tests that:
    VERIFY the success path returns the expected user, org, and permissions data.
    VERIFY that a network error raised by fetch_user propagates as an exception.
    VERIFY that an org not found error raised by fetch_org propagates as an exception.
    VERIFY that an error raised by fetch_permissions propagates as an exception.
EXECUTE the defined tests using an appropriate asynchronous test runner.
