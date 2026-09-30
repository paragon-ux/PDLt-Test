READ the input password string
DETERMINE the password length
EVALUATE whether the password contains only letters
IF length < 8 OR only letters THEN CLASSIFY as 'weak' AND PREPARE suggestion list with "Increase length to at least 8 characters" and "Include digits or symbols"
ELSE IF length between 8 and 12 inclusive AND contains at least one letter AND at least one digit THEN CLASSIFY as 'medium' AND PREPARE suggestion list with "Add uppercase letters" and "Add special characters" if missing
ELSE IF length > 12 AND contains uppercase letters, lowercase letters, digits, AND at least one special character from !@#$%^&* THEN CLASSIFY as 'strong' AND PREPARE empty suggestion list
ELSE CLASSIFY as 'medium' OR 'weak' based on which criteria are unmet AND PREPARE appropriate improvement suggestions
RETURN the classification and the corresponding suggestion list
