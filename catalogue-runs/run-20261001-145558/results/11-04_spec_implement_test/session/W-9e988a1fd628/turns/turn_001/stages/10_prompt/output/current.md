READ the password string input
IF the password length is less than 8 OR the password contains only letters THEN SET strength level to "weak"
ELSE IF the password length is between 8 and 12 inclusive AND the password contains at least one letter AND at least one digit THEN SET strength level to "medium"
ELSE IF the password length is greater than 12 AND the password includes uppercase letters, lowercase letters, digits, AND at least one special character from !@#$%^&* THEN SET strength level to "strong"
GENERATE a list of improvement suggestions describing each unmet criterion for the determined strength level
RETURN the strength level and the suggestions list
