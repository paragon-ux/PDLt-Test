READ the password string input
DETERMINE the password length
CHECK if length is less than 8 OR contains only letters
IF condition true THEN SET strength level to "weak"
ELSE CHECK if length is between 8 and 12 inclusive AND contains at least one letter AND at least one digit
IF condition true THEN SET strength level to "medium"
ELSE CHECK if length is greater than 12 AND includes uppercase letters, lowercase letters, digits, AND at least one special character from !@#$%^&*
IF condition true THEN SET strength level to "strong"
IDENTIFY any unmet criteria for the determined strength level
GENERATE improvement suggestions describing each unmet criterion
RETURN the strength level and the suggestions list
