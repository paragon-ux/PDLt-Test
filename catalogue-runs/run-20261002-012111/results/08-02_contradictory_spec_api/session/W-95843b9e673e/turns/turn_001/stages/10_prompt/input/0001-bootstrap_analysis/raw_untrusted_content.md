The following API specification contains contradictions. Identify each contradiction and propose a resolution.

1. POST /users creates a new user. The response is 201 Created with the user object.
2. POST /users returns 200 OK on success.
3. User email must be unique. If a duplicate email is submitted, return 409 Conflict.
4. If a duplicate email is submitted, silently merge with the existing account and return the merged user.
5. All endpoints require authentication via Bearer token.
6. POST /users is a public registration endpoint and requires no authentication.
7. User IDs are auto-incrementing integers starting from 1.
8. User IDs are UUIDs generated client-side and included in the POST body.
