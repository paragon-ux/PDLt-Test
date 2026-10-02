BUILD a password strength checker
DEFINE classification criteria
    IF password length < 8 OR password contains only letters THEN classify as weak
    IF password length >= 8 AND password length <= 12 AND password contains at least one letter AND at least one digit THEN classify as medium
    IF password length > 12 AND password contains uppercase letters AND lowercase letters AND digits AND at least one special character from !@#$%^&* THEN classify as strong
FOR each evaluated password RETURN the strength level and a list of specific improvement suggestions
PRODUCE a complete implementation, including code and a test suite, that follows the above criteria
