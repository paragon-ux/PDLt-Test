def check_password(password: str) -> dict:
    """Return password strength and improvement suggestions.
    Strength levels: 'weak', 'medium', 'strong'.
    """
    suggestions = []
    length = len(password)
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_letter = any(c.isalpha() for c in password)
    special_chars = set('!@#$%^&*')
    has_special = any(c in special_chars for c in password)
    only_letters = password.isalpha()

    if length < 8 or only_letters:
        strength = 'weak'
        if length < 8:
            suggestions.append('Increase length to at least 8 characters')
        if only_letters:
            suggestions.append('Include digits or symbols')
    elif 8 <= length <= 12 and has_letter and has_digit:
        strength = 'medium'
        if not has_upper:
            suggestions.append('Add uppercase letters')
        if not has_special:
            suggestions.append('Add special characters')
    elif length > 12 and has_upper and has_lower and has_digit and has_special:
        strength = 'strong'
    else:
        # Determine which criteria are missing to classify as medium or weak
        if length < 8 or not has_letter:
            strength = 'weak'
            if length < 8:
                suggestions.append('Increase length to at least 8 characters')
            if not has_letter:
                suggestions.append('Include letters')
        else:
            strength = 'medium'
            if not has_digit:
                suggestions.append('Add digits')
            if not has_upper:
                suggestions.append('Add uppercase letters')
            if not has_special:
                suggestions.append('Add special characters')
    return {'strength': strength, 'suggestions': suggestions}

# Example usage (can be removed in production)
if __name__ == '__main__':
    test_pw = 'Passw0rd!'
    result = check_password(test_pw)
    print(result)
