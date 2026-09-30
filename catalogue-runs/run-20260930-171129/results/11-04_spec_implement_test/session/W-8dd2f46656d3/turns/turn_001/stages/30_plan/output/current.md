READ the input password string
IF length < 8 OR password contains only letters THEN SET strength to weak
ELSE IF length >= 8 AND length <= 12 AND password contains at least one letter AND password contains at least one digit THEN SET strength to medium
ELSE IF length > 12 AND password contains uppercase AND password contains lowercase AND password contains digits AND password contains at least one special character from !@#$%^&* THEN SET strength to strong
ENDIF
GENERATE a list of improvement suggestions based on the evaluated conditions:
- IF length < 8 THEN suggest increasing length to at least 8 characters
- IF password contains only letters THEN suggest adding digits
- IF length between 8 and 12 AND missing digits THEN suggest adding digits
- IF length > 12 AND missing uppercase THEN suggest adding uppercase letters
- IF length > 12 AND missing lowercase THEN suggest adding lowercase letters
- IF length > 12 AND missing digits THEN suggest adding digits
- IF length > 12 AND missing special character THEN suggest adding a special character from !@#$%^&*
RETURN the strength level and the generated suggestion list
