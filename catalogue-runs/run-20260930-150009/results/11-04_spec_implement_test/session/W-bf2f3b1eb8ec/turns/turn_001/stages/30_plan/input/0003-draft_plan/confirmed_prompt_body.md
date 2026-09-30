READ the input password string
IF the length of the password is less than 8 characters OR the password contains only letters THEN CLASSIFY the password as 'weak' AND RETURN a suggestion list including "Increase length to at least 8 characters" and "Include digits or symbols"
ELSE IF the length is between 8 and 12 characters inclusive AND the password contains at least one letter AND at least one digit THEN CLASSIFY the password as 'medium' AND RETURN a suggestion list including "Add uppercase letters" and "Add special characters" if they are missing
ELSE IF the length is greater than 12 characters AND the password contains uppercase letters, lowercase letters, digits, AND at least one special character from !@#$%^&* THEN CLASSIFY the password as 'strong' AND RETURN an empty suggestion list
ELSE CLASSIFY the password as 'medium' OR 'weak' based on which criteria are unmet and RETURN appropriate improvement suggestions
